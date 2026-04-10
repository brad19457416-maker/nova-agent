"""
Read File Plugin - 读取文件工具
"""

import os
from pathlib import Path
from nova_agent.tools.plugin_base import PluginBase, PluginResult


class ReadFilePlugin(PluginBase):
    """读取文件工具"""
    
    name = "read_file"
    description = "Read content from a text file"
    version = "0.1.0"
    parameters_schema = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to the file"
            },
            "max_lines": {
                "type": "integer",
                "description": "Maximum number of lines to read (optional)",
                "default": 1000
            }
        },
        "required": ["path"]
    }
    
    def execute(self, parameters: dict, **kwargs) -> PluginResult:
        path = parameters["path"]
        max_lines = parameters.get("max_lines", 1000)
        
        try:
            # 展开用户目录
            path = os.path.expanduser(path)
            
            if not os.path.exists(path):
                return PluginResult(
                    success=False,
                    error=f"File not found: {path}"
                )
            
            with open(path, 'r', encoding='utf-8') as f:
                lines = []
                for i, line in enumerate(f):
                    if i >= max_lines:
                        lines.append(f"\n... (truncated at {max_lines} lines)")
                        break
                    lines.append(line)
                content = ''.join(lines)
            
            return PluginResult(
                success=True,
                result={
                    "path": path,
                    "content": content,
                    "lines_read": len(lines),
                    "file_size": os.path.getsize(path)
                }
            )
            
        except Exception as e:
            return PluginResult(
                success=False,
                error=f"Failed to read file: {str(e)}"
            )
