"""
Confidence Router - 置信度路由

根据门控分数和累积增益决定是否继续下一层级处理，
达到阈值提前停止，节省 token。
"""

from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


class ConfidenceRouter:
    """
    置信度路由
    
    决定是否需要继续下一层级处理：
    - 如果单块增益 < 最小值，停止
    - 如果累积增益 >= 阈值，停止（已经足够好）
    """
    
    def __init__(self, min_gate: float = 0.15, 
               cumulative_threshold: float = 2.5):
        self.min_gate = min_gate
        self.cumulative_threshold = cumulative_threshold
    
    def should_continue(self, current_gain: float, cumulative_gain: float) -> bool:
        """
        决定是否应该继续下一层级
        
        Args:
            current_gain: 当前层级增益
            cumulative_gain: 累积总增益
        
        Returns:
            True = 继续，False = 停止
        """
        # 如果当前增益太小，停止
        if current_gain < self.min_gate:
            logger.debug(f"Stopping: current_gain {current_gain:.3f} < {self.min_gate}")
            return False
        
        # 如果累积增益达到阈值，停止（已经足够好）
        if cumulative_gain >= self.cumulative_threshold:
            logger.debug(f"Stopping: cumulative_gain {cumulative_gain:.3f} >= {self.cumulative_threshold}")
            return False
        
        return True
    
    def filter_by_confidence(self, blocks: List[Dict], 
                           min_confidence: float = 0.3) -> List[Dict]:
        """过滤掉置信度低于阈值的块"""
        filtered = [
            b for b in blocks
            if b.get('confidence', 0.5) >= min_confidence
        ]
        logger.debug(f"Confidence filtering: {len(blocks)} → {len(filtered)}")
        return filtered
