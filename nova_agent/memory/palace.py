"""
五级宫殿记忆系统
借鉴 MemPalace 宫殿式结构化存储
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime
import json
import os


@dataclass
class MemoryEntry:
    """记忆条目"""
    id: str
    content: str
    level: int  # 0-4
    timestamp: datetime
    importance: float = 1.0  # 0-1
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "content": self.content,
            "level": self.level,
            "timestamp": self.timestamp.isoformat(),
            "importance": self.importance,
            "tags": self.tags,
            "metadata": self.metadata,
            "access_count": self.access_count,
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "MemoryEntry":
        return cls(
            id=data["id"],
            content=data["content"],
            level=data["level"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            importance=data.get("importance", 1.0),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
            access_count=data.get("access_count", 0),
            last_accessed=datetime.fromisoformat(data["last_accessed"]) if data.get("last_accessed") else None
        )


@dataclass
class PalaceLevel:
    """宫殿层级"""
    level: int
    name: str
    description: str
    max_capacity: int
    entries: List[MemoryEntry] = field(default_factory=list)
    
    def add_entry(self, entry: MemoryEntry) -> bool:
        """添加条目，如果满返回False"""
        if len(self.entries) >= self.max_capacity:
            return False
        self.entries.append(entry)
        return True
    
    def search(self, query: str, top_k: int = 5) -> List[MemoryEntry]:
        """简单关键词搜索"""
        query_lower = query.lower()
        matches = []
        for entry in self.entries:
            score = 0
            if query_lower in entry.content.lower():
                score += 1
            for tag in entry.tags:
                if query_lower in tag.lower():
                    score += 0.5
            if score > 0:
                matches.append((score, entry))
        
        # 按分数排序
        matches.sort(key=lambda x: x[0], reverse=True)
        return [entry for _, entry in matches[:top_k]]
    
    def compress(self) -> None:
        """压缩：合并低重要性条目"""
        if len(self.entries) < self.max_capacity * 0.8:
            return
        
        # 按重要性排序，移除最低重要性的
        self.entries.sort(key=lambda e: (e.importance, e.access_count), reverse=True)
        self.entries = self.entries[:int(self.max_capacity * 0.7)]


class MemoryPalace:
    """
    五级宫殿记忆系统
    L0: 工作记忆 - 当前对话上下文
    L1: 短期记忆 - 当前任务相关信息
    L2: 中期记忆 - 会话内重要信息
    L3: 长期记忆 - 跨会话知识
    L4: 永久记忆 - 核心事实和技能
    """
    
    LEVEL_NAMES = {
        0: ("工作记忆", "当前对话上下文"),
        1: ("短期记忆", "当前任务相关信息"),
        2: ("中期记忆", "会话内重要信息"),
        3: ("长期记忆", "跨会话知识"),
        4: ("永久记忆", "核心事实和技能")
    }
    
    def __init__(self, storage_path: str = "./data/memory", max_entries_per_level: int = 1000):
        self.storage_path = storage_path
        self.max_entries = max_entries_per_level
        self.levels: Dict[int, PalaceLevel] = {}
        
        # 初始化五层
        for level in range(5):
            name, desc = self.LEVEL_NAMES[level]
            self.levels[level] = PalaceLevel(
                level=level,
                name=name,
                description=desc,
                max_capacity=max_entries_per_level
            )
        
        # 加载已有记忆
        self._load()
    
    def store(self, content: str, level: int = 1, importance: float = 1.0, 
              tags: Optional[List[str]] = None, metadata: Optional[Dict] = None) -> str:
        """
        存储记忆
        
        Args:
            content: 记忆内容
            level: 层级 0-4
            importance: 重要性 0-1
            tags: 标签列表
            metadata: 元数据
        
        Returns:
            记忆ID
        """
        if level < 0 or level > 4:
            level = 1
        
        entry_id = f"mem_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(content) % 10000}"
        
        entry = MemoryEntry(
            id=entry_id,
            content=content,
            level=level,
            timestamp=datetime.now(),
            importance=importance,
            tags=tags or [],
            metadata=metadata or {}
        )
        
        # 尝试添加到对应层级
        if not self.levels[level].add_entry(entry):
            # 层级满了，尝试压缩或升级
            self.levels[level].compress()
            if not self.levels[level].add_entry(entry):
                # 如果还是满，且不是最高层，升级到下一层
                if level < 4:
                    return self.store(content, level + 1, importance, tags, metadata)
        
        self._save()
        return entry_id
    
    def recall(self, query: str, level: Optional[int] = None, top_k: int = 5) -> List[MemoryEntry]:
        """
        回忆记忆
        
        Args:
            query: 查询内容
            level: 指定层级，None表示搜索全部
            top_k: 返回数量
        
        Returns:
            记忆条目列表
        """
        results = []
        
        levels_to_search = [level] if level is not None else range(4, -1, -1)  # 从高到低
        
        for lvl in levels_to_search:
            entries = self.levels[lvl].search(query, top_k)
            for entry in entries:
                # 更新访问统计
                entry.access_count += 1
                entry.last_accessed = datetime.now()
            results.extend(entries)
        
        # 按重要性排序
        results.sort(key=lambda e: e.importance, reverse=True)
        return results[:top_k]
    
    def get_context(self, max_entries: int = 10) -> str:
        """获取当前上下文（L0+L1）"""
        context_parts = []
        
        # L0: 工作记忆
        l0_entries = self.levels[0].entries[-5:]  # 最近5条
        if l0_entries:
            context_parts.append("【当前对话】")
            for entry in l0_entries:
                context_parts.append(f"- {entry.content}")
        
        # L1: 短期记忆
        l1_entries = sorted(
            self.levels[1].entries,
            key=lambda e: e.importance,
            reverse=True
        )[:5]
        if l1_entries:
            context_parts.append("\n【任务信息】")
            for entry in l1_entries:
                context_parts.append(f"- {entry.content}")
        
        return "\n".join(context_parts)
    
    def promote(self, entry_id: str, new_level: int) -> bool:
        """提升记忆层级"""
        for level in range(5):
            for entry in self.levels[level].entries:
                if entry.id == entry_id:
                    if level == new_level:
                        return True
                    # 移除原层级
                    self.levels[level].entries.remove(entry)
                    # 添加到新层级
                    entry.level = new_level
                    entry.importance = min(1.0, entry.importance + 0.1)
                    return self.levels[new_level].add_entry(entry)
        return False
    
    def _save(self) -> None:
        """保存到文件"""
        os.makedirs(self.storage_path, exist_ok=True)
        
        data = {
            "version": "0.1.0",
            "levels": {}
        }
        
        for level, palace in self.levels.items():
            data["levels"][level] = {
                "name": palace.name,
                "entries": [e.to_dict() for e in palace.entries]
            }
        
        filepath = os.path.join(self.storage_path, "palace_memory.json")
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _load(self) -> None:
        """从文件加载"""
        filepath = os.path.join(self.storage_path, "palace_memory.json")
        
        if not os.path.exists(filepath):
            return
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for level_str, level_data in data.get("levels", {}).items():
                level = int(level_str)
                if level in self.levels:
                    for entry_data in level_data.get("entries", []):
                        entry = MemoryEntry.from_dict(entry_data)
                        self.levels[level].entries.append(entry)
                        
        except Exception as e:
            print(f"加载记忆失败: {e}")
    
    def stats(self) -> Dict:
        """获取统计信息"""
        return {
            "total_entries": sum(len(l.entries) for l in self.levels.values()),
            "by_level": {level: len(p.entries) for level, p in self.levels.items()},
            "level_names": {level: p.name for level, p in self.levels.items()}
        }
