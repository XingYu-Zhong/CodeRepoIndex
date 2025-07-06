"""
复合存储实现

整合多种存储后端，提供统一的存储接口。
"""

from typing import Dict, Any, Optional, List
import logging

from .base import StorageConfig
from .local_storage import LocalFileStorage
from .vector_storage import VectorStorage, ChromaVectorStorage, FaissVectorStorage
from ..core.models import CodeBlock, RepositoryIndex, SearchQuery

logger = logging.getLogger(__name__)


class CompositeStorage:
    """
    复合存储实现
    
    整合代码块存储、向量存储和元数据存储，提供统一的存储接口。
    """
    
    def __init__(
        self,
        code_block_storage,
        vector_storage,
        metadata_storage
    ):
        self.code_block_storage = code_block_storage
        self.vector_storage = vector_storage
        self.metadata_storage = metadata_storage
    
    def connect(self) -> None:
        """连接所有存储后端"""
        self.code_block_storage.connect()
        self.vector_storage.connect()
        self.metadata_storage.connect()
    
    def disconnect(self) -> None:
        """断开所有存储连接"""
        self.code_block_storage.disconnect()
        self.vector_storage.disconnect()
        self.metadata_storage.disconnect()
    
    def health_check(self) -> Dict[str, bool]:
        """健康检查"""
        return {
            "code_block_storage": self.code_block_storage.health_check(),
            "vector_storage": self.vector_storage.health_check(),
            "metadata_storage": self.metadata_storage.health_check()
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """获取存储统计信息"""
        return {
            "code_block_storage": self.code_block_storage.get_stats(),
            "vector_storage": self.vector_storage.get_stats(),
            "metadata_storage": self.metadata_storage.get_stats()
        }
    
    # 代码块存储方法
    def save_code_block(self, code_block: CodeBlock) -> None:
        """保存代码块"""
        self.code_block_storage.save_code_block(code_block)
    
    def save_code_blocks(self, code_blocks: List[CodeBlock]) -> None:
        """批量保存代码块"""
        self.code_block_storage.save_code_blocks(code_blocks)
    
    def get_code_block(self, block_id: str) -> Optional[CodeBlock]:
        """获取代码块"""
        return self.code_block_storage.get_code_block(block_id)
    
    def query_code_blocks(self, **kwargs) -> List[CodeBlock]:
        """查询代码块"""
        return self.code_block_storage.query_code_blocks(**kwargs)
    
    def delete_code_block(self, block_id: str) -> bool:
        """删除代码块"""
        return self.code_block_storage.delete_code_block(block_id)
    
    def delete_code_blocks(self, repository_id: str) -> int:
        """删除仓库的所有代码块"""
        return self.code_block_storage.delete_code_blocks(repository_id)
    
    # 向量存储方法
    def add_vector(
        self,
        vector_id: str,
        vector: List[float],
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """添加向量"""
        self.vector_storage.add_vector(vector_id, vector, metadata)
    
    def search_vectors(
        self,
        query_vector: List[float],
        top_k: int = 10,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """搜索相似向量"""
        return self.vector_storage.search_vectors(query_vector, top_k, metadata_filter)
    
    def delete_vectors(self, vector_ids: List[str]) -> int:
        """批量删除向量"""
        return self.vector_storage.delete_vectors(vector_ids)
    
    # 元数据存储方法
    def save_repository_index(self, repository_index: RepositoryIndex) -> None:
        """保存仓库索引"""
        self.metadata_storage.save_repository_index(repository_index)
    
    def get_repository_index(self, repository_id: str) -> Optional[RepositoryIndex]:
        """获取仓库索引"""
        return self.metadata_storage.get_repository_index(repository_id)
    
    def list_repository_indexes(self) -> List[RepositoryIndex]:
        """列出所有仓库索引"""
        return self.metadata_storage.list_repository_indexes()
    
    def save_search_query(self, query: SearchQuery) -> None:
        """保存搜索查询"""
        self.metadata_storage.save_search_query(query)
    
    # 复合操作
    def save_code_block_with_vector(
        self,
        code_block: CodeBlock,
        vector: Optional[List[float]] = None
    ) -> None:
        """保存代码块和对应的向量"""
        # 保存代码块
        self.save_code_block(code_block)
        
        # 保存向量（如果提供）
        if vector is not None and code_block.embedding is None:
            code_block.embedding = vector
        
        if code_block.embedding:
            self.add_vector(
                vector_id=code_block.block_id,
                vector=code_block.embedding,
                metadata={
                    "repository_id": code_block.repository_id,
                    "file_path": code_block.file_path,
                    "block_type": code_block.block_type.value,
                    "language": code_block.language,
                    "name": code_block.name
                }
            )
    
    def delete_repository_data(self, repository_id: str) -> Dict[str, Any]:
        """删除仓库的所有相关数据"""
        # 获取要删除的代码块
        code_blocks = self.query_code_blocks(repository_id=repository_id)
        block_ids = [block.block_id for block in code_blocks]
        
        # 删除代码块
        deleted_blocks = self.delete_code_blocks(repository_id)
        
        # 删除向量
        deleted_vectors = self.delete_vectors(block_ids) if block_ids else 0
        
        # 删除仓库索引
        deleted_index = self.metadata_storage.delete_repository_index(repository_id)
        
        return {
            "deleted_blocks": deleted_blocks,
            "deleted_vectors": deleted_vectors,
            "deleted_index": deleted_index
        }
    
    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.disconnect()


def create_storage_backend(
    storage_type: str = "local",
    vector_backend: str = "memory",
    base_path: str = "./storage",
    **kwargs
) -> CompositeStorage:
    """
    创建存储后端
    
    Args:
        storage_type: 存储类型 ("local")
        vector_backend: 向量存储后端 ("memory", "chromadb", "faiss")
        base_path: 存储基础路径
        **kwargs: 其他配置参数
        
    Returns:
        CompositeStorage实例
    """
    config = StorageConfig(
        storage_type=storage_type,
        base_path=base_path,
        **kwargs
    )
    
    # 创建代码块和元数据存储
    if storage_type == "local":
        file_storage = LocalFileStorage(config)
        code_block_storage = file_storage.code_block_storage
        metadata_storage = file_storage.metadata_storage
    else:
        raise ValueError(f"不支持的存储类型: {storage_type}")
    
    # 创建向量存储
    vector_config = StorageConfig(
        storage_type=vector_backend,
        base_path=f"{base_path}/vectors",
        **config.extra_config
    )
    
    if vector_backend == "memory":
        vector_storage = VectorStorage(vector_config)
    elif vector_backend == "chromadb":
        vector_storage = ChromaVectorStorage(vector_config)
    elif vector_backend == "faiss":
        vector_storage = FaissVectorStorage(vector_config)
    else:
        raise ValueError(f"不支持的向量存储后端: {vector_backend}")
    
    return CompositeStorage(
        code_block_storage=code_block_storage,
        vector_storage=vector_storage,
        metadata_storage=metadata_storage
    ) 