"""
深度研究模块 - 解决Agent调研策略死板的问题
"""

from nova_agent.research.deep_researcher import DeepResearcher, ResearchConfig
from nova_agent.research.search_strategy import SearchStrategy, IterativeSearch

__all__ = ["DeepResearcher", "ResearchConfig", "SearchStrategy", "IterativeSearch"]
