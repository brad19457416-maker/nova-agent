"""
工作流基础类
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class PhaseHandler(ABC):
    """阶段处理器基类"""
    
    name: str = ""
    description: str = ""
    
    def __init__(self, config: Dict):
        self.config = config
        self.llm = None
        self.skills = None
    
    def inject_dependencies(self, llm, skills):
        """注入依赖"""
        self.llm = llm
        self.skills = skills
    
    @abstractmethod
    async def execute(self, context: Dict) -> Any:
        """执行阶段，返回输出"""
        pass


class BaseWorkflow(ABC):
    """工作流基类"""
    
    name: str = ""
    description: str = ""
    version: str = "1.0.0"
    
    def __init__(self, config: Dict):
        self.config = config
        self.phases: list = []
    
    def get_phases(self) -> list:
        """获取阶段列表"""
        return self.phases
    
    async def run(self, context: Dict) -> Any:
        """运行工作流"""
        raise NotImplementedError