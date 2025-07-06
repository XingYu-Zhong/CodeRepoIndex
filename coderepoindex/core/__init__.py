"""
核心功能模块

提供代码索引和搜索的核心功能。
"""

from .indexer import CodeIndexer, IndexingProgress, create_code_indexer
from .searcher import CodeSearcher, create_code_searcher
from .project_manager import ProjectManager, ProjectInfo, create_project_manager
from .models import (
    CodeBlock,
    RepositoryIndex,
    SearchQuery,
    SearchResult,
    BlockType,
    create_repository_index,
    create_search_query
)

__all__ = [
    # 主要类
    "CodeIndexer",
    "CodeSearcher",
    "ProjectManager",
    "IndexingProgress",
    
    # 数据模型
    "CodeBlock",
    "RepositoryIndex", 
    "SearchQuery",
    "SearchResult",
    "BlockType",
    "ProjectInfo",
    
    # 工厂函数
    "create_code_indexer",
    "create_code_searcher",
    "create_project_manager",
    "create_repository_index",
    "create_search_query"
] 