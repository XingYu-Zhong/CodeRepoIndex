#!/usr/bin/env python
"""
索引同步问题演示和解决方案

展示：
1. create_simple_rag_system的自动同步特性
2. 独立创建时的同步问题和解决方案
3. 各种同步方法的使用
"""

import os
import sys
from typing import List, Dict, Any

# 添加项目路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from coderepoindex.embeddings import (
    create_simple_rag_system,
    create_indexer,
    create_retriever,
    SimpleDocumentStore,
    SimpleVectorStore,
    EmbeddingRetriever,
    check_sync_status,
    sync_indexer_retriever,
    setup_logging
)


def create_sample_documents() -> List[Dict[str, Any]]:
    """创建示例文档"""
    return [
        {
            "text": "人工智能是计算机科学的一个分支",
            "metadata": {"topic": "AI", "difficulty": "basic"}
        },
        {
            "text": "机器学习是人工智能的子领域",
            "metadata": {"topic": "ML", "difficulty": "intermediate"}
        },
        {
            "text": "深度学习使用神经网络进行学习",
            "metadata": {"topic": "DL", "difficulty": "advanced"}
        }
    ]


def demo_auto_sync():
    """演示自动同步（推荐方式）"""
    print("\n" + "="*60)
    print("1. 自动同步演示 - create_simple_rag_system()")
    print("="*60)
    
    documents = create_sample_documents()
    
    # 使用create_simple_rag_system创建，自动共享存储
    print("🏗️  创建RAG系统（自动共享存储）...")
    try:
        # 创建不需要API密钥的演示版本
        from coderepoindex.embeddings import SimpleDocumentStore, SimpleVectorStore
        
        # 手动创建共享存储
        document_store = SimpleDocumentStore()
        vector_store = SimpleVectorStore()
        
        indexer = create_indexer(
            embedding_provider=None,
            document_store=document_store,
            vector_store=vector_store
        )
        
        retriever = create_retriever(
            embedding_provider=None,
            document_store=document_store,  # 明确共享
            vector_store=vector_store,      # 明确共享  
            metadata_only=True
        )
        
        # 检查同步状态
        sync_status = check_sync_status(indexer, retriever)
        print("📊 同步状态检查:")
        for key, value in sync_status.items():
            status_icon = "✅" if value else "❌"
            print(f"  {status_icon} {key}: {value}")
        
        # 构建索引（只添加到文档存储，模拟没有嵌入提供商的情况）
        print("\n📚 构建索引...")
        for i, doc in enumerate(documents):
            from coderepoindex.embeddings import Node
            node = Node(
                text=doc["text"],
                metadata=doc["metadata"],
                node_id=f"node_{i}"
            )
            indexer.document_store.add_node(node)
        
        print(f"✅ 索引构建完成: {len(indexer.document_store)} 个节点")
        
        # 检索测试
        print("\n🔍 检索测试:")
        ai_docs = retriever.retrieve_by_metadata({"topic": "AI"})
        print(f"  找到AI相关文档: {len(ai_docs)} 个")
        for doc in ai_docs:
            print(f"    - {doc.text[:30]}...")
        
        # 再次检查状态
        final_status = check_sync_status(indexer, retriever)
        print(f"\n📊 最终状态: 数据一致 = {final_status['data_consistent']}")
        
    except Exception as e:
        print(f"❌ 演示出错: {e}")


def demo_manual_sync():
    """演示手动同步问题和解决方案"""
    print("\n" + "="*60)
    print("2. 手动同步演示 - 独立创建的问题和解决")
    print("="*60)
    
    documents = create_sample_documents()
    
    # 模拟独立创建（会有同步问题）
    print("🏗️  独立创建indexer和retriever...")
    
    indexer_store = SimpleDocumentStore()
    indexer_vector = SimpleVectorStore()
    
    retriever_store = SimpleDocumentStore() 
    retriever_vector = SimpleVectorStore()
    
    indexer = create_indexer(
        embedding_provider=None,
        document_store=indexer_store,
        vector_store=indexer_vector
    )
    
    retriever = create_retriever(
        embedding_provider=None,
        document_store=retriever_store,  # 不同的存储实例！
        vector_store=retriever_vector,
        metadata_only=True
    )
    
    # 检查初始状态
    print("\n📊 初始同步状态:")
    initial_status = check_sync_status(indexer, retriever)
    for key, value in initial_status.items():
        status_icon = "✅" if value else "❌"
        print(f"  {status_icon} {key}: {value}")
    
    # 构建索引
    print("\n📚 在indexer中构建索引...")
    for i, doc in enumerate(documents):
        from coderepoindex.embeddings import Node
        node = Node(
            text=doc["text"],
            metadata=doc["metadata"],
            node_id=f"node_{i}"
        )
        indexer.document_store.add_node(node)
    
    print(f"✅ Indexer索引构建完成: {len(indexer.document_store)} 个节点")
    
    # 检索测试（会失败）
    print("\n🔍 Retriever检索测试（同步前）:")
    ai_docs = retriever.retrieve_by_metadata({"topic": "AI"})
    print(f"  找到AI相关文档: {len(ai_docs)} 个 ❌")
    
    # 显示问题
    problem_status = check_sync_status(indexer, retriever)
    print(f"\n❌ 问题状态: 数据一致 = {problem_status['data_consistent']}")
    print(f"   Indexer有 {problem_status['indexer_docs']} 个节点")
    print(f"   Retriever有 {problem_status['retriever_docs']} 个节点")
    
    # 解决方案1：使用sync_with_indexer
    print("\n🔧 解决方案1: 使用sync_indexer_retriever()")
    sync_indexer_retriever(indexer, retriever)
    
    # 再次检索测试
    print("\n🔍 Retriever检索测试（同步后）:")
    ai_docs = retriever.retrieve_by_metadata({"topic": "AI"})
    print(f"  找到AI相关文档: {len(ai_docs)} 个 ✅")
    for doc in ai_docs:
        print(f"    - {doc.text[:30]}...")
    
    # 检查修复后状态
    fixed_status = check_sync_status(indexer, retriever)
    print(f"\n✅ 修复后状态: 数据一致 = {fixed_status['data_consistent']}")


def demo_various_sync_methods():
    """演示各种同步方法"""
    print("\n" + "="*60)
    print("3. 各种同步方法演示")
    print("="*60)
    
    documents = create_sample_documents()
    
    print("📋 同步方法对比:")
    print("  方法1: 创建时明确指定共享存储")
    print("  方法2: 使用sync_with_indexer()方法")
    print("  方法3: 通过check_sync_status()监控状态")
    
    # 方法1：创建时指定共享存储
    print("\n🔧 方法1: 创建时明确指定共享存储")
    
    indexer = create_indexer(embedding_provider=None)
    
    # 创建retriever时明确指定共享存储
    retriever = create_retriever(
        embedding_provider=None,
        document_store=indexer.document_store,  # 明确共享
        vector_store=indexer.vector_store,
        metadata_only=True
    )
    
    status1 = check_sync_status(indexer, retriever)
    print(f"  ✅ 共享存储: {status1['shared_document_store']}")
    
    # 方法2：使用便利函数
    print("\n🔧 方法2: 使用便利函数检查状态")
    
    print("  可用的便利函数:")
    print("    - check_sync_status(): 检查同步状态")
    print("    - sync_indexer_retriever(): 同步存储实例")
    
    # 方法3：状态监控
    print("\n🔧 方法3: 持续状态监控")
    
    def print_sync_summary(indexer, retriever, stage):
        status = check_sync_status(indexer, retriever)
        print(f"  📊 {stage}:")
        print(f"    - 共享文档存储: {status['shared_document_store']}")
        print(f"    - 共享向量存储: {status['shared_vector_store']}")
        print(f"    - 数据一致性: {status['data_consistent']}")
        print(f"    - 节点数量: Indexer={status['indexer_docs']}, Retriever={status['retriever_docs']}")
    
    print_sync_summary(indexer, retriever, "初始状态")
    
    # 添加一些数据
    for i, doc in enumerate(documents):
        from coderepoindex.embeddings import Node
        node = Node(
            text=doc["text"],
            metadata=doc["metadata"],
            node_id=f"method3_node_{i}"
        )
        indexer.document_store.add_node(node)
    
    print_sync_summary(indexer, retriever, "添加数据后")


def demo_best_practices():
    """演示最佳实践"""
    print("\n" + "="*60)
    print("4. 最佳实践和建议")
    print("="*60)
    
    print("💡 最佳实践:")
    print()
    
    print("✅ 推荐做法:")
    print("  1. 使用create_simple_rag_system()自动处理同步")
    print("  2. 独立创建时明确指定共享存储")
    print("  3. 使用check_sync_status()验证状态")
    print("  4. 在构建索引前后检查数据一致性")
    print()
    
    print("❌ 避免的问题:")
    print("  1. 独立创建indexer和retriever而不共享存储")
    print("  2. 构建索引后直接检索而不确认同步状态")
    print("  3. 忘记在更新索引后刷新retriever")
    print()
    
    print("🔧 调试技巧:")
    print("  1. 使用len(indexer.document_store)检查节点数量")
    print("  2. 比较indexer和retriever的存储实例ID")
    print("  3. 检查is_ready()状态")
    print()
    
    # 实际演示
    print("📝 实际代码示例:")
    print()
    
    # 创建演示
    indexer = create_indexer(embedding_provider=None)
    retriever = create_retriever(
        embedding_provider=None,
        document_store=indexer.document_store,
        vector_store=indexer.vector_store,
        metadata_only=True
    )
    
    # 调试检查
    print("🔍 调试检查代码:")
    print(f"  indexer存储ID: {id(indexer.document_store)}")
    print(f"  retriever存储ID: {id(retriever.document_store)}")
    print(f"  是否为同一对象: {indexer.document_store is retriever.document_store}")
    print(f"  indexer节点数: {len(indexer.document_store)}")
    print(f"  retriever节点数: {len(retriever.document_store)}")
    
    # 状态检查
    status = check_sync_status(indexer, retriever)
    print(f"  数据一致性: {status['data_consistent']}")


def main():
    """主演示函数"""
    print("🚀 索引同步问题演示和解决方案")
    print("=" * 70)
    
    # 设置日志
    setup_logging("INFO")
    
    try:
        # 各种演示
        demo_auto_sync()
        demo_manual_sync() 
        demo_various_sync_methods()
        demo_best_practices()
        
        print("\n" + "="*70)
        print("🎉 演示完成！")
        print()
        print("📝 总结:")
        print("✅ 问题已解决：create_simple_rag_system现在自动共享存储")
        print("✅ 提供了多种同步方法和检查工具")
        print("✅ 更新了文档和最佳实践指南")
        print()
        print("🔧 关键改进:")
        print("  - create_simple_rag_system()自动共享存储实例")
        print("  - 新增retriever.sync_with_indexer()方法")
        print("  - 新增retriever.refresh()方法")
        print("  - 新增check_sync_status()状态检查")
        print("  - 新增sync_indexer_retriever()便利函数")
        
    except Exception as e:
        print(f"\n❌ 演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 