from typing import List
import re


class VocabularyChecker:
    """词汇难度检查
    
    检查文字是否适合目标年龄段，给出简化建议"""
    
    # 常用简单汉字表（适合低龄儿童）
    SIMPLE_CHARACTERS = set("""一二三四五六七八九十大小上下日月山水人
手口足耳目头发心肝脾胃肾红蓝黄白黑绿青紫橙灰粉金银
春夏秋冬早午晚夜里天晴天阴刮风下雨下雪雷电雾虹云
山川河流湖海森林草地花草树木果实种子苗叶片根枝
鸟鱼虫兽鸡鸭鹅猫狗牛马羊猪虎狮象狼熊鹿兔龙蛇
爸爸妈妈哥哥姐姐弟弟妹妹爷爷奶奶外公外婆舅舅姑姑
大小多少长短高低远近宽窄粗细方圆长短曲直弯直
开关进出开合上下左右前后东西南北中快慢轻重
好坏对错美丑善恶真假公私大小多少远近高低宽窄
东南西北春夏秋冬金木水火土一二三四五六七八九十
百千万亿年岁月日时分秒星期旬季度春夏秋冬
早中晚晨午暮夜上午下午晚上白天黑夜""".replace("\n", "").replace(" ", ""))
    
    def __init__(self, min_age: int, max_age: int):
        self.min_age = min_age
        self.max_age = max_age
    
    def check_difficulty(self, text: str) -> dict:
        """检查文本难度
        
        返回：
        {
            "difficulty_score": 0-1 (越高越难),
            "hard_words": List[str],
            "suggestions": List[str]
        }
        """
        if self.max_age <= 3:
            # 0-3岁：只应该有非常简单的字
            hard_words = []
            for char in text:
                if '\u4e00' <= char <= '\u9fff' and char not in self.SIMPLE_CHARACTERS:
                    hard_words.append(char)
            
            difficulty = len(hard_words) / max(len(text), 1)
            
            suggestions = []
            if difficulty > 0.3:
                suggestions.append("建议简化用词，使用更简单常用的汉字")
            
            return {
                "difficulty_score": difficulty,
                "hard_words": hard_words,
                "suggestions": suggestions
            }
        
        elif self.max_age <= 6:
            # 3-6岁：允许一些复杂词，但不要太多
            # MVP：简化检查
            words = re.findall(r'[\w]+', text)
            long_words = [w for w in words if len(w) > 4]
            difficulty = len(long_words) / max(len(words), 1)
            
            suggestions = []
            if difficulty > 0.4:
                suggestions.append("建议拆分长词为短句")
            
            return {
                "difficulty_score": difficulty,
                "hard_words": long_words,
                "suggestions": suggestions
            }
        
        else:
            # 6岁以上：基本不用检查
            return {
                "difficulty_score": 0,
                "hard_words": [],
                "suggestions": []
            }
