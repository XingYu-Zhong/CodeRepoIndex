"""
CodeRepoIndex 基本使用示例

展示如何使用配置中心和新的API配置方式来创建索引和搜索代码。
"""

import os
from coderepoindex import (
    CodeIndexer, 
    CodeSearcher,
    load_config,
    get_config_template
)
from coderepoindex.repository import create_local_config


def main():
    """主函数演示配置中心的使用"""
    
    print("🚀 CodeRepoIndex 基本使用示例")
    print("=" * 50)
    
    # ============================================================================
    # 方式1: 使用配置中心 - 从环境变量或配置文件加载配置
    # ============================================================================
    print("\n📋 方式1: 使用配置中心")
    print("-" * 30)
    
    # 1.1 从环境变量加载配置
    print("1.1 从环境变量加载配置...")
    
    # 设置环境变量（在实际使用中，您应该在shell中设置这些变量）
    # export CODEREPO_API_KEY="your-api-key"
    # export CODEREPO_BASE_URL="https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
    # export CODEREPO_STORAGE_PATH="./my_storage"
    
    try:
        # 从环境变量和默认配置加载
        config = load_config()
        print(f"✅ 配置加载成功: {config.project_name} v{config.version}")
        print(f"   - 存储路径: {config.storage.base_path}")
        print(f"   - 向量后端: {config.storage.vector_backend}")
        print(f"   - 嵌入模型: {config.embedding.model_name}")
        
        # 使用配置创建索引器和搜索器
        indexer = CodeIndexer(config=config)
        searcher = CodeSearcher(config=config)
        
        print("✅ 使用配置中心创建索引器和搜索器成功")
        
    except Exception as e:
        print(f"⚠️  配置加载失败: {e}")
        print("💡 提示: 请设置环境变量 CODEREPO_API_KEY 和 CODEREPO_BASE_URL")
    
    # 1.2 从配置文件加载配置
    print("\n1.2 从配置文件加载配置...")
    
    # 创建示例配置文件
    config_file = "./config_example.json"
    if not os.path.exists(config_file):
        example_config = get_config_template("development")
        # 更新配置
        example_config.embedding.api_key = "your-api-key-here"
        example_config.embedding.base_url = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
        example_config.storage.base_path = "./storage_example"
        
        from coderepoindex.config import save_config
        save_config(config_file)
        print(f"✅ 创建示例配置文件: {config_file}")
    
    try:
        # 从文件加载配置
        config = load_config(config_path=config_file)
        print(f"✅ 从文件加载配置成功: {config_file}")
    except Exception as e:
        print(f"❌ 从文件加载配置失败: {e}")
    
    # ============================================================================
    # 方式2: 直接传递配置参数
    # ============================================================================
    print("\n📋 方式2: 直接传递配置参数")
    print("-" * 30)
    
    try:
        # 2.1 直接传递API配置
        print("2.1 直接传递API配置...")
        
        # 在实际使用中，请替换为您的真实API密钥和基础URL
        api_key = os.getenv("CODEREPO_API_KEY", "your-api-key-here")
        base_url = os.getenv("CODEREPO_BASE_URL", "https://dashscope-intl.aliyuncs.com/compatible-mode/v1")
        
        indexer = CodeIndexer(
            api_key=api_key,
            base_url=base_url,
            storage_backend="local",
            vector_backend="memory",
            storage_path="./storage_direct"
        )
        
        searcher = CodeSearcher(
            api_key=api_key,
            base_url=base_url,
            storage_backend="local",
            vector_backend="memory",
            storage_path="./storage_direct"
        )
        
        print("✅ 直接配置API参数创建成功")
        
    except Exception as e:
        print(f"❌ 直接配置失败: {e}")
    
    # ============================================================================
    # 方式3: 使用配置模板
    # ============================================================================
    print("\n📋 方式3: 使用配置模板")
    print("-" * 30)
    
    try:
        # 3.1 使用开发模板
        print("3.1 使用开发模板...")
        dev_config = get_config_template("development")
        
        # 更新API配置
        dev_config.embedding.api_key = os.getenv("CODEREPO_API_KEY", "your-api-key-here")
        dev_config.embedding.base_url = os.getenv("CODEREPO_BASE_URL", "https://dashscope-intl.aliyuncs.com/compatible-mode/v1")
        
        indexer = CodeIndexer(config=dev_config)
        searcher = CodeSearcher(config=dev_config)
        
        print("✅ 使用开发模板创建成功")
        print(f"   - 日志级别: {dev_config.log_level}")
        print(f"   - 存储路径: {dev_config.storage.base_path}")
        print(f"   - 批处理大小: {dev_config.embedding.batch_size}")
        
        # 3.2 使用生产模板
        print("\n3.2 使用生产模板...")
        prod_config = get_config_template("production")
        prod_config.embedding.api_key = os.getenv("CODEREPO_API_KEY", "your-api-key-here")
        prod_config.embedding.base_url = os.getenv("CODEREPO_BASE_URL", "https://dashscope-intl.aliyuncs.com/compatible-mode/v1")
        
        print("✅ 生产模板配置:")
        print(f"   - 日志级别: {prod_config.log_level}")
        print(f"   - 向量后端: {prod_config.storage.vector_backend}")
        print(f"   - 缓存大小: {prod_config.storage.cache_size}")
        print(f"   - 批处理大小: {prod_config.embedding.batch_size}")
        
    except Exception as e:
        print(f"❌ 配置模板使用失败: {e}")
    
    # ============================================================================
    # 方式4: 动态配置更新
    # ============================================================================
    print("\n📋 方式4: 动态配置更新")
    print("-" * 30)
    
    try:
        # 4.1 在运行时更新配置
        print("4.1 在运行时更新配置...")
        
        from coderepoindex.config import update_config, get_current_config
        
        # 更新全局配置
        update_config(
            api_key=os.getenv("CODEREPO_API_KEY", "your-api-key-here"),
            base_url=os.getenv("CODEREPO_BASE_URL", "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"),
            storage_backend="local",
            vector_backend="memory"
        )
        
        # 获取更新后的配置
        current_config = get_current_config()
        if current_config:
            print("✅ 配置更新成功")
            print(f"   - API Key: {'***' + current_config.embedding.api_key[-8:] if current_config.embedding.api_key else 'None'}")
            print(f"   - Base URL: {current_config.embedding.base_url}")
        
    except Exception as e:
        print(f"❌ 动态配置更新失败: {e}")
    
    # ============================================================================
    # 实际使用示例: 索引和搜索
    # ============================================================================
    print("\n📋 实际使用示例: 索引和搜索")
    print("-" * 30)
    
    if os.getenv("CODEREPO_API_KEY"):
        try:
            print("5.1 创建索引器和搜索器...")
            
            # 使用环境变量配置
            config = load_config(
                api_key=os.getenv("CODEREPO_API_KEY"),
                base_url=os.getenv("CODEREPO_BASE_URL", "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"),
                storage_backend="local",
                vector_backend="memory",
                storage_base_path="./storage_demo"
            )
            
            indexer = CodeIndexer(config=config)
            searcher = CodeSearcher(config=config)
            
            print("✅ 索引器和搜索器创建成功")
            
            # 5.2 创建仓库索引
            print("\n5.2 创建仓库索引...")
            
            # 使用当前目录作为示例仓库
            repo_config = create_local_config(".")
            
            # 模拟索引创建（实际使用中会执行完整的索引流程）
            print("📚 准备为当前目录创建索引...")
            print("   注意: 这是演示，实际使用时会调用 indexer.index_repository(repo_config)")
            
            # stats = indexer.index_repository(repo_config)
            # print(f"✅ 索引创建完成: {stats}")
            
            # 5.3 执行搜索
            print("\n5.3 执行搜索...")
            
            search_queries = [
                "配置管理和API密钥",
                "代码索引和向量存储",
                "搜索算法实现"
            ]
            
            for query in search_queries:
                print(f"🔍 搜索: '{query}'")
                
                # 模拟搜索（实际使用中会执行真实搜索）
                print("   注意: 这是演示，实际使用时会调用 searcher.search(query)")
                
                # results = searcher.search(query, top_k=3)
                # if results:
                #     for i, result in enumerate(results, 1):
                #         print(f"  {i}. {result.file_path} (相似度: {result.similarity_score:.3f})")
                # else:
                #     print("  😔 没有找到相关结果")
            
        except Exception as e:
            print(f"❌ 实际使用示例失败: {e}")
    else:
        print("⚠️  跳过实际使用示例 - 请设置 CODEREPO_API_KEY 环境变量")
    
    # ============================================================================
    # 配置最佳实践
    # ============================================================================
    print("\n📋 配置最佳实践")
    print("-" * 30)
    
    print("""
🔧 配置最佳实践:

1. 环境变量配置 (推荐):
   export CODEREPO_API_KEY="your-api-key"
   export CODEREPO_BASE_URL="https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
   export CODEREPO_STORAGE_PATH="./storage"
   export CODEREPO_LOG_LEVEL="INFO"

2. 配置文件 (适合复杂配置):
   创建 config.json 或 config.yaml 文件
   使用 load_config("config.json") 加载

3. 配置模板 (适合不同环境):
   - development: 开发环境，调试日志，内存向量存储
   - production: 生产环境，警告日志，ChromaDB向量存储
   - minimal: 最小配置，错误日志，基础功能

4. 安全考虑:
   - 不要在代码中硬编码API密钥
   - 使用环境变量或安全的配置文件
   - 在版本控制中排除配置文件

5. 性能优化:
   - 根据数据量选择合适的向量后端
   - 调整批处理大小以优化内存使用
   - 启用缓存以提高搜索性能
    """)
    
    print("\n🎉 示例完成！")
    print("\n💡 下一步:")
    print("1. 设置您的API密钥和基础URL")
    print("2. 选择合适的配置方式")
    print("3. 开始索引您的代码仓库")
    print("4. 享受强大的语义搜索功能！")


if __name__ == "__main__":
    main() 