# CLI 模块 (`coderepoindex.cli`)

## 1. 概述

`cli` 模块为 `CodeRepoIndex` 项目提供了一个功能强大且易于使用的命令行接口（Command-Line Interface）。它基于优秀的 `click` 库构建，允许用户直接在终端中执行核心的索引和搜索操作，而无需编写Python脚本。

这使得 `CodeRepoIndex` 不仅可以作为一个库被集成到其他应用中，还可以作为一个独立的工具直接使用。

## 2. 核心功能

通过命令行，用户可以执行以下操作：

- **`index`**: 为一个本地的代码仓库创建或更新索引。
- **`search`**: 在已创建的索引中执行语义搜索。
- **`stats`**: 查看当前索引的统计信息。

## 3. 命令详解

### 3.1. `index`

此命令用于将一个代码仓库转换为可搜索的索引。

**用法**:
```bash
coderepoindex index [OPTIONS] REPO_PATH
```

**参数**:
- `REPO_PATH`: (必需) 要索引的本地代码仓库的路径。

**选项**:
- `-l, --language TEXT`: (可选) 只索引特定语言的文件。
- `-e, --exclude TEXT`: (可选) 排除匹配指定模式的文件或目录（可多次使用）。
- `-s, --storage-backend TEXT`: (可选) 指定存储后端，默认为 `chroma`。
- `-m, --embedding-model TEXT`: (可选) 指定要使用的嵌入模型名称。

**示例**:
```bash
# 索引当前目录下的 my-project 文件夹
coderepoindex index ./my-project

# 索引一个项目，但排除所有的测试文件
coderepoindex index /path/to/project -e "*.test.js" -e "tests/"
```

### 3.2. `search`

此命令用于在索引中搜索代码。

**用法**:
```bash
coderepoindex search [OPTIONS] QUERY
```

**参数**:
- `QUERY`: (必需) 你的搜索查询，可以是自然语言描述或一段代码。

**选项**:
- `-k, --top-k INTEGER`: (可选) 返回最相关的结果数量，默认为 10。
- `-l, --language TEXT`: (可选) 将搜索范围限制在特定编程语言内。
- `-t, --threshold FLOAT`: (可选) 设置一个相似度分数阈值（0.0到1.0），只返回高于该分数的结果。

**示例**:
```bash
# 使用自然语言进行搜索
coderepoindex search "a function to calculate fibonacci sequence"

# 搜索与一段代码相似的代码，并只返回前3个Python结果
coderepoindex search "def fib(n): ..." -k 3 -l python
```

### 3.3. `stats`

此命令用于快速查看当前索引的总体情况。

**用法**:
```bash
coderepoindex stats [OPTIONS]
```

**示例输出**:
```
📊 索引统计信息:
  - 总向量数: 12345
  - 支持语言: python, javascript, go
  - 索引大小: 123.4 MB
  - 最后更新: 2023-10-27T10:30:00
```

## 4. 入口点

当通过 `pip` 安装 `CodeRepoIndex` 后，`pyproject.toml` 文件中定义的 `[project.scripts]` 会自动创建一个名为 `coderepoindex` 的可执行脚本在你的环境中，使其可以直接在命令行中调用。

```toml
# pyproject.toml
[project.scripts]
coderepoindex = "coderepoindex.cli:main"
```
