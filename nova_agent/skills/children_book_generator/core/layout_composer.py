from ..models.book import Book
from ..models.page import Page
from PIL import Image, ImageDraw, ImageFont
import os


class LayoutComposer:
    """阶段7：图文排版整合
    
    将文字和图像整合到同一页面，处理文字位置"""
    
    def __init__(self, dpi: int = 300):
        self.dpi = dpi
    
    def compose_page(self, page: Page, book: Book, size: tuple = (2480, 3508)) -> Image.Image:
        """排版单页，默认A4尺寸 300DPI"""
        canvas = Image.new('RGB', size, 'white')
        
        if page.image is None:
            return canvas
        
        # 将插图粘贴到画布
        img = page.image.resize(size)
        canvas.paste(img, (0, 0))
        
        # 添加文字
        if page.text and page.text.strip():
            draw = ImageDraw.Draw(canvas)
            
            # 选择字体，MVP 使用默认
            try:
                font = ImageFont.truetype("sans-serif", 80)
            except:
                font = ImageFont.load_default()
            
            # 计算文字位置
            if page.text_position == "bottom":
                # 文字放在底部，黑色半透明背景
                text_bbox = draw.textbbox((0, 0), page.text, font=font)
                text_width = text_bbox[2] - text_bbox[0]
                text_height = text_bbox[3] - text_bbox[1]
                
                x = (size[0] - text_width) // 2
                y = size[1] - text_height - 100
                
                # 半透明黑色背景
                background = Image.new('RGBA', (size[0], text_height + 40), (0, 0, 0, 180))
                canvas.paste(background, (0, y - 20), background)
                
                draw.text((x, y), page.text, fill="white", font=font)
        
        return canvas
    
    def compose_all(self, book: Book) -> list[Image.Image]:
        """排版所有页，返回图像列表"""
        pages = []
        
        # 添加封面
        if book.cover_image:
            cover = self.compose_cover(book)
            pages.append(cover)
        
        # 添加内页
        for page in sorted(book.pages, key=lambda p: p.page_number):
            composed = self.compose_page(page, book)
            pages.append(composed)
        
        return pages
    
    def compose_cover(self, book: Book) -> Image.Image:
        """排版封面"""
        size = (2480, 3508)  # A4
        canvas = Image.new('RGB', size, 'white')
        
        if book.cover_image:
            cover_img = book.cover_image.resize(size)
            canvas.paste(cover_img, (0, 0))
        
        # 添加书名和作者
        draw = ImageDraw.Draw(canvas)
        try:
            title_font = ImageFont.truetype("sans-serif", 160)
            author_font = ImageFont.truetype("sans-serif", 80)
        except:
            title_font = ImageFont.load_default()
            author_font = ImageFont.load_default()
        
        # 书名放在封面中下位置
        title_bbox = draw.textbbox((0, 0), book.title, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        x = (size[0] - title_width) // 2
        y = size[1] // 2
        
        # 半透明背景
        background = Image.new('RGBA', (size[0], 300), (0, 0, 0, 160))
        canvas.paste(background, (0, y - 50), background)
        
        draw.text((x, y), book.title, fill="white", font=title_font)
        
        # 作者
        author_text = f"by {book.author}"
        author_bbox = draw.textbbox((0, 0), author_text, font=author_font)
        author_width = author_bbox[2] - author_bbox[0]
        x = (size[0] - author_width) // 2
        y = size[1] - 200
        draw.text((x, y), author_text, fill="white", font=author_font)
        
        return canvas
