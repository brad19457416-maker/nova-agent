"""
VectorStore - 抽象向量存储基类

支持多种后端，可插拔替换：
- 内存简单实现
- ChromaDB（推荐）
- 其他后端可扩展
"""

from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


class VectorStore(ABC):
    """向量存储抽象基类"""
    
    @abstractmethod
    def add(self, text: str, metadata: Dict[str, Any]) -> None:
        """添加文本到向量存储"""
        pass
    
    @abstractmethod
    def search(self, query: str, top_k: int = 10) -> List[Dict]:
        """搜索相似文本，返回结果列表，每个包含 text, similarity, metadata"""
        pass
    
    @abstractmethod
    def count(self) -> int:
        """返回存储的向量数量"""
        pass
    
    @abstractmethod
    def delete(self, ids: List[str]) -> None:
        """删除向量"""
        pass


class InMemoryVectorStore(VectorStore):
    """简单内存向量存储（用于测试和小规模场景）"""
    
    def __init__(self):
        self.data: List[Dict] = []
        self._embedder = None
    
    def _get_embedding(self, text: str) -> List[float]:
        """获取嵌入，这里简单使用懒加载"""
        if self._embedder is None:
            from sentence_transformers import SentenceTransformer
            self._embedder = SentenceTransformer('all-MiniLM-L6-v2')
        
        return self._embedder.encode(text).tolist()
    
    def add(self, text: str, metadata: Dict[str, Any]) -> None:
        embedding = self._get_embedding(text)
        self.data.append({
            "text": text,
            "embedding": embedding,
            "metadata": metadata
        })
    
    def _cosine_sim(self, a: List[float], b: List[float]) -> float:
        """余弦相似度计算"""
        import math
        dot = sum(x*y for x,y in zip(a,b))
        mag_a = math.sqrt(sum(x*x for x in a))
        mag_b = math.sqrt(sum(x*x for x in b))
        if mag_a == 0 or mag_b == 0:
            return 0
        return dot / (mag_a * mag_b)
    
    def search(self, query: str, top_k: int = 10) -> List[Dict]:
        query_emb = self._get_embedding(query)
        
        results = []
        for item in self.data:
            sim = self._cosine_sim(query_emb, item["embedding"])
            results.append({
                "text": item["text"],
                "similarity": sim,
                "metadata": item["metadata"]
            })
        
        results.sort(key=lambda x: -x["similarity"])
        return results[:top_k]
    
    def count(self) -> int:
        return len(self.data)
    
    def delete(self, ids: List[str]) -> None:
        # 简单实现，按 metadata id 删除
        self.data = [
            item for item in self.data
            if item["metadata"].get("id") not in ids
        ]


class ChromaDBVectorStore(VectorStore):
    """ChromaDB 向量存储（推荐用于生产）"""
    
    def __init__(self, collection_name: str = "nova_agent_memories",
               persist_directory: str = "./data/chroma"):
        try:
            import chromadb
            self.client = chromadb.PersistentClient(path=persist_directory)
            self.collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info(f"ChromaDB initialized, collection: {collection_name}")
        except ImportError:
            logger.error("ChromaDB not installed, install with: pip install chromadb")
            raise
    
    def add(self, text: str, metadata: Dict[str, Any]) -> None:
        import uuid
        doc_id = str(uuid.uuid4())
        
        # Chroma 自动处理嵌入
        self.collection.add(
            documents=[text],
            metadatas=[metadata],
            ids=[doc_id]
        )
    
    def search(self, query: str, top_k: int = 10) -> List[Dict]:
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k
        )
        
        # 格式化返回
        formatted = []
        if results['documents'] and results['documents'][0]:
            for i, doc in enumerate(results['documents'][0]):
                metadata = results['metadatas'][0][i] if results['metadatas'] else {}
                # Chroma 返回距离，转换为相似度（余弦距离 → 相似度）
                distance = results['distances'][0][i] if results['distances'] else 0
                similarity = 1 - distance  # 因为余弦距离范围 [0,2]，这里简化处理
                
                formatted.append({
                    "text": doc,
                    "similarity": similarity,
                    "metadata": metadata
                })
        
        return formatted
    
    def count(self) -> int:
        return self.collection.count()
    
    def delete(self, ids: List[str]) -> None:
        self.collection.delete(ids=ids)


def VectorStore(backend: str = "chromadb", **kwargs) -> VectorStore:
    """工厂方法创建向量存储"""
    if backend == "memory":
        return InMemoryVectorStore()
    elif backend == "chromadb":
        return ChromaDBVectorStore(**kwargs)
    else:
        raise ValueError(f"Unknown vector store backend: {backend}")
