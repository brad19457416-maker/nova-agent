"""
Evaluator - 效果评估器

评估每次响应的质量，收集用户反馈，
为后续优化提供依据。
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class Evaluation:
    """评估结果"""
    rating: int  # 1-5
    quality_score: float  # 0-1
    should_learn: bool  # 是否应该学习这个案例
    comment: str = ""


class Evaluator:
    """
    效果评估器
    
    收集显式和隐式反馈，评估响应质量。
    """
    
    def __init__(self):
        pass
    
    def evaluate(self, query: str, response: str, 
               rating: Optional[int] = None,
               comment: str = "") -> Evaluation:
        """
        评估响应质量
        
        Args:
            query: 用户查询
            response: Agent 响应
            rating: 显式评分 1-5，如果有
            comment: 用户评论
        
        Returns:
            评估结果
        """
        # 有显式评分直接使用
        if rating is not None:
            quality_score = rating / 5.0
            
            # 如果评分 >= 4，应该学习
            should_learn = rating >= 4
            
            return Evaluation(
                rating=rating,
                quality_score=quality_score,
                should_learn=should_learn,
                comment=comment
            )
        
        # 隐式反馈评估（TODO：基于后续交互判断）
        # 暂时默认中等评分
        return Evaluation(
            rating=3,
            quality_score=0.6,
            should_learn=False,
            comment=comment or "No explicit feedback"
        )
    
    def evaluate_task_result(self, task_result: Dict[str, Any]) -> float:
        """评估任务执行结果，返回成功率分数"""
        if not task_result.get("success", True):
            return 0.0
        
        # 检查是否有错误
        if "error" in task_result and task_result["error"]:
            return 0.5
        
        return 1.0
    
    def is_good_enough(self, evaluation: Evaluation) -> bool:
        """判断结果是否足够好，不需要优化"""
        return evaluation.quality_score >= 0.8
