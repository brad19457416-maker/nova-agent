"""
PluginBase - 插件基类

所有插件继承这个基类，实现统一接口。
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class PluginResult:
    """插件执行结果"""

    success: bool
    result: Any = None
    error: str = ""
    metadata: dict[str, Any] = None

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "result": self.result,
            "error": self.error,
            "metadata": self.metadata,
        }


class PluginBase(ABC):
    """
    插件基类

    所有工具插件必须继承这个类并实现抽象方法。
    """

    name: str = ""
    description: str = ""
    version: str = "0.1.0"
    parameters_schema: dict[str, Any] = {}

    @abstractmethod
    def execute(self, parameters: dict[str, Any], **kwargs) -> PluginResult:
        """
        执行插件

        Args:
            parameters: 参数字典
            **kwargs: 额外参数，比如 sandbox

        Returns:
            执行结果
        """
        pass

    def get_schema(self) -> dict[str, Any]:
        """获取 OpenAI Function Calling 格式 schema"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters_schema,
            },
        }

    def validate_parameters(self, parameters: dict[str, Any]) -> bool:
        """验证参数是否符合 schema"""
        # 简化验证，只检查必填
        required = self.parameters_schema.get("required", [])
        for req in required:
            if req not in parameters:
                logger.error(f"Missing required parameter: {req} for plugin {self.name}")
                return False
        return True

    def __str__(self) -> str:
        return f"{self.name} v{self.version}: {self.description}"
