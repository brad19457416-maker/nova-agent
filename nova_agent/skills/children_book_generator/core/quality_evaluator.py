from typing import List, Dict, Any, Tuple
from ..models.book import Book
from ..models.page import Page
from nova_agent.llm.client_base import LLMClient


class QualityEvaluator:
    """绘本质量评估模块
    
    在生成完成后评估内容质量，不合格自动触发重生成，
    确保输出达到商用级质量标准。"""
    
    # 质量评估标准
    EVALUATION_CRITERIA = {
        "theme_consistency": {
            "name": "主题一致性",
            "description": "故事是否围绕核心主题展开，不跑题"
        },
        "age_appropriateness": {
            "name": "年龄段适配",
            "description": "词汇难度、内容复杂度是否符合目标年龄"
        },
        "rhythm_rhyme": {
            "name": "韵律节奏",
            "description": "语言是否有韵律感，适合朗读"
        },
        "character_consistency": {
            "name": "角色一致性",
            "description": "主角性格、外貌在各页是否保持一致"
        },
        "page_appeal": {
            "name": "每页吸引力",
            "description": "每页是否有看点，能吸引孩子注意力"
        },
        "arc_completeness": {
            "name": "故事完整性",
            "description": "三幕结构是否完整，有开头发展结局"
        },
        "positive_value": {
            "name": "正向价值观",
            "description": "传递积极正向的价值观，无不良内容"
        },
        "text_image_balance": {
            "name": "图文平衡",
            "description": "文字长度合适，为插图留足空间"
        }
    }
    
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client
    
    def evaluate_book(self, book: Book) -> Tuple[float, List[Dict[str, Any]], bool]:
        """评估整本书的质量
        
        返回：
        - overall_score: 0-100分
        - details: 各维度评估详情
        - passed: 是否通过质量门槛（>=70分通过）
        """
        prompt = self._build_evaluation_prompt(book)
        response = self.llm.complete(prompt, temperature=0.3)
        
        return self._parse_evaluation(response)
    
    def _build_evaluation_prompt(self, book: Book) -> str:
        age_min, age_max = book.target_age_range
        pages_text = ""
        
        for page in sorted(book.pages, key=lambda p: p.page_number):
            pages_text += f"第 {page.page_number} 页：\n文字：{page.text}\n场景：{page.scene_description}\n\n"
        
        return f"""你是儿童绘本资深编辑，请对这本已经创作完成的儿童绘本进行质量评估。

绘本信息：
- 标题：{book.title}
- 主题：{book.theme}
- 主角：{book.main_character.name}，{book.main_character.personality}
- 适合年龄：{age_min}-{age_max}岁
- 总页数：{book.total_pages}

完整内容：
{pages_text}

请按照以下8个维度进行评估，每个维度打分0-10分：

1. 主题一致性：故事是否始终围绕核心主题展开，不跑题
2. 年龄段适配：词汇难度、内容复杂度是否符合目标年龄
3. 韵律节奏：语言是否有韵律感，短句，适合儿童朗读
4. 角色一致性：主角性格、特点在各页是否保持一致
5. 每页吸引力：每页是否有明确看点，能吸引孩子注意力
6. 故事完整性：三幕结构是否完整（开头引入→发展探索→结尾解决/成长）
7. 正向价值观：是否传递积极正向价值观，无不良内容
8. 图文平衡：每页文字长度是否合适，是否给插图留足空间

请按照JSON格式输出：

{{
  "evaluations": [
    {{
      "criterion": "维度名称",
      "score": 分数(0-10),
      "comment": "简短评价说明"
    }},
    ...共8个维度...
  ],
  "overall_score": 总分0-100,
  "passed": true/false,
  "improvement_suggestions": ["需要改进的地方列表，每条一句话"]
}}

打分标准：
- 9-10分：优秀，完美符合要求
- 7-8分：良好，基本符合要求，小问题不影响
- 5-6分：合格，但有明显问题需要改进
- 0-4分：不合格，严重问题必须重写

通过标准：overall_score >= 70 分才能通过。

只输出JSON，不要其他内容：
"""
    
    def _parse_evaluation(self, response: str) -> Tuple[float, List[Dict], bool]:
        import json
        try:
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1]
            
            data = json.loads(response.strip())
            
            overall_score = float(data.get("overall_score", 0))
            details = data.get("evaluations", [])
            passed = data.get("passed", overall_score >= 70)
            
            return overall_score, details, passed
            
        except Exception as e:
            # 如果解析失败，默认不通过，让它重生成
            raise ValueError(f"Failed to parse evaluation: {e}\nResponse: {response}")
    
    def generate_improvement_prompt(self, suggestions: List[str]) -> str:
        """根据评估建议生成重写改进的提示词"""
        if not suggestions:
            return ""
        
        suggestions_text = "\n".join([f"- {s}" for s in suggestions])
        
        return f"""
根据质量评估，需要针对以下问题进行改进：

{suggestions_text}

请认真修改，解决这些问题，提升整体质量。
"""
    
    def check_page_text(self, page: Page, target_age: Tuple[int, int]) -> Tuple[bool, str]:
        """单页文字快速检查（简单规则，不需要LLM）"""
        age_min, age_max = target_age
        
        # 字数检查
        text_length = len(page.text.strip())
        if age_max <= 3:
            # 0-3岁，每页最多20字
            if text_length > 30:
                return False, f"文字太长({text_length}字)，0-3岁每页应控制在20字以内"
        elif age_max <= 6:
            # 3-6岁，每页最多60字
            if text_length > 80:
                return False, f"文字太长({text_length}字)，3-6岁每页应控制在60字以内"
        
        # 检查是否有复杂词（简单检查，可以后续优化）
        complex_words = ["然而", "因此", "虽然", "但是", "因为", "所以"]
        # 这里简化处理，完整检查在vocabulary_check.py已有
        
        return True, ""
