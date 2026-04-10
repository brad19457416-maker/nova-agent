"""
协作角色定义
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any, Optional


class AgentRole(Enum):
    """Agent角色"""
    LEADER = "leader"
    SUB = "sub"
    REVIEWER = "reviewer"
    RESEARCHER = "researcher"
    WRITER = "writer"
    CODER = "coder"
    TESTER = "tester"


class AgentState(Enum):
    """Agent状态"""
    IDLE = "idle"
    WAITING = "waiting"
    WORKING = "working"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Agent:
    """Agent定义"""
    id: str
    role: AgentRole
    state: AgentState = AgentState.IDLE
    context: Dict = field(default_factory=dict)
    result: Any = None
    error: str = ""


@dataclass
class Task:
    """任务定义"""
    id: str
    description: str
    status: str = "pending"
    assigned_to: Optional[str] = None
    result: Any = None
    dependencies: list = field(default_factory=list)