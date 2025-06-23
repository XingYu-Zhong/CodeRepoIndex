# CodeRepoIndex

## 项目简介

CodeRepoIndex 是一个开源项目，旨在通过语义理解，提高代码仓库的可发现性和可搜索性。它通过将原始代码转换为可查询的向量化索引，解决了在大型代码库中查找相关代码片段的挑战。

## 核心功能

### 🔧 代码块切分
自动将代码文件分解为有意义、易于管理的代码块，保持代码的逻辑完整性。

### 🧠 向量嵌入
使用先进的嵌入技术将这些代码块转换为高维数值向量，捕获其语义信息。

### 💾 向量存储
有效地存储这些嵌入向量，支持快速检索和持久化。

### 🔍 向量相似度查询
支持快速准确的相似度查询，允许用户根据自然语言描述或示例代码查找语义相似的代码块。

## 特性

- 🌐 **多语言支持**: 支持多种编程语言的代码索引
- ⚡ **高性能**: 优化的向量存储和检索算法
- 🔍 **智能搜索**: 基于语义理解的代码搜索
- 📊 **可扩展**: 支持大型代码库的索引和查询
- 🛠️ **易于集成**: 提供简洁的API接口

## 快速开始

### 安装

```bash
# 克隆项目
git clone https://github.com/XingYu-Zhong/CodeRepoIndex.git
cd CodeRepoIndex

# 安装依赖
pip install -r requirements.txt
```

### 基本使用

```python
from coderepoindex import CodeIndexer, CodeSearcher

# 创建索引器
indexer = CodeIndexer()

# 为代码仓库创建索引
indexer.index_repository("/path/to/your/repository")

# 创建搜索器
searcher = CodeSearcher()

# 搜索相似代码
results = searcher.search("calculate fibonacci sequence")
for result in results:
    print(f"File: {result.file_path}")
    print(f"Code: {result.code_snippet}")
    print(f"Similarity: {result.similarity_score}")
```

## 架构设计

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   代码解析器     │──→ │   向量嵌入器     │──→ │   向量存储器     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                        │                        │
         ▼                        ▼                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   代码块切分     │    │   语义编码       │    │   索引存储       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                                                       ▼
                                              ┌─────────────────┐
                                              │   相似度查询     │
                                              └─────────────────┘
```

## API 文档

### CodeIndexer

#### `index_repository(repo_path: str, language: str = None)`
为指定的代码仓库创建索引。

**参数:**
- `repo_path`: 代码仓库路径
- `language`: 指定编程语言（可选）

#### `index_file(file_path: str)`
为单个代码文件创建索引。

### CodeSearcher

#### `search(query: str, top_k: int = 10)`
根据查询内容搜索相似代码块。

**参数:**
- `query`: 搜索查询（自然语言或代码片段）
- `top_k`: 返回结果数量

## 支持的编程语言

- Python
- JavaScript/TypeScript
- Java
- C/C++
- Go
- Rust
- 更多语言持续支持中...

## 贡献指南

我们欢迎所有形式的贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详细信息。

### 开发环境设置

```bash
# 克隆项目
git clone https://github.com/XingYu-Zhong/CodeRepoIndex.git
cd CodeRepoIndex

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装开发依赖
pip install -r requirements-dev.txt

# 运行测试
pytest tests/
```

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 联系我们

- 项目主页: https://github.com/XingYu-Zhong/CodeRepoIndex
- 问题反馈: https://github.com/XingYu-Zhong/CodeRepoIndex/issues
- 邮箱: your-email@example.com

## 致谢

感谢所有为这个项目做出贡献的开发者们！

---

⭐ 如果这个项目对您有帮助，请给我们一个 Star！ 