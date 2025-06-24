"""
CodeRepoIndex - 通过语义理解提高代码仓库的可发现性和可搜索性

CodeRepoIndex 是一个开源项目，旨在通过语义理解，提高代码仓库的可发现性和可搜索性。
它通过将原始代码转换为可查询的向量化索引，解决了在大型代码库中查找相关代码片段的挑战。
"""

__version__ = "0.1.0"
__author__ = "CodeRepoIndex Team"
__email__ = "contact@coderepoindex.com"

from .core.indexer import CodeIndexer
from .core.searcher import CodeSearcher
from .repository import RepositoryFetcher, RepoSource

__all__ = [
    "CodeIndexer",
    "CodeSearcher",
    "RepositoryFetcher",
    "RepoSource",
] 