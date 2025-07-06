"""
Storage模块

提供统一的存储接口，支持代码块、向量嵌入、元数据的持久化存储。

主要功能：
- 代码块存储：支持文件系统、数据库等后端
- 向量存储：支持向量数据库和内存存储
- 元数据管理：支持索引信息、统计数据的存储
- 缓存机制：提供多级缓存以提高性能

使用示例：
```python
from coderepoindex.storage import (
    create_storage_backend,
    LocalFileStorage,
    VectorStorage
)

# 创建存储后端
storage = create_storage_backend("local", base_path="./storage")

# 存储代码块
storage.save_code_block(code_block)

# 查询代码块
blocks = storage.query_code_blocks(repository_id="repo123")
```
"""

from .base import (
    BaseStorage,
    BaseCodeBlockStorage,
    BaseVectorStorage,
    BaseMetadataStorage,
    StorageConfig,
    StorageError,
    StorageNotFoundError,
    StorageConnectionError
)

from .local_storage import (
    LocalFileStorage,
    LocalCodeBlockStorage,
    LocalMetadataStorage
)

from .vector_storage import (
    VectorStorage,
    ChromaVectorStorage,
    FaissVectorStorage
)

from .composite_storage import (
    CompositeStorage,
    create_storage_backend
)

from .cache import (
    CacheStorage,
    MemoryCache,
    FileCache
)

from .utils import (
    storage_path_utils,
    backup_utils,
    cleanup_utils
)

__all__ = [
    # 基础接口
    'BaseStorage',
    'BaseCodeBlockStorage', 
    'BaseVectorStorage',
    'BaseMetadataStorage',
    'StorageConfig',
    'StorageError',
    'StorageNotFoundError',
    'StorageConnectionError',
    
    # 本地存储
    'LocalFileStorage',
    'LocalCodeBlockStorage',
    'LocalMetadataStorage',
    
    # 向量存储
    'VectorStorage',
    'ChromaVectorStorage',
    'FaissVectorStorage',
    
    # 复合存储
    'CompositeStorage',
    'create_storage_backend',
    
    # 缓存存储
    'CacheStorage',
    'MemoryCache',
    'FileCache',
    
    # 工具函数
    'storage_path_utils',
    'backup_utils',
    'cleanup_utils',
]


# 版本信息
__version__ = "0.1.0"
