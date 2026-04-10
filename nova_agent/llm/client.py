"""
LLM客户端实现

支持:
- OpenClaw (本地Gateway)
- Ollama (本地模型)
- OpenAI API (可选)

使用示例:
    # OpenClaw模式
    llm = OpenClawLLM(base_url="http://localhost:8080")
    
    # Ollama模式
    llm = OllamaLLM(model="qwen2.5:7b", base_url="http://localhost:11434")
    
    # 使用
    response = await llm.complete("你好")
    response = await llm.chat([{"role": "user", "content": "你好"}])
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, AsyncGenerator
import aiohttp
import json
import logging

logger = logging.getLogger(__name__)


class LLMClient(ABC):
    """LLM客户端基类"""
    
    def __init__(self, model: str = None, **kwargs):
        self.model = model
        self.config = kwargs
    
    @abstractmethod
    async def complete(self, prompt: str, **kwargs) -> str:
        """完成文本生成"""
        pass
    
    @abstractmethod
    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """对话生成"""
        pass
    
    @abstractmethod
    async def stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """流式生成"""
        pass


class OpenClawLLM(LLMClient):
    """
    OpenClaw LLM客户端
    
    通过本地Gateway调用模型
    """
    
    def __init__(self, base_url: str = "http://localhost:8080", 
                 model: str = "qwen2.5:7b", **kwargs):
        super().__init__(model, **kwargs)
        self.base_url = base_url.rstrip("/")
        self.session = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """获取或创建session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def complete(self, prompt: str, **kwargs) -> str:
        """完成生成"""
        session = await self._get_session()
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            **kwargs
        }
        
        try:
            async with session.post(
                f"{self.base_url}/v1/completions",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=120)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("choices", [{}])[0].get("text", "")
                else:
                    text = await resp.text()
                    logger.error(f"OpenClaw error: {resp.status} - {text}")
                    return f"[Error: {resp.status}]"
        except Exception as e:
            logger.error(f"OpenClaw request failed: {e}")
            return f"[Error: {e}]"
    
    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """对话生成"""
        session = await self._get_session()
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            **kwargs
        }
        
        try:
            async with session.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=120)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("choices", [{}])[0].get("message", {}).get("content", "")
                else:
                    text = await resp.text()
                    logger.error(f"OpenClaw error: {resp.status} - {text}")
                    return f"[Error: {resp.status}]"
        except Exception as e:
            logger.error(f"OpenClaw request failed: {e}")
            return f"[Error: {e}]"
    
    async def stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """流式生成"""
        session = await self._get_session()
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": True,
            **kwargs
        }
        
        try:
            async with session.post(
                f"{self.base_url}/v1/completions",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=120)
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
        except Exception as e:
            logger.error(f"OpenClaw stream failed: {e}")
            yield f"[Error: {e}]"
    
    async def close(self):
        """关闭连接"""
        if self.session and not self.session.closed:
            await self.session.close()


class OllamaLLM(LLMClient):
    """
    Ollama LLM客户端
    
    直接调用Ollama API
    """
    
    def __init__(self, model: str = "qwen2.5:7b", 
                 base_url: str = "http://localhost:11434",
                 **kwargs):
        super().__init__(model, **kwargs)
        self.base_url = base_url.rstrip("/")
        self.session = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """获取或创建session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
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
                json=payload,
                timeout=aiohttp.ClientTimeout(total=120)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("response", "")
                else:
                    text = await resp.text()
                    logger.error(f"Ollama error: {resp.status} - {text}")
                    return f"[Error: {resp.status}]"
        except Exception as e:
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
                json=payload,
                timeout=aiohttp.ClientTimeout(total=120)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("message", {}).get("content", "")
                else:
                    text = await resp.text()
                    logger.error(f"Ollama error: {resp.status} - {text}")
                    return f"[Error: {resp.status}]"
        except Exception as e:
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
                json=payload,
                timeout=aiohttp.ClientTimeout(total=120)
            ) as resp:
                async for line in resp.content:
                    line = line.decode("utf-8").strip()
                    if line:
                        try:
                            data = json.loads(line)
                            text = data.get("response", "")
                            if text:
                                yield text
                            if data.get("done"):
                                break
                        except json.JSONDecodeError:
                            pass
        except Exception as e:
            logger.error(f"Ollama stream failed: {e}")
            yield f"[Error: {e}]"
    
    async def list_models(self) -> List[str]:
        """列出可用模型"""
        session = await self._get_session()
        
        try:
            async with session.get(f"{self.base_url}/api/tags") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return [m.get("name") for m in data.get("models", [])]
                return []
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return []
    
    async def close(self):
        """关闭连接"""
        if self.session and not self.session.closed:
            await self.session.close()


class MockLLM(LLMClient):
    """
    模拟LLM客户端（用于测试）
    """
    
    async def complete(self, prompt: str, **kwargs) -> str:
        """模拟完成"""
        logger.info(f"[MockLLM] Complete: {prompt[:50]}...")
        return f"[模拟回复] 对于 '{prompt[:30]}...' 的回复"
    
    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """模拟对话"""
        last_msg = messages[-1].get("content", "") if messages else ""
        logger.info(f"[MockLLM] Chat: {last_msg[:50]}...")
        return f"[模拟对话回复] {last_msg[:30]}..."
    
    async def stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """模拟流式"""
        words = ["这是", "一个", "模拟", "的", "流式", "回复"]
        for word in words:
            yield word
            await asyncio.sleep(0.1)


# 创建默认LLM客户端的工厂函数
def create_llm_client(config: Dict = None) -> LLMClient:
    """
    创建LLM客户端
    
    Args:
        config: 配置字典
            - type: "ollama" | "openclaw" | "mock"
            - model: 模型名称
            - base_url: API地址
    
    Returns:
        LLMClient实例
    """
    config = config or {}
    llm_type = config.get("type", "mock")
    
    if llm_type == "ollama":
        return OllamaLLM(
            model=config.get("model", "qwen2.5:7b"),
            base_url=config.get("base_url", "http://localhost:11434")
        )
    elif llm_type == "openclaw":
        return OpenClawLLM(
            model=config.get("model", "qwen2.5:7b"),
            base_url=config.get("base_url", "http://localhost:8080")
        )
    else:
        return MockLLM()
