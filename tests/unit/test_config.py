"""
配置系统单元测试
"""

import os
import tempfile

from nova_agent.config import Config


class TestConfigDefault:
    """测试默认配置"""

    def test_default_config_creation(self):
        """测试默认配置创建"""
        config = Config.default()
        assert config is not None
        assert config.max_levels == 3
        assert config.block_size == 8
        assert config.vector_backend == "chromadb"

    def test_default_memory_settings(self):
        """测试默认记忆设置"""
        config = Config.default()
        assert config.memory_data_dir == "./data/nova-agent/memory"
        assert config.enable_vector_prefilter is True

    def test_default_hgarn_settings(self):
        """测试默认HGARN设置"""
        config = Config.default()
        assert config.cumulative_gain_threshold == 2.5
        assert config.min_gate_for_continue == 0.15
        assert config.enable_recursive_decomposition is True


class TestConfigPresets:
    """测试预设配置模式"""

    def test_conservative_config(self):
        """测试保守配置"""
        config = Config.conservative()
        assert config.max_levels == 4
        assert config.cumulative_gain_threshold == 3.5
        assert config.block_size == 10

    def test_efficient_config(self):
        """测试高效配置"""
        config = Config.efficient()
        assert config.max_levels == 2
        assert config.cumulative_gain_threshold == 1.5
        assert config.block_size == 6


class TestConfigUpdate:
    """测试配置更新"""

    def test_partial_update(self):
        """测试部分更新"""
        config = Config.default()
        config.update({"max_levels": 5, "block_size": 10})
        assert config.max_levels == 5
        assert config.block_size == 10
        # 其他配置保持不变
        assert config.vector_backend == "chromadb"

    def test_update_unknown_key(self):
        """测试更新未知键（应忽略）"""
        config = Config.default()
        config.update({"unknown_key": 123, "max_levels": 5})
        assert config.max_levels == 5
        # unknown_key 不应被添加
        assert not hasattr(config, "unknown_key")


class TestConfigEvolution:
    """测试配置自主进化"""

    def test_low_quality_evolution(self):
        """测试低质量反馈时的进化"""
        config = Config.default()
        original_levels = config.max_levels
        changes = config.apply_evolution(quality_score=0.2)

        # 低质量应该增加处理深度
        assert config.max_levels > original_levels
        assert "max_levels" in changes
        assert "cumulative_gain_threshold" in changes

    def test_high_quality_evolution(self):
        """测试高质量反馈时的进化"""
        config = Config.default()
        original_levels = config.max_levels
        changes = config.apply_evolution(quality_score=0.95)

        # 高质量应该减少处理深度，提升效率
        assert config.max_levels < original_levels
        assert "max_levels" in changes

    def test_medium_quality_no_level_change(self):
        """测试中等质量反馈"""
        config = Config.default()
        config.apply_evolution(quality_score=0.5)

        # 中等质量主要调整侧抑制强度，不调整层级
        assert config.lateral_inhibition_base_strength > 0.2


class TestConfigPersistence:
    """测试配置持久化"""

    def test_save_and_load(self):
        """测试保存和加载配置"""
        config = Config.default()
        config.update({"max_levels": 7, "block_size": 12})

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_path = f.name

        try:
            config.save(temp_path)
            loaded_config = Config.load(temp_path)

            assert loaded_config.max_levels == 7
            assert loaded_config.block_size == 12
            assert loaded_config.vector_backend == config.vector_backend
        finally:
            os.unlink(temp_path)

    def test_load_nonexistent_file(self):
        """测试加载不存在的文件（应返回默认配置）"""
        config = Config.load("/nonexistent/path/config.json")
        assert config.max_levels == Config.default().max_levels


class TestConfigDictConversion:
    """测试配置字典转换"""

    def test_to_dict(self):
        """测试转换为字典"""
        config = Config.default()
        config_dict = config.to_dict()

        assert isinstance(config_dict, dict)
        assert config_dict["max_levels"] == config.max_levels
        assert config_dict["block_size"] == config.block_size

    def test_from_dict(self):
        """测试从字典创建"""
        data = {
            "max_levels": 10,
            "block_size": 15,
            "memory_data_dir": "./custom/memory",
            "vector_backend": "chromadb",
            "cumulative_gain_threshold": 2.5,
            "min_gate_for_continue": 0.15,
            "enable_vector_prefilter": True,
            "vector_similarity_threshold": 0.3,
            "enable_reverse_activation": True,
            "reverse_activation_gain_threshold": 0.3,
            "gate_at_block_level": False,
            "enable_recursive_decomposition": True,
            "max_recursion_depth": 3,
            "wta_max_activate": 7,
            "lateral_inhibition_enabled": True,
            "lateral_inhibition_base_strength": 0.2,
            "enable_dynamic_concurrency": True,
            "min_concurrency": 1,
            "max_concurrency": 8,
            "exponential_backoff_base": 2.0,
            "sandbox_type": "local",
            "sandbox_config": {},
            "llm_provider": "openclaw",
            "llm_config": {},
            "max_tokens_per_completion": 4096,
            "default_temperature": 0.7,
            "evolution_enabled": True,
            "auto_optimize_config": True,
            "min_quality_for_learning": 0.8,
            "skill_forgetting_enabled": True,
            "skill_forgetting_decay": 0.01,
            "enable_working_memory_partition": True,
        }
        config = Config.from_dict(data)
        assert config.max_levels == 10
        assert config.block_size == 15
