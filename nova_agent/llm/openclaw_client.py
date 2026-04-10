"""
OpenClaw Client - OpenClaw 平台 LLM 客户端

适配 OpenClaw 环境，直接调用 OpenClaw 内置 LLM 接口。
"""

import logging
import os
from typing import Dict, List

import requests

from .client_base import LLMClient

logger = logging.getLogger(__name__)


class OpenClawClient(LLMClient):
    """OpenClaw LLM 客户端"""

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.api_base = os.environ.get("OPENCLAW_LLM_API_BASE", "http://localhost:8080/v1")
        self.api_key = os.environ.get("OPENCLAW_LLM_API_KEY", "")
        self.model = self.config.get("model", os.environ.get("OPENCLAW_DEFAULT_MODEL", "default"))
        self.max_tokens = self.config.get("max_tokens", 4096)
        self.temperature = self.config.get("temperature", 0.7)

        logger.info(f"OpenClawClient initialized, model: {self.model}")

    def complete(self, prompt: str, **kwargs) -> str:
        """完成提示 - 单轮补全"""
        messages = [{"role": "user", "content": prompt}]
        return self.chat(messages, **kwargs)

    def chat(self, messages: List[Dict], **kwargs) -> str:
        """聊天对话 - 多轮对话"""
        url = f"{self.api_base}/chat/completions"

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        data = {
            "model": self.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", self.temperature),
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
            "stream": False,
        }

        try:
            response = requests.post(url, headers=headers, json=data, timeout=300)
            response.raise_for_status()
            result = response.json()

            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0]["message"]["content"]
                logger.debug(f"LLM response received, {len(content)} chars")
                return content
            else:
                logger.error("No choices in response")
                return ""

        except requests.exceptions.RequestException as e:
            logger.error(f"LLM request failed: {e}")
            # 如果 API 调用失败，尝试回退到直接使用 OpenClaw 内置调用
            # 在 OpenClaw 插件环境中，可以通过其他方式调用
            raise RuntimeError(f"OpenClaw LLM call failed: {e}") from e

    def count_tokens(self, text: str) -> int:
        """估算 token 数量"""
        # 简单估算：1 token ≈ 4 字符
        return len(text) // 4

    def is_available(self) -> bool:
        """检查 LLM 是否可用"""
        try:
            # 简单测试调用
            self.complete("Hello")
            return True
        except:
            return False
