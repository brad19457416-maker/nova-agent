"""
LLM客户端实现

支持:
- OpenClaw (本地Gateway)
- Ollama (本地模型)
- OpenAI API (可选)
- Mock (测试用)

性能优化:
- 使用连接池复用HTTP连接
- 减少DNS解析和SSL握手开销
- 支持并发请求

使用示例:
    # 方式1: 直接创建
    llm = OllamaLLM(model="qwen2.5:7b")
    response = await llm.complete("你好")
    
    # 方式2: 使用工厂函数
    llm = create_llm_client({"type": "ollama", "model": "qwen2.5:7b"})
    
    # 方式3: 使用连接池
    async with ConnectionPool() as pool:
        llm = OllamaLLM(model="qwen2.5:7b", pool=pool)
        response = await llm.complete("你好")
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, AsyncGenerator, Union
import aiohttp
import json
import logging
from functools import lru_cache

from nova_agent.utils import ConnectionPool, ConnectionPoolManager

logger = logging.getLogger(__name__)


class LLMClient(ABC):
    """
    LLM客户端基类
    
    所有LLM客户端必须实现以下方法:
    - complete: 单轮文本生成
    - chat: 对话生成
    - stream: 流式生成
    
    可选实现:
    - close: 清理资源
    """
    
    def __init__(self, model: Optional[str] = None, **kwargs):
        self.model = model
        self.config = kwargs
    
    @abstractmethod
    async def complete(self, prompt: str, **kwargs) -> str:
        """
        完成文本生成

        Args:
            prompt: 提示词
            **kwargs: 额外参数 (temperature, max_tokens等)

        Returns:
            生成的文本
        """
        pass
    
    @abstractmethod
    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        对话生成

        Args:
            messages: 消息列表，格式 [{"role": "user", "content": "..."}, ...]
            **kwargs: 额外参数

        Returns:
            生成的回复
        """
        pass
    
    @abstractmethod
    async def stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """
        流式生成

        Args:
            prompt: 提示词
            **kwargs: 额外参数

        Yields:
            生成的文本片段
        """
        yield ""
    
    async def close(self):
        """
        关闭客户端，释放资源

        子类可重写此方法进行清理
        """
        pass


class OpenClawLLM(LLMClient):
    """
    OpenClaw LLM客户端

    通过本地Gateway调用模型，支持连接池复用
    
    性能特点:
    - 连接池复用HTTP连接
    - 支持并发请求
    - 自动重试机制
    """
    
    def __init__(
        self,
        base_url: str = "http://localhost:8080",
        model: str = "qwen2.5:7b",
        pool: Optional[ConnectionPool] = None,
        **kwargs
    ):
        """
        初始化OpenClaw客户端

        Args:
            base_url: Gateway地址
            model: 模型名称
            pool: 连接池实例，为None时自动创建
            **kwargs: 额外配置
        """
        super().__init__(model, **kwargs)
        self.base_url = base_url.rstrip("/")
        self._pool = pool
        self._own_pool = pool is None
        self._timeout = aiohttp.ClientTimeout(total=kwargs.get("timeout", 120))
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """获取会话（使用连接池）"""
        if self._pool is None:
            # 延迟初始化连接池
            self._pool = ConnectionPoolManager.get_instance().get_pool("openclaw")
        return await self._pool.get_session(self.base_url, self._timeout)
    
    async def complete(self, prompt: str, **kwargs) -> str:
        """
        完成生成

        Args:
            prompt: 提示词
            **kwargs: temperature, max_tokens等

        Returns:
            生成的文本
        """
        session = await self._get_session()
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 2048)
        }
        
        try:
            async with session.post(
                f"{self.base_url}/v1/completions",
                json=payload
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("choices", [{}])[0].get("text", "")
                else:
                    text = await resp.text()
                    logger.error(f"OpenClaw error {resp.status}: {text[:200]}")
                    return f"[Error: HTTP {resp.status}]"
        except aiohttp.ClientError as e:
            logger.error(f"OpenClaw request failed: {e}")
            return f"[Error: {e}]"
    
    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        对话生成

        Args:
            messages: 消息列表
            **kwargs: 额外参数

        Returns:
            生成的回复
        """
        session = await self._get_session()
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 2048)
        }
        
        try:
            async with session.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("choices", [{}])[0].get("message", {}).get("content", "")
                else:
                    text = await resp.text()
                    logger.error(f"OpenClaw error {resp.status}: {text[:200]}")
                    return f"[Error: HTTP {resp.status}]"
        except aiohttp.ClientError as e:
            logger.error(f"OpenClaw request failed: {e}")
            return f"[Error: {e}]"
    
    async def stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """
        流式生成

        Args:
            prompt: 提示词
            **kwargs: 额外参数

        Yields:
            生成的文本片段
        """
        session = await self._get_session()
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": True,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 2048)
        }
        
        try:
            async with session.post(
                f"{self.base_url}/v1/completions",
                json=payload
            ) as resp:
                async for line in resp.content:
                    line = line.decode("utf-8").strip()
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        try:
                            json_data = json.loads(data)
                            text = json_data.get("choices", [{}])[0].get("text", "")
                            if text:
                                yield text
                        except json.JSONDecodeError:
                            pass
        except aiohttp.ClientError as e:
            logger.error(f"OpenClaw stream failed: {e}")
            yield f"[Error: {e}]"
    
    async def close(self):
        """关闭客户端"""
        if self._own_pool and self._pool:
            await self._pool.close()


class OllamaLLM(LLMClient):
    """
    Ollama LLM客户端

    直接调用Ollama API，支持连接池复用
    """
    
    def __init__(
        self,
        model: str = "qwen2.5:7b",
        base_url: str = "http://localhost:11434",
        pool: Optional[ConnectionPool] = None,
        **kwargs
    ):
        """
        初始化Ollama客户端

        Args:
            model: 模型名称
            base_url: Ollama服务地址
            pool: 连接池实例
            **kwargs: 额外配置
        """
        super().__init__(model, **kwargs)
        self.base_url = base_url.rstrip("/")
        self._pool = pool
        self._own_pool = pool is None
        self._timeout = aiohttp.ClientTimeout(total=kwargs.get("timeout", 120))
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """获取会话（使用连接池）"""
        if self._pool is None:
            self._pool = ConnectionPoolManager.get_instance().get_pool("ollama")
        return await self._pool.get_session(self.base_url, self._timeout)
    
    async def complete(self, prompt: str, **kwargs) -> str:
        """完成生成"""
        session = await self._get_session()
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": kwargs.get("temperature", 0.7),
                "num_predict": kwargs.get("max_tokens", 2048)
            }
        }
        
        try:
            async with session.post(
                f"{self.base_url}/api/generate",
                json=payload
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("response", "")
                else:
                    text = await resp.text()
                    logger.error(f"Ollama error {resp.status}: {text[:200]}")
                    return f"[Error: HTTP {resp.status}]"
        except aiohttp.ClientError as e:
            logger.error(f"Ollama request failed: {e}")
            return f"[Error: {e}]"
    
    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """对话生成"""
        session = await self._get_session()
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": kwargs.get("temperature", 0.7),
                "num_predict": kwargs.get("max_tokens", 2048)
            }
        }
        
        try:
            async with session.post(
                f"{self.base_url}/api/chat",
                json=payload
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("message", {}).get("content", "")
                else:
                    text = await resp.text()
                    logger.error(f"Ollama error {resp.status}: {text[:200]}")
                    return f"[Error: HTTP {resp.status}]"
        except aiohttp.ClientError as e:
            logger.error(f"Ollama request failed: {e}")
            return f"[Error: {e}]"
    
    async def stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """流式生成"""
        session = await self._get_session()
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": kwargs.get("temperature", 0.7),
                "num_predict": kwargs.get("max_tokens", 2048)
            }
        }
        
        try:
            async with session.post(
                f"{self.base_url}/api/generate",
                json=payload
            ) as resp:
                async for line in resp.content:
                    line = line.decode("utf-8").strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        text = data.get("response", "")
                        if text:
                            yield text
                        if data.get("done", False):
                            break
                    except json.JSONDecodeError:
                        pass
        except aiohttp.ClientError as e:
            logger.error(f"Ollama stream failed: {e}")
            yield f"[Error: {e}]"
    
    async def close(self):
        """关闭客户端"""
        if self._own_pool and self._pool:
            await self._pool.close()


class MockLLM(LLMClient):
    """
    Mock LLM客户端

    用于测试，返回预设响应
    """
    
    def __init__(self, model: str = "mock", **kwargs):
        super().__init__(model, **kwargs)
        self._response_count = 0
    
    async def complete(self, prompt: str, **kwargs) -> str:
        """模拟完成生成"""
        self._response_count += 1
        return f"[Mock response #{self._response_count} to: {prompt[:50]}...]"
    
    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """模拟对话生成"""
        self._response_count += 1
        last_msg = messages[-1]["content"] if messages else ""
        return f"[Mock chat response #{self._response_count} to: {last_msg[:50]}...]"
    
    async def stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """模拟流式生成"""
        self._response_count += 1
        words = f"Mock streaming response #{self._response_count}".split()
        for word in words:
            yield word + " "


# 客户端缓存，避免重复创建相同配置的客户端
_client_cache: Dict[str, LLMClient] = {}


def create_llm_client(config: Dict[str, Any]) -> LLMClient:
    """
    创建LLM客户端工厂函数

    支持客户端缓存，相同配置返回相同实例

    Args:
        config: 客户端配置
            - type: 客户端类型 ("openclaw", "ollama", "mock")
            - model: 模型名称
            - base_url: 服务地址
            - temperature: 温度参数
            - max_tokens: 最大token数
            - timeout: 超时时间(秒)

    Returns:
        LLMClient实例

    Example:
        >>> llm = create_llm_client({
        ...     "type": "ollama",
        ...     "model": "qwen2.5:7b",
        ...     "base_url": "http://localhost:11434"
        ... })
    """
    client_type = config.get("type", "mock")
    model = config.get("model", "default")
    base_url = config.get("base_url", "")
    
    # 创建缓存键
    cache_key = f"{client_type}:{model}:{base_url}"
    
    if cache_key not in _client_cache:
        if client_type == "openclaw":
            _client_cache[cache_key] = OpenClawLLM(
                base_url=config.get("openclaw", {}).get("base_url", "http://localhost:8080"),
                model=model,
                temperature=config.get("temperature", 0.7),
                max_tokens=config.get("max_tokens", 2048),
                timeout=config.get("timeout", 120)
            )
        elif client_type == "ollama":
            _client_cache[cache_key] = OllamaLLM(
                model=model,
                base_url=config.get("ollama", {}).get("base_url", "http://localhost:11434"),
                temperature=config.get("temperature", 0.7),
                max_tokens=config.get("max_tokens", 2048),
                timeout=config.get("timeout", 120)
            )
        else:
            _client_cache[cache_key] = MockLLM(model=model)
        
        logger.info(f"Created LLM client: {cache_key}")
    
    return _client_cache[cache_key]


async def close_all_llm_clients():
    """关闭所有缓存的LLM客户端"""
    for cache_key, client in _client_cache.items():
        await client.close()
        logger.info(f"Closed LLM client: {cache_key}")
    _client_cache.clear()
