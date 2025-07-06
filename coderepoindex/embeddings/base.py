"""
Embedding模块的基础抽象类和接口定义
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class BaseDocumentStore(ABC):
    """文档存储的抽象基类"""
    
    @abstractmethod
    def add_nodes(self, nodes: List['Node']) -> None:
        """添加节点到存储中"""
        pass
    
    @abstractmethod
    def get_node(self, node_id: str) -> Optional['Node']:
        """根据ID获取单个节点"""
        pass
    
    @abstractmethod
    def get_nodes(self, node_ids: List[str]) -> List['Node']:
        """根据ID列表获取多个节点"""
        pass
    
    @abstractmethod
    def delete_node(self, node_id: str) -> bool:
        """删除指定节点"""
        pass
    
    @abstractmethod
    def persist(self, filepath: str) -> None:
        """持久化到磁盘"""
        pass
    
    @abstractmethod
    def load_from_path(self, filepath: str) -> None:
        """从磁盘加载"""
        pass
    
    @abstractmethod
    def get_all_node_ids(self) -> List[str]:
        """获取所有节点ID"""
        pass


class BaseVectorStore(ABC):
    """向量存储的抽象基类"""
    
    @abstractmethod
    def add(self, node_id: str, embedding: List[float], metadata: Optional[Dict[str, Any]] = None) -> None:
        """添加向量到存储中"""
        pass
    
    @abstractmethod
    def add_batch(self, data: List[Tuple[str, List[float], Optional[Dict[str, Any]]]]) -> None:
        """批量添加向量"""
        pass
    
    @abstractmethod
    def query(self, query_embedding: List[float], top_k: int = 10, 
             metadata_filter: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """查询最相似的向量"""
        pass
    
    @abstractmethod
    def delete(self, node_id: str) -> bool:
        """删除指定向量"""
        pass
    
    @abstractmethod
    def persist(self, filepath: str) -> None:
        """持久化到磁盘"""
        pass
    
    @abstractmethod
    def load_from_path(self, filepath: str) -> None:
        """从磁盘加载"""
        pass
    
    @abstractmethod
    def get_all_node_ids(self) -> List[str]:
        """获取所有节点ID"""
        pass


class BaseIndexer(ABC):
    """索引构建器的抽象基类"""
    
    @abstractmethod
    def build_index(self, documents: List[Dict[str, Any]], **kwargs) -> None:
        """构建索引"""
        pass
    
    @abstractmethod
    def add_document(self, document: Dict[str, Any], **kwargs) -> None:
        """添加单个文档"""
        pass


class BaseRetriever(ABC):
    """检索器的抽象基类"""
    
    @abstractmethod
    def retrieve(self, query: str, top_k: int = 10, **kwargs) -> List[Dict[str, Any]]:
        """检索相关文档"""
        pass
    
    @abstractmethod
    def retrieve_with_scores(self, query: str, top_k: int = 10, **kwargs) -> List[Tuple[Dict[str, Any], float]]:
        """检索相关文档并返回相似度分数"""
        pass


class BaseSplitter(ABC):
    """文本分块器的抽象基类"""
    
    @abstractmethod
    def split_text(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List['Node']:
        """将文本分割成节点"""
        pass
    
    @abstractmethod
    def split_documents(self, documents: List[Dict[str, Any]]) -> List['Node']:
        """批量分割文档"""
        pass 