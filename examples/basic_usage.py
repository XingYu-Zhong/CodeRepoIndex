"""
CodeRepoIndex 基本使用示例

展示如何使用 CodeRepoIndex 创建索引和搜索代码。
"""

from coderepoindex import CodeIndexer, CodeSearcher


def main():
    """主函数演示基本用法"""
    
    print("🚀 CodeRepoIndex 基本使用示例")
    print("=" * 50)
    
    # 1. 创建代码索引器
    print("\n1. 创建代码索引器...")
    indexer = CodeIndexer(
        embedding_model="sentence-transformers/all-MiniLM-L6-v2",
        storage_backend="chroma"
    )
    print("✅ 索引器创建成功")
    
    # 2. 为代码仓库创建索引
    print("\n2. 为代码仓库创建索引...")
    try:
        # 注意：这里使用当前目录作为示例
        # 在实际使用中，请替换为您的代码仓库路径
        repo_path = "."
        stats = indexer.index_repository(
            repo_path=repo_path,
            exclude_patterns=["*.pyc", "__pycache__", ".git"]
        )
        
        print("✅ 索引创建完成")
        print(f"📊 统计信息: {stats}")
        
    except Exception as e:
        print(f"❌ 索引创建失败: {e}")
    
    # 3. 创建代码搜索器
    print("\n3. 创建代码搜索器...")
    searcher = CodeSearcher(
        storage_backend="chroma",
        embedding_model="sentence-transformers/all-MiniLM-L6-v2"
    )
    print("✅ 搜索器创建成功")
    
    # 4. 进行语义搜索
    print("\n4. 进行语义搜索...")
    
    # 搜索示例
    search_queries = [
        "calculate fibonacci sequence",
        "file reading and writing",
        "database connection setup",
        "error handling and logging"
    ]
    
    for query in search_queries:
        print(f"\n🔍 搜索: '{query}'")
        
        try:
            results = searcher.search(
                query=query,
                top_k=5,
                similarity_threshold=0.1
            )
            
            if results:
                print(f"✅ 找到 {len(results)} 个相关结果")
                for i, result in enumerate(results[:3], 1):  # 只显示前3个
                    print(f"  {i}. {result.file_path} "
                          f"(相似度: {result.similarity_score:.3f})")
            else:
                print("😔 没有找到相关结果")
                
        except Exception as e:
            print(f"❌ 搜索失败: {e}")
    
    # 5. 获取统计信息
    print("\n5. 获取统计信息...")
    try:
        indexer_stats = indexer.get_stats()
        searcher_stats = searcher.get_stats()
        
        print("📊 索引器统计:")
        for key, value in indexer_stats.items():
            print(f"  - {key}: {value}")
        
        print("📊 搜索器统计:")
        for key, value in searcher_stats.items():
            print(f"  - {key}: {value}")
            
    except Exception as e:
        print(f"❌ 获取统计信息失败: {e}")
    
    print("\n🎉 示例完成！")


if __name__ == "__main__":
    main() 