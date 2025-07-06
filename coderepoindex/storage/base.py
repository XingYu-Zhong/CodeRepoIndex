"""
Storage基础接口定义

定义存储模块的抽象基类和异常类。
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Iterator
from dataclasses import dataclass, field
from pathlib import Path

from ..core.models import CodeBlock, RepositoryIndex, SearchQuery, SearchResult


# 异常类定义
class StorageError(Exception):
    """存储基础异常"""
    pass


class StorageNotFoundError(StorageError):
    """存储项未找到异常"""
    pass


class StorageConnectionError(StorageError):
    """存储连接异常"""
    pass


class StorageConfigError(StorageError):
    """存储配置异常"""
    pass


# 配置类
@dataclass
class StorageConfig:
    """存储配置"""
    
    # 基础配置
    storage_type: str = "local"
    base_path: str = "./storage"
    
    # 性能配置
    enable_cache: bool = True
    cache_size: int = 1000
    batch_size: int = 100
    
    # 备份配置
    enable_backup: bool = True
    backup_interval: int = 3600  # 秒
    max_backups: int = 10
    
    # 压缩配置
    enable_compression: bool = True
    compression_level: int = 6
    
    # 安全配置
    enable_encryption: bool = False
    encryption_key: Optional[str] = None
    
    # 其他配置
    extra_config: Dict[str, Any] = field(default_factory=dict)
    
    def validate(self) -> None:
        """验证配置"""
        if not self.base_path:
            raise StorageConfigError("base_path不能为空")
        
        if self.cache_size < 0:
            raise StorageConfigError("cache_size必须为非负数")
        
        if self.batch_size < 1:
            raise StorageConfigError("batch_size必须为正数")


# 抽象基类定义
class BaseStorage(ABC):
    """存储基础接口"""
    
    def __init__(self, config: StorageConfig):
        self.config = config
        self.config.validate()
    
    @abstractmethod
    def connect(self) -> None:
        """连接存储后端"""
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """断开存储连接"""
        pass
    
    @abstractmethod
    def health_check(self) -> bool:
        """健康检查"""
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """获取存储统计信息"""
        pass
    
    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.disconnect()


class BaseCodeBlockStorage(BaseStorage):
    """代码块存储基础接口"""
    
    @abstractmethod
    def save_code_block(self, code_block: CodeBlock) -> None:
        """保存代码块"""
        pass
    
    @abstractmethod
    def save_code_blocks(self, code_blocks: List[CodeBlock]) -> None:
        """批量保存代码块"""
        pass
    
    @abstractmethod
    def get_code_block(self, block_id: str) -> Optional[CodeBlock]:
        """获取代码块"""
        pass
    
    @abstractmethod
    def get_code_blocks(self, block_ids: List[str]) -> List[CodeBlock]:
        """批量获取代码块"""
        pass
    
    @abstractmethod
    def query_code_blocks(
        self,
        repository_id: Optional[str] = None,
        language: Optional[str] = None,
        block_type: Optional[str] = None,
        file_path: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[CodeBlock]:
        """查询代码块"""
        pass
    
    @abstractmethod
    def delete_code_block(self, block_id: str) -> bool:
        """删除代码块"""
        pass
    
    @abstractmethod
    def delete_code_blocks(self, repository_id: str) -> int:
        """删除仓库的所有代码块"""
        pass
    
    @abstractmethod
    def update_code_block(self, code_block: CodeBlock) -> bool:
        """更新代码块"""
        pass
    
    @abstractmethod
    def count_code_blocks(
        self,
        repository_id: Optional[str] = None,
        language: Optional[str] = None,
        block_type: Optional[str] = None
    ) -> int:
        """统计代码块数量"""
        pass
    
    @abstractmethod
    def iter_code_blocks(
        self,
        repository_id: Optional[str] = None,
        batch_size: int = 100
    ) -> Iterator[CodeBlock]:
        """迭代代码块"""
        pass


class BaseVectorStorage(BaseStorage):
    """向量存储基础接口"""
    
    @abstractmethod
    def add_vector(
        self,
        vector_id: str,
        vector: List[float],
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """添加向量"""
        pass
    
    @abstractmethod
    def add_vectors(
        self,
        vector_ids: List[str],
        vectors: List[List[float]],
        metadata: Optional[List[Dict[str, Any]]] = None
    ) -> None:
        """批量添加向量"""
        pass
    
    @abstractmethod
    def search_vectors(
        self,
        query_vector: List[float],
        top_k: int = 10,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """搜索相似向量"""
        pass
    
    @abstractmethod
    def get_vector(self, vector_id: str) -> Optional[Dict[str, Any]]:
        """获取向量"""
        pass
    
    @abstractmethod
    def delete_vector(self, vector_id: str) -> bool:
        """删除向量"""
        pass
    
    @abstractmethod
    def delete_vectors(self, vector_ids: List[str]) -> int:
        """批量删除向量"""
        pass
    
    @abstractmethod
    def update_vector(
        self,
        vector_id: str,
        vector: Optional[List[float]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """更新向量"""
        pass
    
    @abstractmethod
    def count_vectors(
        self,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> int:
        """统计向量数量"""
        pass


class BaseMetadataStorage(BaseStorage):
    """元数据存储基础接口"""
    
    @abstractmethod
    def save_repository_index(self, repository_index: RepositoryIndex) -> None:
        """保存仓库索引"""
        pass
    
    @abstractmethod
    def get_repository_index(self, repository_id: str) -> Optional[RepositoryIndex]:
        """获取仓库索引"""
        pass
    
    @abstractmethod
    def list_repository_indexes(self) -> List[RepositoryIndex]:
        """列出所有仓库索引"""
        pass
    
    @abstractmethod
    def delete_repository_index(self, repository_id: str) -> bool:
        """删除仓库索引"""
        pass
    
    @abstractmethod
    def update_repository_index(self, repository_index: RepositoryIndex) -> bool:
        """更新仓库索引"""
        pass
    
    @abstractmethod
    def save_search_query(self, query: SearchQuery) -> None:
        """保存搜索查询（用于日志和分析）"""
        pass
    
    @abstractmethod
    def get_search_history(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[SearchQuery]:
        """获取搜索历史"""
        pass
    
    @abstractmethod
    def get_metadata(self, key: str) -> Optional[Any]:
        """获取元数据"""
        pass
    
    @abstractmethod
    def set_metadata(self, key: str, value: Any) -> None:
        """设置元数据"""
        pass
    
    @abstractmethod
    def delete_metadata(self, key: str) -> bool:
        """删除元数据"""
        pass
    
    @abstractmethod
    def list_metadata_keys(self) -> List[str]:
        """列出所有元数据键"""
        pass 