from ..models.book import Book
from ..models.page import Page
from ..models.character import Character


class PromptEngineer:
    """阶段5：图像提示词工程
    
    基于分镜生成高质量图像生成提示词
    支持多种AI绘图平台适配：OpenAI DALL-E / 即梦 / 中文平台"""
    
    def __init__(self, platform: str = "j meng"):
        """
        Args:
            platform: 目标平台
            - "openai": OpenAI DALL-E 格式（英文关键词）
            - "jimeng": 即梦 格式（中文，直接描述）
            - "sd": Stable Diffusion 中文格式
        """
        self.platform = platform.lower() if platform else "jimeng"
    
    def engineer_all(self, book: Book) -> Book:
        """为所有页生成提示词"""
        for page in book.pages:
            page.image_prompt = self._build_page_prompt(page, book)
        return book
    
    def _build_page_prompt(self, page: Page, book: Book) -> str:
        """为单页构建图像提示词，根据平台适配"""
        
        if self.platform in ["jimeng", "j meng", "jemeng", "即梦", "中文"]:
            return self._build_jimeng_prompt(page, book)
        else:
            return self._build_openai_prompt(page, book)
    
    def _build_jimeng_prompt(self, page: Page, book: Book) -> str:
        """
        即梦（中文AI绘图平台）深度适配：
        
        即梦特点：
        1. 中文描述效果远好于英文，详细完整描述更好
        2. 关键词顺序权重很高：主体>角色>场景>画质，前面权重高
        3. 支持括号增强权重 (关键词:1.2)
        4. 需要明确构图、视角、氛围
        5. 儿童绘本需要特别强调可爱、圆润、友好
        """
        parts = []
        
        # 1. 【最高权重】核心主体场景（放最前面，即梦权重最高）
        parts.append(f"(儿童绘本插画:{1.2})")
        # 融合场景描述 + 文字内容中的关键细节，确保所有元素都被包含
        full_description = page.scene_description
        # 如果文字内容不长，直接添加进去（提取关键视觉元素）
        if page.text and len(page.text) < 100:
            # 去掉换行，把文字内容也加进去，让AI知道所有细节
            text_clean = page.text.replace('\n', '，')
            full_description = f"{full_description}，{text_clean}"
        parts.append(full_description)
        
        # 2. 【第二权重】主角一致性，非常重要，保持整本绘本角色统一
        # 提升权重到1.3，确保主角特征（比如蝴蝶结）更明显
        char = book.main_character
        parts.append(f"(主角：{char.name}，{char.appearance}:1.3)")
        
        # 强制要求：主角占据主要位置，背景简化
        # 根据即梦实测总结，突出主角并简化背景效果更好
        parts.append("(主角占据画面主要位置:1.2)")
        parts.append("(背景非常简化:1.2)")
        
        # 3. 【第三】整体艺术风格，由风格定义
        style_desc = book.style.to_prompt_chinese()
        if style_desc:
            parts.append(style_desc)
        
        # 4. 构图要求：必须留出空白放文字，这对绘本非常重要
        # 额外强制要求：绝对不要生成任何文字（AI绘画生成文字质量差，我们后期自己加）
        parts.append("(绝对不要生成任何文字:1.4)")
        
        if page.text_position == "bottom":
            parts.append("(底部留出大面积空白放文字:1.3)")
        elif page.text_position == "top":
            parts.append("(顶部留出大面积空白放文字:1.3)")
        elif page.text_position == "left":
            parts.append("(左侧留出大面积空白放文字:1.3)")
        elif page.text_position == "right":
            parts.append("(右侧留出大面积空白放文字:1.3)")
        else:
            parts.append("(底部留出大面积空白放文字:1.2)")  # 默认底部
        
        # 5. 【画质和风格强化】即梦对这些关键词响应很好
        parts.extend([
            "(高清:1.2)",
            "(8k分辨率:1.1)",
            "(线条清晰圆润:1.1)",
            "(色彩柔和明快:1.1)",
            "(可爱友好:1.2)",
            "适合儿童观看",
            "完整单页插图",
            "构图饱满",
        ])
        
        # 6. 指定配色方案
        if book.style.color_palette and len(book.style.color_palette) > 0:
            parts.append(f"(主色调：{'、'.join(book.style.color_palette)}:1.1)")
        
        # 即梦使用中文逗号分隔，权重用括号增强
        return "，".join(parts)
    
    def _build_openai_prompt(self, page: Page, book: Book) -> str:
        """OpenAI DALL-E 格式（英文关键词）"""
        # 基础组件
        parts = []
        
        # 整体风格
        style_suffix = book.style.to_prompt_suffix()
        parts.append(style_suffix)
        
        # 场景描述 + 文字内容中的关键细节，确保所有元素都被包含
        full_description = page.scene_description
        # 如果文字内容不长，直接添加进去
        if page.text and len(page.text) < 100:
            text_clean = page.text.replace('\n', ', ')
            full_description = f"{full_description}, {text_clean}"
        parts.append(full_description)
        
        # 主角一致性
        char = book.main_character
        parts.append(f"main character: {char.name}, {char.appearance}")
        
        # 构图要求：给文字留位置
        if page.text_position == "bottom":
            parts.append("leave empty space at the bottom for text")
        elif page.text_position == "top":
            parts.append("leave empty space at the top for text")
        elif page.text_position == "left":
            parts.append("leave empty space on the left for text")
        elif page.text_position == "right":
            parts.append("leave empty space on the right for text")
        
        # 儿童绘本风格附加
        parts.extend([
            "children's book illustration",
            "high quality",
            "clear outlines",
            "friendly and cute",
        ])
        
        # 如果有调色板
        if book.style.color_palette and len(book.style.color_palette) > 0:
            parts.append(f"color palette: {', '.join(book.style.color_palette)}")
        
        return ", ".join(parts)
