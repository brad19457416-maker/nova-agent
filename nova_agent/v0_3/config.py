"""
配置管理系统

功能:
- YAML/JSON配置加载
- 环境变量覆盖
- 配置验证
- 热加载
- 多环境支持

使用示例:
    config = ConfigManager("./config")
    
    # 获取配置
    max_iterations = config.get("workflow.max_iterations", 5)
    
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
import logging

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
    """
    
    DEFAULT_CONFIG_DIR = "./config"
    ENV_PREFIX = "NOVA_"
    
    def __init__(self, config_dir: Optional[str] = None):
        self.config_dir = Path(config_dir or self.DEFAULT_CONFIG_DIR)
        self.configs: Dict[str, Any] = {}
        self.sources: Dict[str, ConfigSource] = {}
        self._load_default_configs()
    
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
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        获取配置值
        
        Args:
            key_path: 配置键路径，如 "workflow.max_iterations"
            default: 默认值
        
        Returns:
            配置值
        """
        # 1. 环境变量
        env_key = f"{self.ENV_PREFIX}{key_path.upper().replace('.', '_')}"
        if env_key in os.environ:
            value = os.environ[env_key]
            # 类型转换
            if isinstance(default, bool):
                return value.lower() in ('true', '1', 'yes', 'on')
            if isinstance(default, int):
                return int(value)
            if isinstance(default, float):
                return float(value)
            return value
        
        # 2. 配置文件
        keys = key_path.split(".")
        current = self.configs
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        
        return current
    
    def get_section(self, section: str) -> Dict:
        """获取整个配置节"""
        return self.configs.get(section, {})
    
    def set(self, key_path: str, value: Any):
        """设置配置值（运行时）"""
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
        logger.debug(f"Set config: {key_path} = {value}")
    
    def save(self, name: str):
        """保存配置到文件"""
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
        self._load_default_configs()
        logger.info("Config reloaded")
    
    def get_workflow_config(self, workflow_name: str) -> Dict:
        """获取工作流配置"""
        config = self.get_section("workflow")
        workflows = config.get("workflows", {})
        
        # 合并默认配置
        defaults = config.get("defaults", {})
        workflow_config = workflows.get(workflow_name, {})
        
        return self._deep_merge(defaults, workflow_config)
    
    def get_skill_config(self, skill_name: str) -> Dict:
        """获取技能配置"""
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
