"""
Sub Agent - 子任务执行 Agent

每个 Sub Agent 有独立上下文和工具集，隔离执行避免污染。
"""

import logging
from typing import Any, Dict

from ..memory.palace import MemoryPalace
from ..reasoning.hgarn_engine import HGARNEngine
from ..tools.plugin_manager import PluginManager

logger = logging.getLogger(__name__)


class SubAgent:
    """
    Sub Agent - 执行单个子任务

    特性：
    - 独立上下文，与其他 Sub Agent 隔离
    - 专用工具集，可根据子任务类型定制
    - 独立记忆检索，不影响主 Agent
    """

    def __init__(
        self,
        task: Dict[str, Any],
        memory_palace: MemoryPalace,
        plugin_manager: PluginManager,
        config: Dict[str, Any],
    ):
        self.task = task
        self.memory_palace = memory_palace  # 共享同一个记忆宫殿
        self.plugin_manager = plugin_manager
        self.config = config
        self.task_index = task.get("index", 0)

        # 独立推理引擎
        self.reasoning_engine = HGARNEngine(
            block_size=config.get("block_size", 4),
            max_blocks_per_level=config.get("max_blocks_per_level", 2),
            max_levels=config.get("max_levels", 2),
            cumulative_gain_threshold=config.get("cumulative_gain_threshold", 2.5),
        )

    def execute(self) -> Dict[str, Any]:
        """执行子任务"""
        task_description = self.task.get("description", "")
        task_context = self.task.get("context", {})

        logger.info(f"SubAgent {self.task_index} executing: {task_description[:80]}...")

        try:
            # 1. 检索相关记忆
            relevant_memories = self.memory_palace.retrieve(
                task_description, hierarchical_filter=True
            )

            # 2. 构建上下文
            full_context = {
                "task_description": task_description,
                "parent_context": task_context,
                "relevant_memories": relevant_memories,
            }

            # 3. 推理求解
            result = self.reasoning_engine.solve(full_context)

            # 4. 如果需要工具，执行
            tool_results = None
            if result.needs_tools:
                # 执行工具调用
                tool_results = []
                for call in result.tool_calls:
                    plugin = self.plugin_manager.get_plugin(call["plugin_name"])
                    if plugin:
                        res = plugin.execute(call["parameters"])
                        tool_results.append(
                            {"plugin": call["plugin_name"], "result": res, "success": True}
                        )

                # 重新推理整合工具结果
                if tool_results:
                    result = self.reasoning_engine.solve_with_tools(full_context, tool_results)

            return {
                "task_index": self.task_index,
                "task_description": task_description,
                "success": result.success,
                "result": result.final_response,
                "tool_results": tool_results,
                "gain": result.total_gain if hasattr(result, "total_gain") else None,
            }

        except Exception as e:
            logger.error(f"SubAgent {self.task_index} failed: {e}")
            return {
                "task_index": self.task_index,
                "task_description": task_description,
                "success": False,
                "error": str(e),
            }
