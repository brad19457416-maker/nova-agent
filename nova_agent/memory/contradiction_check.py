"""
ContradictionChecker - 矛盾拦截检测

当新输入与记忆中既有事实冲突时，立刻抛出警报，
防止 AI 在错误的基准上继续推理。
"""

from typing import List, Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)


class ContradictionChecker:
    """
    矛盾拦截检测器
    
    MemPalace 核心创新之一：在检索后自动检测新输入与已有记忆是否矛盾，
    提前发现冲突，避免 AI 基于错误信息推理。
    """
    
    def __init__(self, similarity_threshold: float = 0.7, 
               contradiction_threshold: float = 0.5):
        self.similarity_threshold = similarity_threshold
        self.contradiction_threshold = contradiction_threshold
    
    def check(self, new_statement: str, vector_store) -> Tuple[bool, List[Dict]]:
        """
        检查新陈述是否与已有记忆矛盾
        
        Args:
            new_statement: 新陈述
            vector_store: 向量存储
        
        Returns:
            (has_contradiction: bool, contradictions: List[Dict])
        """
        # 检索相似记忆
        similar = vector_store.search(new_statement, top_k=5)
        
        contradictions = []
        
        for result in similar:
            similarity = result.get("similarity", 0)
            if similarity >= self.similarity_threshold:
                # 相似主题，检查是否矛盾
                existing_text = result.get("text", "")
                if self._detect_contradiction(new_statement, existing_text):
                    contradictions.append({
                        "existing": existing_text,
                        "similarity": similarity,
                        "metadata": result.get("metadata", {})
                    })
        
        return len(contradictions) > 0, contradictions
    
    def filter_contradictions(self, query: str, results: List[Dict]) -> List[Dict]:
        """
        从检索结果中过滤掉矛盾记忆
        
        Args:
            query: 查询
            results: 检索结果
        
        Returns:
            过滤后的结果，矛盾标记出来
        """
        # 如果结果太少，不过滤
        if len(results) <= 1:
            return results
        
        # 检查两两之间是否矛盾
        filtered = []
        contradictions_found = []
        
        for i, result_a in enumerate(results):
            is_contradictory = False
            
            for j, result_b in enumerate(results):
                if i != j:
                    text_a = result_a.get("text", "")
                    text_b = result_b.get("text", "")
                    
                    if self._detect_contradiction(text_a, text_b):
                        contradictions_found.append((a, b))
                        # 保留置信度高的那个
                        if result_a.get("confidence", 0) < result_b.get("confidence", 0):
                            is_contradictory = True
                            break
            
            if not is_contradictory:
                filtered.append(result_a)
            else:
                logger.info(f"Contradiction filtered out from retrieval")
        
        return filtered
    
    def _detect_contradiction(self, text_a: str, text_b: str) -> bool:
        """
        检测两段文本是否矛盾
        
        使用简单启发式规则，实际中可交给 LLM 判断
        """
        # 常见矛盾关键词
        contradiction_patterns = [
            ("not", "is"),
            ("never", "always"),
            ("no", "yes"),
            ("false", "true"),
            ("incorrect", "correct"),
            ("wrong", "right"),
            ("versus", "vs"),
            ("vs", "versus"),
            ("contrary", "opposite"),
            ("contradicts", "contradiction"),
        ]
        
        # 快速启发式：检查否定词 + 相同主题
        # 完整检测交给 LLM 在推理阶段处理
        has_negation_a = any(word in text_a.lower() for word in ["not", "never", "no", "false", "incorrect"])
        has_negation_b = any(word in text_b.lower() for word in ["not", "never", "no", "false", "incorrect"])
        
        # 如果一个肯定一个否定，且主题相似，可能是矛盾
        if has_negation_a != has_negation_b:
            # 检查是否有相反断言
            return True
        
        return False
    
    def generate_contradiction_warning(self, contradictions: List[Dict]) -> str:
        """生成矛盾警告信息"""
        warning = "⚠️ **发现矛盾**：新陈述与记忆中已存事实冲突：\n\n"
        for i, c in enumerate(contradictions, 1):
            warning += f"{i}. 已有记忆：{c['existing'][:200]}...\n"
        warning += "\n请确认正确性，避免基于错误信息推理。"
        return warning
