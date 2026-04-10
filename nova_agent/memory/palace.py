"""
MemoryPalace - 五级虚拟记忆宫殿

融合 MemPalace 设计 + 我们已有时序事实图谱

五级结构：
- Wing 侧翼 → 高级分类（项目、人员、领域...）
- Room 房间 → 特定主题或项目
- Hall 厅堂 → 类型（决策、事件、事实...）
- Closet 壁橱 → 分类存储，存放压缩摘要
- Drawer 抽屉 → 原始完整内容
- Tunnel 隧道 → 交叉引用
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Tuple

from .aaak_compress import AAAKCompressor
from .contradiction_check import ContradictionChecker
from .retrieval import HierarchicalRetriever
from .vector_store import VectorStore

logger = logging.getLogger(__name__)


class MemoryPalace:
    """
    五级虚拟记忆宫殿

    空间化组织记忆，支持高效检索和压缩存储。
    """

    def __init__(self, data_dir: str = "./data/memory", vector_backend: str = "chromadb"):
        """
        初始化记忆宫殿

        Args:
            data_dir: 数据存储目录
            vector_backend: 向量存储后端
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # 初始化组件
        self.compressor = AAAKCompressor()
        self.contradiction_checker = ContradictionChecker()
        self.vector_store = VectorStore(backend=vector_backend)
        self.retriever = HierarchicalRetriever(self, self.vector_store)

        # 宫殿结构索引
        self.structure_index: Dict[str, Any] = {"wings": {}, "total_memories": 0}

        # 加载现有索引
        self._load_index()

    def _load_index(self):
        """加载结构索引"""
        index_path = self.data_dir / "palace_index.json"
        if index_path.exists():
            with open(index_path, encoding="utf-8") as f:
                self.structure_index = json.load(f)

    def _save_index(self):
        """保存结构索引"""
        index_path = self.data_dir / "palace_index.json"
        with open(index_path, "w", encoding="utf-8") as f:
            json.dump(self.structure_index, f, indent=2, ensure_ascii=False)

    def add_memory(
        self, wing: str, room: str, hall: str, content: str, compressed: bool = True
    ) -> str:
        """
        添加记忆到宫殿

        Args:
            wing: 侧翼名称
            room: 房间名称
            hall: 厅堂名称
            content: 原始内容
            compressed: 是否压缩存储

        Returns:
            memory_id
        """
        # 创建目录结构
        wing_dir = self.data_dir / wing
        room_dir = wing_dir / room
        hall_dir = room_dir / hall
        hall_dir.mkdir(parents=True, exist_ok=True)

        # 生成记忆ID
        memory_id = f"{wing}_{room}_{hall}_{self.structure_index['total_memories']}"

        # AAAK 压缩
        if compressed:
            compressed_content = self.compressor.compress(content)
        else:
            compressed_content = content

        # 存储：Closet 存压缩，Drawer 存原始
        closet_path = hall_dir / f"{memory_id}_closet.txt"
        drawer_path = hall_dir / f"{memory_id}_drawer.txt"

        with open(closet_path, "w", encoding="utf-8") as f:
            f.write(compressed_content)

        if not compressed:
            with open(drawer_path, "w", encoding="utf-8") as f:
                f.write(content)
        else:
            with open(drawer_path, "w", encoding="utf-8") as f:
                f.write(content)  # Drawer 总是存原始

        # 添加到向量存储
        self.vector_store.add(
            text=compressed_content,
            metadata={
                "memory_id": memory_id,
                "wing": wing,
                "room": room,
                "hall": hall,
                "compressed_length": len(compressed_content),
                "original_length": len(content),
            },
        )

        # 更新结构索引
        if wing not in self.structure_index["wings"]:
            self.structure_index["wings"][wing] = {"rooms": {}}

        if room not in self.structure_index["wings"][wing]["rooms"]:
            self.structure_index["wings"][wing]["rooms"][room] = {"halls": {}}

        if hall not in self.structure_index["wings"][wing]["rooms"][room]["halls"]:
            self.structure_index["wings"][wing]["rooms"][room]["halls"][hall] = {"memories": []}

        self.structure_index["wings"][wing]["rooms"][room]["halls"][hall]["memories"].append(
            {
                "id": memory_id,
                "path_closet": str(closet_path),
                "path_drawer": str(drawer_path),
                "compressed_length": len(compressed_content),
                "original_length": len(content),
            }
        )

        self.structure_index["total_memories"] += 1
        self._save_index()

        logger.debug(
            f"Added memory {memory_id}, compressed ratio: {len(compressed_content)/len(content):.2f}"
        )
        return memory_id

    def retrieve(
        self,
        query: str,
        hierarchical_filter: bool = True,
        contradiction_check: bool = True,
        top_k: int = 10,
    ) -> List[Dict]:
        """
        检索相关记忆

        Args:
            query: 查询文本
            hierarchical_filter: 是否启用分层过滤
            contradiction_check: 是否检查矛盾
            top_k: 返回结果数

        Returns:
            相关记忆列表
        """
        # 分层检索
        if hierarchical_filter:
            results = self.retriever.hierarchical_retrieve(query, top_k=top_k)
        else:
            # 直接向量检索
            results = self.vector_store.search(query, top_k=top_k)

        # 矛盾检查
        if contradiction_check and len(results) > 1:
            results = self.contradiction_checker.filter_contradictions(query, results)

        # 加载完整内容
        for result in results:
            result["content"] = self._load_content(result)

        return results

    def _load_content(self, result: Dict) -> str:
        """加载记忆内容"""
        # 如果已经有路径，直接加载
        if "path_closet" in result:
            with open(result["path_closet"], encoding="utf-8") as f:
                return f.read()
        elif "metadata" in result and "memory_id" in result["metadata"]:
            # 从向量搜索结果中获取信息
            metadata = result["metadata"]
            wing = metadata["wing"]
            room = metadata["room"]
            hall = metadata["hall"]
            memory_id = metadata["memory_id"]

            closet_path = self.data_dir / wing / room / hall / f"{memory_id}_closet.txt"
            if closet_path.exists():
                with open(closet_path, encoding="utf-8") as f:
                    return f.read()

        return result.get("text", "")

    def get_memory_full(self, memory_id: str) -> Dict[str, str]:
        """获取记忆的压缩和原始内容"""
        # 解析 ID 获取位置
        parts = memory_id.split("_")
        if len(parts) >= 4:
            wing, room, hall = parts[0], parts[1], parts[2]
            closet_path = self.data_dir / wing / room / hall / f"{memory_id}_closet.txt"
            drawer_path = self.data_dir / wing / room / hall / f"{memory_id}_drawer.txt"

            compressed = (
                open(closet_path, encoding="utf-8").read() if closet_path.exists() else ""
            )
            original = (
                open(drawer_path, encoding="utf-8").read() if drawer_path.exists() else ""
            )

            return {"compressed": compressed, "original": original}

        return {"compressed": "", "original": ""}

    def add_interaction(self, record: Dict[str, Any]) -> str:
        """添加交互记录到记忆"""
        return self.add_memory(
            wing="interactions",
            room=self._get_date_room(),
            hall="interactions",
            content=json.dumps(record, ensure_ascii=False, indent=2),
            compressed=True,
        )

    def _get_date_room(self) -> str:
        """按日期分房间"""
        from datetime import datetime

        return datetime.now().strftime("%Y_%m")

    def check_contradiction(self, new_statement: str) -> Tuple[bool, List]:
        """检查新陈述是否与已有记忆矛盾"""
        return self.contradiction_checker.check(new_statement, self.vector_store)

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "total_memories": self.structure_index["total_memories"],
            "num_wings": len(self.structure_index["wings"]),
            "vector_size": self.vector_store.count(),
        }

    def list_wings(self) -> List[str]:
        """列出所有侧翼"""
        return list(self.structure_index["wings"].keys())

    def list_rooms(self, wing: str) -> List[str]:
        """列出侧翼下所有房间"""
        if wing in self.structure_index["wings"]:
            return list(self.structure_index["wings"][wing]["rooms"].keys())
        return []
