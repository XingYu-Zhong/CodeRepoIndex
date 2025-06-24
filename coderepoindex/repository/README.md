# 代码仓库获取模块

## 简介

`coderepoindex.repository` 模块提供了统一的接口来获取不同来源的代码仓库，支持：

- **Git 仓库**: 从远程 Git 仓库克隆代码，支持指定分支、标签、提交等
- **本地路径**: 直接使用本地文件系统中的代码仓库
- **ZIP 文件**: 从 ZIP 压缩包中解压代码仓库

## 快速开始

### 安装依赖

```bash
pip install GitPython==3.1.44
```

### 基本用法

```python
from coderepoindex.repository import (
    RepositoryFetcher,
    create_git_config,
    create_local_config,
    create_zip_config
)

# 使用上下文管理器自动清理临时文件
with RepositoryFetcher() as fetcher:
    # 1. 从 Git 仓库获取代码
    git_config = create_git_config(
        repo_url="https://github.com/octocat/Hello-World.git",
        branch="master"
    )
    git_path = fetcher.fetch(git_config)
    print(f"Git 仓库路径: {git_path}")
    
    # 2. 使用本地路径
    local_config = create_local_config("/path/to/local/repo")
    local_path = fetcher.fetch(local_config)
    print(f"本地仓库路径: {local_path}")
    
    # 3. 从 ZIP 文件解压
    zip_config = create_zip_config("/path/to/repo.zip")
    zip_path = fetcher.fetch(zip_config)
    print(f"ZIP 仓库路径: {zip_path}")
```

## 详细用法

### Git 仓库获取

```python
# 克隆主分支（默认会克隆到当前目录下的 .coderepo/repo 目录）
config = create_git_config("https://github.com/user/repo.git")

# 克隆特定分支
config = create_git_config(
    repo_url="https://github.com/user/repo.git",
    branch="develop"
)

# 克隆特定标签
config = create_git_config(
    repo_url="https://github.com/user/repo.git",
    tag="v1.0.0"
)

# 克隆特定提交
config = create_git_config(
    repo_url="https://github.com/user/repo.git",
    commit="abc123def456"
)

# 使用认证令牌（私有仓库）
config = create_git_config(
    repo_url="https://github.com/user/private-repo.git",
    auth_token="ghp_xxxxxxxxxxxx"
)

# 指定目标目录
config = create_git_config(
    repo_url="https://github.com/user/repo.git",
    target_dir="./my-local-repo"
)
```

### 本地仓库访问

```python
# 使用绝对路径
config = create_local_config("/home/user/projects/my-repo")

# 使用相对路径
config = create_local_config("./local-repo")
```

### ZIP 文件解压

```python
# 解压到临时目录
config = create_zip_config("/path/to/repo.zip")

# 解压到指定目录
config = create_zip_config(
    zip_path="/path/to/repo.zip",
    target_dir="./extracted-repo"
)
```

## 高级功能

### 自定义配置

```python
from coderepoindex.repository import RepoConfig, RepoSource

# 手动创建配置
config = RepoConfig(
    source=RepoSource.GIT,
    path="https://github.com/user/repo.git",
    branch="main",
    target_dir="./custom-dir",
    cleanup_on_error=True
)
```

### 错误处理

```python
try:
    with RepositoryFetcher() as fetcher:
        config = create_git_config("https://github.com/invalid/repo.git")
        repo_path = fetcher.fetch(config)
except RuntimeError as e:
    print(f"获取仓库失败: {e}")
```

### 手动清理

```python
fetcher = RepositoryFetcher()
try:
    config = create_git_config("https://github.com/user/repo.git")
    repo_path = fetcher.fetch(config)
    # 处理仓库...
finally:
    fetcher.cleanup_all()  # 手动清理临时文件
```

## API 参考

### RepositoryFetcher

主要的仓库获取器类。

#### 方法

- `__init__(temp_dir=None)`: 初始化获取器
- `fetch(config)`: 根据配置获取仓库，返回本地路径
- `cleanup_all()`: 清理所有临时仓库

### RepoConfig

仓库配置数据类。

#### 属性

- `source`: 仓库源类型 (RepoSource 枚举)
- `path`: 仓库路径或 URL
- `branch`: Git 分支名（可选）
- `tag`: Git 标签名（可选）
- `commit`: Git 提交哈希（可选）
- `auth_token`: 认证令牌（可选）
- `target_dir`: 目标目录（可选）
- `cleanup_on_error`: 错误时是否清理（默认 True）

### 便捷函数

- `create_git_config()`: 创建 Git 仓库配置
- `create_local_config()`: 创建本地仓库配置
- `create_zip_config()`: 创建 ZIP 仓库配置

## 默认行为

- **Git 仓库**: 如果不指定 `target_dir`，仓库将克隆到当前工作目录下的 `.coderepo` 目录
- **智能目录命名**: 根据仓库 URL 和 commit_id 自动生成目录名
  - 格式: `仓库名_commit前8位` (如 `Hello-World_553c2077`)
  - 如果无法获取commit信息，使用 `仓库名` (如 `Hello-World`)
- **版本管理**: 
  - 不同的 commit 会创建不同的目录，实现版本隔离
  - 相同的 commit 会复用已存在的目录，避免重复下载
  - 支持同时保存同一仓库的多个版本
- **自动创建**: `.coderepo` 目录如果不存在会自动创建

### 目录结构示例

```
.coderepo/
├── Hello-World_553c2077/    # master分支的某个commit
├── Hello-World_7fd1a60b/    # 另一个commit版本
└── my-project_abc12345/     # 其他仓库
```

## 注意事项

1. **GitPython 依赖**: Git 功能需要安装 `GitPython` 包
2. **临时文件清理**: 建议使用上下文管理器自动清理临时文件
3. **网络连接**: Git 仓库获取需要网络连接
4. **权限问题**: 确保有足够的权限访问指定的路径和创建 `.coderepo` 目录
5. **磁盘空间**: 大型仓库可能占用大量磁盘空间

## 示例

查看 `examples/repository_demo.py` 获取更多使用示例。 