# Repository 模块 (`coderepoindex.repository`)

## 1. 概述

`repository` 模块是 `CodeRepoIndex` 项目的数据源获取层。它的核心职责是提供一个统一、可靠的接口，用于从各种不同的来源获取代码仓库，并将其准备为本地文件系统上的一个目录，以供后续的 `parsers` 模块进行处理。

该模块将复杂的获取逻辑（如Git克隆、分支处理、ZIP解压等）封装起来，为上层模块提供了一个简单的、配置驱动的调用方式。

## 2. 核心组件

### 2.1. `RepoSource` (Enum)

这是一个枚举类，定义了支持的代码仓库来源类型：
- `GIT`: 表示代码仓库来源于一个 Git URL。
- `LOCAL`: 表示代码仓库是一个本地文件系统上的目录。
- `ZIP`: 表示代码仓库是一个 `.zip` 压缩文件。

### 2.2. `RepoConfig` (Dataclass)

这是一个数据类，用于封装获取一个代码仓库所需的所有配置信息。它是与 `RepositoryFetcher` 交互的主要数据结构。

**核心属性**:
- `source`: `RepoSource` 枚举成员，指定仓库来源。
- `path`: 仓库的路径。根据 `source` 的不同，它可以是一个 Git URL、一个本地文件夹路径或一个 ZIP 文件路径。
- `branch`, `tag`, `commit`: 当 `source` 为 `GIT` 时，可以指定要检出的分支、标签或特定的提交哈希。
- `target_dir`: (可选) 指定一个目录用于存放获取的代码。如果不指定，模块会自动在当前工作目录下的 `.coderepo/` 文件夹中创建一个以仓库名和版本信息命名的缓存目录。
- `auth_token`: (可选) 用于访问私有 Git 仓库的认证令牌。

### 2.3. `RepositoryFetcher` (Class)

这是本模块的核心实现类，负责执行实际的代码获取操作。

- **职责**:
    - **统一接口**: 提供一个 `fetch(config: RepoConfig)` 方法，根据传入的配置自动选择并执行相应的获取逻辑。
    - **Git 操作**: 如果来源是 `GIT`，它会使用 `GitPython` 库来执行 `git clone` 操作。它还能够智能地处理分支、标签和提交，并自动创建缓存目录，避免对同一版本的仓库进行重复克隆。
    - **本地路径处理**: 如果来源是 `LOCAL`，它会验证路径是否存在并直接返回该路径。
    - **ZIP 文件处理**: 如果来源是 `ZIP`，它会自动将 ZIP 文件解压到一个临时目录中。
    - **上下文管理与清理**: `RepositoryFetcher` 实现了上下文管理器协议 (`__enter__`, `__exit__`)，可以在使用完毕后自动清理所有下载的临时文件和目录，确保不留垃圾文件。

### 2.4. 便捷函数

为了简化 `RepoConfig` 对象的创建，模块提供了一系列工厂函数：
- `create_git_config(...)`
- `create_local_config(...)`
- `create_zip_config(...)`

## 3. 工作流程

```mermaid
graph TD
    A[Upstream Module, e.g., CodeIndexer] --> B{Creates RepoConfig};
    B --> C[RepositoryFetcher];
    C -- Calls --> D{fetch(config)};
    
    subgraph "RepositoryFetcher Logic"
        D -- Reads config.source --> E{Switch};
        E -- GIT --> F[Fetch from Git];
        E -- LOCAL --> G[Use Local Path];
        E -- ZIP --> H[Extract from ZIP];
    end

    F --> I[Returns Local Path to Cloned Repo];
    G --> I;
    H --> I;

    I --> A;

    style C fill:#f9f,stroke:#333,stroke-width:2px
```

**典型使用**:
```python
from coderepoindex.repository import RepositoryFetcher, create_git_config

# 1. 创建一个 Git 仓库的配置，指定克隆 master 分支
git_config = create_git_config(
    repo_url="https://github.com/user/repo.git",
    branch="master"
)

# 2. 使用上下文管理器来获取仓库并自动清理
with RepositoryFetcher() as fetcher:
    # fetcher 会克隆仓库并返回其在本地的存储路径
    local_repo_path = fetcher.fetch(git_config)
    
    print(f"仓库已获取到: {local_repo_path}")
    
    # 在这里可以对 local_repo_path 进行解析、索引等操作
    # ...

# 退出 with 代码块后，所有临时下载的文件都会被自动删除
print("Fetcher 已清理临时文件。")
```
