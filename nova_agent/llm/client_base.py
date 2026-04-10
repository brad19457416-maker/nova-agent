"""
LLM Client Base - LLM 客户端抽象基类

支持多种后端，可插拔替换。
"""

from typing import str
from abc import ABC, abstractmethod


class LLMClient(ABC):
    """LLM 客户端抽象基类"""
    
    @abstractmethod
    def complete(self, prompt: str, **kwargs) -> str:
        """
        完成提示，生成响应
        
        Args:
            prompt: 输入提示
            **kwargs: 额外参数
        
        Returns:
            生成的文本响应
        """
        pass
    
    @abstractmethod
    def chat(self, messages: list, **kwargs) -> str:
        """
        聊天对话
        
        Args:
            messages: 消息列表，每个元素是 {"role": "...", "content": "..."}
            **kwargs: 额外参数
        
        Returns:
            生成的文本响应
        """
        pass
