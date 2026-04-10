"""
SkillLearner - 技能学习器

从成功案例中提取可复用的行为模式，
沉淀到技能宫殿，供后续调用。
"""

import json
import logging
from typing import Dict, List

from ..memory.palace import MemoryPalace

logger = logging.getLogger(__name__)


class SkillLearner:
    """
    技能学习器

    从成功的交互中学习新技能，沉淀到记忆宫殿。
    """

    def __init__(self, memory_palace: MemoryPalace):
        self.memory_palace = memory_palace

    def learn_from_example(self, query: str, response: str, evaluation) -> str:
        """
        从成功案例学习技能

        Args:
            query: 用户查询
            response: 成功响应
            evaluation: 评估结果

        Returns:
            新技能 ID
        """
        # 使用 LLM 提取技能模式
        skill_def = self._extract_skill_pattern(query, response)

        # 存储到技能宫殿
        # Wing: skills, Room: <category>, Hall: skills
        skill_id = self._store_skill(skill_def)

        logger.info(f"Learned new skill: {skill_def.get('name', 'unnamed')} → {skill_id}")
        return skill_id

    def _extract_skill_pattern(self, query: str, response: str) -> Dict:
        """提取可复用的技能模式"""
        # 这里需要 LLM 提取模式
        # 实际提取由外层 LLM 完成
        return {
            "query_pattern": query,
            "response_template": response,
            "name": self._generate_skill_name(query),
            "description": f"Learned from: {query[:100]}",
            "created_at": self._get_timestamp(),
        }

    def _generate_skill_name(self, query: str) -> str:
        """生成技能名称"""
        # 取前几个词
        words = query.split()[:5]
        return "_".join(words)

    def _store_skill(self, skill_def: Dict) -> str:
        """存储技能到记忆宫殿"""
        # 分类到技能 wing
        content = json.dumps(skill_def, ensure_ascii=False, indent=2)

        skill_id = self.memory_palace.add_memory(
            wing="skills", room="learned", hall="skills", content=content, compressed=True
        )

        return skill_id

    def list_learned_skills(self) -> List[Dict]:
        """列出所有学习到的技能"""
        wings = self.memory_palace.list_wings()
        if "skills" not in wings:
            return []

        rooms = self.memory_palace.list_rooms("skills")
        skills = []

        # 这里需要遍历，简化返回
        return skills

    def _get_timestamp(self) -> str:
        from datetime import datetime

        return datetime.utcnow().isoformat()
