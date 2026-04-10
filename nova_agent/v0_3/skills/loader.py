"""
技能加载器

YAML配置 + Python实现分离

使用示例:
    loader = SkillLoader("./config/skills")
    
    # 加载技能
    skill = loader.load("research_skill")
    
    # 执行
    result = await skill.execute(context)
    
    # 获取反模式
    antipatterns = loader.get_antipatterns("research_skill")
"""

import yaml
import importlib
import importlib.util
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import logging

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
    """技能基类"""
    
    def __init__(self, config: SkillConfig):
        self.config = config
    
    async def execute(self, context: Dict) -> Any:
        """执行技能"""
        raise NotImplementedError
    
    async def execute_phase(self, phase_name: str, context: Dict) -> Any:
        """执行单个阶段"""
        method = getattr(self, f"phase_{phase_name}", None)
        if method:
            return await method(context)
        return {"error": f"Phase {phase_name} not implemented"}


class SkillLoader:
    """
    技能加载器
    
    特性:
    - YAML配置 + Python实现
    - 自动依赖注入
    - 热加载支持
    """
    
    def __init__(self, config_manager, skills_dir: str = "./config/skills"):
        self.config_manager = config_manager
        self.skills_dir = Path(skills_dir)
        self.loaded_skills: Dict[str, BaseSkill] = {}
        self.skill_configs: Dict[str, SkillConfig] = {}
        
        # 注册默认技能
        self._register_default_skills()
    
    def _register_default_skills(self):
        """注册默认技能"""
        # 从配置加载技能
        skill_config = self.config_manager.get_section("skill")
        skills = skill_config.get("skills", {})
        
        for skill_name, skill_data in skills.items():
            config = SkillConfig(
                name=skill_data.get("name", skill_name),
                description=skill_data.get("description", ""),
                version=skill_data.get("version", "1.0.0"),
                domain=skill_data.get("domain", "general"),
                phases=skill_data.get("phases", []),
                antipatterns=skill_data.get("antipatterns", []),
                references=skill_data.get("references", []),
                metadata=skill_data.get("metadata", {})
            )
            self.skill_configs[skill_name] = config
        
        logger.info(f"Registered {len(self.skill_configs)} skills from config")
    
    def load(self, skill_name: str) -> BaseSkill:
        """加载技能"""
        if skill_name in self.loaded_skills:
            return self.loaded_skills[skill_name]
        
        # 获取配置
        config = self.skill_configs.get(skill_name)
        if not config:
            # 尝试从配置文件加载
            config_path = self.skills_dir / f"{skill_name}.yaml"
            if config_path.exists():
                with open(config_path) as f:
                    data = yaml.safe_load(f)
                    config = SkillConfig(**data)
            else:
                raise FileNotFoundError(f"Skill not found: {skill_name}")
        
        # 尝试加载实现
        skill = self._load_implementation(config)
        
        self.loaded_skills[skill_name] = skill
        logger.info(f"Loaded skill: {skill_name}")
        
        return skill
    
    def _load_implementation(self, config: SkillConfig) -> BaseSkill:
        """加载技能实现"""
        # 尝试查找实现文件
        impl_paths = [
            self.skills_dir.parent / "skills" / "builtin" / f"{config.name}_impl.py",
            self.skills_dir / "impl" / f"{config.name}_impl.py",
            Path("./skills") / f"{config.name}_impl.py"
        ]
        
        for impl_path in impl_paths:
            if impl_path.exists():
                return self._import_skill(impl_path, config)
        
        # 使用默认实现
        logger.warning(f"No implementation found for {config.name}, using default")
        return DefaultSkill(config)
    
    def _import_skill(self, impl_path: Path, config: SkillConfig) -> BaseSkill:
        """导入技能实现"""
        spec = importlib.util.spec_from_file_location(
            f"{config.name}_impl",
            impl_path
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # 构建类名
        class_name = "".join([
            w.capitalize() 
            for w in config.name.replace("-", "_").split("_")
        ]) + "Skill"
        
        skill_class = getattr(module, class_name, None)
        
        if skill_class:
            return skill_class(config)
        
        return DefaultSkill(config)
    
    def load_all(self) -> Dict[str, BaseSkill]:
        """加载所有技能"""
        for skill_name in self.skill_configs.keys():
            try:
                self.load(skill_name)
            except Exception as e:
                logger.error(f"Failed to load {skill_name}: {e}")
        
        return self.loaded_skills
    
    def get_config(self, skill_name: str) -> Optional[SkillConfig]:
        """获取技能配置"""
        return self.skill_configs.get(skill_name)
    
    def get_antipatterns(self, skill_name: str) -> List[Dict]:
        """获取技能反模式"""
        config = self.skill_configs.get(skill_name)
        return config.antipatterns if config else []
    
    def search(self, keyword: str) -> List[str]:
        """搜索技能"""
        results = []
        
        for name, config in self.skill_configs.items():
            if keyword.lower() in name.lower():
                results.append(name)
            elif keyword.lower() in config.description.lower():
                results.append(name)
        
        return results
    
    def list_skills(self) -> List[str]:
        """列出所有技能"""
        return list(self.skill_configs.keys())


class DefaultSkill(BaseSkill):
    """默认技能实现"""
    
    async def execute(self, context: Dict) -> Dict:
        """执行技能"""
        results = {}
        
        for phase in self.config.phases:
            phase_name = phase.get("name", "unknown")
            # 调用LLM执行
            results[phase_name] = f"Executed {phase_name}"
        
        return results


class MockLLM:
    """模拟LLM（用于测试）"""
    
    async def complete(self, prompt: str) -> str:
        return f"Mock response for: {prompt[:50]}..."
