"""
Bidirectional Attention Flow - 双向注意力流

我们首创：传统只有下层 → 上层单向信息流，
我们实现上层发现新线索 → 反向激活下层相关块，
让信息流动更充分。
"""

import logging

logger = logging.getLogger(__name__)


class BidirectionalAttentionFlow:
    """
    双向注意力流

    上层聚合后，如果发现上层提到了下层没有充分挖掘的概念，
    反向激活下层相关块，补充信息。
    """

    def __init__(self, enabled: bool = True, reverse_threshold: float = 0.3):
        self.enabled = enabled
        self.reverse_threshold = reverse_threshold

    def is_enabled(self) -> bool:
        return self.enabled

    def reverse_activate(
        self, aggregation_result, current_blocks: list[dict], context: dict
    ) -> list[dict]:
        """
        反向激活：检查上层聚合结果中提到的新概念，
        在下层激活相关块补充信息。

        Args:
            aggregation_result: 上层聚合结果
            current_blocks: 当前已有块
            context: 上下文

        Returns:
            更新后的块列表（可能新增了块）
        """
        if not self.enabled:
            return current_blocks

        aggregated_text = aggregation_result.aggregated_text

        # 提取聚合文本中的关键概念
        new_concepts = self._extract_new_concepts(aggregated_text, current_blocks)

        if not new_concepts:
            return current_blocks

        # 检查这些新概念是否需要新增块
        new_blocks = self._generate_new_blocks(new_concepts, aggregated_text, context)

        # 合并到现有块
        if new_blocks:
            logger.info(f"Bidirectional attention added {len(new_blocks)} new blocks")
            current_blocks.extend(new_blocks)

        return current_blocks

    def _extract_new_concepts(self, aggregated_text: str, current_blocks: list[dict]) -> list[str]:
        """提取聚合文本中出现的新概念（不在已有块中）"""
        # 简单关键词提取实现
        existing_words = set()
        for block in current_blocks:
            desc = block.get("description", "").lower()
            existing_words.update(desc.split())
            if "result" in block:
                existing_words.update(block["result"].lower().split())

        # 找出聚合文本中不在已有块的重要词汇
        aggregated_words = aggregated_text.lower().split()
        new_concepts = []

        # 滑动窗口找双词短语
        for i in range(len(aggregated_words) - 1):
            phrase = aggregated_words[i] + " " + aggregated_words[i + 1]
            # 检查短语中至少一个词不在现有词中
            words = phrase.split()
            if any(word not in existing_words for word in words) and len(phrase) > 6:
                new_concepts.append(phrase)

        # 去重，限制数量
        new_concepts = list(set(new_concepts))
        return new_concepts[:5]  # 最多反向激活 5 个新概念

    def _generate_new_blocks(
        self, new_concepts: list[str], aggregated_text: str, context: dict
    ) -> list[dict]:
        """为新概念生成新的子任务块"""
        new_blocks = []

        for concept in new_concepts:
            # 检查是否已经有块覆盖这个概念了
            already_covered = False
            for block in context.get("blocks", []):
                if concept in block.get("description", "").lower():
                    already_covered = True
                    break

            if not already_covered:
                new_blocks.append(
                    {
                        "id": f"reverse_{len(new_blocks) + len(context.get('blocks', []))}",
                        "description": f"深入探究'{concept}'相关信息",
                        "is_reverse_activated": True,
                    }
                )

        return new_blocks
