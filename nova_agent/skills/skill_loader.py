"""
Skill Loader - 技能加载器

从 Markdown 文件加载技能，支持渐进式按需加载。
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
import yaml
import re
import logging
from .skill_def import Skill

logger = logging.getLogger(__name__)


class SkillLoader:
    """技能加载器"""
    
    def __init__(self, skills_dir: str = "./skills"):
        self.skills_dir = Path(skills_dir)
    
    def load_from_markdown(self, path: str) -> Optional[Skill]:
        """从 Markdown 文件加载技能，支持 frontmatter"""
        path = Path(path)
        if not path.exists():
            logger.error(f"Skill file not found: {path}")
            return None
        
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 解析 frontmatter
        # 格式：--- yaml --- content
        frontmatter_match = re.match(r'^---\n(.*?)\n---\n(.*)$', content, re.DOTALL)
        
        if frontmatter_match:
            yaml_text = frontmatter_match.group(1)
            body = frontmatter_match.group(2)
            
            try:
                data = yaml.safe_load(yaml_text)
                skill = Skill(**data)
                
                # 如果描述为空，从 body 提取
                if not skill.description:
                    # 取第一段
                    paragraphs = body.split('\n\n')
                    for p in paragraphs:
                        if p.strip() and not p.startswith('#'):
                            skill.description = p.strip()
                            break
                
                return skill
                
            except Exception as e:
                logger.error(f"Failed to parse skill frontmatter: {path}, {e}")
                return None
        
        # 没有 frontmatter，尝试从标题提取
        lines = content.split('\n')
        name = "Unnamed Skill"
        description = ""
        
        for line in lines:
            line = line.strip()
            if line.startswith('# '):
                name = line[2:].strip()
            elif line and not description:
                description = line
                break
        
        return Skill(
            name=name,
            description=description
        )
    
    def load_from_directory(self, public_only: bool = True) -> List[Skill]:
        """从目录批量加载技能"""
        skills = []
        
        if not self.skills_dir.exists():
            logger.warning(f"Skills directory {self.skills_dir} does not exist")
            return skills
        
        for file in self.skills_dir.glob("**/*.md"):
            if file.name.startswith('_'):
                continue
            if public_only and 'custom' in str(file):
                continue
            
            skill = self.load_from_markdown(file)
            if skill:
                skills.append(skill)
        
        logger.info(f"Loaded {len(skills)} skills from {self.skills_dir}")
        return skills
    
    def save_skill(self, skill: Skill, path: Optional[str] = None) -> bool:
        """保存技能到文件"""
        if path is None:
            filename = f"{skill.name.lower().replace(' ', '_')}.md"
            path = self.skills_dir / filename
        else:
            path = Path(path)
        
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # 生成 frontmatter
        data = skill.to_dict()
        yaml_text = yaml.dump(data, allow_unicode=True, default_flow_style=False)
        
        content = f"---\n{yaml_text}---\n\n{skill.to_markdown()}"
        
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"Saved skill {skill.name} to {path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save skill {skill.name}: {e}")
            return False
