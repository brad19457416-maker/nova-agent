"""
搜索策略模块
提供多种搜索策略，适应不同场景
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from enum import Enum
import random


class SearchPattern(Enum):
    """搜索模式"""
    BREADTH_FIRST = "breadth_first"    # 广度优先 - 覆盖广
    DEPTH_FIRST = "depth_first"        # 深度优先 - 挖得深
    ADAPTIVE = "adaptive"              # 自适应 - 智能选择
    FOCUSED = "focused"                # 聚焦式 - 围绕核心
    EXPLORATORY = "exploratory"        # 探索式 - 发现新方向


@dataclass
class SearchResult:
    """搜索结果"""
    query: str
    content: str
    source: str
    relevance: float
    depth: int
    timestamp: str
    metadata: Dict[str, Any]


class SearchStrategy(ABC):
    """搜索策略基类"""
    
    @abstractmethod
    async def search(self, query: str, context: Optional[Dict] = None) -> List[SearchResult]:
        """执行搜索"""
        pass
    
    @abstractmethod
    def should_expand(self, result: SearchResult, current_depth: int) -> bool:
        """判断是否应展开"""
        pass


class BreadthFirstSearch(SearchStrategy):
    """
    广度优先搜索
    适合: 快速了解全貌，收集多方面信息
    特点: 覆盖广，但每个方向不深
    """
    
    def __init__(self, max_breadth: int = 10):
        self.max_breadth = max_breadth
    
    async def search(self, query: str, context: Optional[Dict] = None) -> List[SearchResult]:
        """执行广度搜索"""
        # 生成多个相关查询
        variations = self._generate_variations(query)
        
        results = []
        for var in variations[:self.max_breadth]:
            # 模拟搜索结果
            result = SearchResult(
                query=var,
                content=f"关于{var}的搜索结果...",
                source="search_engine",
                relevance=0.7,
                depth=0,
                timestamp="2024-01-01",
                metadata={}
            )
            results.append(result)
        
        return results
    
    def should_expand(self, result: SearchResult, current_depth: int) -> bool:
        """广度优先只展开第一层"""
        return current_depth < 1 and result.relevance > 0.6
    
    def _generate_variations(self, query: str) -> List[str]:
        """生成查询变体"""
        variations = [query]
        
        # 添加常见变体
        templates = [
            f"{query} 是什么",
            f"{query} 原理",
            f"{query} 应用",
            f"{query} 优缺点",
            f"{query} vs 其他",
        ]
        
        variations.extend(templates)
        return variations


class DepthFirstSearch(SearchStrategy):
    """
    深度优先搜索
    适合: 深入研究特定方向
    特点: 挖得深，可能错过其他方向
    """
    
    def __init__(self, max_depth: int = 5, min_relevance: float = 0.7):
        self.max_depth = max_depth
        self.min_relevance = min_relevance
    
    async def search(self, query: str, context: Optional[Dict] = None) -> List[SearchResult]:
        """执行深度搜索"""
        results = []
        
        # 获取该主题的详细资料
        detailed_queries = [
            f"{query} 详细介绍",
            f"{query} 技术细节",
            f"{query} 深入分析",
            f"{query} 案例研究",
        ]
        
        for q in detailed_queries:
            result = SearchResult(
                query=q,
                content=f"关于{q}的深度内容...",
                source="technical_docs",
                relevance=0.85,
                depth=0,
                timestamp="2024-01-01",
                metadata={}
            )
            results.append(result)
        
        return results
    
    def should_expand(self, result: SearchResult, current_depth: int) -> bool:
        """深度优先持续深入高相关度结果"""
        return (current_depth < self.max_depth and 
                result.relevance > self.min_relevance)


class AdaptiveSearch(SearchStrategy):
    """
    自适应搜索
    智能选择广度或深度，基于结果质量动态调整
    
    策略:
    - 初期广度探索
    - 发现高质量方向后深度挖掘
    - 遇到瓶颈时切换方向
    """
    
    def __init__(
        self,
        initial_breadth: int = 5,
        depth_threshold: float = 0.8,
        switch_threshold: int = 3
    ):
        self.initial_breadth = initial_breadth
        self.depth_threshold = depth_threshold
        self.switch_threshold = switch_threshold
        
        self.search_count = 0
        self.high_quality_directions = []
    
    async def search(self, query: str, context: Optional[Dict] = None) -> List[SearchResult]:
        """自适应搜索"""
        
        # 如果是初期阶段，广度探索
        if self.search_count < self.initial_breadth:
            return await self._breadth_search(query)
        
        # 如果有高质量方向，深度挖掘
        if self.high_quality_directions:
            direction = self.high_quality_directions.pop(0)
            return await self._depth_search(direction)
        
        # 否则继续广度
        return await self._breadth_search(query)
    
    async def _breadth_search(self, query: str) -> List[SearchResult]:
        """广度搜索阶段"""
        variations = [
            query,
            f"{query} 概述",
            f"{query} 最新进展",
            f"{query} 专家观点",
        ]
        
        results = []
        for var in variations:
            result = SearchResult(
                query=var,
                content=f"关于{var}的信息...",
                source="search",
                relevance=random.uniform(0.6, 0.9),
                depth=0,
                timestamp="2024-01-01",
                metadata={}
            )
            results.append(result)
            self.search_count += 1
        
        # 识别高质量方向
        for r in results:
            if r.relevance > self.depth_threshold:
                self.high_quality_directions.append(r.query)
        
        return results
    
    async def _depth_search(self, query: str) -> List[SearchResult]:
        """深度搜索阶段"""
        detailed = [
            f"{query} 详细分析",
            f"{query} 技术实现",
            f"{query} 深入研究",
        ]
        
        results = []
        for q in detailed:
            result = SearchResult(
                query=q,
                content=f"关于{q}的深度内容...",
                source="technical",
                relevance=0.85,
                depth=1,
                timestamp="2024-01-01",
                metadata={}
            )
            results.append(result)
        
        return results
    
    def should_expand(self, result: SearchResult, current_depth: int) -> bool:
        """基于结果质量决定是否展开"""
        if result.relevance > self.depth_threshold:
            return current_depth < 3  # 高质量结果最多深挖3层
        return current_depth < 1  # 普通结果只展开1层


class IterativeSearch:
    """
    迭代式搜索
    多轮迭代，每轮基于上一轮结果优化查询
    """
    
    def __init__(self, max_iterations: int = 5):
        self.max_iterations = max_iterations
        self.iteration = 0
        self.previous_results = []
    
    async def search_iterative(
        self,
        query: str,
        search_func,
        llm_client
    ) -> List[SearchResult]:
        """
        迭代式搜索
        
        Args:
            query: 初始查询
            search_func: 搜索函数
            llm_client: LLM客户端用于优化查询
        """
        all_results = []
        current_query = query
        
        for i in range(self.max_iterations):
            self.iteration = i
            
            # 执行搜索
            results = await search_func(current_query)
            all_results.extend(results)
            
            # 分析结果，生成下一轮查询
            if i < self.max_iterations - 1:
                current_query = await self._refine_query(
                    current_query,
                    results,
                    llm_client
                )
                
                # 如果查询没有变化，停止迭代
                if current_query == query:
                    break
        
        return all_results
    
    async def _refine_query(
        self,
        original_query: str,
        results: List[SearchResult],
        llm_client
    ) -> str:
        """基于结果优化查询"""
        if not results:
            return original_query
        
        # 提取关键发现
        findings = "\n".join([r.content[:200] for r in results[:3]])
        
        prompt = f"""基于以下搜索结果，生成一个更精确、更深入的查询。

原始查询: {original_query}

已发现的信息:
{findings}

请分析:
1. 还缺少哪些关键信息？
2. 哪些方向值得深入探索？
3. 如何优化查询以获得更详细的结果？

请输出优化后的查询（更具体、更深入）：

优化查询:"""

        try:
            refined = await llm_client.complete(prompt)
            refined = refined.strip()
            
            # 确保查询有变化
            if refined and len(refined) > 5 and refined != original_query:
                return refined
        except:
            pass
        
        return original_query


class QueryExpansion:
    """
    查询扩展
    基于语义和相关性生成扩展查询
    """
    
    def __init__(self, llm_client):
        self.llm = llm_client
    
    async def expand(
        self,
        query: str,
        num_expansions: int = 3,
        expansion_types: List[str] = None
    ) -> List[str]:
        """
        扩展查询
        
        Args:
            query: 原始查询
            num_expansions: 扩展数量
            expansion_types: 扩展类型 ["semantic", "temporal", "comparative", "causal"]
        
        Returns:
            扩展查询列表
        """
        expansion_types = expansion_types or ["semantic", "temporal", "causal"]
        
        expansions = []
        
        if "semantic" in expansion_types:
            # 语义扩展 - 同义词、相关概念
            semantic = await self._semantic_expand(query)
            expansions.extend(semantic)
        
        if "temporal" in expansion_types:
            # 时间扩展 - 历史、现状、未来
            temporal = await self._temporal_expand(query)
            expansions.extend(temporal)
        
        if "comparative" in expansion_types:
            # 对比扩展 - 与其他事物比较
            comparative = await self._comparative_expand(query)
            expansions.extend(comparative)
        
        if "causal" in expansion_types:
            # 因果扩展 - 原因、影响
            causal = await self._causal_expand(query)
            expansions.extend(causal)
        
        # 去重并限制数量
        unique = []
        seen = set()
        for exp in expansions:
            exp_lower = exp.lower()
            if exp_lower not in seen and exp_lower != query.lower():
                seen.add(exp_lower)
                unique.append(exp)
        
        return unique[:num_expansions]
    
    async def _semantic_expand(self, query: str) -> List[str]:
        """语义扩展"""
        prompt = f"""请为"{query}"生成语义相关的查询变体。

包括:
1. 同义词表达
2. 相关概念
3. 不同角度的表述

输出格式（每行一个）:
变体1
变体2
变体3

最多3个。"""
        
        try:
            response = await self.llm.complete(prompt)
            return [line.strip() for line in response.split('\n') if line.strip()]
        except:
            return []
    
    async def _temporal_expand(self, query: str) -> List[str]:
        """时间扩展"""
        return [
            f"{query} 历史发展",
            f"{query} 最新进展",
            f"{query} 未来趋势"
        ]
    
    async def _comparative_expand(self, query: str) -> List[str]:
        """对比扩展"""
        prompt = f"""请为"{query}"生成对比类查询。

格式:
- {query} vs [竞品/替代方案]
- {query} 与 [相关概念] 的区别

输出（每行一个）:"""
        
        try:
            response = await self.llm.complete(prompt)
            return [line.strip() for line in response.split('\n') if line.strip()]
        except:
            return []
    
    async def _causal_expand(self, query: str) -> List[str]:
        """因果扩展"""
        return [
            f"{query} 原因",
            f"{query} 影响",
            f"{query} 机制"
        ]
