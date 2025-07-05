#!/usr/bin/env python
"""
元数据检索功能演示

展示如何使用embedding模块的各种元数据检索功能：
1. 根据ID检索
2. 纯元数据检索
3. 元数据包含检索
4. 元数据范围检索
5. 混合检索（向量+元数据）
6. 元数据统计
"""

import os
import sys
from datetime import datetime
from typing import List, Dict, Any

# 添加项目路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from coderepoindex.embeddings import (
    create_simple_rag_system,
    search_by_metadata,
    search_by_id,
    search_by_ids,
    search_metadata_contains,
    search_metadata_range,
    hybrid_search,
    get_metadata_info,
    setup_logging
)


def create_sample_documents() -> List[Dict[str, Any]]:
    """创建示例文档"""
    return [
        {
            "text": "Python是一种高级编程语言，具有简洁的语法和强大的功能。",
            "metadata": {
                "doc_id": "doc_001",
                "category": "programming",
                "language": "python",
                "difficulty": "beginner",
                "words": 20,
                "date": "2024-01-15",
                "tags": ["syntax", "features"],
                "author": "张三"
            }
        },
        {
            "text": "JavaScript是一种动态编程语言，主要用于web开发。",
            "metadata": {
                "doc_id": "doc_002", 
                "category": "programming",
                "language": "javascript",
                "difficulty": "intermediate",
                "words": 18,
                "date": "2024-02-01",
                "tags": ["web", "dynamic"],
                "author": "李四"
            }
        },
        {
            "text": "机器学习是人工智能的一个重要分支，涉及算法和统计模型。",
            "metadata": {
                "doc_id": "doc_003",
                "category": "ai",
                "language": "general",
                "difficulty": "advanced",
                "words": 22,
                "date": "2024-01-30",
                "tags": ["algorithm", "statistics"],
                "author": "王五"
            }
        },
        {
            "text": "深度学习是机器学习的一个子领域，使用神经网络进行模式识别。",
            "metadata": {
                "doc_id": "doc_004",
                "category": "ai",
                "language": "general", 
                "difficulty": "advanced",
                "words": 25,
                "date": "2024-02-10",
                "tags": ["neural_network", "pattern_recognition"],
                "author": "赵六"
            }
        },
        {
            "text": "Web开发涉及前端和后端技术，需要掌握多种编程语言和框架。",
            "metadata": {
                "doc_id": "doc_005",
                "category": "programming",
                "language": "general",
                "difficulty": "intermediate",
                "words": 24,
                "date": "2024-01-20",
                "tags": ["frontend", "backend"],
                "author": "钱七"
            }
        }
    ]


def demo_basic_metadata_search(retriever):
    """演示基础元数据检索"""
    print("\n" + "="*50)
    print("1. 基础元数据检索演示")
    print("="*50)
    
    # 1. 根据单个条件检索
    print("\n🔍 检索所有编程类文档:")
    nodes = search_by_metadata(retriever, {"category": "programming"})
    for node in nodes:
        print(f"  - {node.metadata['doc_id']}: {node.text[:30]}...")
    
    # 2. 根据多个条件检索
    print("\n🔍 检索中级难度的编程文档:")
    nodes = search_by_metadata(retriever, {
        "category": "programming", 
        "difficulty": "intermediate"
    })
    for node in nodes:
        print(f"  - {node.metadata['doc_id']}: {node.text[:30]}...")
    
    # 3. 根据作者检索
    print("\n🔍 检索张三的文档:")
    nodes = search_by_metadata(retriever, {"author": "张三"})
    for node in nodes:
        print(f"  - {node.metadata['doc_id']}: {node.text[:30]}...")


def demo_id_search(retriever):
    """演示ID检索"""
    print("\n" + "="*50)
    print("2. ID检索演示")
    print("="*50)
    
    # 获取所有节点ID用于演示
    all_stats = get_metadata_info(retriever)
    print(f"\n📊 当前索引中共有 {sum(stats['count'] for stats in all_stats.values())} 个节点")
    
    # 1. 根据单个文档ID检索
    print("\n🔍 检索文档 doc_002 的所有节点:")
    nodes = retriever.retrieve_by_doc_id("doc_002")
    for node in nodes:
        print(f"  - 节点ID: {node.node_id}")
        print(f"    文本: {node.text[:50]}...")
    
    # 2. 根据节点ID检索（假设我们知道一个节点ID）
    if nodes:
        node_id = nodes[0].node_id
        print(f"\n🔍 根据节点ID检索: {node_id}")
        node = search_by_id(retriever, node_id)
        if node:
            print(f"  找到节点: {node.text[:50]}...")
        else:
            print("  节点未找到")
    
    # 3. 批量ID检索
    if len(nodes) > 1:
        node_ids = [node.node_id for node in nodes[:2]]
        print(f"\n🔍 批量检索节点: {node_ids}")
        batch_nodes = search_by_ids(retriever, node_ids)
        for node in batch_nodes:
            print(f"  - {node.node_id}: {node.text[:30]}...")


def demo_contains_search(retriever):
    """演示包含检索"""
    print("\n" + "="*50)
    print("3. 元数据包含检索演示")
    print("="*50)
    
    # 1. 搜索标签包含特定值的文档
    print("\n🔍 搜索标签包含'web'的文档:")
    nodes = search_metadata_contains(retriever, "tags", "web")
    for node in nodes:
        print(f"  - {node.metadata['doc_id']}: {node.metadata['tags']}")
    
    # 2. 搜索作者名称包含特定字符的文档
    print("\n🔍 搜索作者名称包含'三'的文档:")
    nodes = search_metadata_contains(retriever, "author", "三")
    for node in nodes:
        print(f"  - {node.metadata['doc_id']}: 作者 {node.metadata['author']}")
    
    # 3. 搜索分类包含特定词的文档
    print("\n🔍 搜索分类包含'ai'的文档:")
    nodes = search_metadata_contains(retriever, "category", "ai")
    for node in nodes:
        print(f"  - {node.metadata['doc_id']}: {node.metadata['category']}")


def demo_range_search(retriever):
    """演示范围检索"""
    print("\n" + "="*50)
    print("4. 元数据范围检索演示")
    print("="*50)
    
    # 1. 按字数范围检索
    print("\n🔍 检索字数在20-25之间的文档:")
    nodes = search_metadata_range(retriever, "words", min_value=20, max_value=25)
    for node in nodes:
        print(f"  - {node.metadata['doc_id']}: {node.metadata['words']}字")
    
    # 2. 按日期范围检索
    print("\n🔍 检索2024年2月的文档:")
    nodes = search_metadata_range(retriever, "date", min_value="2024-02-01", max_value="2024-02-28")
    for node in nodes:
        print(f"  - {node.metadata['doc_id']}: {node.metadata['date']}")
    
    # 3. 只设置最小值
    print("\n🔍 检索字数超过20的文档:")
    nodes = search_metadata_range(retriever, "words", min_value=20)
    for node in nodes:
        print(f"  - {node.metadata['doc_id']}: {node.metadata['words']}字")


def demo_hybrid_search(retriever):
    """演示混合检索"""
    print("\n" + "="*50)
    print("5. 混合检索演示（向量+元数据）")
    print("="*50)
    
    # 1. 语义搜索 + 分类过滤
    print("\n🔍 在编程类文档中搜索'语言':")
    try:
        results = hybrid_search(
            retriever, 
            query="语言",
            metadata_filter={"category": "programming"},
            top_k=3,
            metadata_weight=0.3,
            vector_weight=0.7
        )
        for result in results:
            print(f"  - {result['node_id']}: 混合分数 {result.get('hybrid_score', 0):.3f}")
            print(f"    向量分数: {result.get('vector_score', 0):.3f}, 元数据分数: {result.get('metadata_score', 0):.3f}")
            print(f"    文本: {result['text'][:50]}...")
    except Exception as e:
        print(f"  ⚠️  混合检索需要有效的嵌入提供商: {e}")
    
    # 2. 语义搜索 + 难度过滤
    print("\n🔍 在高级难度文档中搜索'学习':")
    try:
        results = hybrid_search(
            retriever,
            query="学习",
            metadata_filter={"difficulty": "advanced"},
            top_k=3
        )
        for result in results:
            print(f"  - {result['node_id']}: 混合分数 {result.get('hybrid_score', 0):.3f}")
            print(f"    文本: {result['text'][:50]}...")
    except Exception as e:
        print(f"  ⚠️  混合检索需要有效的嵌入提供商: {e}")


def demo_metadata_statistics(retriever):
    """演示元数据统计"""
    print("\n" + "="*50)
    print("6. 元数据统计信息演示")
    print("="*50)
    
    # 1. 获取所有元数据统计
    print("\n📊 所有元数据统计:")
    stats = get_metadata_info(retriever)
    for key, stat in stats.items():
        print(f"  {key}:")
        print(f"    - 数量: {stat['count']}")
        print(f"    - 唯一值: {stat['unique_values']}")
        print(f"    - 覆盖率: {stat['coverage']:.2%}")
        if 'min' in stat:
            print(f"    - 范围: {stat['min']} - {stat['max']}")
            print(f"    - 平均值: {stat['avg']:.2f}")
    
    # 2. 获取特定元数据的所有值
    print("\n📊 所有分类值:")
    categories = get_metadata_info(retriever, "category")
    print(f"  {categories}")
    
    print("\n📊 所有难度级别:")
    difficulties = get_metadata_info(retriever, "difficulty")
    print(f"  {difficulties}")
    
    print("\n📊 所有作者:")
    authors = get_metadata_info(retriever, "author")
    print(f"  {authors}")


def demo_advanced_queries(retriever):
    """演示高级查询"""
    print("\n" + "="*50)
    print("7. 高级查询演示")
    print("="*50)
    
    # 1. 复合元数据查询
    print("\n🔍 检索存在特定元数据键的文档:")
    nodes = retriever.retrieve_by_metadata_exists(["tags", "author"], require_all=True)
    print(f"  找到 {len(nodes)} 个同时包含tags和author的文档")
    
    nodes = retriever.retrieve_by_metadata_exists(["tags", "author"], require_all=False)
    print(f"  找到 {len(nodes)} 个包含tags或author的文档")
    
    # 2. 组合查询示例
    print("\n🔍 复杂组合查询示例:")
    
    # 先按分类过滤
    programming_nodes = search_by_metadata(retriever, {"category": "programming"})
    print(f"  编程类文档: {len(programming_nodes)} 个")
    
    # 再在其中按字数过滤
    if programming_nodes:
        prog_node_ids = [node.node_id for node in programming_nodes]
        # 这里我们手动组合过滤，实际应用中可以扩展更复杂的查询接口
        long_prog_nodes = [
            node for node in programming_nodes 
            if node.metadata.get('words', 0) > 20
        ]
        print(f"  其中字数>20的: {len(long_prog_nodes)} 个")
        
        for node in long_prog_nodes:
            print(f"    - {node.metadata['doc_id']}: {node.metadata['words']}字")


def main():
    """主演示函数"""
    print("🚀 元数据检索功能演示")
    print("=" * 60)
    
    # 设置日志
    setup_logging("INFO")
    
    # 创建示例文档
    documents = create_sample_documents()
    print(f"\n📚 创建了 {len(documents)} 个示例文档")
    
    try:
        # 尝试创建带有模拟嵌入提供商的RAG系统
        print("\n🏗️  创建RAG系统...")
        
        # 这里我们创建一个不需要真实API的版本用于演示
        # 注意：某些功能需要真实的嵌入提供商才能完整工作
        from coderepoindex.embeddings import create_indexer, create_retriever
        
        # 直接创建存储组件，避免依赖嵌入提供商
        from coderepoindex.embeddings import SimpleDocumentStore, SimpleVectorStore, EmbeddingRetriever
        
        # 创建文档存储和向量存储
        document_store = SimpleDocumentStore()
        vector_store = SimpleVectorStore()
        
        # 创建检索器（不需要嵌入提供商用于元数据检索）
        retriever = EmbeddingRetriever(
            embedding_provider=None,  # 元数据检索不需要
            document_store=document_store,
            vector_store=vector_store,
            metadata_only=True  # 启用元数据检索模式
        )
        
        # 模拟构建索引（只构建文档存储部分）
        print("📚 构建文档索引...")
        for i, doc in enumerate(documents):
            from coderepoindex.embeddings import Node
            # 创建节点
            node = Node(
                text=doc["text"],
                metadata=doc["metadata"],
                node_id=f"node_{doc['metadata']['doc_id']}_{i}"
            )
            # 添加到文档存储
            document_store.add_node(node)
        
        print(f"✅ 索引构建完成，共 {len(document_store._nodes)} 个节点")
        
        # 执行各种演示
        demo_basic_metadata_search(retriever)
        demo_id_search(retriever)
        demo_contains_search(retriever)
        demo_range_search(retriever)
        demo_hybrid_search(retriever)
        demo_metadata_statistics(retriever)
        demo_advanced_queries(retriever)
        
        print("\n" + "="*60)
        print("🎉 元数据检索功能演示完成！")
        print("\n💡 主要功能总结:")
        print("   ✅ 基础元数据检索 - 精确匹配")
        print("   ✅ ID检索 - 单个和批量")
        print("   ✅ 包含检索 - 模糊匹配")
        print("   ✅ 范围检索 - 数值和字符串范围")
        print("   ✅ 混合检索 - 向量+元数据组合")
        print("   ✅ 统计信息 - 元数据分析")
        print("   ✅ 高级查询 - 复合条件")
        
        print("\n📝 注意事项:")
        print("   - 混合检索需要有效的嵌入提供商")
        print("   - 范围检索支持数值和字符串比较")
        print("   - 所有方法都包含错误处理")
        print("   - 支持复杂的元数据结构")
        
    except Exception as e:
        print(f"\n❌ 演示过程中出现错误: {e}")
        print("请检查依赖配置和环境设置")


if __name__ == "__main__":
    main() 