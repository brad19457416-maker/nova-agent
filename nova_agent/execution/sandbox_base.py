"""
Sandbox Base - 沙箱基类

定义沙箱执行接口，支持多种实现。
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


@dataclass
class SandboxResult:
    """沙箱执行结果"""
    success: bool
    output: str = ""
    exit_code: int = 0
    error: str = ""
    duration_ms: int = 0
    files_created: list[str] = None


class Sandbox(ABC):
    """沙箱抽象基类"""
    
    @abstractmethod
    def execute(self, command: str, working_dir: Optional[str] = None, 
              timeout: int = 300) -> SandboxResult:
        """
        执行命令
        
        Args:
            command: 命令字符串
            working_dir: 工作目录
            timeout: 超时秒数
        
        Returns:
            执行结果
        """
        pass
    
    @abstractmethod
    def write_file(self, path: str, content: str) -> bool:
        """
        写入文件到沙箱
        
        Args:
            path: 相对路径
            content: 文件内容
        
        Returns:
            是否成功
        """
        pass
    
    @abstractmethod
    def read_file(self, path: str) -> Optional[str]:
        """
        从沙箱读取文件
        
        Args:
            path: 相对路径
        
        Returns:
            文件内容，None 表示读取失败
        """
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """清理沙箱"""
        pass
    
    def is_alive(self) -> bool:
        """检查沙箱是否活跃"""
        return True
