"""
文件操作工具
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, List
import logging

from .base import BaseTool, ToolResult

logger = logging.getLogger(__name__)


class FileReadTool(BaseTool):
    """文件读取工具"""
    
    name = "file_read"
    description = "读取文件内容"
    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "文件路径"
            },
            "limit": {
                "type": "integer",
                "description": "读取行数限制",
                "default": 100
            }
        },
        "required": ["path"]
    }
    
    async def execute(self, path: str, limit: int = 100, **kwargs) -> ToolResult:
        """读取文件"""
        try:
            file_path = Path(path)
            
            if not file_path.exists():
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"File not found: {path}"
                )
            
            if not file_path.is_file():
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Not a file: {path}"
                )
            
            # 读取文件
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            total_lines = len(lines)
            content = ''.join(lines[:limit])
            
            return ToolResult(
                success=True,
                data={
                    "path": str(file_path.absolute()),
                    "content": content,
                    "lines_read": min(limit, total_lines),
                    "total_lines": total_lines
                },
                metadata={"encoding": "utf-8"}
            )
        
        except Exception as e:
            logger.error(f"File read failed: {e}")
            return ToolResult(
                success=False,
                data=None,
                error=str(e)
            )


class FileWriteTool(BaseTool):
    """文件写入工具"""
    
    name = "file_write"
    description = "写入文件内容"
    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "文件路径"
            },
            "content": {
                "type": "string",
                "description": "文件内容"
            },
            "append": {
                "type": "boolean",
                "description": "是否追加",
                "default": False
            }
        },
        "required": ["path", "content"]
    }
    
    async def execute(self, path: str, content: str, append: bool = False, **kwargs) -> ToolResult:
        """写入文件"""
        try:
            file_path = Path(path)
            
            # 确保目录存在
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            mode = 'a' if append else 'w'
            with open(file_path, mode, encoding='utf-8') as f:
                f.write(content)
            
            return ToolResult(
                success=True,
                data={
                    "path": str(file_path.absolute()),
                    "bytes_written": len(content.encode('utf-8')),
                    "mode": "append" if append else "write"
                }
            )
        
        except Exception as e:
            logger.error(f"File write failed: {e}")
            return ToolResult(
                success=False,
                data=None,
                error=str(e)
            )


class FileListTool(BaseTool):
    """文件列表工具"""
    
    name = "file_list"
    description = "列出目录内容"
    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "目录路径"
            },
            "pattern": {
                "type": "string",
                "description": "文件匹配模式",
                "default": "*"
            }
        },
        "required": ["path"]
    }
    
    async def execute(self, path: str, pattern: str = "*", **kwargs) -> ToolResult:
        """列出目录"""
        try:
            dir_path = Path(path)
            
            if not dir_path.exists():
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Directory not found: {path}"
                )
            
            files = []
            for item in dir_path.glob(pattern):
                files.append({
                    "name": item.name,
                    "type": "directory" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else None
                })
            
            return ToolResult(
                success=True,
                data={
                    "path": str(dir_path.absolute()),
                    "files": files,
                    "count": len(files)
                }
            )
        
        except Exception as e:
            logger.error(f"File list failed: {e}")
            return ToolResult(
                success=False,
                data=None,
                error=str(e)
            )


class JsonReadTool(BaseTool):
    """JSON文件读取工具"""
    
    name = "json_read"
    description = "读取JSON文件"
    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "JSON文件路径"
            }
        },
        "required": ["path"]
    }
    
    async def execute(self, path: str, **kwargs) -> ToolResult:
        """读取JSON"""
        try:
            file_path = Path(path)
            
            if not file_path.exists():
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"File not found: {path}"
                )
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return ToolResult(
                success=True,
                data=data,
                metadata={"path": str(file_path.absolute())}
            )
        
        except json.JSONDecodeError as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Invalid JSON: {e}"
            )
        except Exception as e:
            logger.error(f"JSON read failed: {e}")
            return ToolResult(
                success=False,
                data=None,
                error=str(e)
            )


class JsonWriteTool(BaseTool):
    """JSON文件写入工具"""
    
    name = "json_write"
    description = "写入JSON文件"
    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "JSON文件路径"
            },
            "data": {
                "type": "object",
                "description": "JSON数据"
            },
            "indent": {
                "type": "integer",
                "description": "缩进",
                "default": 2
            }
        },
        "required": ["path", "data"]
    }
    
    async def execute(self, path: str, data: Dict, indent: int = 2, **kwargs) -> ToolResult:
        """写入JSON"""
        try:
            file_path = Path(path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=indent, ensure_ascii=False)
            
            return ToolResult(
                success=True,
                data={"path": str(file_path.absolute())}
            )
        
        except Exception as e:
            logger.error(f"JSON write failed: {e}")
            return ToolResult(
                success=False,
                data=None,
                error=str(e)
            )