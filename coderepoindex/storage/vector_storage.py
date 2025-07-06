"""
向量存储实现

支持多种向量数据库后端，包括ChromaDB、FAISS等。
"""

import json
import numpy as np
from typing import List, Optional, Dict, Any, Union
from pathlib import Path
import logging

from .base import BaseVectorStorage, StorageConfig, StorageError, StorageConnectionError

logger = logging.getLogger(__name__)


class VectorStorage(BaseVectorStorage):
    """
    向量存储基础实现
    
    提供通用的向量存储接口。
    """
    
    def __init__(self, config: StorageConfig):
        super().__init__(config)
        self.vectors: Dict[str, Dict[str, Any]] = {}
        self.dimension = None
    
    def connect(self) -> None:
        """连接存储后端"""
        logger.info("向量存储连接成功")
    
    def disconnect(self) -> None:
        """断开存储连接"""
        logger.info("向量存储连接已断开")
    
    def health_check(self) -> bool:
        """健康检查"""
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """获取存储统计信息"""
        return {
            "total_vectors": len(self.vectors),
            "dimension": self.dimension,
            "storage_type": "memory"
        }
    
    def add_vector(
        self,
        vector_id: str,
        vector: List[float],
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """添加向量"""
        if self.dimension is None:
            self.dimension = len(vector)
        elif len(vector) != self.dimension:
            raise ValueError(f"向量维度不匹配: 期望{self.dimension}, 实际{len(vector)}")
        
        self.vectors[vector_id] = {
            "vector": vector,
            "metadata": metadata or {}
        }
    
    def add_vectors(
        self,
        vector_ids: List[str],
        vectors: List[List[float]],
        metadata: Optional[List[Dict[str, Any]]] = None
    ) -> None:
        """批量添加向量"""
        if len(vector_ids) != len(vectors):
            raise ValueError("向量ID和向量数量不匹配")
        
        metadata = metadata or [{}] * len(vector_ids)
        
        for i, (vector_id, vector) in enumerate(zip(vector_ids, vectors)):
            self.add_vector(vector_id, vector, metadata[i])
    
    def search_vectors(
        self,
        query_vector: List[float],
        top_k: int = 10,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """搜索相似向量"""
        if not self.vectors:
            return []
        
        # 计算相似度
        similarities = []
        query_np = np.array(query_vector)
        
        for vector_id, data in self.vectors.items():
            vector = np.array(data["vector"])
            metadata = data["metadata"]
            
            # 应用元数据过滤
            if metadata_filter:
                if not self._matches_filter(metadata, metadata_filter):
                    continue
            
            # 计算余弦相似度
            similarity = self._cosine_similarity(query_np, vector)
            similarities.append({
                "id": vector_id,
                "score": similarity,
                "metadata": metadata
            })
        
        # 排序并返回top_k
        similarities.sort(key=lambda x: x["score"], reverse=True)
        return similarities[:top_k]
    
    def get_vector(self, vector_id: str) -> Optional[Dict[str, Any]]:
        """获取向量"""
        return self.vectors.get(vector_id)
    
    def delete_vector(self, vector_id: str) -> bool:
        """删除向量"""
        if vector_id in self.vectors:
            del self.vectors[vector_id]
            return True
        return False
    
    def delete_vectors(self, vector_ids: List[str]) -> int:
        """批量删除向量"""
        deleted_count = 0
        for vector_id in vector_ids:
            if self.delete_vector(vector_id):
                deleted_count += 1
        return deleted_count
    
    def update_vector(
        self,
        vector_id: str,
        vector: Optional[List[float]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """更新向量"""
        if vector_id not in self.vectors:
            return False
        
        if vector is not None:
            self.vectors[vector_id]["vector"] = vector
        
        if metadata is not None:
            self.vectors[vector_id]["metadata"] = metadata
        
        return True
    
    def count_vectors(
        self,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> int:
        """统计向量数量"""
        if not metadata_filter:
            return len(self.vectors)
        
        count = 0
        for data in self.vectors.values():
            if self._matches_filter(data["metadata"], metadata_filter):
                count += 1
        
        return count
    
    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """计算余弦相似度"""
        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return dot_product / (norm_a * norm_b)
    
    def _matches_filter(self, metadata: Dict[str, Any], filter_dict: Dict[str, Any]) -> bool:
        """检查元数据是否匹配过滤条件"""
        for key, value in filter_dict.items():
            if key not in metadata:
                return False
            
            if isinstance(value, list):
                if metadata[key] not in value:
                    return False
            else:
                if metadata[key] != value:
                    return False
        
        return True


class ChromaVectorStorage(BaseVectorStorage):
    """
    ChromaDB向量存储实现
    
    使用ChromaDB作为向量数据库后端。
    """
    
    def __init__(self, config: StorageConfig):
        super().__init__(config)
        self.base_path = Path(config.base_path)
        self.collection_name = config.extra_config.get("collection_name", "code_vectors")
        self.client = None
        self.collection = None
    
    def connect(self) -> None:
        """连接存储后端"""
        try:
            import chromadb
            from chromadb.config import Settings
            
            # 创建目录
            self.base_path.mkdir(parents=True, exist_ok=True)
            
            # 连接ChromaDB
            self.client = chromadb.PersistentClient(
                path=str(self.base_path),
                settings=Settings(anonymized_telemetry=False)
            )
            
            # 获取或创建集合
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            
            logger.info(f"ChromaDB向量存储连接成功: {self.base_path}")
            
        except ImportError:
            raise StorageConnectionError("ChromaDB未安装: pip install chromadb")
        except Exception as e:
            logger.error(f"连接ChromaDB失败: {e}")
            raise StorageConnectionError(f"连接失败: {e}")
    
    def disconnect(self) -> None:
        """断开存储连接"""
        if self.client:
            self.client = None
            self.collection = None
            logger.info("ChromaDB向量存储连接已断开")
    
    def health_check(self) -> bool:
        """健康检查"""
        try:
            if not self.collection:
                return False
            
            # 检查集合是否可用
            self.collection.count()
            return True
            
        except Exception:
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """获取存储统计信息"""
        try:
            return {
                "total_vectors": self.collection.count(),
                "collection_name": self.collection_name,
                "storage_type": "chromadb",
                "base_path": str(self.base_path)
            }
            
        except Exception as e:
            logger.error(f"获取ChromaDB统计信息失败: {e}")
            return {}
    
    def add_vector(
        self,
        vector_id: str,
        vector: List[float],
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """添加向量"""
        try:
            self.collection.add(
                ids=[vector_id],
                embeddings=[vector],
                metadatas=[metadata or {}]
            )
            
        except Exception as e:
            logger.error(f"添加向量失败: {e}")
            raise StorageError(f"添加向量失败: {e}")
    
    def add_vectors(
        self,
        vector_ids: List[str],
        vectors: List[List[float]],
        metadata: Optional[List[Dict[str, Any]]] = None
    ) -> None:
        """批量添加向量"""
        try:
            self.collection.add(
                ids=vector_ids,
                embeddings=vectors,
                metadatas=metadata or [{}] * len(vector_ids)
            )
            
        except Exception as e:
            logger.error(f"批量添加向量失败: {e}")
            raise StorageError(f"批量添加向量失败: {e}")
    
    def search_vectors(
        self,
        query_vector: List[float],
        top_k: int = 10,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """搜索相似向量"""
        try:
            results = self.collection.query(
                query_embeddings=[query_vector],
                n_results=top_k,
                where=metadata_filter
            )
            
            # 转换结果格式
            search_results = []
            if results["ids"] and results["ids"][0]:
                for i, vector_id in enumerate(results["ids"][0]):
                    result = {
                        "id": vector_id,
                        "score": 1.0 - results["distances"][0][i],  # 转换为相似度
                        "metadata": results["metadatas"][0][i] if results["metadatas"][0] else {}
                    }
                    search_results.append(result)
            
            return search_results
            
        except Exception as e:
            logger.error(f"搜索向量失败: {e}")
            return []
    
    def get_vector(self, vector_id: str) -> Optional[Dict[str, Any]]:
        """获取向量"""
        try:
            results = self.collection.get(
                ids=[vector_id],
                include=["embeddings", "metadatas"]
            )
            
            if results["ids"] and results["ids"][0] == vector_id:
                return {
                    "vector": results["embeddings"][0] if results["embeddings"] else None,
                    "metadata": results["metadatas"][0] if results["metadatas"] else {}
                }
            
            return None
            
        except Exception as e:
            logger.error(f"获取向量失败: {e}")
            return None
    
    def delete_vector(self, vector_id: str) -> bool:
        """删除向量"""
        try:
            self.collection.delete(ids=[vector_id])
            return True
            
        except Exception as e:
            logger.error(f"删除向量失败: {e}")
            return False
    
    def delete_vectors(self, vector_ids: List[str]) -> int:
        """批量删除向量"""
        try:
            self.collection.delete(ids=vector_ids)
            return len(vector_ids)
            
        except Exception as e:
            logger.error(f"批量删除向量失败: {e}")
            return 0
    
    def update_vector(
        self,
        vector_id: str,
        vector: Optional[List[float]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """更新向量"""
        try:
            # ChromaDB的更新操作
            if vector is not None and metadata is not None:
                self.collection.update(
                    ids=[vector_id],
                    embeddings=[vector],
                    metadatas=[metadata]
                )
            elif vector is not None:
                self.collection.update(
                    ids=[vector_id],
                    embeddings=[vector]
                )
            elif metadata is not None:
                self.collection.update(
                    ids=[vector_id],
                    metadatas=[metadata]
                )
            
            return True
            
        except Exception as e:
            logger.error(f"更新向量失败: {e}")
            return False
    
    def count_vectors(
        self,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> int:
        """统计向量数量"""
        try:
            if metadata_filter:
                results = self.collection.get(where=metadata_filter)
                return len(results["ids"])
            else:
                return self.collection.count()
                
        except Exception as e:
            logger.error(f"统计向量数量失败: {e}")
            return 0


class FaissVectorStorage(BaseVectorStorage):
    """
    FAISS向量存储实现
    
    使用FAISS作为向量数据库后端。
    """
    
    def __init__(self, config: StorageConfig):
        super().__init__(config)
        self.base_path = Path(config.base_path)
        self.index_file = self.base_path / "faiss_index.bin"
        self.metadata_file = self.base_path / "faiss_metadata.json"
        self.index = None
        self.metadata = {}
        self.id_to_idx = {}
        self.idx_to_id = {}
        self.next_idx = 0
    
    def connect(self) -> None:
        """连接存储后端"""
        try:
            import faiss
            
            # 创建目录
            self.base_path.mkdir(parents=True, exist_ok=True)
            
            # 加载已有索引
            if self.index_file.exists():
                self.index = faiss.read_index(str(self.index_file))
                logger.info(f"加载已有FAISS索引: {self.index_file}")
            
            # 加载元数据
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.metadata = data.get("metadata", {})
                    self.id_to_idx = data.get("id_to_idx", {})
                    self.idx_to_id = {v: k for k, v in self.id_to_idx.items()}
                    self.next_idx = data.get("next_idx", 0)
            
            logger.info(f"FAISS向量存储连接成功: {self.base_path}")
            
        except ImportError:
            raise StorageConnectionError("FAISS未安装: pip install faiss-cpu")
        except Exception as e:
            logger.error(f"连接FAISS失败: {e}")
            raise StorageConnectionError(f"连接失败: {e}")
    
    def disconnect(self) -> None:
        """断开存储连接"""
        try:
            self._save_index()
            self._save_metadata()
            logger.info("FAISS向量存储连接已断开")
            
        except Exception as e:
            logger.error(f"断开FAISS连接失败: {e}")
    
    def health_check(self) -> bool:
        """健康检查"""
        return self.base_path.exists()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取存储统计信息"""
        try:
            return {
                "total_vectors": self.index.ntotal if self.index else 0,
                "dimension": self.index.d if self.index else 0,
                "storage_type": "faiss",
                "base_path": str(self.base_path)
            }
            
        except Exception as e:
            logger.error(f"获取FAISS统计信息失败: {e}")
            return {}
    
    def add_vector(
        self,
        vector_id: str,
        vector: List[float],
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """添加向量"""
        try:
            import faiss
            
            # 初始化索引
            if self.index is None:
                dimension = len(vector)
                self.index = faiss.IndexFlatIP(dimension)  # 内积索引
            
            # 添加向量
            vector_np = np.array([vector], dtype=np.float32)
            self.index.add(vector_np)
            
            # 保存映射关系
            idx = self.next_idx
            self.id_to_idx[vector_id] = idx
            self.idx_to_id[idx] = vector_id
            self.next_idx += 1
            
            # 保存元数据
            self.metadata[vector_id] = metadata or {}
            
        except Exception as e:
            logger.error(f"添加向量失败: {e}")
            raise StorageError(f"添加向量失败: {e}")
    
    def add_vectors(
        self,
        vector_ids: List[str],
        vectors: List[List[float]],
        metadata: Optional[List[Dict[str, Any]]] = None
    ) -> None:
        """批量添加向量"""
        for i, (vector_id, vector) in enumerate(zip(vector_ids, vectors)):
            meta = metadata[i] if metadata else {}
            self.add_vector(vector_id, vector, meta)
    
    def search_vectors(
        self,
        query_vector: List[float],
        top_k: int = 10,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """搜索相似向量"""
        try:
            if not self.index or self.index.ntotal == 0:
                return []
            
            # 搜索
            query_np = np.array([query_vector], dtype=np.float32)
            scores, indices = self.index.search(query_np, min(top_k, self.index.ntotal))
            
            # 转换结果
            results = []
            for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
                if idx == -1:  # 无效索引
                    continue
                
                vector_id = self.idx_to_id.get(idx)
                if not vector_id:
                    continue
                
                vector_metadata = self.metadata.get(vector_id, {})
                
                # 应用元数据过滤
                if metadata_filter:
                    if not self._matches_filter(vector_metadata, metadata_filter):
                        continue
                
                results.append({
                    "id": vector_id,
                    "score": float(score),
                    "metadata": vector_metadata
                })
            
            return results
            
        except Exception as e:
            logger.error(f"搜索向量失败: {e}")
            return []
    
    def get_vector(self, vector_id: str) -> Optional[Dict[str, Any]]:
        """获取向量"""
        try:
            if vector_id not in self.id_to_idx:
                return None
            
            idx = self.id_to_idx[vector_id]
            
            # FAISS不直接支持获取向量，这里只返回元数据
            return {
                "vector": None,  # FAISS不支持直接获取向量
                "metadata": self.metadata.get(vector_id, {})
            }
            
        except Exception as e:
            logger.error(f"获取向量失败: {e}")
            return None
    
    def delete_vector(self, vector_id: str) -> bool:
        """删除向量"""
        # FAISS不支持删除单个向量，这里只从元数据中移除
        try:
            if vector_id in self.metadata:
                del self.metadata[vector_id]
            
            if vector_id in self.id_to_idx:
                idx = self.id_to_idx[vector_id]
                del self.id_to_idx[vector_id]
                if idx in self.idx_to_id:
                    del self.idx_to_id[idx]
            
            return True
            
        except Exception as e:
            logger.error(f"删除向量失败: {e}")
            return False
    
    def delete_vectors(self, vector_ids: List[str]) -> int:
        """批量删除向量"""
        deleted_count = 0
        for vector_id in vector_ids:
            if self.delete_vector(vector_id):
                deleted_count += 1
        return deleted_count
    
    def update_vector(
        self,
        vector_id: str,
        vector: Optional[List[float]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """更新向量"""
        try:
            # FAISS不支持更新向量，只能更新元数据
            if metadata is not None and vector_id in self.metadata:
                self.metadata[vector_id] = metadata
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"更新向量失败: {e}")
            return False
    
    def count_vectors(
        self,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> int:
        """统计向量数量"""
        try:
            if not metadata_filter:
                return len(self.metadata)
            
            count = 0
            for vector_metadata in self.metadata.values():
                if self._matches_filter(vector_metadata, metadata_filter):
                    count += 1
            
            return count
            
        except Exception as e:
            logger.error(f"统计向量数量失败: {e}")
            return 0
    
    def _save_index(self) -> None:
        """保存索引"""
        try:
            import faiss
            
            if self.index:
                faiss.write_index(self.index, str(self.index_file))
                
        except Exception as e:
            logger.error(f"保存FAISS索引失败: {e}")
    
    def _save_metadata(self) -> None:
        """保存元数据"""
        try:
            data = {
                "metadata": self.metadata,
                "id_to_idx": self.id_to_idx,
                "next_idx": self.next_idx
            }
            
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"保存FAISS元数据失败: {e}")
    
    def _matches_filter(self, metadata: Dict[str, Any], filter_dict: Dict[str, Any]) -> bool:
        """检查元数据是否匹配过滤条件"""
        for key, value in filter_dict.items():
            if key not in metadata:
                return False
            
            if isinstance(value, list):
                if metadata[key] not in value:
                    return False
            else:
                if metadata[key] != value:
                    return False
        
        return True 