"""
工具基类与注册表

性能优化:
- 工具单例缓存
- 延迟加载策略
- 并发执行支持
- 执行超时控制
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
import logging

logger = logging.getLogger(__name__)


@dataclass
class ToolResult:
    """工具执行结果"""
    success: bool
    data: Any
    error: str = ""
    metadata: Dict = field(default_factory=dict)
    duration_ms: float = 0.0
    executed_at: str = field(default_factory=lambda: datetime.now().isoformat())


class BaseTool(ABC):
    """
    工具基类
    
    所有工具必须继承此类并实现execute方法
    """
    
    name: str = ""
    description: str = ""
    parameters: Dict = field(default_factory=dict)
    timeout: float = 30.0  # 默认超时30秒
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self._initialized = False
    
    async def _init(self):
        """延迟初始化 (子类可重写)"""
        if not self._initialized:
            await self._setup()
            self._initialized = True
    
    async def _setup(self):
        """工具初始化逻辑 (子类重写)"""
        pass
    
    @abstractmethod
    async def _execute(self, **kwargs) -> Any:
        """实际执行逻辑 (子类必须实现)"""
        pass
    
    async def execute(self, **kwargs) -> ToolResult:
        """
        执行工具 (带超时和错误处理)
        
        Args:
            **kwargs: 工具参数
        
        Returns:
            ToolResult: 执行结果
        """
        start_time = asyncio.get_event_loop().time()
        
        try:
            # 初始化
            await asyncio.wait_for(
                self._init(),
                timeout=5.0  # 初始化最多5秒
            )
            
            # 执行
            result = await asyncio.wait_for(
                self._execute(**kwargs),
                timeout=self.timeout
            )
            
            duration = (asyncio.get_event_loop().time() - start_time) * 1000
            
            return ToolResult(
                success=True,
                data=result,
                duration_ms=duration
            )
            
        except asyncio.TimeoutError:
            duration = (asyncio.get_event_loop().time() - start_time) * 1000
            logger.error(f"Tool timeout: {self.name}")
            return ToolResult(
                success=False,
                data=None,
                error=f"Tool execution timed out after {self.timeout}s",
                duration_ms=duration
            )
        except Exception as e:
            duration = (asyncio.get_event_loop().time() - start_time) * 1000
            logger.error(f"Tool error: {self.name} - {e}")
            return ToolResult(
                success=False,
                data=None,
                error=str(e),
                duration_ms=duration
            )
    
    def get_schema(self) -> Dict:
        """获取工具schema"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters or {},
            "timeout": self.timeout
        }


class ToolRegistry:
    """
    工具注册表
    
    性能特性:
    - 单例模式: 全局唯一实例
    - 延迟加载: 工具首次使用时初始化
    - 并发安全: 异步锁保护注册过程
    """
    
    _instance: Optional['ToolRegistry'] = None
    _lock = asyncio.Lock()
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.tools: Dict[str, BaseTool] = {}
        self._lazy_tools: Dict[str, type] = {}  # 延迟加载的工具类
        self._initialized = True
        
        # 注册延迟加载的工具
        self._register_lazy_tools()
    
    def _register_lazy_tools(self):
        """注册延迟加载的工具"""
        # 延迟导入，避免循环依赖
        from .web import WebSearchTool, WebFetchTool
        from .code import CodeExecutionTool
        from .files import (
            FileReadTool, FileWriteTool, FileListTool,
            JsonReadTool, JsonWriteTool
        )
        from .inkcore import MockInkcoreTool
        
        self._lazy_tools = {
            "web_search": WebSearchTool,
            "web_fetch": WebFetchTool,
            "code_execute": CodeExecutionTool,
            "file_read": FileReadTool,
            "file_write": FileWriteTool,
            "file_list": FileListTool,
            "json_read": JsonReadTool,
            "json_write": JsonWriteTool,
            "inkcore": MockInkcoreTool,
        }
    
    async def _load_tool(self, name: str) -> Optional[BaseTool]:
        """延迟加载工具"""
        if name in self.tools:
            return self.tools[name]
        
        if name not in self._lazy_tools:
            return None
        
        async with self._lock:
            # 双重检查
            if name in self.tools:
                return self.tools[name]
            
            tool_class = self._lazy_tools[name]
            tool = tool_class()
            self.tools[name] = tool
            logger.info(f"Lazy loaded tool: {name}")
            return tool
    
    def register(self, tool: BaseTool):
        """注册工具"""
        self.tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")
    
    async def get(self, name: str) -> Optional[BaseTool]:
        """获取工具 (支持延迟加载)"""
        if name in self.tools:
            return self.tools[name]
        return await self._load_tool(name)
    
    def get_sync(self, name: str) -> Optional[BaseTool]:
        """同步获取工具 (仅已加载的工具)"""
        return self.tools.get(name)
    
    def list_tools(self) -> List[str]:
        """列出所有已加载的工具"""
        return list(self.tools.keys())
    
    def list_all_tools(self) -> List[str]:
        """列出所有可用工具 (包括延迟加载的)"""
        all_tools = set(self.tools.keys()) | set(self._lazy_tools.keys())
        return list(all_tools)
    
    def get_schemas(self) -> List[Dict]:
        """获取所有已加载工具的schema"""
        return [tool.get_schema() for tool in self.tools.values()]
    
    async def execute(self, tool_name: str, **kwargs) -> ToolResult:
        """执行工具"""
        tool = await self.get(tool_name)
        if not tool:
            return ToolResult(
                success=False,
                data=None,
                error=f"Tool not found: {tool_name}"
            )
        
        return await tool.execute(**kwargs)
    
    async def batch_execute(self, tasks: List[Dict[str, Any]]) -> List[ToolResult]:
        """
        批量执行工具
        
        Args:
            tasks: 任务列表，每项包含:
                - tool: 工具名称
                - params: 参数字典
        
        Returns:
            结果列表
        
        Example:
            results = await registry.batch_execute([
                {"tool": "web_search", "params": {"query": "Python"}},
                {"tool": "file_read", "params": {"path": "test.txt"}},
            ])
        """
        coros = []
        for task in tasks:
            tool_name = task.get("tool")
            params = task.get("params", {})
            coros.append(self.execute(tool_name, **params))
        
        return await asyncio.gather(*coros, return_exceptions=True)
    
    @classmethod
    def reset_instance(cls):
        """重置单例 (主要用于测试)"""
        cls._instance = None