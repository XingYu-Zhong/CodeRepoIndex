"""
CodeRepoIndex 基本使用示例

演示如何使用 CodeRepoIndex 进行代码仓库索引和搜索，
包括新的分离式配置方式。
"""

import os
from pathlib import Path

# 导入核心模块
from coderepoindex.core import CodeIndexer, CodeSearcher
from coderepoindex.config import load_config, ConfigManager


def main():
    """主函数：演示各种配置和使用方式"""
    
    print("=== CodeRepoIndex 基本使用示例 ===\n")
    
    # ========== 配置方式演示 ==========
    print("1. 配置方式演示:")
    
    # 方式1: 使用环境变量配置（推荐用于生产环境）
    print("\n方式1: 环境变量配置")
    os.environ['CODEREPO_LLM_API_KEY'] = 'your-llm-api-key'
    os.environ['CODEREPO_LLM_BASE_URL'] = 'https://dashscope.aliyuncs.com/compatible-mode/v1'
    os.environ['CODEREPO_LLM_MODEL'] = 'qwen-plus'
    
    os.environ['CODEREPO_EMBEDDING_API_KEY'] = 'your-embedding-api-key'
    os.environ['CODEREPO_EMBEDDING_BASE_URL'] = 'https://dashscope.aliyuncs.com/compatible-mode/v1'
    os.environ['CODEREPO_EMBEDDING_MODEL'] = 'text-embedding-v3'
    
    config1 = load_config()
    print(f"  LLM配置: {config1.llm.model_name} @ {config1.llm.base_url}")
    print(f"  Embedding配置: {config1.embedding.model_name} @ {config1.embedding.base_url}")
    
    # 方式2: 使用配置文件
    print("\n方式2: 配置文件")
    config2 = load_config("config_example.json")
    print(f"  项目名称: {config2.project_name}")
    print(f"  LLM模型: {config2.llm.model_name}")
    print(f"  Embedding模型: {config2.embedding.model_name}")
    
    # 方式3: 使用字典配置
    print("\n方式3: 字典配置")
    config_dict = {
        "llm": {
            "api_key": "your-llm-key",
            "base_url": "https://api.openai.com/v1",
            "model_name": "gpt-4"
        },
        "embedding": {
            "api_key": "your-embedding-key", 
            "base_url": "https://api.openai.com/v1",
            "model_name": "text-embedding-ada-002"
        },
        "storage": {
            "base_path": "./custom_storage"
        }
    }
    config3 = load_config(config_dict=config_dict)
    print(f"  LLM: {config3.llm.model_name}")
    print(f"  Embedding: {config3.embedding.model_name}")
    print(f"  存储路径: {config3.storage.base_path}")
    
    # 方式4: 直接传参（最高优先级）
    print("\n方式4: 直接传参")
    config4 = load_config(
        llm_api_key="direct-llm-key",
        llm_model_name="qwen-turbo",
        embedding_api_key="direct-embedding-key", 
        embedding_model_name="text-embedding-v2"
    )
    print(f"  LLM密钥: {config4.llm.api_key}")
    print(f"  Embedding密钥: {config4.embedding.api_key}")
    
    # 方式5: 兼容性配置（统一API key）
    print("\n方式5: 兼容性配置")
    config5 = load_config(
        api_key="unified-api-key",
        base_url="https://unified-api.example.com"
    )
    print(f"  LLM API Key: {config5.llm.api_key}")
    print(f"  Embedding API Key: {config5.embedding.api_key}")
    print(f"  LLM Base URL: {config5.llm.base_url}")
    print(f"  Embedding Base URL: {config5.embedding.base_url}")
    
    # ========== 索引功能演示 ==========
    print("\n\n2. 索引功能演示:")
    
    # 创建索引器
    indexer = CodeIndexer()
    
    # 索引本地代码仓库
    repo_path = "./test_repo"  # 替换为实际的仓库路径
    
    print(f"\n正在索引仓库: {repo_path}")
    try:
        # 执行索引
        index_result = indexer.index_repository(
            repo_path,
            include_patterns=["*.py", "*.js", "*.ts"],
            exclude_patterns=["*.pyc", "node_modules/*"]
        )
        
        print(f"索引完成!")
        print(f"  - 总文件数: {index_result.total_files}")
        print(f"  - 代码块数: {index_result.total_blocks}")
        print(f"  - 索引大小: {index_result.index_size_mb:.2f} MB")
        print(f"  - 耗时: {index_result.duration:.2f} 秒")
        
    except Exception as e:
        print(f"索引失败: {e}")
        print("注意: 请确保目标仓库路径存在且包含代码文件")
    
    # ========== 搜索功能演示 ==========
    print("\n\n3. 向量语义搜索演示:")
    
    # 创建搜索器
    searcher = CodeSearcher()
    
    # 搜索示例
    search_queries = [
        "函数定义",
        "异常处理", 
        "数据库连接",
        "API接口",
        "配置管理"
    ]
    
    with searcher:
        for query in search_queries:
            print(f"\n搜索: '{query}'")
            try:
                results = searcher.search(
                    query=query,
                    top_k=3,
                    similarity_threshold=0.3
                )
                
                if results:
                    print(f"  找到 {len(results)} 个相关结果:")
                    for i, result in enumerate(results[:2], 1):
                        print(f"    {i}. {result.block.file_path}:{result.block.line_start}")
                        print(f"       相似度: {result.score:.3f}")
                        print(f"       类型: {result.block.block_type}")
                        print(f"       函数: {result.block.name}")
                else:
                    print("  未找到相关结果")
                    
            except Exception as e:
                print(f"  搜索失败: {e}")
    
    # ========== 高级过滤搜索演示 ==========
    print("\n\n4. 高级过滤搜索演示:")
    
    # 语言过滤搜索
    print("\n按语言过滤搜索:")
    with searcher:
        try:
            results = searcher.search(
                query="错误处理",
                top_k=5,
                language="python",
                similarity_threshold=0.4
            )
            print(f"  Python错误处理结果: {len(results)} 个")
            for result in results[:2]:
                print(f"    - {result.block.file_path}: {result.block.name} (分数: {result.score:.3f})")
            
        except Exception as e:
            print(f"  语言过滤搜索失败: {e}")
    
    # 代码块类型过滤搜索
    print("\n按代码块类型过滤搜索:")
    with searcher:
        try:
            from coderepoindex.core.models import BlockType
            results = searcher.search(
                query="数据处理",
                top_k=5,
                block_type=BlockType.FUNCTION,
                similarity_threshold=0.3
            )
            print(f"  函数级搜索结果: {len(results)} 个")
            for result in results[:2]:
                print(f"    - {result.block.file_path}: {result.block.name} (分数: {result.score:.3f})")
                
        except Exception as e:
            print(f"  类型过滤搜索失败: {e}")
    
    # ========== 配置管理演示 ==========
    print("\n\n5. 配置管理演示:")
    
    # 获取配置管理器
    config_manager = ConfigManager()
    current_config = config_manager.get_config()
    
    if current_config:
        print(f"当前配置:")
        print(f"  - 项目: {current_config.project_name}")
        print(f"  - LLM模型: {current_config.llm.model_name}")
        print(f"  - Embedding模型: {current_config.embedding.model_name}")
        print(f"  - 存储后端: {current_config.storage.storage_backend}")
        print(f"  - 向量后端: {current_config.storage.vector_backend}")
    
    # 动态更新配置
    print("\n动态更新配置:")
    config_manager.update_config(
        log_level="DEBUG",
        storage_cache_size=2000
    )
    updated_config = config_manager.get_config()
    print(f"  - 日志级别: {updated_config.log_level}")
    print(f"  - 缓存大小: {updated_config.storage.cache_size}")
    
    print("\n=== 示例完成 ===")


if __name__ == "__main__":
    # 运行示例
    main() 