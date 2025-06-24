"""
代码仓库获取模块

提供多种方式获取代码仓库的功能：
- Git 仓库克隆和检出
- 本地路径访问
- ZIP 文件解压
"""

from .repo_fetcher import (
    RepositoryFetcher, 
    RepoSource, 
    RepoConfig,
    create_git_config,
    create_local_config,
    create_zip_config
)

__all__ = [
    "RepositoryFetcher", 
    "RepoSource",
    "RepoConfig",
    "create_git_config",
    "create_local_config", 
    "create_zip_config"
] 