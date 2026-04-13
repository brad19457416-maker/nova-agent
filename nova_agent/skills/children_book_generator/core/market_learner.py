from typing import List, Dict, Any, Tuple
from ..models.book import Book
from ..models.character import Character
from nova_agent.llm.client_base import LLMClient


class MarketInspirationLearner:
    """市场灵感学习模块
    
    分析优秀儿童绘本的成功要素，为当前创作提供参考，避免雷同抄袭，
    只学习结构、节奏、吸引力法则等抽象要素。"""
    
    SUCCESSFUL_PICTURE_BOOKS = [
        {
            "title": "好饿的毛毛虫",
            "theme": "认知数字和食物，成长变化",
            "character": "毛毛虫",
            "target_age": "0-3岁",
            "success_factors": [
                "互动式洞洞设计增加触觉体验",
                "简单重复的语言节奏，适合认知学习",
                "清晰的成长变化弧线，满足好奇心",
                "从饥饿到饱足的完整闭环",
                "色彩鲜明，图形简洁"
            ],
            "structure": [
                "开篇引入主角",
                "每天吃不同东西，重复中带变化",
                "化茧成蝶的惊喜结局"
            ]
        },
        {
            "title": "猜猜我是谁",
            "theme": "认知动物，亲子互动猜谜",
            "character": "各种动物",
            "target_age": "0-3岁",
            "success_factors": [
                "洞洞镂空设计引发猜测",
                "一问一答互动结构，适合亲子共读",
                "重复句式，语言学习效果好",
                "每次翻页都有惊喜感",
                "图形识别启蒙"
            ],
            "structure": [
                "露出一部分让读者猜",
                "翻页揭晓完整答案",
                "重复这个模式直到最后"
            ]
        },
        {
            "title": "布朗家的乔治",
            "theme": "友谊，接纳不同，自我认同",
            "character": "紫色的河马乔治",
            "target_age": "3-6岁",
            "success_factors": [
                "独特的外貌设定引发身份认同话题",
                "温暖包容的价值观传递自然不生硬",
                "朋友一起解决问题，传递正能量",
                "柔软温馨的画风匹配主题",
                "简单重复的名字记忆点强"
            ],
            "structure": [
                "介绍乔治与众不同",
                "朋友们一开始不习惯",
                "乔治帮助大家，获得接纳",
                "大家都喜欢乔治"
            ]
        },
        {
            "title": "神奇飞书",
            "theme": "书籍的力量，阅读改变生活",
            "character": "爱书的年轻人莫里斯",
            "target_age": "6-12岁",
            "success_factors": [
                "强烈的视觉冲击力，飓风场景震撼",
                "书拟人化，赋予情感生命",
                "从孤独到充实，精神成长弧线清晰",
                "呼吁珍惜书籍，主题升华自然",
                "画面层次感强，想象力丰富"
            ],
            "structure": [
                "平静生活被灾难打破",
                "遇到神奇的飞书被吸引",
                "拯救书籍，重新建立精神家园",
                "传承给下一代"
            ]
        },
        {
            "title": "肚子里有个火车站",
            "theme": "健康饮食，消化系统科普",
            "character": "小女孩茱莉娅",
            "target_age": "3-6岁",
            "success_factors": [
                "把消化系统拟人化为火车站，生动好懂",
                "健康饮食习惯的知识自然融入故事",
                "问题-解决结构清晰，有教育意义",
                "小精灵工作的画面童趣盎然",
                "家长喜欢，孩子也听得懂"
            ],
            "structure": [
                "茱莉娅吃得太快太多",
                "小精灵们加班干活，出问题了",
                "肠胃不舒服，肚子痛",
                "好好休息恢复正常，养成好习惯"
            ]
        },
        {
            "title": "安的种子",
            "theme": "耐心等待，顺应自然",
            "character": "三个小和尚安、本、静",
            "target_age": "3-6岁",
            "success_factors": [
                "富含东方哲理，寓意深远但不晦涩",
                "三个角色三种态度对比鲜明",
                "四季变化的时间感营造得好",
                "水墨风格，意境优美",
                "大人孩子都能读懂不同层次"
            ],
            "structure": [
                "师傅分给每人一颗莲花种子",
                "本急于种，静太小心，安顺其自然",
                "冬天等待，春天播种",
                "莲花终于盛开，安成功了"
            ]
        },
        {
            "title": "大卫不可以",
            "theme": "规则教育，母爱包容",
            "character": "调皮小男孩大卫",
            "target_age": "3-6岁",
            "success_factors": [
                '真实再现孩子的调皮日常，共鸣强',
                '妈妈说"不可以"但最后还是爱孩子，情感完整',
                "大画面夸张表情，孩子喜欢看",
                "每个跨页一个调皮行为，节奏感好",
                "结尾温暖，管教不是目的，爱才是"
            ],
            "structure": [
                "大卫各种调皮捣蛋，妈妈不断制止",
                "闯大祸打翻东西，大卫害怕了",
                "妈妈拥抱大卫说我爱你",
                "最后大卫乖乖睡觉"
            ]
        },
        {
            "title": "我爸爸",
            "theme": "父子亲情，孩子眼中的爸爸",
            "character": "小男孩的爸爸",
            "target_age": "0-3岁",
            "success_factors": [
                '简单重复的句式，"我爸爸真的很棒"，记忆点强',
                "孩子视角的夸张赞美，情感真挚",
                "每页一个特点，跳跃但统一，温暖感强",
                "画风粗犷随性，符合爸爸形象",
                '结尾"我爱你，爸爸也爱我"情感升华'
            ],
            "structure": [
                "开篇点题\"我爸爸真棒\"",
                "每页列举爸爸的一个优点/能力",
                "各种夸张有趣的形容",
                "结尾情感定格，我爱爸爸"
            ]
        }
    ]
    
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client
    
    def analyze_topic(
        self,
        user_topic: str,
        target_age: Tuple[int, int],
        theme: str = None
    ) -> Dict[str, Any]:
        """根据用户主题，分析市场上类似成功绘本的可学习要素
        
        返回抽象的创作建议，不抄袭具体内容"""
        
        # 筛选同年龄段的成功案例
        age_min, age_max = target_age
        relevant_cases = self._filter_relevant_cases(user_topic, age_min, age_max)
        
        prompt = self._build_analysis_prompt(
            user_topic, theme, target_age, relevant_cases
        )
        response = self.llm.complete(prompt, temperature=0.6)
        
        return self._parse_analysis_response(response)
    
    def _filter_relevant_cases(
        self, topic: str, age_min: int, age_max: int
    ) -> List[Dict]:
        """根据主题和年龄段筛选相关案例"""
        # 简单匹配：同年龄段优先，主题关键词匹配
        filtered = []
        topic_lower = topic.lower()
        
        for case in self.SUCCESSFUL_PICTURE_BOOKS:
            case_age_min = int(case["target_age"].split("-")[0])
            case_age_max = int(case["target_age"].split("-")[1])
            
            # 年龄段重叠就算相关
            if not (case_age_max < age_min or case_age_min > age_max):
                # 检查主题关键词是否有重叠
                case_words = (case["title"] + case["theme"]).lower()
                if any(word in case_words for word in topic_lower.split()):
                    filtered.append(case)
                else:
                    # 至少保留1-2个同年龄段案例
                    if len(filtered) < 2:
                        filtered.append(case)
        
        # 最多返回4个案例，避免prompt太长
        return filtered[:4]
    
    def _build_analysis_prompt(
        self,
        topic: str,
        theme: str,
        target_age: Tuple[int, int],
        relevant_cases: List[Dict]
    ) -> str:
        age_str = f"{target_age[0]}-{target_age[1]}岁"
        theme_part = f"核心主题：{theme}" if theme else "主题由故事自然生发"
        
        cases_text = ""
        for i, case in enumerate(relevant_cases):
            cases_text += f"""
案例{i+1}: 《{case['title']}》
- 适合年龄：{case['target_age']}
- 主题：{case['theme']}
- 成功要素：{', '.join(case['success_factors'])}
- 结构：{' → '.join(case['structure'])}
"""
        
        return f"""你是儿童绘本创作顾问，擅长分析市场上成功儿童绘本的成功经验，
并为新创作提供抽象的启发建议。

我们现在要创作一本新的儿童绘本：
- 用户主题：{topic}
- {theme_part}
- 适合年龄：{age_str}

参考市场上类似主题/年龄段的成功绘本案例（只学习抽象经验，绝对不能抄袭这些作品的具体内容和角色）：

{cases_text}

请分析提炼出对我们这本新绘本创作有帮助的启发建议。从以下几个方面分析：

1. 结构节奏建议：如何分配起承转合，每页信息量如何控制
2. 吸引力设计：如何制造惊喜、互动、记忆点，让孩子喜欢反复读
3. 主题传递：如何自然传递核心主题，不生硬说教
4. 语言风格：适合这个年龄段的语言特点，韵律、字数、重复技巧
5. 角色塑造：如何让主角形象鲜明，让孩子产生共鸣

请按照JSON格式输出：

{{
  "structure_advice": "结构节奏建议（一句话）",
  "appeal_advice": "吸引力设计建议（一句话）",
  "theme_advice": "主题传递建议（一句话）",
  "language_advice": "语言风格建议（一句话）",
  "character_advice": "角色塑造建议（一句话）",
  "key_tips": ["最重要的3-5条可落地创作技巧列表"]
}}

只输出JSON，不要其他内容：
"""
    
    def _parse_analysis_response(self, response: str) -> Dict[str, Any]:
        import json
        try:
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1]
            
            data = json.loads(response.strip())
            return data
            
        except Exception as e:
            raise ValueError(f"Failed to parse market analysis: {e}\nResponse: {response}")
    
    def get_inspiration_prompt_addition(self, analysis: Dict[str, Any]) -> str:
        """将分析结果转换为给后续创作阶段的额外提示词"""
        
        tips = "\n".join([f"- {tip}" for tip in analysis.get("key_tips", [])])
        
        return f"""
创作质量提升参考（来自市场成功案例启发）：

结构节奏：{analysis.get('structure_advice', '')}
吸引力设计：{analysis.get('appeal_advice', '')}
主题传递：{analysis.get('theme_advice', '')}
语言风格：{analysis.get('language_advice', '')}
角色塑造：{analysis.get('character_advice', '')}

关键创作要点：
{tips}
"""
