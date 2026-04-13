from typing import List
from ..models.book import Book
from ..models.page import Page
from nova_agent.llm.client_base import LLMClient


class StoryboardWriter:
    """阶段3：分镜脚本创作
    
    逐页创作文字内容，细化场景描述"""
    
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client
    
    def write_storyboard(self, book: Book) -> Book:
        """为每一页创作文字内容和详细场景描述"""
        import json
        
        # 逐页生成，保持上下文连贯
        # MVP 版本：一次性生成所有页，验证流程
        
        prompt = self._build_prompt(book)
        response = self.llm.complete(prompt, temperature=0.7)
        
        return self._parse_and_fill(response, book)
    
    def _build_prompt(self, book: Book) -> str:
        pages_summary = "\n".join([
            f"第 {p.page_number} 页：{p.scene_description}"
            for p in book.pages
        ])
        
        age_min, age_max = book.target_age_range
        age_desc = f"{age_min}-{age_max}岁儿童"
        
        return f"""你是儿童绘本文字作者。请为《{book.title}》逐页创作文字内容。

故事主题：{book.theme}
主角：{book.main_character.name}，{book.main_character.appearance}，性格{book.main_character.personality}
适合年龄：{age_desc}

页面规划：
{pages_summary}

要求：
1. 文字要简单易懂，适合{age_desc}阅读
2. 语言要有韵律感，短句，重复有助于儿童语言学习
3. 每页文字通常在 20-50 字之间（低龄儿童更短）
4. 为插图创作留足空间，文字不能太长

请按照JSON格式输出：

{{
  "pages": [
    {{
      "page_number": 1,
      "text": "这一页的文字内容",
      "scene_description": "详细的场景描述，给插图画家看"
    }},
    ...
  ]
}}

只输出JSON，不要其他内容：
"""
    
    def _parse_and_fill(self, response: str, book: Book) -> Book:
        import json
        try:
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1]
            
            data = json.loads(response.strip())
            
            for page_data in data["pages"]:
                page_num = page_data["page_number"]
                for page in book.pages:
                    if page.page_number == page_num:
                        page.text = page_data["text"]
                        page.scene_description = page_data["scene_description"]
                        break
            
            return book
            
        except Exception as e:
            raise ValueError(f"Failed to parse storyboard: {e}\nResponse: {response}")
