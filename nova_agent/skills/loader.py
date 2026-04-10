"""
技能加载器

性能优化:
- 技能配置缓存
- 延迟加载实现
- 模块热重载
- 并发安全

使用示例:
    loader = SkillLoader(config_manager)
    
    # 异步加载 (带缓存)
    skill = await loader.load("research_skill")
    
    # 批量加载
    skills = await loader.load_batch(["research_skill", "writing_skill"])
    
    # 执行
    result = await skill.execute(context)
"""

import asyncio
import yaml
import importlib
import importlib.util
from pathlib import Path
from typing import Dict, List, Optional, Any, Type
from dataclasses import dataclass, field
from functools import lru_cache
import logging
import time

logger = logging.getLogger(__name__)


@dataclass
class SkillConfig:
    """技能配置"""
    name: str
    description: str
    version: str = "1.0.0"
    domain: str = "general"
    phases: List[Dict] = field(default_factory=list)
    antipatterns: List[Dict] = field(default_factory=list)
    references: List[Dict] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)


class BaseSkill:
    """
    技能基类
    
    所有技能必须继承此类
    """
    
    def __init__(self, config: SkillConfig):
        self.config = config
        self._initialized = False
    
    async def _init(self):
        """延迟初始化"""
        if not self._initialized:
            await self._setup()
            self._initialized = True
    
    async def _setup(self):
        """初始化逻辑 (子类重写)"""
        pass
    
    async def execute(self, context: Dict) -> Any:
        """执行技能"""
        await self._init()
        raise NotImplementedError
    
    async def execute_phase(self, phase_name: str, context: Dict) -> Any:
        """执行单个阶段"""
        await self._init()
        method = getattr(self, f"phase_{phase_name}", None)
        if method:
            return await method(context)
        return {"error": f"Phase {phase_name} not implemented"}


class SkillLoader:
    """
    技能加载器

    性能特性:
    - 技能配置LRU缓存
    - 延迟加载实现模块
    - 热重载支持 (开发模式)
    - 并发安全
    - 批量加载优化
    """
    
    def __init__(
        self,
        config_manager,
        skills_dir: str = "./config/skills",
        enable_cache: bool = True,
        cache_ttl: float = 60.0
    ):
        """
        初始化技能加载器

        Args:
            config_manager: 配置管理器
            skills_dir: 技能配置目录
            enable_cache: 是否启用缓存
            cache_ttl: 缓存有效期(秒)
        """
        self.config_manager = config_manager
        self.skills_dir = Path(skills_dir)
        self._enable_cache = enable_cache
        self._cache_ttl = cache_ttl
        
        # 技能缓存
        self._skill_cache: Dict[str, BaseSkill] = {}
        self._config_cache: Dict[str, SkillConfig] = {}
        self._cache_timestamp: Dict[str, float] = {}
        
        # 锁
        self._lock = asyncio.Lock()
        
        # 延迟加载的技能类
        self._skill_classes: Dict[str, Type[BaseSkill]] = {}
        
        # 注册默认技能
        self._register_default_skills()
    
    def _register_default_skills(self):
        """注册默认技能 (延迟加载)"""
        # 默认技能配置
        default_configs = {
            "research_skill": {
                "name": "research_skill",
                "description": "深度研究技能",
                "domain": "research",
                "phases": ["clarify", "plan", "search", "expand", "verify", "synthesize", "deliver"]
            },
            "writing_skill": {
                "name": "writing_skill",
                "description": "专业写作技能",
                "domain": "writing",
                "phases": ["outline", "draft", "review", "revise", "polish", "deliver"]
            },
            "code_skill": {
                "name": "code_skill",
                "description": "代码开发技能",
                "domain": "code",
                "phases": ["analyze", "design", "implement", "test", "refactor", "deliver"]
            }
        }
        
        for name, config in default_configs.items():
            self._config_cache[name] = SkillConfig(**config)
    
    def _get_cache_key(self, skill_name: str) -> str:
        """获取缓存键"""
        return f"skill:{skill_name}"
    
    def _is_cache_valid(self, skill_name: str) -> bool:
        """检查缓存是否有效"""
        if not self._enable_cache:
            return False
        
        key = self._get_cache_key(skill_name)
        if key not in self._skill_cache:
            return False
        
        timestamp = self._cache_timestamp.get(key, 0)
        return time.time() - timestamp < self._cache_ttl
    
    def _set_cache(self, skill_name: str, skill: BaseSkill):
        """设置缓存"""
        if not self._enable_cache:
            return
        
        key = self._get_cache_key(skill_name)
        self._skill_cache[key] = skill
        self._cache_timestamp[key] = time.time()
    
    def _invalidate_cache(self, skill_name: str = None):
        """使缓存失效"""
        if skill_name:
            key = self._get_cache_key(skill_name)
            self._skill_cache.pop(key, None)
            self._cache_timestamp.pop(key, None)
        else:
            self._skill_cache.clear()
            self._cache_timestamp.clear()
    
    async def load(self, skill_name: str) -> Optional[BaseSkill]:
        """
        加载技能 (带缓存)

        Args:
            skill_name: 技能名称

        Returns:
            技能实例或None
        """
        # 检查缓存
        if self._is_cache_valid(skill_name):
            return self._skill_cache[self._get_cache_key(skill_name)]
        
        async with self._lock:
            # 双重检查
            if self._is_cache_valid(skill_name):
                return self._skill_cache[self._get_cache_key(skill_name)]
            
            # 加载配置
            config = await self._load_config(skill_name)
            if not config:
                logger.warning(f"Skill config not found: {skill_name}")
                return None
            
            # 创建技能实例
            skill = self._create_skill(config)
            if skill:
                self._set_cache(skill_name, skill)
                logger.info(f"Loaded skill: {skill_name}")
            
            return skill
    
    async def load_batch(self, skill_names: List[str]) -> Dict[str, Optional[BaseSkill]]:
        """
        批量加载技能

        比逐个加载更高效，因为可以并发执行

        Args:
            skill_names: 技能名称列表

        Returns:
            技能字典 {name: skill}
        """
        tasks = [self.load(name) for name in skill_names]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return {
            name: result if not isinstance(result, Exception) else None
            for name, result in zip(skill_names, results)
        }
    
    async def _load_config(self, skill_name: str) -> Optional[SkillConfig]:
        """加载技能配置"""
        # 检查内存缓存
        if skill_name in self._config_cache:
            return self._config_cache[skill_name]
        
        # 从配置管理器加载
        config_data = self.config_manager.get_skill_config(skill_name)
        
        if not config_data:
            return None
        
        config = SkillConfig(
            name=config_data.get("name", skill_name),
            description=config_data.get("description", ""),
            version=config_data.get("version", "1.0.0"),
            domain=config_data.get("domain", "general"),
            phases=config_data.get("phases", []),
            antipatterns=config_data.get("antipatterns", []),
            references=config_data.get("references", []),
            metadata=config_data.get("metadata", {})
        )
        
        self._config_cache[skill_name] = config
        return config
    
    def _create_skill(self, config: SkillConfig) -> Optional[BaseSkill]:
        """创建技能实例"""
        # 首先尝试从已注册的类创建
        if config.name in self._skill_classes:
            skill_class = self._skill_classes[config.name]
            return skill_class(config)
        
        # 尝试动态加载
        skill = self._load_dynamic_skill(config)
        if skill:
            return skill
        
        # 使用默认基类
        return BaseSkill(config)
    
    def _load_dynamic_skill(self, config: SkillConfig) -> Optional[BaseSkill]:
        """动态加载技能实现"""
        # 尝试从文件加载
        skill_file = self.skills_dir / f"{config.name}.py"
        
        if not skill_file.exists():
            return None
        
        try:
            spec = importlib.util.spec_from_file_location(
                config.name, skill_file
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # 查找技能类
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and 
                    issubclass(attr, BaseSkill) and 
                    attr is not BaseSkill):
                    return attr(config)
            
            return None
        except Exception as e:
            logger.error(f"Failed to load skill {config.name}: {e}")
            return None
    
    def register_skill_class(self, name: str, skill_class: Type[BaseSkill]):
        """
        注册技能类

        Args:
            name: 技能名称
            skill_class: 技能类
        """
        self._skill_classes[name] = skill_class
        self._invalidate_cache(name)
        logger.info(f"Registered skill class: {name}")
    
    def get_antipatterns(self, skill_name: str) -> List[Dict]:
        """获取技能反模式"""
        config = self._config_cache.get(skill_name)
        if config:
            return config.antipatterns
        return []
    
    def list_skills(self) -> List[str]:
        """列出所有已加载的技能"""
        return [
            key.split(":")[1] 
            for key in self._skill_cache.keys() 
            if key.startswith("skill:")
        ]
    
    def invalidate_skill(self, skill_name: str):
        """使技能缓存失效"""
        self._invalidate_cache(skill_name)
        logger.info(f"Invalidated skill cache: {skill_name}")
    
    def clear_cache(self):
        """清除所有缓存"""
        self._invalidate_cache()
        self._config_cache.clear()
        logger.info("Skill cache cleared")
