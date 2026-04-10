"""
Skill Definition - 技能定义

SuperPowers 启发，技能使用 Markdown 定义，包含：
- 技能名称、描述、用途
- 工作流程、最佳实践
- 参数说明、使用示例
- 资源引用
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
import json

@dataclass
class Skill:
    """
    技能定义
    
    技能可以预先定义，也可以从成功案例自动学习沉淀。
    """
    name: str
    description: str
    category: str = "general"
    version: str = "0.1.0"
    author: str = ""
    created_at: str = ""
    
    # 工作流程描述（步骤列表）
    workflow: list[str] = None
    
    # 最佳实践
    best_practices: list[str] = None
    
    # 参数定义
    parameters: Dict[str, str] = None
    
    # 使用示例
    example: str = ""
    
    # 参考资源
    references: list[str] = None
    
    # 统计信息
    usage_count: int = 0
    success_rate: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Skill':
        """从字典创建"""
        return cls(**data)
    
    def to_markdown(self) -> str:
        """转换为 Markdown 格式（可直接被 LLM 读取）"""
        md = f"# {self.name}\n\n"
        md += f"**Description:** {self.description}\n\n"
        
        if self.workflow and len(self.workflow) > 0:
            md += "## Workflow\n\n"
            for i, step in enumerate(self.workflow, 1):
                md += f"{i}. {step}\n"
            md += "\n"
        
        if self.best_practices and len(self.best_practices) > 0:
            md += "## Best Practices\n\n"
            for practice in self.best_practices:
                md += f"- {practice}\n"
            md += "\n"
        
        if self.parameters and len(self.parameters) > 0:
            md += "## Parameters\n\n"
            for name, desc in self.parameters.items():
                md += f"- **{name}**: {desc}\n"
            md += "\n"
        
        if self.example:
            md += "## Example\n\n```\n{self.example}\n```\n\n"
        
        if self.references and len(self.references) > 0:
            md += "## References\n\n"
            for ref in self.references:
                md += f"- {ref}\n"
            md += "\n"
        
        md += f"**Usage:** {self.usage_count} | **Success Rate:** {self.success_rate:.1%}\n"
        
        return md
    
    def increment_usage(self, success: bool) -> None:
        """增加使用计数，更新成功率"""
        total = self.usage_count
        success_total = int(self.success_rate * total)
        
        self.usage_count = total + 1
        if success:
            success_total += 1
        
        self.success_rate = success_total / self.usage_count
