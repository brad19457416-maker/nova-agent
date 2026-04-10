"""
工具系统基础类
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, List
from datetime import datetime
import json


@dataclass
class ToolParameter:
    """工具参数定义"""
    name: str
    type: str  # string, number, boolean, array, object
    description: str
    required: bool = True
    default: Any = None
    enum: List[str] = field(default_factory=list)


@dataclass
class ToolResult:
    """工具执行结果"""
    success: bool
    data: Any = None
    error: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "metadata": self.metadata
        }


class BaseTool(ABC):
    """
    工具基类
    
    所有工具都必须继承此类并实现execute方法
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        parameters: List[ToolParameter] = None
    ):
        self.name = name
        self.description = description
        self.parameters = parameters or []
        self.usage_count = 0
        self.last_used = None
    
    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """
        执行工具
        
        Args:
            **kwargs: 工具参数
            
        Returns:
            ToolResult: 执行结果
        """
        pass
    
    def get_schema(self) -> Dict:
        """获取工具的JSON Schema"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    p.name: {
                        "type": p.type,
                        "description": p.description,
                        "default": p.default,
                        "enum": p.enum
                    }
                    for p in self.parameters
                },
                "required": [p.name for p in self.parameters if p.required]
            }
        }
    
    def validate_params(self, params: Dict) -> tuple[bool, str]:
        """
        验证参数
        
        Returns:
            (is_valid, error_message)
        """
        for param in self.parameters:
            if param.required and param.name not in params:
                return False, f"Missing required parameter: {param.name}"
            
            if param.name in params:
                value = params[param.name]
                expected_type = param.type
                
                # 类型检查
                if expected_type == "string" and not isinstance(value, str):
                    return False, f"Parameter {param.name} must be string"
                elif expected_type == "number" and not isinstance(value, (int, float)):
                    return False, f"Parameter {param.name} must be number"
                elif expected_type == "boolean" and not isinstance(value, bool):
                    return False, f"Parameter {param.name} must be boolean"
                elif expected_type == "array" and not isinstance(value, list):
                    return False, f"Parameter {param.name} must be array"
                elif expected_type == "object" and not isinstance(value, dict):
                    return False, f"Parameter {param.name} must be object"
                
                # 枚举检查
                if param.enum and value not in param.enum:
                    return False, f"Parameter {param.name} must be one of {param.enum}"
        
        return True, ""
    
    def record_usage(self):
        """记录使用情况"""
        self.usage_count += 1
        self.last_used = datetime.now()
    
    def get_stats(self) -> Dict:
        """获取使用统计"""
        return {
            "name": self.name,
            "usage_count": self.usage_count,
            "last_used": self.last_used.isoformat() if self.last_used else None
        }


class ToolCollection:
    """
    工具集合
    管理多个工具的分组
    """
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.tools: Dict[str, BaseTool] = {}
    
    def add(self, tool: BaseTool):
        """添加工具"""
        self.tools[tool.name] = tool
    
    def get(self, name: str) -> Optional[BaseTool]:
        """获取工具"""
        return self.tools.get(name)
    
    def remove(self, name: str) -> bool:
        """移除工具"""
        if name in self.tools:
            del self.tools[name]
            return True
        return False
    
    def list_tools(self) -> List[str]:
        """列出所有工具"""
        return list(self.tools.keys())
    
    def search(self, keyword: str) -> List[BaseTool]:
        """搜索工具"""
        results = []
        for tool in self.tools.values():
            if (keyword.lower() in tool.name.lower() or 
                keyword.lower() in tool.description.lower()):
                results.append(tool)
        return results
