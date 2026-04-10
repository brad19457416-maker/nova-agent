"""
工具基类
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ToolResult:
    """工具执行结果"""
    success: bool
    data: Any
    error: str = ""
    metadata: Dict = None


class BaseTool(ABC):
    """工具基类"""
    
    name: str = ""
    description: str = ""
    parameters: Dict = None
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
    
    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """执行工具"""
        pass
    
    def get_schema(self) -> Dict:
        """获取工具schema"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters or {}
        }


class ToolRegistry:
    """
    工具注册表
    
    管理所有可用工具
    """
    
    def __init__(self):
        self.tools: Dict[str, BaseTool] = {}
        self._register_builtin_tools()
    
    def _register_builtin_tools(self):
        """注册内置工具"""
        from .web import WebSearchTool, WebFetchTool
        from .code import CodeExecutionTool
        from .files import (
            FileReadTool, FileWriteTool, FileListTool,
            JsonReadTool, JsonWriteTool
        )
        from .inkcore import InkcoreTool, MockInkcoreTool
        
        self.register(WebSearchTool())
        self.register(WebFetchTool())
        self.register(CodeExecutionTool())
        self.register(FileReadTool())
        self.register(FileWriteTool())
        self.register(FileListTool())
        self.register(JsonReadTool())
        self.register(JsonWriteTool())
        self.register(MockInkcoreTool())  # 使用模拟版本，避免依赖外部服务
    
    def register(self, tool: BaseTool):
        """注册工具"""
        self.tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")
    
    def get(self, name: str) -> Optional[BaseTool]:
        """获取工具"""
        return self.tools.get(name)
    
    def list_tools(self) -> List[str]:
        """列出所有工具"""
        return list(self.tools.keys())
    
    def get_schemas(self) -> List[Dict]:
        """获取所有工具schema"""
        return [tool.get_schema() for tool in self.tools.values()]
    
    async def execute(self, tool_name: str, **kwargs) -> ToolResult:
        """执行工具"""
        tool = self.get(tool_name)
        if not tool:
            return ToolResult(
                success=False,
                data=None,
                error=f"Tool not found: {tool_name}"
            )
        
        try:
            return await tool.execute(**kwargs)
        except Exception as e:
            logger.error(f"Tool execution failed: {tool_name} - {e}")
            return ToolResult(
                success=False,
                data=None,
                error=str(e)
            )