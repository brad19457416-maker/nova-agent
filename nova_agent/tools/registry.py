"""
工具注册表 - 管理所有可用工具
"""

from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
import asyncio

from nova_agent.tools.base import BaseTool, ToolResult, ToolCollection


@dataclass
class ToolDiscoveryResult:
    """工具发现结果"""
    tool: BaseTool
    confidence: float
    reason: str


class ToolRegistry:
    """
    工具注册表
    
    功能:
    - 注册/注销工具
    - 自动工具发现
    - 工具链编排
    - 工具执行
    """
    
    def __init__(self):
        self.tools: Dict[str, BaseTool] = {}
        self.collections: Dict[str, ToolCollection] = {}
        self.tool_usage: Dict[str, int] = {}
    
    def register(self, tool: BaseTool, collection: str = "default"):
        """
        注册工具
        
        Args:
            tool: 工具实例
            collection: 所属集合
        """
        self.tools[tool.name] = tool
        
        # 添加到集合
        if collection not in self.collections:
            self.collections[collection] = ToolCollection(collection)
        self.collections[collection].add(tool)
        
        self.tool_usage[tool.name] = 0
    
    def unregister(self, name: str) -> bool:
        """注销工具"""
        if name in self.tools:
            tool = self.tools[name]
            del self.tools[name]
            
            # 从所有集合中移除
            for collection in self.collections.values():
                collection.remove(name)
            
            return True
        return False
    
    def get(self, name: str) -> Optional[BaseTool]:
        """获取工具"""
        return self.tools.get(name)
    
    def list_all(self) -> List[str]:
        """列出所有工具"""
        return list(self.tools.keys())
    
    def list_collections(self) -> List[str]:
        """列出所有集合"""
        return list(self.collections.keys())
    
    def get_by_collection(self, collection: str) -> List[BaseTool]:
        """获取集合中的工具"""
        coll = self.collections.get(collection)
        if coll:
            return list(coll.tools.values())
        return []
    
    async def execute(
        self,
        tool_name: str,
        params: Dict = None,
        **kwargs
    ) -> ToolResult:
        """
        执行工具
        
        Args:
            tool_name: 工具名称
            params: 参数
            **kwargs: 额外参数
            
        Returns:
            ToolResult
        """
        params = params or {}
        
        tool = self.tools.get(tool_name)
        if not tool:
            return ToolResult(
                success=False,
                error=f"Tool not found: {tool_name}"
            )
        
        # 验证参数
        is_valid, error = tool.validate_params(params)
        if not is_valid:
            return ToolResult(success=False, error=error)
        
        # 执行
        try:
            result = await tool.execute(**params)
            
            # 记录使用
            self.tool_usage[tool_name] = self.tool_usage.get(tool_name, 0) + 1
            tool.record_usage()
            
            return result
            
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Tool execution failed: {str(e)}"
            )
    
    async def execute_chain(
        self,
        chain: List[Dict]
    ) -> List[ToolResult]:
        """
        执行工具链
        
        Args:
            chain: 工具链配置
                [
                    {"tool": "tool1", "params": {...}},
                    {"tool": "tool2", "params": {...}, "use_prev": true}
                ]
        
        Returns:
            结果列表
        """
        results = []
        prev_result = None
        
        for step in chain:
            tool_name = step.get("tool")
            params = step.get("params", {})
            
            # 是否使用上一步结果
            if step.get("use_prev", False) and prev_result:
                params["_previous_result"] = prev_result.data
            
            result = await self.execute(tool_name, params)
            results.append(result)
            
            if not result.success:
                break
            
            prev_result = result
        
        return results
    
    async def discover(
        self,
        task: str,
        context: Dict = None
    ) -> List[ToolDiscoveryResult]:
        """
        自动发现适合的工具
        
        基于任务描述自动选择合适的工具
        
        Args:
            task: 任务描述
            context: 上下文信息
            
        Returns:
            可能的工具列表（按置信度排序）
        """
        context = context or {}
        candidates = []
        
        # 简单的关键词匹配
        task_lower = task.lower()
        
        for name, tool in self.tools.items():
            confidence = 0.0
            reason = ""
            
            # 搜索相关
            if any(k in task_lower for k in ["搜索", "查找", "找", "search", "find", "look"]):
                if "search" in name.lower():
                    confidence += 0.8
                    reason = "关键词匹配"
            
            # 获取网页
            if any(k in task_lower for k in ["获取", "抓取", "fetch", "get", "read"]):
                if "fetch" in name.lower() or "web" in name.lower():
                    confidence += 0.7
            
            # 执行代码
            if any(k in task_lower for k in ["代码", "编程", "code", "run", "execute"]):
                if "code" in name.lower() or "execute" in name.lower():
                    confidence += 0.8
            
            # 计算
            if any(k in task_lower for k in ["计算", "算", "calculate", "compute"]):
                if "calculator" in name.lower():
                    confidence += 0.9
            
            # 文件操作
            if any(k in task_lower for k in ["文件", "读写", "file"]):
                if "file" in name.lower():
                    confidence += 0.7
            
            if confidence > 0:
                candidates.append(ToolDiscoveryResult(
                    tool=tool,
                    confidence=confidence,
                    reason=reason
                ))
        
        # 按置信度排序
        candidates.sort(key=lambda x: x.confidence, reverse=True)
        return candidates[:5]  # 返回前5个
    
    def get_usage_stats(self) -> Dict:
        """获取使用统计"""
        return {
            "total_tools": len(self.tools),
            "total_usage": sum(self.tool_usage.values()),
            "by_tool": dict(self.tool_usage)
        }
    
    def get_all_schemas(self) -> List[Dict]:
        """获取所有工具的Schema"""
        return [tool.get_schema() for tool in self.tools.values()]


class GlobalToolRegistry:
    """
    全局工具注册表
    单例模式，提供全局访问
    """
    
    _instance = None
    _registry: Optional[ToolRegistry] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._registry = ToolRegistry()
        return cls._instance
    
    @property
    def registry(self) -> ToolRegistry:
        return self._registry
    
    def reset(self):
        """重置注册表"""
        self._registry = ToolRegistry()
