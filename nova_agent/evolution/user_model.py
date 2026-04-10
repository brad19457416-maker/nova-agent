"""
UserModel - 用户画像建模

记录用户偏好、行为模式、任务类型，
实现个性化适配。
"""

import logging
from collections import defaultdict
from typing import Any, Optional

logger = logging.getLogger(__name__)


class UserModel:
    """
    用户画像模型

    跟踪用户偏好，提供个性化体验。
    """

    def __init__(self):
        # 偏好统计
        self.preferences: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        # 任务类型统计
        self.task_types: dict[str, int] = defaultdict(int)
        # 活跃时间
        self.active_hours: set[int] = set()
        # 交互次数
        self.total_interactions = 0

    def record_interaction(self, query: str, response: str, rating: Optional[int] = None) -> None:
        """记录一次交互"""
        self.total_interactions += 1

        # 记录时间
        from datetime import datetime

        hour = datetime.now().hour
        self.active_hours.add(hour)

        # 提取任务类型关键词
        task_type = self._classify_task(query)
        self.task_types[task_type] += 1

        # 如果有评分，记录偏好
        if rating is not None:
            # 提取关键词偏好
            words = set(query.lower().split())
            for word in words:
                if len(word) > 3:  # 过滤太短的
                    self.preferences[word][str(rating)] += 1

    def _classify_task(self, query: str) -> str:
        """简单任务分类"""
        query_lower = query.lower()

        if any(word in query_lower for word in ["code", "写代码", "编程", "debug"]):
            return "coding"
        elif any(word in query_lower for word in ["write", "写", "文章", "报告"]):
            return "writing"
        elif any(word in query_lower for word in ["search", "find", "搜索", "查找"]):
            return "search"
        elif any(word in query_lower for word in ["analyze", "分析", "分析一下"]):
            return "analysis"
        else:
            return "general"

    def get_preferred_style(self) -> dict[str, Any]:
        """获取用户偏好风格"""
        # 统计偏好
        preferences = {
            "most_common_task": self._get_most_common(self.task_types),
            "total_interactions": self.total_interactions,
            "active_hours": list(self.active_hours),
        }

        return preferences

    def personalized_prompt(self, base_prompt: str) -> str:
        """根据用户偏好个性化提示"""
        preferences = self.get_preferred_style()
        task_type = preferences["most_common_task"]

        # 根据任务类型添加个性化提示
        if task_type == "coding":
            base_prompt += "\n\n用户偏好：更关注代码可读性和注释，喜欢简洁实现。"
        elif task_type == "writing":
            base_prompt += "\n\n用户偏好：结构清晰，逻辑连贯，喜欢详细说明。"
        elif task_type == "analysis":
            base_prompt += "\n\n用户偏好：数据分析要透彻，给出明确结论。"

        return base_prompt

    def _get_most_common(self, counter: dict[str, int]) -> str:
        """获取出现最多的"""
        if not counter:
            return "general"
        return max(counter.items(), key=lambda x: x[1])[0]

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            "total_interactions": self.total_interactions,
            "num_task_types": len(self.task_types),
            "task_distribution": dict(self.task_types),
            "active_hours": list(self.active_hours),
        }

    def save(self, path: str) -> None:
        """保存用户模型"""
        import json

        data = {
            "preferences": {k: dict(v) for k, v in self.preferences.items()},
            "task_types": dict(self.task_types),
            "active_hours": list(self.active_hours),
            "total_interactions": self.total_interactions,
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load(self, path: str) -> None:
        """加载用户模型"""
        import json
        import os

        if not path or not os.path.exists(path):
            return

        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        self.preferences = defaultdict(lambda: defaultdict(int))
        for k, v in data.get("preferences", {}).items():
            for sk, sv in v.items():
                self.preferences[k][sk] = sv

        self.task_types = defaultdict(int)
        for k, v in data.get("task_types", {}).items():
            self.task_types[k] = v

        self.active_hours = set(data.get("active_hours", []))
        self.total_interactions = data.get("total_interactions", 0)
