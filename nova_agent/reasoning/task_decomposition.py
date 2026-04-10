"""
Task Decomposer - 任务分解器

将复杂任务分解为可独立执行的子任务，
支持递归分解。
"""

import json
import logging
import re
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class TaskDecomposer:
    """任务分解器"""

    def __init__(self, max_subtasks: int = 8, max_depth: int = 3):
        self.max_subtasks = max_subtasks
        self.max_depth = max_depth

    def decompose(self, query: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        分解任务

        Args:
            query: 任务查询
            context: 上下文

        Returns:
            子任务列表
        """
        # 如果已有 LLM 客户端，使用 LLM 分解
        if "llm_client" in context:
            return self._llm_decompose(query, context)

        # 否则简单启发式分解
        return self._heuristic_decompose(query)

    def _llm_decompose(self, query: str, context: Dict[str, Any]) -> List[Dict]:
        """使用 LLM 分解"""
        prompt = self._build_prompt(query, context)
        response = context["llm_client"].complete(prompt)
        return self._parse_response(response)

    def _build_prompt(self, query: str, context: Dict[str, Any]) -> str:
        """构建分解提示"""
        prompt = f"""请将以下复杂任务分解为可独立执行的子任务：

原始任务：{query}

分解规则：
1. 每个子任务必须目标明确，可以由一个 AI Agent 独立完成
2. 子任务之间尽量减少依赖
3. 子任务粒度适中，不要太大也不要太小
4. 最多 {self.max_subtasks} 个子任务
5. 使用 JSON 格式输出，格式如下：

{{
  "subtasks": [
    {{
      "id": "1",
      "description": "子任务描述",
      "dependencies": []  // 依赖的子任务 id，若无留空
    }}
  ]
}}

"""
        if "relevant_memories" in context and context["relevant_memories"]:
            prompt += "\n相关参考信息：\n"
            for i, mem in enumerate(context["relevant_memories"][:2]):
                content = mem.get("content", "")[:150]
                prompt += f"{i+1}. {content}...\n"

        return prompt

    def _parse_response(self, response: str) -> List[Dict]:
        """解析 LLM 响应"""
        # 尝试提取 JSON
        try:
            # 查找 JSON 块
            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                if "subtasks" in data:
                    subtasks = data["subtasks"]
                    # 添加 index
                    for i, st in enumerate(subtasks):
                        st["index"] = i
                    return subtasks

            # 如果 JSON 解析失败，尝试行解析
            lines = response.split("\n")
            subtasks = []
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                # 匹配数字开头
                match = re.match(r"^\d+[\.\)]\s*(.*)$", line)
                if match:
                    desc = match.group(1)
                    if desc:
                        subtasks.append(
                            {
                                "id": str(len(subtasks) + 1),
                                "index": len(subtasks),
                                "description": desc,
                                "dependencies": [],
                            }
                        )

            if subtasks:
                return subtasks[: self.max_subtasks]

        except Exception as e:
            logger.warning(f"Failed to parse decomposition: {e}")

        # 如果都失败，返回一个默认任务
        return [{"id": "1", "index": 0, "description": query, "dependencies": []}]

    def _heuristic_decompose(self, query: str) -> List[Dict]:
        """简单启发式分解（按换行分割）"""
        lines = [line.strip() for line in query.split("\n") if line.strip()]
        if len(lines) <= 1:
            return [{"id": "1", "index": 0, "description": query, "dependencies": []}]

        subtasks = []
        for i, line in enumerate(lines):
            if line:
                subtasks.append(
                    {"id": str(i + 1), "index": i, "description": line, "dependencies": []}
                )

        return subtasks[: self.max_subtasks]

    def can_recurse(self, current_depth: int) -> bool:
        """检查是否可以继续递归分解"""
        return current_depth < self.max_depth
