"""
Gated Residual Aggregator - 门控残差聚合器

对多个块的结果进行门控聚合，计算信息增益，
过滤掉增益低的冗余信息。
"""

from typing import Dict, Any, List, Tuple
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class AggregationResult:
    """聚合结果"""
    aggregated_text: str
    gain: float
    num_input_blocks: int
    gate_scores: List[float]


class GatedResidualAggregator:
    """
    门控残差聚合器
    
    为每个输入块计算门控分数（信息增益），
    只保留有信息增益的残差，过滤冗余。
    """
    
    def __init__(self, enable_json_compression: bool = True):
        self.enable_json_compression = enable_json_compression
    
    def aggregate(self, blocks: List[Dict], level: int, context: Dict) -> AggregationResult:
        """
        聚合多个块的结果
        
        Args:
            blocks: 输入块列表，每个包含 description 和 result
            level: 当前层级
            context: 上下文
        
        Returns:
            聚合结果，包含信息增益
        """
        # 提取所有块结果
        block_results = []
        for block in blocks:
            result_text = block.get("result", "")
            if not result_text and "final_response" in block:
                result_text = block["final_response"]
            
            block_results.append({
                "description": block.get("description", ""),
                "result": result_text,
                "gain": 0.0
            })
        
        # 计算每个块的门控分数（信息增益）
        gate_scores = self._calculate_gate_scores(block_results, context)
        
        # 只保留门控分数大于阈值的块
        filtered_blocks = [
            (br, gs) for br, gs in zip(block_results, gate_scores)
            if gs > 0.05  # 最小增益阈值
        ]
        
        # 计算总增益
        total_gain = sum(gs for _, gs in filtered_blocks)
        
        # 聚合文本
        aggregated_text = self._generate_aggregated_text(
            [br for br, _ in filtered_blocks],
            context["query"] if "query" in context else ""
        )
        
        return AggregationResult(
            aggregated_text=aggregated_text,
            gain=total_gain,
            num_input_blocks=len(blocks),
            gate_scores=gate_scores
        )
    
    def _calculate_gate_scores(self, blocks: List[Dict], context: Dict) -> List[float]:
        """
        计算每个块的门控分数（信息增益）
        
        使用 LLM 判断每个块带来了多少新信息。
        """
        query = context.get("query", "")
        existing_info = context.get("existing_info", "")
        
        # 如果压缩启用，使用 JSON 输出压缩 token
        if self.enable_json_compression:
            prompt = f"""原始问题: {query}

现有信息: {existing_info[:500]}

请为每个子任务结果打分，分数表示这个结果带来的**新信息增益**：
0 = 没有新信息，完全冗余
0.5 = 有部分新信息
1.0 = 有显著新信息

子任务结果:
{self._format_blocks_for_scoring(blocks)}

请以 JSON 格式输出分数：{{"scores": [score1, score2, ...]}}
"""
        else:
            prompt = f"""原始问题: {query}

请给每个子任务的信息增益打分（0-1）：
{self._format_blocks_for_scoring(blocks)}

输出分数列表：
"""
        
        # 这里需要调用 LLM，实际调用由外层处理
        # 返回默认均分，实际计算注入 LLM
        scores = [0.5 for _ in blocks]
        
        # 如果有 LLM 客户端，实际计算
        if "llm_client" in context:
            try:
                response = context["llm_client"].complete(prompt)
                scores = self._parse_scores(response, len(blocks))
            except Exception as e:
                logger.warning(f"Failed to calculate gate scores: {e}")
        
        return scores
    
    def _format_blocks_for_scoring(self, blocks: List[Dict]) -> str:
        """格式化块供打分"""
        formatted = ""
        for i, block in enumerate(blocks):
            desc = block["description"]
            result = block["result"]
            formatted += f"{i+1}. [{desc}]: {result[:300]}\n"
        return formatted
    
    def _parse_scores(self, response: str, num_blocks: int) -> List[float]:
        """解析分数输出"""
        import json
        import re
        
        # 尝试 JSON
        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                if "scores" in data:
                    scores = [float(s) for s in data["scores"]]
                    while len(scores) < num_blocks:
                        scores.append(0.5)
                    return scores[:num_blocks]
        except:
            pass
        
        # 尝试逐行提取数字
        scores = []
        for line in response.split('\n'):
            matches = re.findall(r'[\d\.]+', line)
            for match in matches:
                try:
                    scores.append(float(match))
                except:
                    pass
                if len(scores) >= num_blocks:
                    break
            if len(scores) >= num_blocks:
                break
        
        while len(scores) < num_blocks:
            scores.append(0.5)
        
        return scores[:num_blocks]
    
    def _generate_aggregated_text(self, blocks: List[Dict], query: str) -> str:
        """生成聚合文本"""
        if len(blocks) == 1:
            # 只有一个块，直接返回
            return blocks[0]["result"]
        
        # 多个块聚合
        aggregated = f"针对问题「{query}」，聚合结果：\n\n"
        for i, block in enumerate(blocks):
            aggregated += f"### {block['description']}\n{block['result']}\n\n"
        
        return aggregated
