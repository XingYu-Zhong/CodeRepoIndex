#!/usr/bin/env python
"""
向量语义搜索功能演示

展示如何使用CodeSearcher进行纯向量语义搜索：
1. 基础自然语言搜索
2. 代码片段搜索 
3. 多语言搜索
4. 过滤条件搜索
5. 相似度阈值控制
6. 批量搜索对比
"""

import os
import sys
from typing import List

# 添加项目路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from coderepoindex.core import CodeSearcher, create_code_searcher
from coderepoindex.core.models import BlockType
from coderepoindex.config import load_config


def demo_basic_vector_search():
    """演示基础向量搜索"""
    print("\n" + "="*60)
    print("1. 基础向量语义搜索演示")
    print("="*60)
    
    # 创建搜索器
    config = load_config()
    searcher = create_code_searcher(config=config)
    
    # 自然语言查询示例
    natural_queries = [
        "如何处理文件上传",
        "数据库连接池配置",
        "错误处理和异常捕获", 
        "用户认证和授权",
        "How to parse JSON data"
    ]
    
    with searcher:
        for query in natural_queries:
            print(f"\n🔍 查询: {query}")
            try:
                results = searcher.search(
                    query=query,
                    top_k=3,
                    similarity_threshold=0.3
                )
                
                if results:
                    print(f"  找到 {len(results)} 个相关结果:")
                    for i, result in enumerate(results, 1):
                        print(f"    {i}. {result.block.file_path}:{result.block.line_start}")
                        print(f"       函数: {result.block.name}")
                        print(f"       相似度: {result.score:.4f}")
                        print(f"       语言: {result.block.language}")
                        print(f"       内容: {result.block.content[:60]}...")
                        print()
                else:
                    print("  未找到相关结果")
                    
            except Exception as e:
                print(f"  搜索失败: {e}")


def demo_code_snippet_search():
    """演示代码片段搜索"""
    print("\n" + "="*60)
    print("2. 代码片段语义搜索演示")
    print("="*60)
    
    config = load_config()
    searcher = create_code_searcher(config=config)
    
    # 代码片段查询示例
    code_queries = [
        "def upload_file(request):",
        "try:\n    # error handling",
        "class UserManager:",
        "SELECT * FROM users WHERE",
        "import requests\nresponse = requests.get"
    ]
    
    with searcher:
        for query in code_queries:
            print(f"\n🔍 代码查询: {repr(query)}")
            try:
                results = searcher.search(
                    query=query,
                    top_k=3,
                    similarity_threshold=0.25
                )
                
                if results:
                    print(f"  找到 {len(results)} 个语义相似的代码:")
                    for i, result in enumerate(results, 1):
                        print(f"    {i}. {result.block.file_path}:{result.block.line_start}")
                        print(f"       函数: {result.block.name}")
                        print(f"       相似度: {result.score:.4f}")
                        print(f"       代码预览:")
                        # 显示代码的前几行
                        code_lines = result.block.content.split('\n')[:3]
                        for line in code_lines:
                            print(f"         {line}")
                        print()
                else:
                    print("  未找到语义相似的代码")
                    
            except Exception as e:
                print(f"  代码搜索失败: {e}")


def demo_filtered_search():
    """演示过滤条件搜索"""
    print("\n" + "="*60)
    print("3. 过滤条件搜索演示")
    print("="*60)
    
    config = load_config()
    searcher = create_code_searcher(config=config)
    
    with searcher:
        # 1. 按编程语言过滤
        print("\n🔍 按编程语言过滤搜索:")
        languages = ["python", "javascript", "java"]
        query = "HTTP请求处理"
        
        for lang in languages:
            print(f"\n  {lang.upper()} 语言中的 '{query}':")
            try:
                results = searcher.search(
                    query=query,
                    language=lang,
                    top_k=2,
                    similarity_threshold=0.3
                )
                
                if results:
                    for result in results:
                        print(f"    - {result.block.file_path}: {result.block.name} ({result.score:.3f})")
                else:
                    print(f"    - 未找到{lang}相关代码")
                    
            except Exception as e:
                print(f"    - 搜索失败: {e}")
        
        # 2. 按代码块类型过滤
        print(f"\n🔍 按代码块类型过滤搜索:")
        block_types = [
            (BlockType.FUNCTION, "函数"),
            (BlockType.CLASS, "类"),
            (BlockType.METHOD, "方法")
        ]
        query = "数据验证"
        
        for block_type, type_name in block_types:
            print(f"\n  {type_name} 中的 '{query}':")
            try:
                results = searcher.search(
                    query=query,
                    block_type=block_type,
                    top_k=2,
                    similarity_threshold=0.3
                )
                
                if results:
                    for result in results:
                        print(f"    - {result.block.name} in {result.block.file_path} ({result.score:.3f})")
                else:
                    print(f"    - 未找到{type_name}相关代码")
                    
            except Exception as e:
                print(f"    - 搜索失败: {e}")
        
        # 3. 按文件路径过滤
        print(f"\n🔍 按文件路径过滤搜索:")
        path_patterns = [
            "*/models/*",
            "*/utils/*", 
            "*/api/*"
        ]
        query = "配置管理"
        
        for pattern in path_patterns:
            print(f"\n  {pattern} 路径中的 '{query}':")
            try:
                results = searcher.search(
                    query=query,
                    file_path=pattern,
                    top_k=2,
                    similarity_threshold=0.3
                )
                
                if results:
                    for result in results:
                        print(f"    - {result.block.file_path}: {result.block.name} ({result.score:.3f})")
                else:
                    print(f"    - 未找到{pattern}路径相关代码")
                    
            except Exception as e:
                print(f"    - 搜索失败: {e}")


def demo_similarity_threshold():
    """演示相似度阈值控制"""
    print("\n" + "="*60)
    print("4. 相似度阈值控制演示")
    print("="*60)
    
    config = load_config()
    searcher = create_code_searcher(config=config)
    
    query = "用户登录验证"
    thresholds = [0.1, 0.3, 0.5, 0.7]
    
    with searcher:
        print(f"🔍 查询: '{query}' - 不同相似度阈值对比")
        
        for threshold in thresholds:
            print(f"\n  相似度阈值 >= {threshold}:")
            try:
                results = searcher.search(
                    query=query,
                    top_k=5,
                    similarity_threshold=threshold
                )
                
                print(f"    结果数量: {len(results)}")
                if results:
                    print(f"    分数范围: {min(r.score for r in results):.3f} - {max(r.score for r in results):.3f}")
                    # 显示前2个结果
                    for i, result in enumerate(results[:2], 1):
                        print(f"      {i}. {result.block.name} ({result.score:.3f})")
                else:
                    print("    无结果")
                    
            except Exception as e:
                print(f"    搜索失败: {e}")


def demo_multi_repository_search():
    """演示多仓库搜索对比"""
    print("\n" + "="*60)
    print("5. 多仓库搜索对比演示")
    print("="*60)
    
    config = load_config()
    searcher = create_code_searcher(config=config)
    
    query = "文件处理"
    
    with searcher:
        print(f"🔍 查询: '{query}' - 多仓库对比")
        
        # 首先获取所有仓库的结果
        print(f"\n  全局搜索:")
        try:
            all_results = searcher.search(
                query=query,
                top_k=10,
                similarity_threshold=0.3
            )
            
            if all_results:
                # 按仓库分组结果
                repo_results = {}
                for result in all_results:
                    repo_id = getattr(result.block, 'repository_id', 'unknown')
                    if repo_id not in repo_results:
                        repo_results[repo_id] = []
                    repo_results[repo_id].append(result)
                
                print(f"    找到 {len(all_results)} 个结果，涉及 {len(repo_results)} 个仓库")
                
                # 显示每个仓库的最佳结果
                for repo_id, results in repo_results.items():
                    best_result = max(results, key=lambda x: x.score)
                    print(f"    {repo_id}: {best_result.block.name} ({best_result.score:.3f})")
            else:
                print("    未找到结果")
                
        except Exception as e:
            print(f"    全局搜索失败: {e}")


def demo_batch_comparison():
    """演示批量搜索对比"""
    print("\n" + "="*60)
    print("6. 批量搜索对比演示")
    print("="*60)
    
    config = load_config()
    searcher = create_code_searcher(config=config)
    
    # 相关查询对比
    related_queries = [
        "文件上传",
        "file upload",
        "upload file to server",
        "处理上传的文件"
    ]
    
    with searcher:
        print("🔍 相关查询语义搜索对比:")
        
        all_query_results = {}
        
        for query in related_queries:
            print(f"\n  查询: '{query}'")
            try:
                results = searcher.search(
                    query=query,
                    top_k=3,
                    similarity_threshold=0.3
                )
                
                all_query_results[query] = results
                
                if results:
                    print(f"    结果数量: {len(results)}")
                    best_result = results[0]
                    print(f"    最佳匹配: {best_result.block.name} ({best_result.score:.3f})")
                else:
                    print("    无结果")
                    
            except Exception as e:
                print(f"    搜索失败: {e}")
        
        # 分析结果重叠度
        print(f"\n📊 结果重叠度分析:")
        query_list = list(related_queries)
        for i, query1 in enumerate(query_list):
            for query2 in query_list[i+1:]:
                results1 = all_query_results.get(query1, [])
                results2 = all_query_results.get(query2, [])
                
                if results1 and results2:
                    # 计算重叠的文件
                    files1 = {r.block.file_path for r in results1}
                    files2 = {r.block.file_path for r in results2}
                    overlap = len(files1 & files2)
                    total = len(files1 | files2)
                    
                    if total > 0:
                        overlap_percent = (overlap / total) * 100
                        print(f"  '{query1}' vs '{query2}': {overlap_percent:.1f}% 重叠")


def main():
    """主函数：运行所有演示"""
    print("🚀 CodeRepoIndex 向量语义搜索功能演示")
    print("=" * 60)
    
    try:
        # 检查配置
        config = load_config()
        print(f"✅ 配置加载成功")
        print(f"   Embedding模型: {config.embedding.model_name}")
        print(f"   存储路径: {config.storage.base_path}")
        
        # 运行各种演示
        demo_basic_vector_search()
        demo_code_snippet_search() 
        demo_filtered_search()
        demo_similarity_threshold()
        demo_multi_repository_search()
        demo_batch_comparison()
        
        print("\n" + "="*60)
        print("🎉 所有向量搜索演示完成!")
        print("="*60)
        
    except Exception as e:
        print(f"❌ 演示运行失败: {e}")
        print("\n💡 请确保:")
        print("   1. 已正确配置API密钥")
        print("   2. 已索引至少一个代码仓库")
        print("   3. embedding服务可正常访问")


if __name__ == "__main__":
    main() 