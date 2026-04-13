"""
Children's Book Generator Skill for Nova Agent
全自动儿童绘本生成技能

使用方式：
```python
from nova_agent.skills.children_book_generator import ChildrenBookGenerator

generator = ChildrenBookGenerator(
    llm_client=llm,
    image_api_key="your-openai-key",  # 用于 DALL-E
)

book = generator.generate(
    topic="一只爱冒险的小猫咪",
    target_age=(3, 6),
    character_name="咪咪",
    style="水彩风",
)

pdf_path = generator.save_pdf(book)
print(f"Generated PDF: {pdf_path}")
```
"""

from .core import (
    StoryConceiver,
    StoryPlanner,
    StoryboardWriter,
    StyleDefiner,
    PromptEngineer,
    ImageGenerator,
    LayoutComposer,
    OutputGenerator,
    MarketInspirationLearner,
    QualityEvaluator,
)
from .models import Book, Character, StyleConfig, Page
from nova_agent.llm.client_base import LLMClient
from typing import Tuple, Optional, Dict, Any, List


class ChildrenBookGenerator:
    """完整的儿童绘本生成器
    
    整合八阶段+双优化工作流，从创意到PDF输出
    
    新增优化功能：
    - 市场灵感学习：从成功绘本学习抽象创作经验
    - 质量评估闭环：不合格自动重生成，保证商用质量
    """
    
    def __init__(
        self,
        llm_client: LLMClient,
        image_api_key: str = None,
        image_backend: str = "mock",  # "dalle", "mock", "sd", "jimeng"
        image_base_url: str = None,
        output_dir: str = "./nova_output/childrens_books",
        prompt_platform: str = "jimeng",  # "jimeng"(即梦) / "openai"
        enable_market_learning: bool = True,
        enable_quality_check: bool = True,
        max_regeneration_attempts: int = 2,
        quality_threshold: float = 70.0,
        jimeng_output_dir: str = "./nova_output/childrens_books/images",
    ):
        self.llm = llm_client
        
        # 初始化各阶段
        self.conceiver = StoryConceiver(llm_client)
        self.market_learner = MarketInspirationLearner(llm_client)
        self.planner = StoryPlanner(llm_client)
        self.writer = StoryboardWriter(llm_client)
        self.style_definer = StyleDefiner(llm_client)
        self.quality_evaluator = QualityEvaluator(llm_client)
        self.prompt_engineer = PromptEngineer(platform=prompt_platform)
        self.image_generator = ImageGenerator(
            api_key=image_api_key,
            backend=image_backend,
            base_url=image_base_url,
            output_dir=jimeng_output_dir,
        )
        self.composer = LayoutComposer()
        self.output_generator = OutputGenerator(output_dir)
        
        # 优化功能开关
        self.enable_market_learning = enable_market_learning
        self.enable_quality_check = enable_quality_check
        self.max_regeneration_attempts = max_regeneration_attempts
        self.quality_threshold = quality_threshold
    
    def generate(
        self,
        topic: str,
        target_age: Tuple[int, int] = (3, 6),
        character_name: str = None,
        style: str = None,
        total_pages: int = None,
    ) -> Book:
        """生成完整绘本（带市场学习和质量检查闭环）"""
        
        # 阶段1：核心创意生成
        title, character, style_config, theme = self.conceiver.conceive(
            topic, target_age, character_name, style
        )
        
        # 优化阶段A：市场灵感学习（新增）
        inspiration_advice = None
        if self.enable_market_learning:
            inspiration_advice = self.market_learner.analyze_topic(
                topic, target_age, theme
            )
        
        # 阶段2：故事结构规划
        if total_pages is None:
            # 根据年龄段自动选页数
            if target_age[1] <= 3:
                total_pages = 12
            elif target_age[1] <= 6:
                total_pages = 16 if self.enable_quality_check else 24
            else:
                total_pages = 36
        
        # 加入市场灵感建议进行规划
        book = self._plan_with_inspiration(
            title, theme, character, style_config, target_age,
            total_pages, inspiration_advice
        )
        
        # 阶段3：分镜脚本创作（带质量改进循环）
        book = self._write_with_quality_check(book, inspiration_advice)
        
        # 阶段4：风格细化定义
        book = self.style_definer.define_style(book)
        
        # 阶段5：生成图像提示词
        book = self.prompt_engineer.engineer_all(book)
        
        # 阶段6：生成图像
        book = self.image_generator.generate_all(book)
        
        return book
    
    def _plan_with_inspiration(
        self,
        title: str,
        theme: str,
        character: Character,
        style_config: StyleConfig,
        target_age: Tuple[int, int],
        total_pages: int,
        inspiration_advice: Optional[Dict[str, Any]]
    ) -> Book:
        """使用市场灵感建议进行故事规划"""
        if inspiration_advice is None:
            return self.planner.plan(
                title, theme, character, style_config, target_age, total_pages
            )
        
        # 给 planner 的prompt注入灵感建议
        # 这里我们需要重写prompt，所以直接复制planner逻辑加上建议
        inspiration_text = self.market_learner.get_inspiration_prompt_addition(inspiration_advice)
        
        prompt = self._build_planner_prompt_with_inspiration(
            title, theme, character, target_age, total_pages, inspiration_text
        )
        response = self.llm.complete(prompt, temperature=0.7)
        
        return self._parse_planner_response(
            response, title, theme, character, style_config, target_age, total_pages
        )
    
    def _build_planner_prompt_with_inspiration(
        self, title, theme, character, age, pages, inspiration_text
    ):
        """构建带市场灵感建议的规划prompt"""
        age_str = f"{age[0]}-{age[1]}岁"
        base_prompt = f"""你是儿童绘本故事策划师。请为《{title}》设计故事结构，总共{pages}页。

故事主题：{theme}
主角：{character.name}, {character.age}岁, {character.personality}, {character.appearance}
适合年龄：{age_str}

儿童绘本故事通常是三幕结构：
- 开头（第1-约1/3页）：介绍主角和背景，引出问题
- 发展（中1/3页）：主角展开探索，遇到挑战
- 结尾（最后1/3页）：解决问题，得到成长，点题

{inspiration_text}

请为每一页设计内容要点，每页一句话说明。按照以下JSON格式输出：

{{
  "plan": [
    {{
      "page_number": 1,
      "content_summary": "这一页的内容要点（一句话）"
    }},
    ...
  ]
}}

只输出JSON，不要其他内容：
"""
        return base_prompt
    
    def _parse_planner_response(
        self, response, title, theme, character, style, target_age, total_pages
    ):
        """解析规划响应（复用planner逻辑）"""
        import json
        from ..models.book import Book
        from ..models.page import Page
        
        try:
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1]
            
            data = json.loads(response.strip())
            
            pages_list = []
            for item in data["plan"]:
                page = Page(
                    page_number=item["page_number"],
                    text="",  # 稍后填充
                    scene_description=item["content_summary"],
                    image_prompt="",  # 稍后填充
                )
                pages_list.append(page)
            
            book = Book(
                title=title,
                author="AI Generated by Nova Agent",
                target_age_range=target_age,
                total_pages=len(pages_list),
                main_character=character,
                style=style,
                pages=pages_list,
                theme=theme,
            )
            
            return book
            
        except Exception as e:
            raise ValueError(f"Failed to parse story plan: {e}\nResponse: {response}")
    
    def _write_with_quality_check(self, book: Book, inspiration_advice: Dict) -> Book:
        """分镜创作带质量检查闭环，不合格自动重写"""
        from copy import deepcopy
        
        # 初次创作
        current_book = self.writer.write_storyboard(deepcopy(book))
        
        if not self.enable_quality_check:
            return current_book
        
        # 质量评估
        attempts = 0
        while attempts < self.max_regeneration_attempts:
            score, details, passed = self.quality_evaluator.evaluate_book(current_book)
            
            if passed and score >= self.quality_threshold:
                # 通过了，返回结果
                return current_book
            
            # 不通过，根据建议重写
            suggestions = self._extract_suggestions(details)
            improvement_prompt = self.quality_evaluator.generate_improvement_prompt(suggestions)
            
            # 加入市场灵感，重新创作
            current_book = self._rewrite_with_improvement(
                deepcopy(book), improvement_prompt, inspiration_advice
            )
            attempts += 1
        
        # 尝试次数用完了，返回最后结果（即使分数不够也只能这样了）
        return current_book
    
    def _extract_suggestions(self, details: List[Dict]) -> List[str]:
        """从评估详情中提取改进建议"""
        suggestions = []
        for d in details:
            score = d.get("score", 10)
            comment = d.get("comment", "")
            if score < 7 and comment:
                suggestions.append(comment)
        return suggestions
    
    def _rewrite_with_improvement(
        self, book: Book, improvement_prompt: str, inspiration_advice: Dict
    ) -> Book:
        """根据改进建议重写故事"""
        pages_summary = "\n".join([
            f"第 {p.page_number} 页：{p.scene_description}"
            for p in book.pages
        ])
        
        age_min, age_max = book.target_age_range
        age_desc = f"{age_min}-{age_max}岁儿童"
        
        inspiration_text = ""
        if inspiration_advice:
            inspiration_text = self.market_learner.get_inspiration_prompt_addition(inspiration_advice)
        
        prompt = f"""你是儿童绘本文字作者。请为《{book.title}》逐页重写文字内容，解决之前发现的问题。

故事主题：{book.theme}
主角：{book.main_character.name}，{book.main_character.appearance}，性格{book.main_character.personality}
适合年龄：{age_desc}

原页面规划：
{pages_summary}

{inspiration_text}

{improvement_prompt}

要求：
1. 文字要简单易懂，适合{age_desc}阅读
2. 语言要有韵律感，短句，重复有助于儿童语言学习
3. 每页文字通常在 20-50 字之间（低龄儿童更短）
4. 为插图创作留足空间，文字不能太长
5. 认真解决上述改进建议中提到的问题

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
        response = self.llm.complete(prompt, temperature=0.7)
        
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
            # 重写失败，返回原书
            print(f"Rewrite failed: {e}, using original")
            return book
    
    def compose_and_save(
        self, book: Book, output_format: str = "pdf"
    ) -> str:
        """排版并保存输出"""
        
        # 阶段7：图文排版
        composed_pages = self.composer.compose_all(book)
        
        # 阶段8：输出
        if output_format == "pdf":
            path = self.output_generator.generate_pdf(composed_pages, book.title)
            return path
        elif output_format == "png":
            paths = self.output_generator.save_images(composed_pages, book.title)
            return paths[0] if paths else None
        else:
            raise ValueError(f"Unknown format: {output_format}")
    
    def full_generate(
        self,
        topic: str,
        target_age: Tuple[int, int] = (3, 6),
        character_name: str = None,
        style: str = None,
        output_format: str = "pdf",
    ) -> str:
        """完整流水线：从主题到输出文件（带质量优化）"""
        book = self.generate(topic, target_age, character_name, style)
        output_path = self.compose_and_save(book, output_format)
        return output_path
