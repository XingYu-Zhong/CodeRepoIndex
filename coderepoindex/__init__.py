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
from .config import (
    ConfigManager,
    CodeRepoConfig,
    load_config,
    save_config,
    get_current_config,
    update_config,
    get_config_template
)

__all__ = [
    # 核心功能
    "CodeIndexer",
    "CodeSearcher",
    "RepositoryFetcher",
    "RepoSource",
    
    # 配置管理
    "ConfigManager",
    "CodeRepoConfig",
    "load_config",
    "save_config",
    "get_current_config",
    "update_config",
    "get_config_template",
] 