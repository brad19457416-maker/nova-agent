"""
Lead-Sub Collaboration - Lead/Sub 分层协作

DeerFlow 启发：Lead Agent 分解任务，Sub Agent 并行执行。
"""

import logging
from typing import Any

from ..agent.lead_agent import LeadAgent

logger = logging.getLogger(__name__)


class LeadSubCollaboration:
    """
    Lead/Sub 分层协作

    适用场景：复杂任务可以分解为多个独立子任务，
    Lead Agent 负责规划分解聚合，Sub Agent 并行执行。
    """

    def __init__(self, memory_palace, plugin_manager, config: dict[str, Any] = None):
        self.config = config or {}
        self.memory_palace = memory_palace
        self.plugin_manager = plugin_manager
        self.lead_agent = LeadAgent(config)

    def run(self, query: str, context: dict[str, Any]) -> dict[str, Any]:
        """运行完整的 Lead/Sub 协作"""
        return self.lead_agent.run(
            query=query,
            context=context,
            memory_palace=self.memory_palace,
            plugin_manager=self.plugin_manager,
        )
