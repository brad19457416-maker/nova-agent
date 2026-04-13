from typing import Tuple, Dict, Optional
from ..models.character import Character
from ..models.style import StyleConfig
from nova_agent.llm.client_base import LLMClient


class StoryConceiver:
    """阶段1：核心创意生成
    
    根据用户输入，生成故事核心理念、主角设定、主题确定"""
    
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client
    
    def conceive(
        self,
        user_topic: str,
        target_age: Tuple[int, int],
        user_character_name: str = None,
        user_style: str = None,
        inspiration_advice: Dict = None,
    ) -> Tuple[str, Character, StyleConfig, str]:
        """
        参数：
        - user_topic: 用户输入的主题描述
        - target_age: 适合年龄段 (min_age, max_age)
        - user_character_name: 用户指定的主角名字
        - user_style: 用户指定的风格
        - inspiration_advice: 市场灵感学习建议（可选）
        
        返回：
        - story_title: 故事标题
        - character: 主角设定
        - style_config: 风格配置
        - theme: 核心主题
        """
        prompt = self._build_prompt(user_topic, target_age, user_character_name, user_style, inspiration_advice)
        response = self.llm.complete(prompt, temperature=0.8)
        
        return self._parse_response(response)
    
    def _build_prompt(
        self, topic: str, age: Tuple[int, int], char_name: str, style: str, inspiration_advice: Dict = None
    ) -> str:
        age_str = f"{age[0]}-{age[1]}岁儿童"
        char_name_part = f"主角名字叫 {char_name}" if char_name else "由你决定主角名字"
        
        style_part = f"艺术风格要求：{style}" if style else "由你推荐适合的艺术风格"
        
        inspiration_text = ""
        if inspiration_advice:
            from ..market_learner import MarketInspirationLearner
            ml = MarketInspirationLearner(None)
            inspiration_text = ml.get_inspiration_prompt_addition(inspiration_advice)
        
        return f"""你是儿童绘本创意总监。请为{age_str}创作一个儿童绘本故事生成核心创意。

用户主题：{topic}
{char_name_part}
{style_part}

{inspiration_text}

请按照以下JSON格式输出，不要加其他内容：

{{
  "title": "故事标题（吸引人，适合儿童",
  "theme": "故事传递的核心主题（一句话",
  "character": {{
    "name": "主角名字",
    "age": 主角年龄(数字，适合儿童故事的年龄",
    "personality": "性格特点（一句话）",
    "appearance": "外貌描述（一句话）
  }},
  "style": {{
    "art_style": "艺术风格，如水彩/卡通/扁平风/中国风/油画等",
    "additional_prompts": ["额外风格描述词列表"]
  }}
}}

开始输出JSON：
"""
    
    def _parse_response(self, response: str) -> Tuple[str, Character, StyleConfig, str]:
        # 简单解析，MVP 版本
        import json
        try:
            # 提取JSON部分
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1]
            
            data = json.loads(response.strip())
            
            character = Character(
                name=data["character"]["name"],
                age=int(data["character"]["age"]),
                personality=data["character"]["personality"],
                appearance=data["character"]["appearance"],
            )
            
            style = StyleConfig(
                art_style=data["style"]["art_style"],
                additional_prompts=data["style"].get("additional_prompts", []),
            )
            
            title = data["title"]
            theme = data["theme"]
            
            return title, character, style, theme
            
        except Exception as e:
            # 如果解析失败，使用 fallback
            raise ValueError(f"Failed to parse response: {e}\nResponse: {response}")
