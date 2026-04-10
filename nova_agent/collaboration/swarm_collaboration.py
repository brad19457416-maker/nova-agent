"""
Swarm Collaboration - 群体智能平行推演

MiroFish 启发：多个独立智能体平行推演，统计共识和分歧。
"""

import logging
from typing import Any, Dict

from ..agent.swarm_coordinator import SwarmCoordinator

logger = logging.getLogger(__name__)


class SwarmCollaboration:
    """
    群体智能平行推演

    适用场景：预测类问题、决策探索，需要多种独立视角论证。
    每个智能体独立推演，最后统计共识。
    """

    def __init__(self, memory_palace, plugin_manager, config: Dict[str, Any] = None):
        self.config = config or {}
        self.memory_palace = memory_palace
        self.plugin_manager = plugin_manager
        self.num_agents = config.get("num_agents", 5)
        self.coordinator = SwarmCoordinator({"num_agents": self.num_agents, **(config or {})})

    def run(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """运行群体推演"""
        return self.coordinator.run(
            query=query,
            context=context,
            memory_palace=self.memory_palace,
            plugin_manager=self.plugin_manager,
        )
