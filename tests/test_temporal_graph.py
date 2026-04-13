"""
测试技能反模式检查
"""

import pytest
from nova_agent.skills import AntipatternChecker
from nova_agent.config import ConfigManager
import tempfile
from pathlib import Path


def test_antipattern_checker_init():
    """测试反模式检查器初始化"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建默认配置目录
        (Path(tmpdir) / "default").mkdir()
        config = ConfigManager(tmpdir)
        checker = AntipatternChecker(config, None)
        assert checker is not None
        # 应该加载了反模式


def test_antipattern_checker_empty():
    """测试空内容检查"""
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "default").mkdir()
        config = ConfigManager(tmpdir)
        checker = AntipatternChecker(config, None)
        
        issues = checker.check("")
        assert len(issues) == 0


def test_antipattern_checker_category():
    """测试按类别检查"""
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "default").mkdir()
        config = ConfigManager(tmpdir)
        # 添加一个自定义反模式到配置
        config.set("antipatterns.general", [{
            "id": "test_inter_font",
            "name": "Inter 字体",
            "description": "使用Inter字体是常见AI生成的反模式",
            "keywords": ["Inter", "inter字体"],
            "severity": "major"
        }])
        checker = AntipatternChecker(config, None)
        
        text_with_antipattern = "这里使用了Inter字体设计"
        issues = checker.check(text_with_antipattern, "general")
        assert len(issues) > 0
        assert any("Inter" in issue["name"] for issue in issues)
