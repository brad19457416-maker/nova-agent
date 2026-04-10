"""
代码执行工具
"""

import subprocess
import tempfile
import os
from typing import Dict, Any
import logging

from .base import BaseTool, ToolResult

logger = logging.getLogger(__name__)


class CodeExecutionTool(BaseTool):
    """
    代码执行工具
    
    安全执行Python代码
    """
    
    name = "code_execute"
    description = "执行Python代码"
    parameters = {
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": "Python代码"
            },
            "timeout": {
                "type": "integer",
                "description": "超时时间(秒)",
                "default": 30
            }
        },
        "required": ["code"]
    }
    
    async def execute(self, code: str, timeout: int = 30, **kwargs) -> ToolResult:
        """执行代码"""
        try:
            # 创建临时文件
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            try:
                # 执行代码
                result = subprocess.run(
                    ['python3', temp_file],
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
                
                return ToolResult(
                    success=result.returncode == 0,
                    data={
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                        "returncode": result.returncode
                    },
                    error=result.stderr if result.returncode != 0 else "",
                    metadata={"execution_time": timeout}
                )
            finally:
                os.unlink(temp_file)
        
        except subprocess.TimeoutExpired:
            return ToolResult(
                success=False,
                data=None,
                error=f"Code execution timeout after {timeout}s"
            )
        except Exception as e:
            logger.error(f"Code execution failed: {e}")
            return ToolResult(
                success=False,
                data=None,
                error=str(e)
            )