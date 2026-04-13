from dataclasses import dataclass
from typing import List, Optional


@dataclass
class StyleConfig:
    """插图风格配置"""
    art_style: str         # 艺术风格 (水彩, 卡通, 油画, 扁平风, 中国风等
    color_palette: Optional[List[str]] = None  # 颜色列表
    composition: str = "full page illustration"  # 构图描述
    additional_prompts: List[str] = None
    
    def __post_init__(self):
        if self.additional_prompts is None:
            self.additional_prompts = []
        if self.color_palette is None:
            self.color_palette = []
    
    def to_prompt_suffix(self) -> str:
        """生成英文提示词后缀 (for OpenAI DALL-E)"""
        parts = [self.art_style]
        if self.color_palette:
            parts.append(f"colors: {', '.join(self.color_palette)}")
        parts.extend(self.additional_prompts)
        return ", ".join(parts)
    
    def to_prompt_chinese(self) -> str:
        """生成中文提示词 (for 即梦等中文AI绘图平台)"""
        parts = []
        if self.additional_prompts:
            parts.extend(self.additional_prompts)
        return "，".join(parts)
