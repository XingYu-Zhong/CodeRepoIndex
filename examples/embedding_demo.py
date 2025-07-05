"""
Embedding模块使用示例

演示如何使用类似LlamaIndex的本地嵌入存储模块
"""

import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from coderepoindex.embeddings import (
    create_simple_rag_system,
    quick_index_and_search,
    SimpleTextSplitter,
    Node,
    Document,
    setup_logging
)
from coderepoindex.models import create_openai_providers


def demo_basic_usage():
    """演示基本使用方法"""
    print("\n=== 基本使用示例 ===")
    
    # 创建嵌入提供商（注意：需要配置正确的API密钥）
    try:
        provider = create_openai_providers(
            api_key="sk-test-key",  # 请替换为实际的API密钥
            base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
            embedding_model="text-embedding-v3"
        )
        embedding_provider = provider.embedding_provider
        print(f"✅ 嵌入提供商创建成功: {embedding_provider.get_model_name()}")
    except Exception as e:
        print(f"❌ 创建嵌入提供商失败: {e}")
        print("注意：请配置正确的API密钥")
        return
    
    # 创建RAG系统
    indexer, retriever = create_simple_rag_system(
        embedding_provider=embedding_provider,
        persist_dir="./demo_index",
        chunk_size=500,
        chunk_overlap=100
    )
    
    # 准备示例文档
    documents = [
        {
            "text": "人工智能（AI）是计算机科学的一个分支，致力于创建能够执行通常需要人类智能的任务的系统。这包括学习、推理、问题解决、感知和语言理解。",
            "metadata": {"source": "AI_introduction", "topic": "artificial_intelligence"}
        },
        {
            "text": "机器学习是人工智能的一个子领域，专注于开发能够从数据中学习并做出预测或决策的算法，而无需明确编程。",
            "metadata": {"source": "ML_basics", "topic": "machine_learning"}
        },
        {
            "text": "深度学习是机器学习的一个子集，使用具有多个层的神经网络来模拟人脑处理信息的方式。它在图像识别、自然语言处理等领域取得了突破性进展。",
            "metadata": {"source": "DL_overview", "topic": "deep_learning"}
        },
        {
            "text": "自然语言处理（NLP）是人工智能的一个分支，专注于使计算机能够理解、解释和生成人类语言。",
            "metadata": {"source": "NLP_intro", "topic": "natural_language_processing"}
        }
    ]
    
    # 构建索引
    print("📖 构建索引...")
    indexer.build_index(documents)
    
    # 获取索引统计信息
    stats = indexer.get_statistics()
    print(f"📊 索引统计: {stats['documents']['total_nodes']} 个节点, {stats['vectors']['total_vectors']} 个向量")
    
    # 进行检索
    query = "什么是深度学习？"
    print(f"\n🔍 查询: {query}")
    
    results = retriever.retrieve(query, top_k=3)
    
    print("📋 检索结果:")
    for i, result in enumerate(results, 1):
        print(f"\n{i}. 相似度: {result['score']:.4f}")
        print(f"   来源: {result['metadata'].get('source', 'Unknown')}")
        print(f"   主题: {result['metadata'].get('topic', 'Unknown')}")
        print(f"   文本: {result['text'][:100]}...")


def demo_text_splitters():
    """演示不同的文本分块器"""
    print("\n=== 文本分块器示例 ===")
    
    long_text = """
    人工智能的发展历程可以追溯到20世纪50年代。在这个时期，计算机科学家开始探索如何让机器模拟人类的思维过程。

    早期的人工智能研究主要集中在符号推理和专家系统上。这些系统使用预定义的规则来解决特定领域的问题。

    随着计算能力的提升和大数据的出现，机器学习方法开始兴起。特别是神经网络的发展，为人工智能带来了新的突破。

    今天，深度学习已经成为人工智能领域的主流方法，在计算机视觉、自然语言处理、语音识别等领域都取得了显著的成果。
    """
    
    # 简单文本分块器
    simple_splitter = SimpleTextSplitter(chunk_size=200, chunk_overlap=50)
    simple_nodes = simple_splitter.split_text(long_text, {"source": "AI_history"})
    
    print(f"📄 简单分块器生成 {len(simple_nodes)} 个节点:")
    for i, node in enumerate(simple_nodes):
        print(f"  节点{i+1}: {len(node.text)} 字符")
        print(f"    内容预览: {node.text[:80].strip()}...")
    
    # 创建文档对象
    doc = Document.from_text(long_text, metadata={"title": "AI发展历程", "type": "article"})
    print(f"\n📜 文档对象: ID={doc.get_doc_id()[:8]}..., 长度={len(doc)} 字符")


def demo_node_operations():
    """演示节点操作"""
    print("\n=== 节点操作示例 ===")
    
    # 创建节点
    node = Node.from_text(
        "这是一个示例文本节点，用于演示Node类的功能。",
        metadata={"type": "example", "category": "demo"}
    )
    
    print(f"📝 创建节点: {node}")
    print(f"   ID: {node.node_id}")
    print(f"   文本长度: {len(node)}")
    
    # 添加元数据
    node.add_metadata("priority", "high")
    node.add_metadata("tags", ["demo", "example", "test"])
    
    print(f"📋 更新后的元数据: {node.metadata}")
    
    # 添加关系
    node.add_relationship("parent", "parent-node-id")
    node.add_relationship("next", "next-node-id")
    
    print(f"🔗 节点关系: {node.relationships}")
    
    # 转换为字典
    node_dict = node.to_dict()
    print(f"📄 节点字典格式: {list(node_dict.keys())}")
    
    # 从字典恢复
    restored_node = Node.from_dict(node_dict)
    print(f"🔄 恢复的节点: {restored_node.node_id == node.node_id}")


def demo_quick_search():
    """演示快速索引和搜索"""
    print("\n=== 快速索引和搜索示例 ===")
    
    # 创建嵌入提供商（这里使用模拟的方式，实际使用时需要真实的API密钥）
    try:
        provider = create_openai_providers(
            api_key="sk-test-key",
            base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
            embedding_model="text-embedding-v3"
        )
        embedding_provider = provider.embedding_provider
    except Exception as e:
        print(f"❌ 无法创建嵌入提供商: {e}")
        print("跳过快速搜索示例（需要真实的API密钥）")
        return
    
    # 准备文档
    tech_documents = [
        {"text": "Python是一种高级编程语言，以其简洁和可读性而闻名。", "metadata": {"topic": "python"}},
        {"text": "JavaScript是一种动态编程语言，主要用于Web开发。", "metadata": {"topic": "javascript"}},
        {"text": "React是一个用于构建用户界面的JavaScript库。", "metadata": {"topic": "react"}},
        {"text": "Docker是一个容器化平台，用于应用程序的打包和部署。", "metadata": {"topic": "docker"}},
    ]
    
    # 快速搜索
    query = "编程语言"
    print(f"🔍 查询: {query}")
    
    results = quick_index_and_search(
        documents=tech_documents,
        query=query,
        embedding_provider=embedding_provider,
        top_k=2
    )
    
    print("📋 快速搜索结果:")
    for i, result in enumerate(results, 1):
        print(f"{i}. 相似度: {result['score']:.4f}")
        print(f"   主题: {result['metadata'].get('topic', 'Unknown')}")
        print(f"   内容: {result['text']}")


def demo_persistence():
    """演示持久化功能"""
    print("\n=== 持久化功能示例 ===")
    
    from coderepoindex.embeddings import create_indexer, create_retriever
    
    # 创建带持久化的索引构建器
    persist_dir = "./persistence_demo"
    
    try:
        provider = create_openai_providers(
            api_key="sk-test-key",
            base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
            embedding_model="text-embedding-v3"
        )
        embedding_provider = provider.embedding_provider
    except Exception as e:
        print(f"❌ 无法创建嵌入提供商: {e}")
        print("跳过持久化示例（需要真实的API密钥）")
        return
    
    indexer = create_indexer(
        embedding_provider=embedding_provider,
        persist_dir=persist_dir
    )
    
    # 添加一些文档
    sample_docs = [
        {"text": "持久化是数据存储的重要特性。", "metadata": {"type": "definition"}},
        {"text": "索引可以加速数据检索过程。", "metadata": {"type": "concept"}},
    ]
    
    print("💾 构建并持久化索引...")
    indexer.build_index(sample_docs)
    
    print(f"📁 索引已保存到: {persist_dir}")
    print(f"📊 文档存储文件: {os.path.exists(os.path.join(persist_dir, 'document_store.json'))}")
    print(f"📊 向量存储文件: {os.path.exists(os.path.join(persist_dir, 'vector_store.json'))}")
    
    # 创建新的检索器来加载持久化的索引
    new_retriever = create_retriever(
        embedding_provider=embedding_provider,
        persist_dir=persist_dir
    )
    
    print("🔄 从持久化文件加载索引...")
    stats = new_retriever.get_statistics()
    print(f"📈 加载的统计信息: {stats['documents']['total_nodes']} 个节点")


def main():
    """主函数"""
    print("🚀 Embedding模块完整示例")
    print("=" * 50)
    
    # 设置日志级别
    setup_logging("INFO")
    
    # 运行各种演示
    demo_node_operations()
    demo_text_splitters()
    
    # 需要真实API密钥的演示
    print("\n" + "=" * 50)
    print("⚠️  以下演示需要配置真实的API密钥才能运行")
    print("请在代码中替换 'sk-test-key' 为您的实际API密钥")
    print("=" * 50)
    
    demo_basic_usage()
    demo_quick_search()
    demo_persistence()
    
    print("\n🎉 演示完成！")
    print("\n📚 使用提示:")
    print("1. 配置正确的API密钥和base_url")
    print("2. 根据需要选择合适的chunk_size和chunk_overlap")
    print("3. 使用持久化功能保存索引以便后续使用")
    print("4. 利用元数据过滤功能进行精确检索")


if __name__ == "__main__":
    main() 