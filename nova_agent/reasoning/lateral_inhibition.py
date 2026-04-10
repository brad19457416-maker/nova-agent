"""
Adaptive Lateral Inhibition - 自适应侧抑制

神经科学启发：相邻神经元相互抑制，
结果越相似抑制越强，自动去重减少冗余。
"""

import logging

logger = logging.getLogger(__name__)


class AdaptiveLateralInhibition:
    """
    自适应侧抑制

    当多个块结果高度相似时，自动抑制冗余，
    结果越多抑制越强，减少信息冗余。
    """

    def __init__(self, base_inhibition: float = 0.1, similarity_threshold: float = 0.7):
        self.base_inhibition = base_inhibition
        self.similarity_threshold = similarity_threshold

    def inhibit(self, blocks: list[dict], query: str) -> list[dict]:
        """
        应用侧抑制，减少冗余

        Args:
            blocks: 块列表，每个块有 similarity 或 score
            query: 查询

        Returns:
            抑制后的块列表（移除被完全抑制的块）
        """
        if len(blocks) <= 1:
            return blocks

        # 计算块之间相似度矩阵
        n = len(blocks)
        # 简化：基于关键词重叠计算相似度
        similarities = self._compute_similarity_matrix(blocks)

        # 计算每个块的抑制强度
        # 块受到的抑制 = Σ(相似度 * 得分)
        inhibited = []
        for i in range(n):
            total_inhibition = 0.0
            for j in range(n):
                if i != j and similarities[i][j] > self.similarity_threshold:
                    score_j = blocks[j].get("similarity", 0.5)
                    total_inhibition += similarities[i][j] * score_j

            # 抑制强度随结果数量增加
            adaptive_inhibition = self.base_inhibition * (n / 5)
            total_inhibition *= adaptive_inhibition

            # 原始得分
            original_score = blocks[i].get("similarity", 0.5)
            inhibited_score = original_score - total_inhibition

            block_copy = blocks[i].copy()
            block_copy["inhibited_score"] = max(inhibited_score, 0.0)
            block_copy["inhibition"] = total_inhibition

            if inhibited_score > 0:
                inhibited.append(block_copy)

        logger.debug(f"Lateral inhibition: {len(blocks)} → {len(inhibited)} blocks")
        return inhibited

    def _compute_similarity_matrix(self, blocks: list[dict]) -> list[list[float]]:
        """计算块之间的相似度矩阵"""
        n = len(blocks)
        matrix = [[0.0 for _ in range(n)] for _ in range(n)]

        # 预计算每个块的词集合
        word_sets = []
        for block in blocks:
            text = block.get("description", "").lower()
            if "result" in block:
                text += " " + block["result"][:200].lower()
            words = set(text.split())
            word_sets.append(words)

        # 计算 Jaccard 相似度
        for i in range(n):
            for j in range(n):
                if i == j:
                    matrix[i][j] = 1.0
                else:
                    set_i = word_sets[i]
                    set_j = word_sets[j]
                    intersection = len(set_i & set_j)
                    union = len(set_i | set_j)
                    if union == 0:
                        matrix[i][j] = 0
                    else:
                        matrix[i][j] = intersection / union

        return matrix
