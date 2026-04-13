from ..models.book import Book
from ..models.style import StyleConfig
from nova_agent.llm.client_base import LLMClient


class StyleDefiner:
    """阶段4：插图风格定义
    
    细化整体艺术风格，确定色彩方案，角色视觉设定"""
    
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client
    
    def define_style(self, book: Book) -> Book:
        """细化风格定义"""
        
        prompt = self._build_prompt(book)
        response = self.llm.complete(prompt, temperature=0.7)
        
        return self._parse_and_update(response, book)
    
    def _build_prompt(self, book: Book) -> str:
        return f"""你是儿童绘本艺术总监。请为《{book.title}》定义详细的插图风格。

故事主题：{book.theme}
主角：{book.main_character.name}，{book.main_character.appearance}
初步风格：{book.style.art_style}

请推荐适合这个故事的色彩方案，补充风格细节。按照JSON格式输出：

{{
  "art_style": "最终确定的艺术风格",
  "color_palette": ["主色调1", "主色调2", "辅助色1", ...],
  "additional_prompts": [
    "额外的风格描述词，让AI画图更准确",
    ...
  ]
}}

只输出JSON，不要其他内容：
"""
    
    def _parse_and_update(self, response: str, book: Book) -> Book:
        import json
        try:
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1]
            
            data = json.loads(response.strip())
            
            book.style = StyleConfig(
                art_style=data.get("art_style", book.style.art_style),
                color_palette=data.get("color_palette", []),
                additional_prompts=data.get("additional_prompts", []),
            )
            
            return book
            
        except Exception as e:
            # 如果解析失败，保持原样
            return book
