"""
测试技能加载
"""

import pytest
import tempfile
from pathlib import Path
from nova_agent.config import ConfigManager
from nova_agent.skills import SkillLoader


def test_skill_loader_init():
    """测试技能加载器初始化"""
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "default").mkdir()
        config = ConfigManager(tmpdir)
        # 设置技能搜索路径
        config.set("skills.search_paths", ["./nova_agent/skills"])
        loader = SkillLoader(config)
        assert loader is not None


def test_skill_list_skills():
    """测试列出技能"""
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "default").mkdir()
        config = ConfigManager(tmpdir)
        config.set("skills.search_paths", ["./nova_agent/skills"])
        loader = SkillLoader(config)
        # 列出已加载技能
        skills = loader.list_skills()
        assert isinstance(skills, list)
