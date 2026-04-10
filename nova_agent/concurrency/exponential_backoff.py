"""
Exponential Backoff - 指数退避

重试失败请求时使用指数退避，避免雪崩。
"""

import time
import random
from typing import Callable, Any


class ExponentialBackoff:
    """指数退避重试"""
    
    def __init__(self, base_delay: float = 1.0, 
               max_delay: float = 60.0,
               factor: float = 2.0,
               jitter: bool = True):
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.factor = factor
        self.jitter = jitter
    
    def get_delay(self, attempt: int) -> float:
        """获取本次重试延迟"""
        delay = self.base_delay * (self.factor ** attempt)
        
        if delay > self.max_delay:
            delay = self.max_delay
        
        if self.jitter:
            # 添加随机抖动，避免惊群
            delay = delay * (0.5 + random.random())
        
        return delay
    
    def wait(self, attempt: int) -> None:
        """等待"""
        delay = self.get_delay(attempt)
        time.sleep(delay)
    
    def retry(self, func: Callable, max_attempts: int = 5, 
             *args, **kwargs) -> Any:
        """
        重试执行函数
        
        Args:
            func: 要执行的函数
            max_attempts: 最大重试次数
            *args: 函数参数
            **kwargs: 函数关键字参数
        
        Returns:
            函数结果
        
        Raises:
            最后一次异常，如果所有重试都失败
        """
        last_exception = None
        
        for attempt in range(max_attempts):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < max_attempts - 1:
                    self.wait(attempt)
        
        raise last_exception
