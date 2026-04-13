from typing import List
from PIL.Image import Image
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader


class PDFExporter:
    """PDF导出工具"""
    
    def __init__(self, output_dir: str = "./output"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def export(self, pages: List[Image], title: str) -> str:
        """导出PDF"""
        filename = self._clean_filename(title) + ".pdf"
        output_path = os.path.join(self.output_dir, filename)
        
        c = canvas.Canvas(output_path, pagesize=A4)
        width, height = A4
        
        for page_img in pages:
            img_reader = ImageReader(page_img)
            c.drawImage(img_reader, 0, 0, width, height)
            c.showPage()
        
        c.save()
        return output_path
    
    def export_pngs(self, pages: List[Image], title: str) -> List[str]:
        """导出每页为PNG"""
        base_name = self._clean_filename(title)
        saved_paths = []
        
        for i, page_img in enumerate(pages):
            filename = f"{base_name}_page_{i+1}.png"
            path = os.path.join(self.output_dir, filename)
            page_img.save(path, "PNG")
            saved_paths.append(path)
        
        return saved_paths
    
    def _clean_filename(self, filename: str) -> str:
        """清理文件名中的非法字符"""
        invalid_chars = '<>:"/\\|?*'
        for c in invalid_chars:
            filename = filename.replace(c, '_')
        return filename
