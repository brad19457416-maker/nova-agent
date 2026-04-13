from dataclasses import dataclass
from typing import Optional, List
import numpy as np
from PIL.Image import Image


@dataclass
class Character:
    """角色数据模型"""
    name: str
    age: int
    personality: str
    appearance: str
    reference_image: Optional[Image] = None
    embedding: Optional[np.ndarray] = None
    
    def to_description(self) -> str:
        """生成角色描述文本"""
        return f"""{self.name}, {self.age}岁。
性格: {self.personality}
外貌: {self.appearance}"""
