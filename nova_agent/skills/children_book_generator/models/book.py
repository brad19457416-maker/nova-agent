from dataclasses import dataclass
from typing import List, Optional, Tuple
from PIL.Image import Image
from .character import Character
from .page import Page
from .style import StyleConfig


@dataclass
class Book:
    """完整绘本数据模型"""
    title: str
    author: str
    target_age_range: Tuple[int, int]  # 适合年龄段 (min, max)
    total_pages: int
    main_character: Character
    style: StyleConfig
    pages: List[Page]
    theme: str  # 核心主题
    cover_image: Optional[Image] = None
    
    @property
    def min_age(self) -> int:
        return self.target_age_range[0]
    
    @property
    def max_age(self) -> int:
        return self.target_age_range[1]
    
    def get_page(self, page_number: int) -> Optional[Page]:
        """获取指定页"""
        for page in self.pages:
            if page.page_number == page_number:
                return page
        return None
    
    def to_summary(self) -> str:
        """生成绘本概要"""
        age_str = f"{self.min_age}-{self.max_age}岁"
        page_count = f"{self.total_pages}页"
        return f"""《{self.title}》
主题: {self.theme}
适合年龄: {age_str}
总页数: {page_count}
主角: {self.main_character.name}
风格: {self.style.art_style}
"""
