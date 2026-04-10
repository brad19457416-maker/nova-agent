"""
深度研究引擎
解决Agent调研策略死板、不会关联展开、不深入挖掘的问题
"""

import time
import uuid
from typing import List, Dict, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json


class ResearchPhase(Enum):
    """研究阶段"""
    PLANNING = "planning"           # 规划
    EXPLORATION = "exploration"     # 探索
    DEEP_DIVE = "deep_dive"         # 深入挖掘
    SYNTHESIS = "synthesis"         # 综合
    VERIFICATION = "verification"   # 验证


@dataclass
class ResearchQuery:
    """研究查询"""
    id: str
    query: str
    parent_id: Optional[str] = None
    depth: int = 0
    priority: int = 1
    source: str = "initial"  # initial, expansion, extraction
    results: List[Dict] = field(default_factory=list)
    status: str = "pending"  # pending, processing, completed, failed


@dataclass
class ResearchFinding:
    """研究发现"""
    id: str
    content: str
    source: str
    confidence: float
    query_id: str
    entities: List[str] = field(default_factory=list)
    related_findings: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ResearchConfig:
    """研究配置"""
    max_depth: int = 3                    # 最大探索深度
    max_queries_per_depth: int = 5        # 每层最大查询数
    min_confidence: float = 0.6           # 最小置信度
    expansion_threshold: float = 0.7      # 展开阈值
    cross_validation: bool = True         # 交叉验证
    max_iterations: int = 10              # 最大迭代次数
    timeout: int = 300                    # 总超时时间


@dataclass
class ResearchResult:
    """研究结果"""
    query: str
    summary: str
    findings: List[ResearchFinding]
    knowledge_graph: Dict[str, Any]
    sources: List[str]
    confidence: float
    iterations: int
    duration: float


class DeepResearcher:
    """
    深度研究引擎
    
    核心特性:
    1. 迭代式探索 - 多轮深入，不满足表面结果
    2. 关联展开 - 从关键词生成相关查询
    3. 深度挖掘 - 自动识别需要深入的方向
    4. 交叉验证 - 多源验证信息准确性
    5. 知识图谱 - 结构化存储研究发现
    """
    
    def __init__(
        self,
        llm_client,
        search_tool: Optional[Callable] = None,
        config: Optional[ResearchConfig] = None
    ):
        self.llm = llm_client
        self.search_tool = search_tool
        self.config = config or ResearchConfig()
        
        # 研究状态
        self.queries: Dict[str, ResearchQuery] = {}
        self.findings: Dict[str, ResearchFinding] = {}
        self.knowledge_graph: Dict[str, List[str]] = {}  # entity -> findings
        
    async def research(self, query: str, context: Optional[str] = None) -> ResearchResult:
        """
        执行深度研究
        
        Args:
            query: 研究主题/问题
            context: 额外上下文
        
        Returns:
            研究结果
        """
        start_time = time.time()
        
        # 1. 规划研究策略
        plan = await self._plan_research(query, context)
        
        # 2. 迭代探索
        iteration = 0
        while iteration < self.config.max_iterations:
            # 获取待处理的查询
            pending = self._get_pending_queries()
            if not pending:
                break
            
            # 执行查询
            for q in pending[:self.config.max_queries_per_depth]:
                await self._execute_query(q)
            
            # 生成扩展查询
            await self._generate_expansion_queries()
            
            iteration += 1
            
            # 检查是否超时
            if time.time() - start_time > self.config.timeout:
                break
        
        # 3. 交叉验证
        if self.config.cross_validation:
            await self._cross_validate()
        
        # 4. 综合结果
        summary = await self._synthesize_results(query)
        
        duration = time.time() - start_time
        
        return ResearchResult(
            query=query,
            summary=summary,
            findings=list(self.findings.values()),
            knowledge_graph=self.knowledge_graph,
            sources=list(set(f.source for f in self.findings.values())),
            confidence=self._calculate_overall_confidence(),
            iterations=iteration,
            duration=duration
        )
    
    async def _plan_research(self, query: str, context: Optional[str]) -> List[str]:
        """规划研究策略，生成初始查询列表"""
        prompt = f"""请为以下研究主题制定详细的调研策略。

研究主题: {query}

请分析:
1. 这个主题的核心概念是什么？
2. 需要调研哪些子方向？
3. 每个子方向应该搜索什么关键词？
4. 可能的信息来源有哪些？

请以JSON格式输出研究计划:
{{
    "core_concepts": ["概念1", "概念2"],
    "sub_directions": [
        {{
            "direction": "子方向名称",
            "keywords": ["关键词1", "关键词2"],
            "sources": ["可能来源"]
        }}
    ]
}}

输出JSON:"""

        try:
            response = await self.llm.complete(prompt)
            plan = json.loads(response)
            
            # 创建初始查询
            initial_queries = []
            for sub in plan.get("sub_directions", []):
                for keyword in sub.get("keywords", []):
                    q = ResearchQuery(
                        id=str(uuid.uuid4())[:8],
                        query=keyword,
                        depth=0,
                        source="initial"
                    )
                    self.queries[q.id] = q
                    initial_queries.append(q)
            
            return initial_queries
            
        except Exception as e:
            # 如果解析失败，直接使用原始查询
            q = ResearchQuery(
                id=str(uuid.uuid4())[:8],
                query=query,
                depth=0,
                source="initial"
            )
            self.queries[q.id] = q
            return [q]
    
    async def _execute_query(self, query: ResearchQuery):
        """执行单个查询"""
        query.status = "processing"
        
        if not self.search_tool:
            query.status = "failed"
            return
        
        try:
            # 执行搜索
            results = await self.search_tool(query.query)
            query.results = results
            
            # 提取发现
            for result in results:
                finding = ResearchFinding(
                    id=str(uuid.uuid4())[:8],
                    content=result.get("content", ""),
                    source=result.get("source", "unknown"),
                    confidence=result.get("confidence", 0.5),
                    query_id=query.id,
                    entities=result.get("entities", [])
                )
                self.findings[finding.id] = finding
                
                # 更新知识图谱
                for entity in finding.entities:
                    if entity not in self.knowledge_graph:
                        self.knowledge_graph[entity] = []
                    self.knowledge_graph[entity].append(finding.id)
            
            query.status = "completed"
            
        except Exception as e:
            query.status = "failed"
    
    async def _generate_expansion_queries(self):
        """生成扩展查询 - 关联展开的关键"""
        # 获取已完成的查询
        completed = [q for q in self.queries.values() if q.status == "completed"]
        
        for query in completed:
            if query.depth >= self.config.max_depth:
                continue
            
            # 分析结果，识别需要深入的方向
            prompt = f"""基于以下搜索结果，识别需要进一步调研的方向。

原始查询: {query.query}
搜索结果:
{self._format_results(query.results)}

请分析:
1. 这些结果中有哪些重要但不够深入的信息？
2. 有哪些相关概念需要进一步了解？
3. 有哪些矛盾或需要验证的信息？

请输出需要深入调研的方向（最多3个），格式:
方向1: [具体查询]
方向2: [具体查询]
方向3: [具体查询]

如果没有需要深入的方向，输出"无需深入"。

输出:"""

            try:
                response = await self.llm.complete(prompt)
                
                if "无需深入" not in response:
                    # 解析扩展方向
                    lines = response.strip().split('\n')
                    for line in lines[:3]:  # 最多3个扩展
                        if ':' in line or '：' in line:
                            direction = line.split(':', 1)[-1].split('：', 1)[-1].strip()
                            if direction and len(direction) > 3:
                                # 检查是否已存在类似查询
                                if not self._is_duplicate_query(direction):
                                    q = ResearchQuery(
                                        id=str(uuid.uuid4())[:8],
                                        query=direction,
                                        parent_id=query.id,
                                        depth=query.depth + 1,
                                        source="expansion",
                                        priority=2  # 扩展查询优先级较低
                                    )
                                    self.queries[q.id] = q
                                    
            except Exception as e:
                pass  # 扩展失败不影响主流程
    
    async def _cross_validate(self):
        """交叉验证 - 确保信息准确性"""
        # 按实体分组发现
        entity_findings: Dict[str, List[ResearchFinding]] = {}
        for finding in self.findings.values():
            for entity in finding.entities:
                if entity not in entity_findings:
                    entity_findings[entity] = []
                entity_findings[entity].append(finding)
        
        # 对有多来源的实体进行验证
        for entity, findings in entity_findings.items():
            if len(findings) < 2:
                continue
            
            sources = set(f.source for f in findings)
            if len(sources) < 2:
                continue  # 只有一个来源，无法交叉验证
            
            # 检查一致性
            contents = [f.content for f in findings]
            prompt = f"""请判断以下关于"{entity}"的信息是否一致。

信息来源:
{chr(10).join(f"来源{i+1}: {content[:200]}..." for i, content in enumerate(contents))}

请分析:
1. 这些信息是否相互印证？
2. 是否有矛盾之处？
3. 整体可信度如何？

以JSON格式输出:
{{
    "consistent": true/false,
    "confidence": 0-1,
    "notes": "分析说明"
}}

输出JSON:"""

            try:
                response = await self.llm.complete(prompt)
                validation = json.loads(response)
                
                # 更新发现的置信度
                confidence = validation.get("confidence", 0.5)
                for finding in findings:
                    finding.confidence = (finding.confidence + confidence) / 2
                    
            except Exception as e:
                pass
    
    async def _synthesize_results(self, original_query: str) -> str:
        """综合所有发现，生成最终报告"""
        # 按置信度排序
        sorted_findings = sorted(
            self.findings.values(),
            key=lambda f: f.confidence,
            reverse=True
        )
        
        # 只使用高置信度的发现
        high_confidence = [f for f in sorted_findings if f.confidence >= self.config.min_confidence]
        
        if not high_confidence:
            high_confidence = sorted_findings[:10]  # 至少使用前10个
        
        findings_text = "\n\n".join([
            f"[置信度{f.confidence:.2f}] {f.content[:300]}..."
            for f in high_confidence[:20]  # 最多20个发现
        ])
        
        prompt = f"""请基于以下研究发现，撰写一份综合调研报告。

原始问题: {original_query}

研究发现:
{findings_text}

知识图谱实体: {list(self.knowledge_graph.keys())[:10]}

请撰写报告，包括:
1. 核心发现总结（3-5个要点）
2. 关键概念解释
3. 不同观点的对比（如有）
4. 信息来源说明
5. 置信度评估

报告:"""

        try:
            summary = await self.llm.complete(prompt)
            return summary
        except Exception as e:
            return f"研究完成，但综合报告生成失败: {e}"
    
    def _get_pending_queries(self) -> List[ResearchQuery]:
        """获取待处理的查询"""
        return [
            q for q in self.queries.values()
            if q.status == "pending" and q.depth < self.config.max_depth
        ]
    
    def _is_duplicate_query(self, query_str: str) -> bool:
        """检查是否已有类似查询"""
        query_lower = query_str.lower()
        for q in self.queries.values():
            if query_lower in q.query.lower() or q.query.lower() in query_lower:
                return True
        return False
    
    def _format_results(self, results: List[Dict]) -> str:
        """格式化搜索结果"""
        if not results:
            return "无结果"
        return "\n\n".join([
            f"结果{i+1}:\n{r.get('content', '')[:300]}..."
            for i, r in enumerate(results[:5])
        ])
    
    def _calculate_overall_confidence(self) -> float:
        """计算整体置信度"""
        if not self.findings:
            return 0.0
        return sum(f.confidence for f in self.findings.values()) / len(self.findings)
    
    def get_research_tree(self) -> Dict:
        """获取研究树结构"""
        tree = {
            "total_queries": len(self.queries),
            "completed_queries": len([q for q in self.queries.values() if q.status == "completed"]),
            "total_findings": len(self.findings),
            "knowledge_graph_size": len(self.knowledge_graph),
            "query_tree": []
        }
        
        # 构建查询树
        root_queries = [q for q in self.queries.values() if q.parent_id is None]
        for root in root_queries:
            tree["query_tree"].append(self._build_query_subtree(root))
        
        return tree
    
    def _build_query_subtree(self, query: ResearchQuery) -> Dict:
        """构建查询子树"""
        children = [q for q in self.queries.values() if q.parent_id == query.id]
        return {
            "query": query.query,
            "depth": query.depth,
            "status": query.status,
            "findings_count": len([f for f in self.findings.values() if f.query_id == query.id]),
            "children": [self._build_query_subtree(child) for child in children]
        }
