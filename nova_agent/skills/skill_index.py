"""
Skill Index - 技能索引检索

基于向量检索快速找到相关技能。
"""

import logging
from typing import Any, Dict, List, Optional

from ..memory.vector_store import VectorStore
from .skill_def import Skill

logger = logging.getLogger(__name__)


class SkillIndex:
    """技能索引"""

    def __init__(self, vector_store: VectorStore = None):
        self.vector_store = vector_store or VectorStore("memory")
        self.skills: Dict[str, Skill] = {}

    def add_skill(self, skill: Skill) -> None:
        """添加技能到索引"""
        self.skills[skill.name] = skill

        # 索引用于检索
        text = f"{skill.name} {skill.description}"
        if skill.workflow:
            text += " " + " ".join(skill.workflow)

        self.vector_store.add(
            text=text,
            metadata={"name": skill.name, "category": skill.category, "version": skill.version},
        )

        logger.debug(f"Added skill to index: {skill.name}")

    def search_relevant(self, query: str, top_k: int = 5) -> List[Skill]:
        """搜索相关技能"""
        results = self.vector_store.search(query, top_k=top_k)

        skills = []
        for result in results:
            metadata = result.get("metadata", {})
            name = metadata.get("name")
            if name in self.skills:
                skills.append(self.skills[name])

        return skills

    def get_by_name(self, name: str) -> Optional[Skill]:
        """按名称获取技能"""
        return self.skills.get(name)

    def list_skills(self, category: Optional[str] = None) -> List[Skill]:
        """列出所有技能"""
        if category:
            return [s for s in self.skills.values() if s.category == category]
        return list(self.skills.values())

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        categories = {}
        for skill in self.skills.values():
            cat = skill.category
            categories[cat] = categories.get(cat, 0) + 1

        return {"total_skills": len(self.skills), "by_category": categories}

    def load_from_loader(self, loader) -> None:
        """从加载器加载所有技能"""
        skills = loader.load_from_directory()
        for skill in skills:
            self.add_skill(skill)
        logger.info(f"Loaded {len(skills)} skills into index")
