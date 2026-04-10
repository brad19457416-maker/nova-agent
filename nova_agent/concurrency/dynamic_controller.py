"""
Dynamic Concurrency Controller - 动态并发控制器

根据执行结果动态调整并发数：
- 成功多了 → 增加并发
- 失败多了 → 减少并发
- 指数退避避免雪崩
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class DynamicConcurrencyController:
    """动态并发控制器

    根据执行结果动态调整并发数：
    - 成功多了 → 增加并发
    - 失败多了 → 减少并发
    - 指数退避避免雪崩
    """

    def __init__(
        self,
        min_concurrency: int = 1,
        max_concurrency: int = 8,
        initial_concurrency: int = None,
        step_up: float = 1.0,
        step_down: float = 0.5,
        backoff_base: float = 2.0,
    ):
        """
        初始化

        Args:
            min_concurrency: 最小并发数
            max_concurrency: 最大并发数
            initial_concurrency: 初始并发数，默认是 min
            step_up: 成功后增加幅度
            step_down: 失败后减少幅度
            backoff_base: 指数退避底数
        """
        self.min_concurrency = min_concurrency
        self.max_concurrency = max_concurrency
        self.current = initial_concurrency if initial_concurrency else min_concurrency
        self.step_up = step_up
        self.step_down = step_down
        self.backoff_base = backoff_base

        # 统计
        self.total_success = 0
        self.total_failure = 0
        self.consecutive_failures = 0

    def get_current_concurrency(self) -> int:
        """获取当前并发数"""
        return int(round(self.current))

    def on_success(self) -> None:
        """成功后回调"""
        self.total_success += 1
        self.consecutive_failures = 0
        if self.current < self.max_concurrency:
            self.current += self.step_up
            if self.current > self.max_concurrency:
                self.current = self.max_concurrency
            logger.debug(f"Increased concurrency to {self.current}")

    def on_failure(self) -> None:
        """失败后回调"""
        self.total_failure += 1
        self.consecutive_failures += 1
        if self.current > self.min_concurrency:
            # 连续失败使用指数退避
            if self.consecutive_failures > 1:
                backoff = self.backoff_base ** (self.consecutive_failures - 1)
                self.current -= self.step_down * backoff
            else:
                self.current -= self.step_down
            if self.current < self.min_concurrency:
                self.current = self.min_concurrency
            logger.debug(
                f"Decreased concurrency to {self.current} (consecutive failures: {self.consecutive_failures})"
            )

    def get_stats(self) -> Dict[str, Any]:
        """获取统计"""
        total = self.total_success + self.total_failure
        success_rate = self.total_success / total if total > 0 else 0

        return {
            "current_concurrency": self.get_current_concurrency(),
            "total_success": self.total_success,
            "total_failure": self.total_failure,
            "consecutive_failures": self.consecutive_failures,
            "success_rate": success_rate,
        }
