"""
即梦（Jingmeng）AI绘画 API 客户端
用于全自动生成图像，不需要手动复制粘贴
"""

from typing import List, Dict, Any, Optional
import requests
import json
import os
from urllib.parse import urlparse


class JingmengAPIClient:
    """即梦API客户端"""
    
    API_BASE = "https://api.jingmeng.ai/v1"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
    
    def generate_image(
        self,
        prompt: str,
        negative_prompt: str = "文字，水印，模糊，扭曲，多余肢体，丑，劣质",
        aspect_ratio: str = "1:1",  # 正方形适合绘本
        model: str = "jimeng-v1",
        num_images: int = 4,  # 每次生成4张供筛选
    ) -> Dict[str, Any]:
        """生成图像
        
        返回：包含图片URL的响应
        """
        payload = {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "aspect_ratio": aspect_ratio,
            "model": model,
            "num_images": num_images,
        }
        
        response = requests.post(
            f"{self.API_BASE}/generations",
            headers=self.headers,
            json=payload,
            timeout=120,
        )
        response.raise_for_status()
        return response.json()
    
    def get_generation_status(self, generation_id: str) -> Dict[str, Any]:
        """查询生成状态"""
        response = requests.get(
            f"{self.API_BASE}/generations/{generation_id}",
            headers=self.headers,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()
    
    def download_image(self, image_url: str, save_path: str) -> str:
        """下载图片到本地"""
        response = requests.get(image_url, timeout=60)
        response.raise_for_status()
        
        with open(save_path, "wb") as f:
            f.write(response.content)
        
        return save_path


class JingmengImageGenerator:
    """即梦图像生成器（集成到绘本流程）"""
    
    def __init__(
        self,
        api_key: str,
        output_dir: str = "./output/childrens_books/images",
        default_num_images: int = 4,
    ):
        self.client = JingmengAPIClient(api_key)
        self.output_dir = output_dir
        self.default_num_images = default_num_images
        os.makedirs(output_dir, exist_ok=True)
    
    def generate_and_download(
        self,
        prompt: str,
        page_number: int,
        book_title: str,
    ) -> List[str]:
        """生成并下载多张图片，返回本地文件路径列表"""
        
        # 绘本专用默认负提示
        negative_prompt = """文字，字体，字母，数字，水印，签名，logo，模糊，扭曲，变形，
        多余肢体，缺胳膊少腿，丑，劣质，不协调，多余物体，背景杂乱，"""
        
        result = self.client.generate_image(
            prompt=prompt,
            negative_prompt=negative_prompt,
            aspect_ratio="1:1",
            num_images=self.default_num_images,
        )
        
        generation_id = result["id"]
        
        # 这里即梦是异步生成，需要轮询等待
        import time
        for _ in range(30):  # 最多等待5分钟
            status = self.client.get_generation_status(generation_id)
            if status["status"] == "completed":
                break
            elif status["status"] == "failed":
                raise RuntimeError(f"Generation failed: {status.get('error', 'Unknown error')}")
            time.sleep(10)
        
        # 下载所有图片
        saved_paths = []
        for i, image in enumerate(status["output"]["images"]):
            filename = f"{book_title.replace(' ', '_')}_page_{page_number}_image_{i+1}.png"
            save_path = os.path.join(self.output_dir, filename)
            self.client.download_image(image["url"], save_path)
            saved_paths.append(save_path)
        
        return saved_paths
