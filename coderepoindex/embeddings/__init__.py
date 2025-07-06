"""
Embedding模块

类似LlamaIndex的本地嵌入存储模块，提供文档索引和语义搜索功能。

核心组件：
- Node: 文本节点，表示文档片段
- Document: 文档类，继承自Node
- BaseDocumentStore, SimpleDocumentStore: 文档存储
- BaseVectorStore, SimpleVectorStore: 向量存储
- EmbeddingIndexer: 索引构建器
- EmbeddingRetriever: 检索器
- 文本分块器: SimpleTextSplitter, SentenceSplitter
- 工具函数: 相似度计算、向量操作等

使用示例：
```python
from coderepoindex.embeddings import (
    create_indexer, 
    create_retriever, 
    SimpleTextSplitter
)
from coderepoindex.models import create_embedding_provider

# 创建嵌入提供商
embedding_provider = create_embedding_provider(
    provider_type="api",
    model_name="text-embedding-v3",
    api_key="your-api-key"
)

# 创建索引构建器
indexer = create_indexer(
    embedding_provider=embedding_provider,
    persist_dir="./my_index"
)

# 构建索引
documents = [
    {"text": "这是第一个文档", "metadata": {"source": "doc1"}},
    {"text": "这是第二个文档", "metadata": {"source": "doc2"}}
]
indexer.build_index(documents)

# 创建检索器
retriever = create_retriever(
    embedding_provider=embedding_provider,
    persist_dir="./my_index"
)

# 检索相关文档
results = retriever.retrieve("搜索查询", top_k=5)
for result in results:
    print(f"Score: {result['score']:.4f}")
    print(f"Text: {result['text'][:100]}...")
```
"""

# 基础类和接口
from .base import (
    BaseDocumentStore,
    BaseVectorStore,
    BaseIndexer,
    BaseRetriever,
    BaseSplitter
)

# 节点和文档类
from .node import (
    Node,
    Document
)

# 存储组件
from .document_store import (
    SimpleDocumentStore,
    create_document_store
)

from .vector_store import (
    SimpleVectorStore,
    create_vector_store
)

# 核心功能组件
from .indexer import (
    EmbeddingIndexer,
    create_indexer
)

from .retriever import (
    EmbeddingRetriever,
    create_retriever
)

# 工具函数和分块器
from .utils import (
    SimpleTextSplitter,
    SentenceSplitter,
    cosine_similarity,
    euclidean_distance,
    batch_cosine_similarity,
    normalize_vector,
    filter_metadata,
    create_default_splitter,
    get_vector_dimension,
    validate_vector_dimensions
)

__all__ = [
    # 基础接口
    'BaseDocumentStore',
    'BaseVectorStore', 
    'BaseIndexer',
    'BaseRetriever',
    'BaseSplitter',
    
    # 节点和文档
    'Node',
    'Document',
    
    # 存储组件
    'SimpleDocumentStore',
    'SimpleVectorStore',
    'create_document_store',
    'create_vector_store',
    
    # 核心功能
    'EmbeddingIndexer',
    'EmbeddingRetriever',
    'create_indexer',
    'create_retriever',
    
    # 文本分块器
    'SimpleTextSplitter',
    'SentenceSplitter',
    'create_default_splitter',
    
    # 工具函数
    'cosine_similarity',
    'euclidean_distance',
    'batch_cosine_similarity',
    'normalize_vector',
    'filter_metadata',
    'get_vector_dimension',
    'validate_vector_dimensions',
]


def setup_logging(level="INFO"):
    """
    设置embedding模块的日志级别
    
    Args:
        level: 日志级别 ("DEBUG", "INFO", "WARNING", "ERROR")
    """
    import logging
    
    # 设置embedding模块的日志级别
    logger = logging.getLogger('coderepoindex.embeddings')
    logger.setLevel(getattr(logging, level.upper()))
    
    # 如果没有handler，添加一个console handler
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)


# 便利函数
def create_simple_rag_system(
    embedding_provider=None,
    persist_dir: str = "./rag_index",
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    **kwargs
):
    """
    创建简单的RAG系统
    
    Args:
        embedding_provider: 嵌入提供商，如果不提供则使用默认配置
        persist_dir: 持久化目录
        chunk_size: 文本块大小
        chunk_overlap: 文本块重叠
        **kwargs: 其他参数
        
    Returns:
        (indexer, retriever) 元组
    """
    from ..models import create_embedding_provider
    
    # 创建嵌入提供商
    if embedding_provider is None:
        embedding_provider = create_embedding_provider()
    
    # 创建文本分块器
    text_splitter = SimpleTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    
    # 创建索引构建器
    indexer = create_indexer(
        embedding_provider=embedding_provider,
        persist_dir=persist_dir,
        text_splitter=text_splitter,
        **kwargs
    )
    
    # 创建检索器，共享indexer的存储实例
    retriever = create_retriever(
        embedding_provider=embedding_provider,
        persist_dir=persist_dir,
        document_store=indexer.document_store,  # 共享文档存储
        vector_store=indexer.vector_store,      # 共享向量存储
        **kwargs
    )
    
    return indexer, retriever


def quick_index_and_search(
    documents,
    query: str,
    embedding_provider=None,
    top_k: int = 5,
    **kwargs
):
    """
    快速索引和搜索
    适用于小规模的临时索引和搜索
    
    Args:
        documents: 文档列表
        query: 查询文本
        embedding_provider: 嵌入提供商
        top_k: 返回结果数量
        **kwargs: 其他参数
        
    Returns:
        检索结果列表
    """
    from ..models import create_embedding_provider
    
    # 创建嵌入提供商
    if embedding_provider is None:
        embedding_provider = create_embedding_provider()
    
    # 创建临时的索引构建器和检索器（不持久化）
    indexer = create_indexer(
        embedding_provider=embedding_provider,
        persist_dir=None,  # 不持久化
        **kwargs
    )
    
    retriever = create_retriever(
        embedding_provider=embedding_provider,
        persist_dir=None,  # 不持久化
        document_store=indexer.document_store,
        vector_store=indexer.vector_store
    )
    
    # 构建索引
    indexer.build_index(documents)
    
    # 检索
    return retriever.retrieve(query, top_k=top_k)


# 元数据检索工具函数
def search_by_metadata(
    retriever: EmbeddingRetriever, 
    metadata_filter: dict, 
    top_k: int = 10
):
    """
    基于元数据的检索
    
    Args:
        retriever: 检索器实例
        metadata_filter: 元数据过滤条件
        top_k: 返回的节点数量
        
    Returns:
        匹配的节点列表
    """
    return retriever.retrieve_by_metadata(metadata_filter, top_k)


def search_by_id(retriever: EmbeddingRetriever, node_id: str):
    """
    根据ID检索节点
    
    Args:
        retriever: 检索器实例
        node_id: 节点ID
        
    Returns:
        检索到的节点或None
    """
    return retriever.retrieve_by_node_id(node_id)


def search_by_ids(retriever: EmbeddingRetriever, node_ids: list):
    """
    根据ID列表批量检索节点
    
    Args:
        retriever: 检索器实例
        node_ids: 节点ID列表
        
    Returns:
        检索到的节点列表
    """
    return retriever.retrieve_by_node_ids(node_ids)


def search_metadata_contains(retriever: EmbeddingRetriever, metadata_key: str, search_value, top_k: int = 10):
    """
    搜索元数据包含指定值的节点
    
    Args:
        retriever: 检索器实例
        metadata_key: 元数据键
        search_value: 搜索值
        top_k: 返回的节点数量
        
    Returns:
        匹配的节点列表
    """
    return retriever.retrieve_metadata_contains(metadata_key, search_value, top_k)


def search_metadata_range(
    retriever: EmbeddingRetriever, 
    metadata_key: str, 
    min_value=None, 
    max_value=None, 
    top_k: int = 10
):
    """
    搜索元数据在指定范围内的节点
    
    Args:
        retriever: 检索器实例
        metadata_key: 元数据键
        min_value: 最小值（可选）
        max_value: 最大值（可选）
        top_k: 返回的节点数量
        
    Returns:
        匹配的节点列表
    """
    return retriever.retrieve_metadata_range(metadata_key, min_value, max_value, top_k)


def hybrid_search(
    retriever: EmbeddingRetriever,
    query: str,
    metadata_filter: dict = None,
    top_k: int = 10,
    metadata_weight: float = 0.3,
    vector_weight: float = 0.7
):
    """
    混合搜索：结合向量搜索和元数据过滤
    
    Args:
        retriever: 检索器实例
        query: 查询文本
        metadata_filter: 元数据过滤条件
        top_k: 返回的节点数量
        metadata_weight: 元数据权重
        vector_weight: 向量权重
        
    Returns:
        检索结果列表
    """
    return retriever.retrieve_hybrid(
        query=query,
        metadata_filter=metadata_filter,
        top_k=top_k,
        metadata_weight=metadata_weight,
        vector_weight=vector_weight
    )


def get_metadata_info(retriever: EmbeddingRetriever, metadata_key: str = None):
    """
    获取元数据信息
    
    Args:
        retriever: 检索器实例
        metadata_key: 指定的元数据键，如果不提供则返回所有统计信息
        
    Returns:
        元数据值列表或统计信息字典
    """
    if metadata_key:
        return retriever.get_metadata_values(metadata_key)
    else:
        return retriever.get_metadata_statistics()


def sync_indexer_retriever(indexer: EmbeddingIndexer, retriever: EmbeddingRetriever):
    """
    同步indexer和retriever的存储实例
    
    Args:
        indexer: 索引构建器
        retriever: 检索器
    """
    retriever.sync_with_indexer(indexer)


def check_sync_status(indexer: EmbeddingIndexer, retriever: EmbeddingRetriever) -> dict:
    """
    检查indexer和retriever的同步状态
    
    Args:
        indexer: 索引构建器
        retriever: 检索器
        
    Returns:
        同步状态信息
    """
    return {
        'shared_document_store': indexer.document_store is retriever.document_store,
        'shared_vector_store': indexer.vector_store is retriever.vector_store,
        'indexer_docs': len(indexer.document_store),
        'retriever_docs': len(retriever.document_store),
        'indexer_vectors': len(indexer.vector_store),
        'retriever_vectors': len(retriever.vector_store),
        'data_consistent': (len(indexer.document_store) == len(retriever.document_store) and
                           len(indexer.vector_store) == len(retriever.vector_store))
    }


# 添加便利函数到导出列表
__all__.extend([
    'setup_logging',
    'create_simple_rag_system',
    'quick_index_and_search',
    # 元数据检索函数
    'search_by_metadata',
    'search_by_id',
    'search_by_ids',
    'search_metadata_contains',
    'search_metadata_range',
    'hybrid_search',
    'get_metadata_info',
    # 同步管理函数
    'sync_indexer_retriever',
    'check_sync_status'
])
