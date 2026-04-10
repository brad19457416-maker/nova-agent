"""
LLM 客户端抽象层
支持 OpenClaw 和其他 LLM 提供商
"""

import requests
import json
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Generator
from dataclasses import dataclass
import time


@dataclass
class LLMResponse:
    """LLM响应封装"""
    content: str
    usage: Dict[str, int]
    latency_ms: float
    model: str
    finish_reason: str = "stop"


@dataclass
class LLMMessage:
    """消息封装"""
    role: str  # system, user, assistant
    content: str


class LLMClient(ABC):
    """LLM客户端抽象基类"""
    
    @abstractmethod
    def chat(self, messages: List[LLMMessage], **kwargs) -> LLMResponse:
        """非流式聊天"""
        pass
    
    @abstractmethod
    def chat_stream(self, messages: List[LLMMessage], **kwargs) -> Generator[str, None, None]:
        """流式聊天"""
        pass
    
    def complete(self, prompt: str, **kwargs) -> str:
        """简单完成接口"""
        messages = [LLMMessage(role="user", content=prompt)]
        response = self.chat(messages, **kwargs)
        return response.content


class OpenClawLLMClient(LLMClient):
    """
    OpenClaw LLM 客户端
    直接调用本地Ollama或其他兼容OpenAI API的端点
    """
    
    def __init__(
        self,
        model: str = "qwen2.5:7b",
        base_url: str = "http://localhost:11434",
        api_key: Optional[str] = None,
        timeout: int = 120
    ):
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        
    def _build_messages(self, messages: List[LLMMessage]) -> List[Dict[str, str]]:
        """构建消息格式"""
        return [{"role": m.role, "content": m.content} for m in messages]
    
    def chat(self, messages: List[LLMMessage], **kwargs) -> LLMResponse:
        """调用LLM"""
        start_time = time.time()
        
        url = f"{self.base_url}/api/chat"
        
        payload = {
            "model": self.model,
            "messages": self._build_messages(messages),
            "stream": False,
            "options": {
                "temperature": kwargs.get("temperature", 0.7),
                "num_predict": kwargs.get("max_tokens", 2000)
            }
        }
        
        try:
            response = requests.post(
                url,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            
            latency_ms = (time.time() - start_time) * 1000
            
            return LLMResponse(
                content=data.get("message", {}).get("content", ""),
                usage={"prompt_tokens": 0, "completion_tokens": 0},  # Ollama不提供
                latency_ms=latency_ms,
                model=self.model
            )
            
        except Exception as e:
            raise RuntimeError(f"LLM调用失败: {e}")
    
    def chat_stream(self, messages: List[LLMMessage], **kwargs) -> Generator[str, None, None]:
        """流式调用"""
        url = f"{self.base_url}/api/chat"
        
        payload = {
            "model": self.model,
            "messages": self._build_messages(messages),
            "stream": True,
            "options": {
                "temperature": kwargs.get("temperature", 0.7),
                "num_predict": kwargs.get("max_tokens", 2000)
            }
        }
        
        try:
            response = requests.post(
                url,
                json=payload,
                stream=True,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        if "message" in data and "content" in data["message"]:
                            yield data["message"]["content"]
                    except json.JSONDecodeError:
                        continue
                        
        except Exception as e:
            raise RuntimeError(f"流式LLM调用失败: {e}")


class SimpleMockLLMClient(LLMClient):
    """
    模拟LLM客户端，用于测试
    """
    
    def chat(self, messages: List[LLMMessage], **kwargs) -> LLMResponse:
        """返回模拟响应"""
        last_message = messages[-1].content if messages else ""
        
        # 简单的规则匹配模拟
        if "总结" in last_message or "概括" in last_message:
            content = "这是对输入内容的简要概括..."
        elif "分析" in last_message:
            content = "1. 第一要点\n2. 第二要点\n3. 第三要点"
        else:
            content = f"收到你的消息：{last_message[:50]}..."
        
        return LLMResponse(
            content=content,
            usage={"prompt_tokens": 100, "completion_tokens": 50},
            latency_ms=100,
            model="mock"
        )
    
    def chat_stream(self, messages: List[LLMMessage], **kwargs) -> Generator[str, None, None]:
        """模拟流式响应"""
        response = self.chat(messages, **kwargs)
        words = response.content.split()
        for word in words:
            yield word + " "
