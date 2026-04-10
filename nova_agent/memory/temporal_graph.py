"""
TemporalFactGraph - 时序事实图谱

继承我们 HGARN 的创新：
- 实体-关系-实体 三元组结构
- 支持事实有效性时间窗口
- 更新不删除历史，保持完整时间线
- 支持时间感知查询
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class Fact:
    """事实三元组"""

    subject: str
    predicate: str
    object: str
    start_time: str  # ISO 格式，有效开始时间
    end_time: Optional[str] = None  # 有效结束时间，None 表示仍然有效
    fact_id: Optional[str] = None
    confidence: float = 1.0
    source: Optional[str] = None

    def is_valid_at(self, query_time: str) -> bool:
        """检查在查询时间点是否有效"""
        if self.end_time is None:
            return query_time >= self.start_time
        return self.start_time <= query_time <= self.end_time

    def to_dict(self) -> Dict:
        return {
            "subject": self.subject,
            "predicate": self.predicate,
            "object": self.object,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "fact_id": self.fact_id,
            "confidence": self.confidence,
            "source": self.source,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Fact":
        return cls(**data)


class TemporalFactGraph:
    """
    时序事实图谱

    核心特性：
    - 追踪实体关系随时间变化
    - 不删除历史，只添加新事实
    - 每个事实有有效性时间窗口
    - 支持基于时间的查询
    """

    def __init__(self):
        self.facts: List[Fact] = []
        self.entity_index: Dict[str, List[str]] = {}  # entity -> fact_ids
        self.next_id = 0

    def add_fact(
        self,
        subject: str,
        predicate: str,
        object_: str,
        start_time: Optional[str] = None,
        confidence: float = 1.0,
        source: Optional[str] = None,
    ) -> Fact:
        """
        添加新事实

        如果已经存在同一 (subject, predicate) 的事实，自动设置其 end_time
        """
        if start_time is None:
            start_time = datetime.utcnow().isoformat()

        # 查找现有的相同主题-谓词事实
        existing = self._find_open_facts(subject, predicate)

        # 关闭现有事实（设置 end_time）
        for fact in existing:
            fact.end_time = start_time

        # 创建新事实
        fact = Fact(
            subject=subject,
            predicate=predicate,
            object=object_,
            start_time=start_time,
            end_time=None,
            fact_id=f"fact_{self.next_id}",
            confidence=confidence,
            source=source,
        )

        self.next_id += 1
        self.facts.append(fact)

        # 更新索引
        if subject not in self.entity_index:
            self.entity_index[subject] = []
        self.entity_index[subject].append(fact.fact_id)

        if object_ not in self.entity_index:
            self.entity_index[object_] = []
        self.entity_index[object_].append(fact.fact_id)

        logger.debug(f"Added fact: {subject} {predicate} {object_}")
        return fact

    def _find_open_facts(self, subject: str, predicate: str) -> List[Fact]:
        """查找当前开放（end_time=None）的相同主题-谓词事实"""
        return [
            f
            for f in self.facts
            if f.subject == subject and f.predicate == predicate and f.end_time is None
        ]

    def get_current_facts(self, subject: str, predicate: Optional[str] = None) -> List[Fact]:
        """获取当前有效的事实"""
        facts = []
        for fact in self.facts:
            if fact.subject == subject:
                if predicate is None or fact.predicate == predicate:
                    if fact.end_time is None:
                        facts.append(fact)
        return facts

    def get_facts_at_time(
        self, subject: str, query_time: str, predicate: Optional[str] = None
    ) -> List[Fact]:
        """获取在指定时间点有效的事实"""
        facts = []
        for fact in self.facts:
            if fact.subject == subject:
                if predicate is None or fact.predicate == predicate:
                    if fact.is_valid_at(query_time):
                        facts.append(fact)
        return facts

    def get_history(self, subject: str, predicate: str) -> List[Fact]:
        """获取事实的完整历史变化"""
        facts = [f for f in self.facts if f.subject == subject and f.predicate == predicate]
        # 按开始时间排序
        facts.sort(key=lambda f: f.start_time)
        return facts

    def search_relevant(self, query: str, top_k: int = 10) -> List[Dict]:
        """搜索与查询相关的事实（简单关键词匹配，向量检索在外层）"""
        relevant = []
        query_words = set(query.lower().split())

        for fact in self.facts:
            text = f"{fact.subject} {fact.predicate} {fact.object}".lower()
            overlap = len(query_words & set(text.split()))
            if overlap > 0:
                relevant.append(
                    {
                        "fact": fact.to_dict(),
                        "overlap": overlap,
                        "is_current": fact.end_time is None,
                    }
                )

        relevant.sort(key=lambda x: -x["overlap"])
        return relevant[:top_k]

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        current_count = sum(1 for f in self.facts if f.end_time is None)
        entities = set()
        for fact in self.facts:
            entities.add(fact.subject)
            entities.add(fact.object)

        return {
            "total_facts": len(self.facts),
            "current_valid_facts": current_count,
            "total_entities": len(entities),
        }

    def save(self, path: str) -> None:
        """保存图谱到文件"""
        data = {
            "facts": [f.to_dict() for f in self.facts],
            "next_id": self.next_id,
            "entity_index": self.entity_index,
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load(self, path: str) -> None:
        """从文件加载图谱"""
        import json

        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        self.facts = [Fact.from_dict(d) for d in data["facts"]]
        self.next_id = data.get("next_id", len(self.facts))
        self.entity_index = data.get("entity_index", {})

    def query_chain(self, start_entity: str, max_depth: int = 3) -> List[Dict]:
        """BFS 遍历查询实体关系链"""
        visited = set()
        queue = [(start_entity, 0)]
        visited.add(start_entity)
        results = []

        while queue:
            entity, depth = queue.pop(0)
            if depth >= max_depth:
                continue

            fact_ids = self.entity_index.get(entity, [])
            for fact_id in fact_ids:
                fact = next((f for f in self.facts if f.fact_id == fact_id), None)
                if fact:
                    results.append({"depth": depth, "fact": fact.to_dict()})

                    next_entity = fact.object
                    if next_entity not in visited:
                        visited.add(next_entity)
                        queue.append((next_entity, depth + 1))

        return results
