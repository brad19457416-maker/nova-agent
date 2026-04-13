from typing import Optional, List
from ..models.book import Book
from ..models.page import Page
from PIL import Image
import requests
import io
import os
from .jimeng_api import JingmengImageGenerator


class ImageGenerator:
    """阶段6：图像生成与优化
    
    支持多个后端：
    - dalle: OpenAI DALL-E 3
    - jimeng: 即梦 AI 绘画 API（全自动生成4张图）
    - mock: 测试模式，不生成真实图像
    - sd: Stable Diffusion (预留)
    """
    
    def __init__(self, api_key: str = None, backend: str = "dalle", base_url: str = None, output_dir: str = "./output/childrens_books/images"):
        self.api_key = api_key
        self.backend = backend
        self.base_url = base_url
        self.output_dir = output_dir
        
        # 初始化即梦生成器
        if backend == "jimeng":
            self.jimeng_generator = JingmengImageGenerator(
                api_key=api_key,
                output_dir=output_dir,
                default_num_images=4,  # 每页生成4张供筛选
            )
    
    def generate_all(self, book: Book) -> Book:
        """生成所有页插图"""
        if self.backend == "jimeng":
            # 即梦模式：每页生成4张，保存到本地，供后续筛选
            for page in book.pages:
                image_paths = self.generate_image(book.title, page.page_number, page.image_prompt)
                page.generated_images = image_paths  # 保存多张路径
            return book
        else:
            # 原有模式：单张生成
            for page in book.pages:
                image = self.generate_single(page.image_prompt)
                page.image = image
            
            # 生成封面
            if not book.cover_image:
                cover_prompt = self._build_cover_prompt(book)
                cover_image = self.generate_single(cover_prompt)
                book.cover_image = cover_image
            
            return book
    
    def generate_single(self, prompt: str, size: str = "1024x1024") -> Optional[Image]:
        """生成单张图（原有接口兼容）"""
        if self.backend == "dalle":
            return self._generate_dalle(prompt, size)
        elif self.backend == "mock":
            # 测试用，返回空白图
            return Image.new('RGB', (1024, 1024), color='white')
        else:
            raise NotImplementedError(f"Backend {self.backend} not implemented")
    
    def generate_image(self, book_title: str, page_number: int, prompt: str) -> List[str]:
        """即梦专用：生成多张图片并下载，返回本地路径列表"""
        if self.backend != "jimeng":
            raise ValueError("This method is only for jimeng backend")
        
        return self.jimeng_generator.generate_and_download(
            prompt=prompt,
            page_number=page_number,
            book_title=book_title,
        )
    
    def _generate_dalle(self, prompt: str, size: str) -> Optional[Image]:
        """调用 OpenAI DALL-E 3"""
        if not self.api_key:
            raise ValueError("OpenAI API key required for DALL-E")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "dall-e-3",
            "prompt": prompt,
            "n": 1,
            "size": size,
            "response_format": "url"
        }
        
        base_url = self.base_url or "https://api.openai.com/v1/images/generations"
        
        try:
            response = requests.post(base_url, headers=headers, json=data, timeout=120)
            response.raise_for_status()
            result = response.json()
            
            if "data" in result and len(result["data"]) > 0:
                image_url = result["data"][0]["url"]
                image_response = requests.get(image_url, timeout=60)
                image = Image.open(io.BytesIO(image_response.content))
                return image
            
            return None
        except Exception as e:
            print(f"Image generation failed: {e}")
            return None
    
    def _build_cover_prompt(self, book: Book) -> str:
        """生成封面提示词"""
        prompt = f"children's book cover for '{book.title}', "
        prompt += f"theme: {book.theme}, "
        prompt += f"main character: {book.main_character.name}, {book.main_character.appearance}, "
        prompt += book.style.to_prompt_suffix()
        prompt += ", book cover, children's book illustration, high quality"
        return prompt
