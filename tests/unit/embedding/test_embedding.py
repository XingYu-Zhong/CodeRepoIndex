import sys
from pathlib import Path
from loguru import logger
logger.remove()  # 移除默认handler
logger.add(sys.stderr, level="INFO")  # 只显示INFO及以上级别的日志

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))


from coderepoindex.embeddings import create_simple_rag_system
from coderepoindex.models import create_embedding_provider


# 1. 创建嵌入提供商
embedding_provider = create_embedding_provider(
    provider_type="api",
    model_name="text-embedding-v3", 
    api_key="sk-xxx",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
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
print(results)
for result in results:
    print(f"相似度: {result['score']:.4f}")
    print(f"内容: {result['text']}")