"""
代码仓库获取器单元测试
"""

import sys
import os
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import Mock, patch
# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from coderepoindex.repository import (
    RepositoryFetcher,
    RepoSource,
    RepoConfig,
    create_git_config,
    create_local_config,
    create_zip_config
)



config = RepoConfig(
    source=RepoSource.GIT,
    path="https://github.com/XingYu-Zhong/testpythonproject",
    branch="master",
    cleanup_on_error=True
)

git_config = create_git_config(
    repo_url="https://github.com/XingYu-Zhong/testpythonproject",
    branch="master"
)

fetcher = RepositoryFetcher()
path = fetcher.fetch(config)
print(path)