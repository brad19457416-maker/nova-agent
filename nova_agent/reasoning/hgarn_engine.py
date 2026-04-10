"""
HGARN Engine - Hierarchical Gated Attention Residual Network Engine

我们独创的核心推理引擎：
- 层次化门控残差网络
- 双向注意力流（首创）
- 动态门控 + 置信度路由 + 累积增益早停
- JSON 压缩门控输出，减少 token
- 自适应侧抑制 + WTA 赢者通吃
- 工作记忆分区 + 7±2 激活容量限制
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import logging

from .gated_residual import GatedResidualAggregator
from .bidirectional_attn import BidirectionalAttentionFlow
from .confidence_routing import ConfidenceRouter
from .lateral_inhibition import AdaptiveLateralInhibition
from .wta import WTASelection
from ..llm.client_base import LLMClient

logger = logging.getLogger(__name__)


@dataclass
class ReasoningResult:
    """推理结果"""
    success: bool
    final_response: str
    needs_tools: bool = False
    tool_calls: Optional[List[Dict]] = None
    total_gain: float = 0.0
    confidence: float = 0.0
    tools_used: List[str] = None
    num_blocks: int = 0
    num_levels: int = 0


class HGARNEngine:
    """
    HGARN 推理引擎
    
    层次化门控注意力残差网络，我们的核心创新。
    """
    
    def __init__(self,
                 block_size: int = 8,
                 max_blocks_per_level: int = 2,
                 max_levels: int = 3,
                 enable_recursive_decomposition: bool = True,
                 max_recursion_depth: int = 3,
                 cumulative_gain_threshold: float = 2.5,
                 enable_vector_prefilter: bool = True,
                 vector_similarity_threshold: float = 0.3,
                 min_gate_for_continue: float = 0.15,
                 enable_reverse_activation: bool = True,
                 reverse_activation_gain_threshold: float = 0.3,
                 wta_max_activate: int = 7,
                 lateral_inhibition_enabled: bool = True):
        """
        初始化 HGARN 引擎
        
        Args:
            block_size: 每个块最大子任务数
            max_blocks_per_level: 每个层级最大块数
            max_levels: 最大层级数
            enable_recursive_decomposition: 是否允许递归分解
            max_recursion_depth: 最大递归深度
            cumulative_gain_threshold: 累积增益达到这个值提前停止
            enable_vector_prefilter: 是否开启向量预过滤
            vector_similarity_threshold: 向量相似度阈值
            min_gate_for_continue: 继续下一层级的最小门控分数
            enable_reverse_activation: 是否启用双向注意力流
            reverse_activation_gain_threshold: 反向激活增益阈值
            wta_max_activate: WTA 最大激活数 (7±2 认知法则)
            lateral_inhibition_enabled: 是否启用侧抑制
        """
        self.block_size = block_size
        self.max_blocks_per_level = max_blocks_per_level
        self.max_levels = max_levels
        self.enable_recursive_decomposition = enable_recursive_decomposition
        self.max_recursion_depth = max_recursion_depth
        self.cumulative_gain_threshold = cumulative_gain_threshold
        self.enable_vector_prefilter = enable_vector_prefilter
        self.vector_similarity_threshold = vector_similarity_threshold
        self.min_gate_for_continue = min_gate_for_continue
        self.enable_reverse_activation = enable_reverse_activation
        self.reverse_activation_gain_threshold = reverse_activation_gain_threshold
        self.wta_max_activate = wta_max_activate
        self.lateral_inhibition_enabled = lateral_inhibition_enabled
        
        # 初始化组件
        self.gated_aggregator = GatedResidualAggregator()
        self.bidirectional_attn = BidirectionalAttentionFlow(
            reverse_threshold=reverse_activation_gain_threshold
        )
        self.confidence_router = ConfidenceRouter(
            min_gate=min_gate_for_continue,
            cumulative_threshold=cumulative_gain_threshold
        )
        self.lateral_inhibition = AdaptiveLateralInhibition()
        self.wta = WTASelection(max_activate=wta_max_activate)
        
        # LLM 客户端（注入）
        self.llm_client: Optional[LLMClient] = None
    
    def set_llm_client(self, client: LLMClient):
        """设置 LLM 客户端"""
        self.llm_client = client
    
    def solve(self, context: Dict[str, Any], **kwargs) -> ReasoningResult:
        """
        求解问题
        
        Args:
            context: 上下文，包含 query 和检索到的记忆
            **kwargs: 额外参数
        
        Returns:
            推理结果
        """
        if self.llm_client is None:
            raise ValueError("LLM client not set, call set_llm_client first")
        
        # 1. 任务分解
        blocks = self._decompose_task(context["query"], context)
        logger.info(f"Task decomposed into {len(blocks)} blocks")
        
        # 2. 向量预过滤
        if self.enable_vector_prefilter and "relevant_memories" in context:
            blocks = self._prefilter_blocks(blocks, context["relevant_memories"])
        
        # 3. WTA 赢者通吃，限制激活区容量
        blocks = self.wta.select(blocks, context["query"])
        logger.info(f"After WTA: {len(blocks)} blocks remaining")
        
        # 4. 自适应侧抑制
        blocks = self.lateral_inhibition.inhibit(blocks, context["query"])
        
        # 5. 层次化门控聚合
        current_level = 1
        cumulative_gain = 0.0
        aggregated = blocks
        
        while current_level < self.max_levels and cumulative_gain < self.cumulative_gain_threshold:
            # 聚合当前层级块
            aggregation_result = self.gated_aggregator.aggregate(
                aggregated,
                level=current_level,
                context=context
            )
            
            # 计算信息增益
            gain = aggregation_result.gain
            cumulative_gain += gain
            
            # 置信度路由：决定是否继续下一层级
            if not self.confidence_router.should_continue(gain, cumulative_gain):
                logger.info(f"Stopping early at level {current_level}, cumulative_gain={cumulative_gain:.2f}")
                break
            
            # 双向注意力流：上层发现反向激活下层相关块
            if self.bidirectional_attn.is_enabled():
                new_blocks = self.bidirectional_attn.reverse_activate(
                    aggregation_result,
                    blocks,
                    context
                )
                if len(new_blocks) > len(aggregated):
                    logger.info(f"Reverse activation added {len(new_blocks) - len(aggregated)} new blocks")
                    aggregated = new_blocks
            
            aggregated = [aggregation_result]
            current_level += 1
        
        # 6. 生成最终响应
        final_response = self._generate_response(aggregated, context)
        
        # 7. 检查是否需要工具调用
        needs_tools, tool_calls = self._check_tool_calls(final_response)
        
        return ReasoningResult(
            success=True,
            final_response=final_response,
            needs_tools=needs_tools,
            tool_calls=tool_calls,
            total_gain=cumulative_gain,
            confidence=self._calculate_confidence(cumulative_gain, current_level),
            num_blocks=len(blocks),
            num_levels=current_level
        )
    
    def solve_with_tools(self, context: Dict[str, Any], 
                       tool_results: List[Dict], **kwargs) -> ReasoningResult:
        """工具调用后重新推理整合"""
        # 将工具结果加入上下文，重新推理
        context["tool_results"] = tool_results
        return self.solve(context, **kwargs)
    
    def _decompose_task(self, query: str, context: Dict) -> List[Dict]:
        """任务分解为块"""
        # 使用 LLM 分解
        prompt = self._build_decomposition_prompt(query, context)
        response = self.llm_client.complete(prompt)
        
        # 解析分解结果
        blocks = self._parse_decomposition(response)
        return blocks
    
    def _build_decomposition_prompt(self, query: str, context: Dict) -> str:
        """构建分解提示"""
        prompt = f"""请将以下任务分解为可独立执行的子任务：

任务：{query}

分解规则：
1. 每个子任务应该是独立可执行的
2. 每个子任务目标明确
3. 不要超过 {self.block_size} 个子任务
4. 使用 JSON 格式输出：{{"blocks": [{{"id": "1", "description": "..."}}]}}
"""
        
        if "relevant_memories" in context and context["relevant_memories"]:
            prompt += "\n相关记忆可参考：\n"
            for i, mem in enumerate(context["relevant_memories"][:3]):
                prompt += f"{i+1}. {mem.get('content', '')[:200]}...\n"
        
        return prompt
    
    def _parse_decomposition(self, response: str) -> List[Dict]:
        """解析分解响应"""
        import json
        try:
            # 尝试提取 JSON
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                if "blocks" in data:
                    return data["blocks"]
            
            # 如果失败，简单分割
            lines = [line.strip() for line in response.split('\n') if line.strip()]
            blocks = []
            for i, line in enumerate(lines):
                if line and not line.startswith('#'):
                    clean = re.sub(r'^\d+[\.\)]\s*', '', line)
                    if clean:
                        blocks.append({
                            "id": str(i+1),
                            "description": clean
                        })
            return blocks
            
        except Exception as e:
            logger.error(f"Failed to parse decomposition: {e}")
            # 返回一个默认块
            return [{"id": "1", "description": "Solve the query: " + query}]
    
    def _prefilter_blocks(self, blocks: List[Dict], memories: List) -> List[Dict]:
        """向量预过滤，过滤掉不相关块"""
        # 简化实现，基于关键词重叠过滤
        filtered = []
        memory_texts = [m.get('content', '').lower() for m in memories]
        memory_words = set()
        for text in memory_texts:
            memory_words.update(text.split())
        
        for block in blocks:
            desc = block["description"].lower()
            block_words = set(desc.split())
            overlap = len(block_words & memory_words)
            if overlap > 0 or not memory_words:
                filtered.append(block)
        
        return filtered if filtered else blocks
    
    def _generate_response(self, aggregated: List[Dict], context: Dict) -> str:
        """生成最终响应"""
        if len(aggregated) == 1 and "aggregated_text" in aggregated[0]:
            # 已经聚合
            return aggregated[0]["aggregated_text"]
        
        # 多个结果需要聚合
        prompt = self._build_aggregation_prompt(aggregated, context)
        response = self.llm_client.complete(prompt)
        return response
    
    def _build_aggregation_prompt(self, aggregated: List[Dict], context: Dict) -> str:
        """构建聚合提示"""
        prompt = f"""请聚合以下子任务结果，生成针对原始问题的完整回答：

原始问题：{context['query']}

子任务结果：
"""
        for i, block in enumerate(aggregated, 1):
            desc = block.get('description', 'Result')
            result = block.get('result', 'No result')
            prompt += f"\n--- 子任务 {i}: {desc} ---\n{result[:800]}\n"
        
        prompt += f"""
请生成完整连贯的最终回答：
"""
        return prompt
    
    def _check_tool_calls(self, response: str) -> Tuple[bool, Optional[List[Dict]]]:
        """检查是否需要工具调用"""
        import re
        import json
        
        # 查找 JSON 格式的工具调用
        tool_call_pattern = r'\[.*tool_call.*\]'
        matches = re.findall(r'\{.*"plugin_name".*}', response, re.DOTALL)
        
        if not matches:
            return False, None
        
        tool_calls = []
        for match in matches:
            try:
                call = json.loads(match)
                if "plugin_name" in call:
                    tool_calls.append(call)
            except:
                continue
        
        return len(tool_calls) > 0, tool_calls if tool_calls else None
    
    def _calculate_confidence(self, cumulative_gain: float, num_levels: int) -> float:
        """计算整体置信度"""
        # 累积增益越高越置信
        base = min(cumulative_gain / self.cumulative_gain_threshold, 1.0)
        # 层级越深，处理越充分，置信度略高
        level_bonus = num_levels / self.max_levels * 0.1
        return min(base + level_bonus, 1.0)
