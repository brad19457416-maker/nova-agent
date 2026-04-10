"""
WTA - Winner-Take-All 赢者通吃

根据 7±2 认知法则，限制同时激活的块数量，
只保留最相关的 Top-K，减少认知负荷和 token 消耗。
"""

from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class WTASelection:
    """
    WTA 赢者通吃
    
    限制激活区容量，遵循 7±2 认知法则，
    每个相似度簇只保留 Top-K。
    """
    
    def __init__(self, max_activate: int = 7, clusters: int = 2):
        """
        初始化
        
        Args:
            max_activate: 最大同时激活数（默认 7，7±2）
            clusters: 聚类数量
        """
        self.max_activate = max_activate
        self.clusters = clusters
    
    def select(self, blocks: List[Dict], query: str) -> List[Dict]:
        """
        选择最相关的 Top-K 块
        
        Args:
            blocks: 输入块列表
            query: 查询
        
        Returns:
            选择后的块列表，不超过 max_activate
        """
        if len(blocks) <= self.max_activate:
            return blocks
        
        # 按相关性排序（假设已有 similarity）
        sorted_blocks = sorted(
            blocks,
            key=lambda b: b.get('similarity', b.get('gain', 0)),
            reverse=True
        )
        
        # 保留最相关的
        selected = sorted_blocks[:self.max_activate]
        
        logger.debug(f"WTA selection: {len(blocks)} → {len(selected)} blocks")
        return selected
    
    def select_per_cluster(self, blocks: List[Dict], 
                         clusters: List[List[int]], 
                         top_per_cluster: int = 3) -> List[Dict]:
        """
        每个簇选 Top-K，保持多样性
        
        Args:
            blocks: 块列表
            clusters: 聚类结果，每个簇是块索引列表
            top_per_cluster: 每个簇保留数量
        
        Returns:
            选择后的块列表
        """
        selected = []
        for cluster in clusters:
            cluster_blocks = [blocks[i] for i in cluster]
            cluster_sorted = sorted(
                cluster_blocks,
                key=lambda b: b.get('similarity', 0),
                reverse=True
            )
            selected.extend(cluster_sorted[:top_per_cluster])
        
        # 如果总数超限，再次 WTA
        if len(selected) > self.max_activate:
            selected = sorted(
                selected,
                key=lambda b: b.get('similarity', 0),
                reverse=True
            )[:self.max_activate]
        
        return selected
