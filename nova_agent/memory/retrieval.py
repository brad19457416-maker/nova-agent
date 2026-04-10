"""
HierarchicalRetriever - 分层检索器

MemPalace 启发：先按宫殿层级过滤，再向量检索，提升精度。
"""

import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class HierarchicalRetriever:
    """
    分层检索器

    先按 Wing → Room 层级过滤，只在相关区域内检索，
    减少干扰，提升精度。
    """

    def __init__(self, memory_palace, vector_store):
        self.palace = memory_palace
        self.vector_store = vector_store

    def hierarchical_retrieve(
        self, query: str, wing: Optional[str] = None, room: Optional[str] = None, top_k: int = 10
    ) -> List[Dict]:
        """
        分层检索

        Args:
            query: 查询文本
            wing: 可选，限定侧翼（如果知道当前项目
            room: 可选，限定房间
            top_k: 返回结果数

        Returns:
            检索结果列表
        """
        # 如果没有限定，先基于查询推断 Wing 和 Room
        if wing is None:
            # 先做全局检索，让 LLM 看结果
            return self._global_retrieve(query, top_k)
        else:
            # 限定在指定 Wing 内
            if room is None:
                return self._retrieve_in_wing(query, wing, top_k)
            else:
                return self._retrieve_in_room(query, wing, room, top_k)

    def _global_retrieve(self, query: str, top_k: int) -> List[Dict]:
        """全局检索"""
        return self.vector_store.search(query, top_k=top_k)

    def _retrieve_in_wing(self, query: str, wing: str, top_k: int) -> List[Dict]:
        """在指定侧翼内检索"""
        all_results = self.vector_store.search(query, top_k=top_k * 2)

        # 过滤出该侧翼
        wing_results = [r for r in all_results if r.get("metadata", {}).get("wing") == wing]

        # 如果不够，补充其他结果
        if len(wing_results) < top_k:
            other_results = [r for r in all_results if r.get("metadata", {}).get("wing") != wing]
            wing_results.extend(other_results[: top_k - len(wing_results)])

        return wing_results[:top_k]

    def _retrieve_in_room(self, query: str, wing: str, room: str, top_k: int) -> List[Dict]:
        """在指定房间内检索"""
        all_results = self.vector_store.search(query, top_k=top_k * 3)

        # 双层过滤
        room_results = [
            r
            for r in all_results
            if r.get("metadata", {}).get("wing") == wing
            and r.get("metadata", {}).get("room") == room
        ]

        # 不够补充翼内其他房间
        if len(room_results) < top_k:
            wing_other = [
                r
                for r in all_results
                if r.get("metadata", {}).get("wing") == wing
                and r.get("metadata", {}).get("room") != room
            ]
            room_results.extend(wing_other[: top_k - len(room_results)])

            # 还不够补充全局
            if len(room_results) < top_k:
                other = [r for r in all_results if r.get("metadata", {}).get("wing") != wing]
                room_results.extend(other[: top_k - len(room_results)])

        return room_results[:top_k]

    def filter_by_hall(self, results: List[Dict], hall: str) -> List[Dict]:
        """按厅堂类型过滤"""
        return [r for r in results if r.get("metadata", {}).get("hall") == hall]
