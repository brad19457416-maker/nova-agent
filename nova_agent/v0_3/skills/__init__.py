"""
技能系统
"""

from .loader import SkillLoader, SkillConfig
from .antipatterns import AntipatternChecker, Antipattern

__all__ = ["SkillLoader", "SkillConfig", "AntipatternChecker", "Antipattern"]