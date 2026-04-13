"""
测试配置系统
"""

import pytest
import tempfile
import os
from pathlib import Path
from nova_agent.config import ConfigManager


def test_config_manager_init():
    """测试配置管理器初始化"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建默认配置目录
        (Path(tmpdir) / "default").mkdir()
        config = ConfigManager(tmpdir)
        assert config is not None


def test_config_get_set():
    """测试配置获取和设置"""
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "default").mkdir()
        config = ConfigManager(tmpdir)
        config.set("test.key", "value")
        assert config.get("test.key") == "value"


def test_config_get_default():
    """测试配置获取带默认值"""
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "default").mkdir()
        config = ConfigManager(tmpdir)
        # 获取不存在的键应该返回默认值
        assert config.get("non.existent.key", "default_value") == "default_value"


def test_config_get_section():
    """测试批量获取配置"""
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "default").mkdir()
        config = ConfigManager(tmpdir)
        config.set("llm.model", "gpt-4")
        config.set("llm.temperature", 0.7)
        llm_config = config.get_section("llm")
        assert llm_config["model"] == "gpt-4"
        assert llm_config["temperature"] == 0.7
