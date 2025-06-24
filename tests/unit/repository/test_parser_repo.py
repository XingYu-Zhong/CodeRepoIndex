"""
代码仓库获取器单元测试
"""

import sys

from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from coderepoindex.repository import (
    RepositoryFetcher,
    RepoSource,
    RepoConfig,
    create_git_config,
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


from coderepoindex.parsers import parse_directory, create_directory_config

# 基础用法
result = parse_directory(path)

# 查看结果
print(f"处理了 {result.processed_files} 个文件")
print(f"生成了 {len(result.snippets)} 个代码片段")

# 检查不同类型的片段
for snippet in result.snippets:
    print(f"{snippet.type}: {snippet.path} ({snippet.filename})")
    print(snippet)