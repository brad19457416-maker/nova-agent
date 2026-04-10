"""
时序事实图谱
支持时间推理和事实关联
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set, Any
from datetime import datetime
from enum import Enum
import json
import os


class FactType(Enum):
    """事实类型"""
    EVENT = "event"           # 事件
    STATE = "state"          # 状态
    RELATION = "relation"    # 关系
    ATTRIBUTE = "attribute"  # 属性


@dataclass
class FactNode:
    """事实节点"""
    id: str
    content: str
    fact_type: FactType
    timestamp: datetime
    confidence: float = 1.0
    source: Optional[str] = None
    entities: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "content": self.content,
            "fact_type": self.fact_type.value,
            "timestamp": self.timestamp.isoformat(),
            "confidence": self.confidence,
            "source": self.source,
            "entities": self.entities,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "FactNode":
        return cls(
            id=data["id"],
            content=data["content"],
            fact_type=FactType(data.get("fact_type", "event")),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            confidence=data.get("confidence", 1.0),
            source=data.get("source"),
            entities=data.get("entities", []),
            metadata=data.get("metadata", {})
        )


@dataclass
class TemporalEdge:
    """时序边 - 连接两个事实"""
    source_id: str
    target_id: str
    relation: str  # before, after, during, causes, etc.
    weight: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class TemporalGraph:
    """
    时序事实图谱
    管理带时间戳的事实及其关系
    """
    
    def __init__(self, storage_path: str = "./data/memory"):
        self.storage_path = storage_path
        self.nodes: Dict[str, FactNode] = {}
        self.edges: List[TemporalEdge] = []
        self.entity_index: Dict[str, Set[str]] = {}  # entity -> fact_ids
        
        self._load()
    
    def add_fact(
        self,
        content: str,
        fact_type: FactType = FactType.EVENT,
        timestamp: Optional[datetime] = None,
        entities: Optional[List[str]] = None,
        confidence: float = 1.0,
        source: Optional[str] = None
    ) -> str:
        """添加事实"""
        fact_id = f"fact_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(content) % 10000}"
        
        node = FactNode(
            id=fact_id,
            content=content,
            fact_type=fact_type,
            timestamp=timestamp or datetime.now(),
            confidence=confidence,
            source=source,
            entities=entities or []
        )
        
        self.nodes[fact_id] = node
        
        # 更新实体索引
        for entity in node.entities:
            if entity not in self.entity_index:
                self.entity_index[entity] = set()
            self.entity_index[entity].add(fact_id)
        
        self._save()
        return fact_id
    
    def add_relation(
        self,
        source_id: str,
        target_id: str,
        relation: str,
        weight: float = 1.0
    ) -> bool:
        """添加事实间关系"""
        if source_id not in self.nodes or target_id not in self.nodes:
            return False
        
        edge = TemporalEdge(
            source_id=source_id,
            target_id=target_id,
            relation=relation,
            weight=weight
        )
        
        self.edges.append(edge)
        self._save()
        return True
    
    def query_by_time(
        self,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        fact_type: Optional[FactType] = None
    ) -> List[FactNode]:
        """按时间范围查询"""
        results = []
        
        for node in self.nodes.values():
            if start and node.timestamp < start:
                continue
            if end and node.timestamp > end:
                continue
            if fact_type and node.fact_type != fact_type:
                continue
            results.append(node)
        
        # 按时间排序
        results.sort(key=lambda n: n.timestamp)
        return results
    
    def query_by_entity(self, entity: str) -> List[FactNode]:
        """按实体查询相关事实"""
        fact_ids = self.entity_index.get(entity, set())
        return [self.nodes[fid] for fid in fact_ids if fid in self.nodes]
    
    def query_timeline(self, entity: str) -> List[FactNode]:
        """查询实体的完整时间线"""
        facts = self.query_by_entity(entity)
        facts.sort(key=lambda f: f.timestamp)
        return facts
    
    def find_causal_chain(self, start_fact_id: str, max_depth: int = 3) -> List[List[str]]:
        """查找因果链"""
        chains = []
        
        def dfs(current_id: str, current_chain: List[str], depth: int):
            if depth >= max_depth:
                chains.append(current_chain.copy())
                return
            
            # 查找因果关系
            for edge in self.edges:
                if edge.source_id == current_id and edge.relation in ["causes", "leads_to"]:
                    current_chain.append(edge.target_id)
                    dfs(edge.target_id, current_chain, depth + 1)
                    current_chain.pop()
        
        dfs(start_fact_id, [start_fact_id], 0)
        return chains
    
    def infer_temporal_relation(self, fact1_id: str, fact2_id: str) -> Optional[str]:
        """推断两个事实间的时间关系"""
        if fact1_id not in self.nodes or fact2_id not in self.nodes:
            return None
        
        f1 = self.nodes[fact1_id]
        f2 = self.nodes[fact2_id]
        
        # 直接比较时间戳
        if f1.timestamp < f2.timestamp:
            return "before"
        elif f1.timestamp > f2.timestamp:
            return "after"
        else:
            return "simultaneous"
    
    def get_summary(self, entity: Optional[str] = None) -> str:
        """获取图谱摘要"""
        if entity:
            facts = self.query_by_entity(entity)
            if not facts:
                return f"未找到关于 '{entity}' 的事实"
            
            lines = [f"【{entity}的时间线】"]
            for fact in sorted(facts, key=lambda f: f.timestamp):
                time_str = fact.timestamp.strftime("%Y-%m-%d %H:%M")
                lines.append(f"  [{time_str}] {fact.content}")
            return "\n".join(lines)
        else:
            return f"图谱包含 {len(self.nodes)} 个事实，{len(self.edges)} 条关系"
    
    def _save(self) -> None:
        """保存到文件"""
        os.makedirs(self.storage_path, exist_ok=True)
        
        data = {
            "version": "0.1.0",
            "nodes": {fid: node.to_dict() for fid, node in self.nodes.items()},
            "edges": [
                {
                    "source": e.source_id,
                    "target": e.target_id,
                    "relation": e.relation,
                    "weight": e.weight
                }
                for e in self.edges
            ]
        }
        
        filepath = os.path.join(self.storage_path, "temporal_graph.json")
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _load(self) -> None:
        """从文件加载"""
        filepath = os.path.join(self.storage_path, "temporal_graph.json")
        
        if not os.path.exists(filepath):
            return
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 加载节点
            for fact_id, node_data in data.get("nodes", {}).items():
                node = FactNode.from_dict(node_data)
                self.nodes[fact_id] = node
                
                # 重建实体索引
                for entity in node.entities:
                    if entity not in self.entity_index:
                        self.entity_index[entity] = set()
                    self.entity_index[entity].add(fact_id)
            
            # 加载边
            for edge_data in data.get("edges", []):
                edge = TemporalEdge(
                    source_id=edge_data["source"],
                    target_id=edge_data["target"],
                    relation=edge_data["relation"],
                    weight=edge_data.get("weight", 1.0)
                )
                self.edges.append(edge)
                
        except Exception as e:
            print(f"加载时序图谱失败: {e}")
    
    def stats(self) -> Dict:
        """获取统计信息"""
        return {
            "total_nodes": len(self.nodes),
            "total_edges": len(self.edges),
            "entity_count": len(self.entity_index),
            "fact_types": {
                ft.value: sum(1 for n in self.nodes.values() if n.fact_type == ft)
                for ft in FactType
            }
        }
