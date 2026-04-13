from typing import List
from PIL import Image
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader


class OutputGenerator:
    """阶段8：输出打包
    
    生成完整PDF文件"""
    
    def __init__(self, output_dir: str = "./output"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def generate_pdf(self, pages: List[Image.Image], title: str) -> str:
        """生成PDF文件，返回文件路径"""
        filename = f"{title.replace(' ', '_')}.pdf"
        output_path = os.path.join(self.output_dir, filename)
        
        c = canvas.Canvas(output_path, pagesize=A4)
        width, height = A4
        
        for page_img in pages:
            # 将PIL图像转换为ReportLab可用格式
            img_reader = ImageReader(page_img)
            # 铺满整个页面
            c.drawImage(img_reader, 0, 0, width, height)
            c.showPage()
        
        c.save()
        return output_path
    
    def save_images(self, pages: List[Image.Image], title: str) -> List[str]:
        """保存每页为单独PNG文件"""
        saved_paths = []
        base_name = title.replace(' ', '_')
        
        for i, page_img in enumerate(pages):
            filename = f"{base_name}_page_{i+1}.png"
            path = os.path.join(self.output_dir, filename)
            page_img.save(path, "PNG")
            saved_paths.append(path)
        
        return saved_paths
