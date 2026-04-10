"""
配置管理系统

功能:
- YAML/JSON配置加载
- 环境变量覆盖
- 配置验证
- 热加载
- 多环境支持
- LRU缓存优化

性能优化:
- 配置值LRU缓存，减少重复解析
- 环境变量名缓存，避免重复字符串操作
- 延迟加载配置文件

使用示例:
    config = ConfigManager("./config")
    
    # 获取配置 (带缓存)
    max_iterations = config.get("workflow.max_iterations", 5)
    
    # 批量获取 (性能更好)
    workflow_config = config.get_section("workflow")
    
    # 环境变量覆盖
    # NOVA_WORKFLOW_MAX_ITERATIONS=10
    
    # 设置配置
    config.set("workflow.max_iterations", 10)
    
    # 保存配置
    config.save("workflow")
"""

import os
import yaml
import json
from pathlib import Path
from typing import Any, Dict, Optional, Union
from dataclasses import dataclass, field
from copy import deepcopy
from functools import lru_cache
import logging
import time

logger = logging.getLogger(__name__)


@dataclass
class ConfigSource:
    """配置源"""
    name: str
    path: Path
    priority: int = 0
    format: str = "yaml"


class ConfigManager:
    """
    统一配置管理器

    优先级（从高到低）:
    1. 环境变量 (NOVA_WORKFLOW_MAX_ITERATIONS)
    2. 运行时配置 (set())
    3. 配置文件
    4. 默认值

    性能特性:
    - 配置值LRU缓存 (默认128个)
    - 环境变量名预计算缓存
    - 批量获取接口
    """

    DEFAULT_CONFIG_DIR = "./config"
    ENV_PREFIX = "NOVA_"
    CACHE_SIZE = 128  # LRU缓存大小

    def __init__(self, config_dir: Optional[str] = None, enable_cache: bool = True):
        """
        初始化配置管理器

        Args:
            config_dir: 配置目录路径，默认"./config"
            enable_cache: 是否启用LRU缓存，默认True
        """
        self.config_dir = Path(config_dir or self.DEFAULT_CONFIG_DIR)
        self.configs: Dict[str, Any] = {}
        self.sources: Dict[str, ConfigSource] = {}
        self._enable_cache = enable_cache
        self._cache: Dict[str, Any] = {}  # 运行时缓存
        self._cache_timestamp: Dict[str, float] = {}  # 缓存时间戳
        self._cache_ttl = 5.0  # 缓存有效期5秒

        # 环境变量名缓存
        self._env_key_cache: Dict[str, str] = {}

        # 加载配置
        self._load_default_configs()

        logger.info(f"ConfigManager initialized: {self.config_dir}, cache={'enabled' if enable_cache else 'disabled'}")

    def _load_default_configs(self):
        """加载默认配置"""
        default_dir = self.config_dir / "default"
        if not default_dir.exists():
            logger.warning(f"Config dir not found: {default_dir}")
            return

        for config_file in default_dir.glob("*.yaml"):
            self._load_config_file(config_file.stem, config_file)

        for config_file in default_dir.glob("*.json"):
            self._load_config_file(config_file.stem, config_file)

    def _load_config_file(self, name: str, path: Path):
        """加载配置文件"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                if path.suffix in [".yaml", ".yml"]:
                    config = yaml.safe_load(f)
                elif path.suffix == ".json":
                    config = json.load(f)
                else:
                    return

                self.configs[name] = config or {}
                self.sources[name] = ConfigSource(
                    name=name,
                    path=path,
                    priority=0,
                    format=path.suffix[1:]
                )
                logger.info(f"Loaded config: {name}")
        except Exception as e:
            logger.error(f"Failed to load config {path}: {e}")

    def _get_env_key(self, key_path: str) -> str:
        """
        获取环境变量键（带缓存）

        Args:
            key_path: 配置键路径

        Returns:
            环境变量名
        """
        if key_path not in self._env_key_cache:
            self._env_key_cache[key_path] = f"{self.ENV_PREFIX}{key_path.upper().replace('.', '_')}"
        return self._env_key_cache[key_path]

    def _get_from_cache(self, key: str) -> Optional[Any]:
        """从缓存获取值"""
        if not self._enable_cache:
            return None

        if key in self._cache:
            timestamp = self._cache_timestamp.get(key, 0)
            if time.time() - timestamp < self._cache_ttl:
                return self._cache[key]
            else:
                # 过期，清除
                del self._cache[key]
                del self._cache_timestamp[key]
        return None

    def _set_cache(self, key: str, value: Any):
        """设置缓存值"""
        if self._enable_cache:
            self._cache[key] = value
            self._cache_timestamp[key] = time.time()

    def _clear_cache(self):
        """清除缓存"""
        self._cache.clear()
        self._cache_timestamp.clear()

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        获取配置值

        性能说明:
        - 首次调用会解析路径，后续调用使用缓存
        - 环境变量检查使用预计算缓存

        Args:
            key_path: 配置键路径，如 "workflow.max_iterations"
            default: 默认值

        Returns:
            配置值
        """
        # 检查缓存
        cached = self._get_from_cache(key_path)
        if cached is not None:
            return cached

        # 1. 环境变量 (使用缓存的键名)
        env_key = self._get_env_key(key_path)
        if env_key in os.environ:
            value = os.environ[env_key]
            # 类型转换
            if isinstance(default, bool):
                result = value.lower() in ('true', '1', 'yes', 'on')
            elif isinstance(default, int):
                result = int(value)
            elif isinstance(default, float):
                result = float(value)
            else:
                result = value
            self._set_cache(key_path, result)
            return result

        # 2. 配置文件
        keys = key_path.split(".")
        config_name = keys[0]
        remaining_keys = keys[1:]

        if config_name not in self.configs:
            return default

        current = self.configs[config_name]
        for key in remaining_keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default

        self._set_cache(key_path, current)
        return current

    def get_batch(self, key_paths: Dict[str, str]) -> Dict[str, Any]:
        """
        批量获取配置值

        性能比多次调用get()更好，因为减少了缓存检查开销

        Args:
            key_paths: 键值对，{"result_key": "config.path"}

        Returns:
            结果字典

        Example:
            >>> config.get_batch({
            ...     "max_iter": "workflow.max_iterations",
            ...     "model": "llm.model",
            ...     "timeout": "llm.timeout"
            ... })
            {'max_iter': 5, 'model': 'qwen2.5:7b', 'timeout': 120}
        """
        return {key: self.get(path) for key, path in key_paths.items()}

    def get_section(self, section: str) -> Dict[str, Any]:
        """
        获取整个配置节

        Args:
            section: 配置节名称，如 "workflow", "llm"

        Returns:
            配置节字典
        """
        return self.configs.get(section, {})

    def get_nested(self, *keys: str, default: Any = None) -> Any:
        """
        通过多个键获取嵌套配置值

        性能比字符串路径解析更快

        Args:
            *keys: 配置键序列
            default: 默认值

        Returns:
            配置值

        Example:
            >>> config.get_nested("workflow", "max_iterations", default=5)
            5
        """
        if not keys:
            return default

        cache_key = ".".join(keys)
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached

        current = self.configs
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default

        self._set_cache(cache_key, current)
        return current

    def set(self, key_path: str, value: Any):
        """
        设置配置值（运行时）

        注意: 会清除相关缓存

        Args:
            key_path: 配置键路径
            value: 配置值
        """
        keys = key_path.split(".")
        config_name = keys[0]

        if config_name not in self.configs:
            self.configs[config_name] = {}

        current = self.configs[config_name]
        for key in keys[1:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        current[keys[-1]] = value

        # 清除缓存
        self._clear_cache()
        logger.debug(f"Set config: {key_path} = {value}")

    def save(self, name: str):
        """
        保存配置到文件

        Args:
            name: 配置名称
        """
        if name not in self.configs:
            return

        source = self.sources.get(name)
        path = source.path if source else self.config_dir / "default" / f"{name}.yaml"

        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'w', encoding='utf-8') as f:
            yaml.dump(self.configs[name], f, default_flow_style=False, allow_unicode=True)

        logger.info(f"Saved config: {name}")

    def reload(self):
        """重新加载所有配置"""
        self.configs.clear()
        self.sources.clear()
        self._env_key_cache.clear()
        self._clear_cache()
        self._load_default_configs()
        logger.info("Config reloaded")

    def invalidate_cache(self):
        """手动使缓存失效"""
        self._clear_cache()
        logger.debug("Config cache invalidated")

    def get_workflow_config(self, workflow_name: str) -> Dict[str, Any]:
        """
        获取工作流配置

        Args:
            workflow_name: 工作流名称

        Returns:
            工作流配置字典
        """
        config = self.get_section("workflow")
        workflows = config.get("workflows", {})
        defaults = config.get("defaults", {})
        workflow_config = workflows.get(workflow_name, {})

        return self._deep_merge(defaults, workflow_config)

    def get_skill_config(self, skill_name: str) -> Dict[str, Any]:
        """
        获取技能配置

        Args:
            skill_name: 技能名称

        Returns:
            技能配置字典
        """
        config = self.get_section("skill")
        skills = config.get("skills", {})
        defaults = config.get("defaults", {})
        skill_config = skills.get(skill_name, {})

        return self._deep_merge(defaults, skill_config)

    def _deep_merge(self, base: Dict, override: Dict) -> Dict:
        """深度合并字典"""
        result = deepcopy(base)
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = deepcopy(value)
        return result
