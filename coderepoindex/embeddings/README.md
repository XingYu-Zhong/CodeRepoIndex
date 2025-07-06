# Embedding模块

类似LlamaIndex的本地嵌入存储模块，提供文档索引和语义搜索功能。

## 功能特性

### 🎯 核心功能
- **文档索引**：将文档转换为可搜索的嵌入向量索引
- **语义搜索**：基于向量相似度的语义检索
- **元数据检索**：支持多种元数据查询方式（精确匹配、模糊搜索、范围查询等）
- **混合检索**：结合向量相似度和元数据过滤的智能检索
- **持久化存储**：支持将索引保存到磁盘并加载
- **文本分块**：智能的文本分割，支持重叠分块
- **元数据管理**：丰富的元数据支持和统计分析

### 🏗️ 架构设计
基于"关注点分离"原则，将文档存储与向量存储解耦：

- **文档存储（Document Store）**：管理文本内容和元数据
- **向量存储（Vector Store）**：管理嵌入向量和相似性搜索
- **索引构建器（Indexer）**：负责构建和管理索引
- **检索器（Retriever）**：负责查询和检索

## 快速开始

### 安装依赖

```bash
pip install numpy  # 向量计算
```

### 基本使用

```python
from coderepoindex.embeddings import create_simple_rag_system
from coderepoindex.models import create_embedding_provider

# 1. 创建嵌入提供商
embedding_provider = create_embedding_provider(
    provider_type="api",
    model_name="text-embedding-v3", 
    api_key="your-api-key",
    base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
)

# 2. 创建RAG系统
indexer, retriever = create_simple_rag_system(
    embedding_provider=embedding_provider,
    persist_dir="./my_index"
)

# 3. 构建索引
documents = [
    {"text": "人工智能是计算机科学的分支", "metadata": {"topic": "AI"}},
    {"text": "机器学习是AI的子领域", "metadata": {"topic": "ML"}}
]
indexer.build_index(documents)

# 4. 检索相关文档
results = retriever.retrieve("什么是人工智能？", top_k=5)
for result in results:
    print(f"相似度: {result['score']:.4f}")
    print(f"内容: {result['text']}")

# 5. 元数据检索示例
from coderepoindex.embeddings import search_by_metadata, search_metadata_contains

# 根据元数据精确查找
ai_docs = search_by_metadata(retriever, {"topic": "AI"})

# 模糊匹配查找
ml_docs = search_metadata_contains(retriever, "topic", "ML")
```

### 快速搜索

```python
from coderepoindex.embeddings import quick_index_and_search

documents = [
    {"text": "Python是编程语言"},
    {"text": "JavaScript用于Web开发"}
]

results = quick_index_and_search(
    documents=documents,
    query="编程语言",
    embedding_provider=embedding_provider,
    top_k=2
)
```

## 详细使用指南

### 1. 文本分块

```python
from coderepoindex.embeddings import SimpleTextSplitter, SentenceSplitter

# 简单分块器 - 基于字符数
splitter = SimpleTextSplitter(
    chunk_size=1000,     # 每块最大字符数
    chunk_overlap=200,   # 重叠字符数
    separator="\n\n"     # 分割符
)

# 句子分块器 - 基于句子边界
sentence_splitter = SentenceSplitter(
    chunk_size=1000,
    chunk_overlap=200
)

nodes = splitter.split_text("长文本内容...", metadata={"source": "doc1"})
```

### 2. 节点操作

```python
from coderepoindex.embeddings import Node, Document

# 创建节点
node = Node.from_text(
    text="这是文本内容",
    metadata={"category": "example", "priority": "high"}
)

# 添加元数据和关系
node.add_metadata("tags", ["important", "demo"])
node.add_relationship("parent", "parent-node-id")

# 创建文档
doc = Document.from_text("文档内容", metadata={"title": "示例文档"})
```

### 3. 存储组件

```python
from coderepoindex.embeddings import create_document_store, create_vector_store

# 文档存储
doc_store = create_document_store(persist_path="./docs.json")
doc_store.add_nodes([node1, node2])
retrieved_nodes = doc_store.get_nodes(["node-id-1", "node-id-2"])

# 向量存储
vector_store = create_vector_store(persist_path="./vectors.json")
vector_store.add("node-id", [0.1, 0.2, 0.3], metadata={"type": "text"})
results = vector_store.query([0.1, 0.2, 0.3], top_k=5)
```

### 4. 高级检索功能

```python
# 阈值检索 - 只返回相似度超过阈值的结果
results = retriever.retrieve_with_threshold(
    query="查询文本",
    threshold=0.8,
    max_results=50
)

# 上下文检索 - 包含相邻的文本块
results = retriever.retrieve_with_context(
    query="查询文本",
    top_k=5,
    context_window=2  # 前后各2个节点
)

# 相似节点检索
similar_results = retriever.retrieve_similar_to_node(
    node_id="reference-node-id",
    top_k=10
)

# 元数据过滤
results = retriever.retrieve(
    query="查询文本",
    top_k=5,
    metadata_filter={"category": "technical", "priority": "high"}
)
```

### 5. 持久化和加载

```python
# 持久化索引
indexer.persist()  # 保存到配置的persist_dir

# 加载已有索引
retriever.load_index("./existing_index")

# 获取统计信息
stats = indexer.get_statistics()
print(f"文档数: {stats['documents']['total_nodes']}")
print(f"向量数: {stats['vectors']['total_vectors']}")
```

### 6. 文档管理

```python
# 更新文档
new_document = {"text": "更新后的内容", "metadata": {"version": "2.0"}}
indexer.update_document("doc-id", new_document)

# 删除文档
indexer.delete_document("doc-id")

# 从文件构建索引
indexer.add_documents_from_files(
    file_paths=["doc1.txt", "doc2.txt"],
    metadata={"source": "file_upload"}
)
```

### 7. 索引同步管理

**重要**：`indexer.build_index()` 后，`retriever` 需要能访问到新的数据。

#### 自动同步（推荐）
使用 `create_simple_rag_system()` 创建的indexer和retriever会**自动共享存储**：

```python
# 自动共享存储，无需手动同步
indexer, retriever = create_simple_rag_system(
    embedding_provider=embedding_provider,
    persist_dir="./my_index"
)

indexer.build_index(documents)
# retriever立即可以检索到新数据，无需额外操作
results = retriever.retrieve("查询内容")
```

#### 手动同步
如果是独立创建的indexer和retriever：

```python
# 方法1：同步存储实例
retriever.sync_with_indexer(indexer)

# 方法2：通过持久化同步
indexer.persist()           # 保存到磁盘
retriever.refresh()         # 从磁盘重新加载

# 方法3：明确指定共享存储
retriever = create_retriever(
    embedding_provider=embedding_provider,
    document_store=indexer.document_store,  # 共享存储
    vector_store=indexer.vector_store
)
```

#### 验证同步状态
```python
# 检查是否共享存储
print("共享存储:", indexer.document_store is retriever.document_store)

# 检查数据一致性
print("Indexer节点数:", len(indexer.document_store))
print("Retriever节点数:", len(retriever.document_store))
```

### 8. 元数据检索

除了向量相似度检索，embedding模块还提供了丰富的元数据检索功能：

```python
from coderepoindex.embeddings import (
    search_by_metadata,
    search_by_id,
    search_by_ids,
    search_metadata_contains,
    search_metadata_range,
    hybrid_search,
    get_metadata_info
)

# 精确元数据匹配
nodes = search_by_metadata(retriever, {
    "category": "programming",
    "difficulty": "intermediate"
})

# 根据ID检索
node = search_by_id(retriever, "node_123")
nodes = search_by_ids(retriever, ["node_1", "node_2", "node_3"])

# 包含检索（模糊匹配）
nodes = search_metadata_contains(retriever, "tags", "web")  # 标签包含"web"
nodes = search_metadata_contains(retriever, "author", "张")  # 作者名包含"张"

# 范围检索
nodes = search_metadata_range(retriever, "words", min_value=20, max_value=50)  # 字数20-50
nodes = search_metadata_range(retriever, "date", min_value="2024-01-01")  # 2024年后的文档

# 混合检索（向量+元数据）
results = hybrid_search(
    retriever,
    query="机器学习算法",
    metadata_filter={"category": "ai", "difficulty": "advanced"},
    top_k=10,
    metadata_weight=0.3,  # 元数据匹配权重
    vector_weight=0.7     # 向量相似度权重
)

# 元数据统计分析
stats = get_metadata_info(retriever)  # 所有元数据统计
categories = get_metadata_info(retriever, "category")  # 特定键的所有值

# 高级元数据查询
# 检索包含特定元数据键的节点
nodes = retriever.retrieve_by_metadata_exists(
    metadata_keys=["tags", "author"], 
    require_all=True  # 必须同时包含tags和author
)

# 直接使用检索器方法
nodes = retriever.retrieve_metadata_contains("title", "Python")
nodes = retriever.retrieve_metadata_range("score", min_value=0.8)
```

#### 元数据检索功能特性

1. **精确匹配**：完全匹配指定的元数据值
2. **包含检索**：
   - 字符串包含（忽略大小写）
   - 列表包含（检查元素是否在列表中）
3. **范围查询**：
   - 数值范围（整数、浮点数）
   - 字符串范围（字典序比较）
   - 日期范围（字符串格式）
4. **混合检索**：
   - 向量相似度+元数据过滤
   - 可调节权重
   - 支持复合评分
5. **统计分析**：
   - 元数据覆盖率
   - 唯一值统计
   - 数值类型的最值和平均值

## 核心组件

### Node类
表示文本片段和元数据的基本单元：

```python
node = Node(
    node_id="unique-id",
    text="文本内容", 
    metadata={"key": "value"},
    relationships={"parent": "parent-id"},
    embedding=[0.1, 0.2, 0.3]  # 可选的嵌入向量
)
```

### Document类
继承自Node，用于表示完整文档：

```python
doc = Document.from_file("path/to/file.txt")
doc_id = doc.get_doc_id()
```

### 存储组件

#### SimpleDocumentStore
- 基于内存字典的文档存储
- 支持JSON持久化
- 提供丰富的查询和管理方法
- 支持多种元数据检索方式：
  - 精确匹配查询
  - 包含模糊查询
  - 范围查询
  - 键存在性查询
  - 统计分析功能

#### SimpleVectorStore  
- 基于内存的向量存储
- 使用暴力搜索进行相似性计算
- 支持元数据过滤和阈值搜索

### 索引构建器（EmbeddingIndexer）
负责整个索引构建流程：

1. **文档处理**：读取和解析文档
2. **文本分块**：将长文档分割成合适的片段
3. **生成嵌入**：调用模型生成向量表示
4. **存储管理**：将文档和向量分别存储
5. **持久化**：保存索引到磁盘

### 检索器（EmbeddingRetriever）
提供多种检索功能：

- **标准语义检索**：基于向量相似度的语义搜索
- **阈值过滤检索**：只返回相似度超过阈值的结果
- **上下文感知检索**：包含相邻文本块的上下文信息
- **相似节点查找**：查找与指定节点相似的其他节点
- **元数据检索**：
  - 精确匹配检索
  - 包含模糊检索
  - 范围查询检索
  - ID检索（单个和批量）
  - 元数据键存在性检索
- **混合检索**：结合向量相似度和元数据过滤
- **统计分析**：元数据统计信息和分布

## 配置选项

### 文本分块配置
```python
splitter = SimpleTextSplitter(
    chunk_size=1000,        # 块大小
    chunk_overlap=200,      # 重叠大小
    separator="\n\n",       # 分割符
    keep_separator=True     # 保留分割符
)
```

### 索引构建配置
```python
indexer = create_indexer(
    embedding_provider=provider,
    persist_dir="./index",
    embed_batch_size=10,    # 批处理大小
    text_splitter=splitter
)
```

### 向量搜索配置
```python
results = vector_store.query(
    query_embedding=embedding,
    top_k=10,                           # 返回数量
    metadata_filter={"type": "doc"},    # 元数据过滤
)
```

## 性能考虑

### 向量搜索性能
- 当前使用暴力搜索，时间复杂度O(n)
- 适合小到中等规模的数据集（< 10万个向量）
- 对于大规模数据，建议使用专业向量数据库（如FAISS、Pinecone等）

### 内存使用
- 所有数据存储在内存中
- 向量维度通常为768-1536，占用空间较大
- 建议监控内存使用情况

### 批处理优化
```python
# 批量生成嵌入可以提高效率
indexer = create_indexer(
    embedding_provider=provider,
    embed_batch_size=50  # 根据GPU内存调整
)
```

## 扩展性

### 自定义分块器
```python
from coderepoindex.embeddings.base import BaseSplitter

class CustomSplitter(BaseSplitter):
    def split_text(self, text, metadata=None):
        # 实现自定义分块逻辑
        pass
```

### 自定义存储
```python
from coderepoindex.embeddings.base import BaseVectorStore

class CustomVectorStore(BaseVectorStore):
    def query(self, query_embedding, top_k=10, **kwargs):
        # 实现自定义向量搜索逻辑
        pass
```

## 最佳实践

1. **选择合适的块大小**：
   - 太小：语义信息不足
   - 太大：检索精度下降
   - 推荐：500-1500字符

2. **使用重叠分块**：
   - 避免重要信息被分割
   - 推荐重叠：10-20%

3. **元数据设计**：
   - 添加有意义的元数据
   - 便于过滤和分类
   - 使用一致的命名规范
   - 考虑元数据的查询需求

4. **元数据检索策略**：
   - 精确匹配用于分类和标签
   - 包含检索用于模糊搜索
   - 范围查询用于数值和日期
   - 混合检索平衡精确性和相关性

5. **索引同步策略**：
   - 使用`create_simple_rag_system()`创建的indexer和retriever自动共享存储
   - 独立创建时使用`retriever.sync_with_indexer(indexer)`同步
   - 持久化场景使用`retriever.refresh()`重新加载

6. **持久化策略**：
   - 定期保存索引
   - 备份重要数据

7. **性能监控**：
   - 监控内存使用
   - 评估检索质量
   - 分析元数据分布和使用

## 错误处理

```python
try:
    results = retriever.retrieve("query")
except Exception as e:
    logger.error(f"检索失败: {e}")
    # 处理错误
```

## 日志配置

```python
from coderepoindex.embeddings import setup_logging

# 设置日志级别
setup_logging("DEBUG")  # DEBUG, INFO, WARNING, ERROR
```

## 示例项目

查看以下示例文件获取完整的使用指南：

- `examples/embedding_demo.py` - 基础使用示例
- `examples/metadata_search_demo.py` - 元数据检索功能演示

## 限制和注意事项

1. **API依赖**：需要配置有效的嵌入模型API
2. **内存限制**：大量文档可能导致内存不足
3. **搜索性能**：大规模数据下搜索速度较慢
4. **模型一致性**：索引和检索必须使用相同的嵌入模型

## 未来改进

- [ ] 支持增量索引更新
- [ ] 集成专业向量数据库（FAISS、Pinecone等）
- [ ] 支持多种嵌入模型
- [ ] 添加搜索结果重排序
- [ ] 支持关键词检索和全文搜索
- [ ] 优化大文件处理性能
- [ ] 支持向量量化和压缩
- [ ] 添加查询缓存机制

