"""
StrategyOptimizer - 策略优化器

根据评估结果优化策略，调整参数和提示词。
"""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class StrategyOptimizer:
    """
    策略优化器

    根据反馈优化参数和提示策略。
    """

    def __init__(self):
        self.strategy_history: List[Dict] = []

    def optimize(self, evaluation, current_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        根据评估优化配置

        Args:
            evaluation: 评估结果
            current_config: 当前配置

        Returns:
            优化后的配置
        """
        new_config = current_config.copy()

        quality = evaluation.quality_score

        # 如果质量很低，调整参数
        if quality < 0.3:
            # 需要更深层次推理
            new_config["max_levels"] = current_config.get("max_levels", 3) + 1
            new_config["cumulative_gain_threshold"] = (
                current_config.get("cumulative_gain_threshold", 2.5) + 0.5
            )
            logger.info("Low quality, increased max_levels and cumulative threshold")

        elif quality > 0.9:
            # 很好，可以尝试提前停止，节省 token
            new_config["max_levels"] = max(current_config.get("max_levels", 3) - 1, 2)
            new_config["cumulative_gain_threshold"] = max(
                current_config.get("cumulative_gain_threshold", 2.5) - 0.3, 1.0
            )
            logger.info("High quality, decreased max_levels for efficiency")

        # 记录历史
        self.strategy_history.append(
            {
                "before": current_config,
                "after": new_config,
                "quality": quality,
                "timestamp": self._get_timestamp(),
            }
        )

        return new_config

    def ab_test(self, strategy_a: Dict, strategy_b: Dict, query: str, evaluation) -> Dict:
        """A/B 测试两种策略"""
        winner = strategy_a if evaluation["a"] > evaluation["b"] else strategy_b
        loser = strategy_b if winner is strategy_a else strategy_a

        logger.info(f"A/B test: {winner['name']} won over {loser['name']}")

        return {"winner": winner, "loser": loser, "evaluation": evaluation}

    def get_history(self) -> List[Dict]:
        """获取优化历史"""
        return self.strategy_history

    def _get_timestamp(self) -> str:
        from datetime import datetime

        return datetime.utcnow().isoformat()
