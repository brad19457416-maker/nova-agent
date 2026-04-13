from dataclasses import dataclass
from typing import Optional
from PIL.Image import Image


@dataclass
class Page:
    """单页数据模型"""
    page_number: int
    text: str              # 文字内容
    scene_description: str # 场景描述
    image_prompt: str      # 图像生成提示词
    image: Optional[Image] = None
    text_position: str = "bottom"  # top/bottom/left/right
    
    @property
    def is_cover(self) -> bool:
        """是否是封面"""
        return self.page_number == 0
    
    @property
    def is_back_cover(self) -> bool:
        """是否是封底"""
        return False  # MVP 暂不处理封底
