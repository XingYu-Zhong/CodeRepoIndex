#!/usr/bin/env python3
"""
目录解析器使用示例

演示如何使用 DirectoryParser 解析整个代码仓库目录
"""

import json
from pathlib import Path

from coderepoindex.parsers import (
    DirectoryParser,
    DirectoryConfig,
    create_directory_config,
    parse_directory,
    SnippetType
)

def demo_basic_directory_parsing():
    """演示基础目录解析功能"""
    print("\n=== 基础目录解析示例 ===")
    
    # 使用当前项目作为示例
    current_project = Path(__file__).parent.parent
    
    # 创建基础配置
    config = create_directory_config(
        chunk_size=256,  # 较小的切片用于演示
        max_depth=3,     # 限制深度避免递归太深
        only_extensions={'py', 'md', 'txt', 'yml', 'yaml', 'json'}  # 只处理这些类型
    )
    
    # 解析目录
    result = parse_directory(str(current_project), config)
    
    print(f"解析结果:")
    print(f"- 根目录: {result.root_path}")
    print(f"- 总文件数: {result.total_files}")
    print(f"- 已处理文件数: {result.processed_files}")
    print(f"- 代码文件数: {result.code_files}")
    print(f"- 文本文件数: {result.text_files}")
    print(f"- 跳过文件数: {result.skipped_files}")
    print(f"- 成功率: {result.success_rate:.2%}")
    print(f"- 生成片段数: {len(result.snippets)}")
    print(f"- 处理时间: {result.processing_time:.2f}s")
    
    # 显示不同类型的片段统计
    snippet_stats = {}
    for snippet in result.snippets:
        snippet_type = snippet.type
        snippet_stats[snippet_type] = snippet_stats.get(snippet_type, 0) + 1
    
    print(f"\n片段类型统计:")
    for snippet_type, count in snippet_stats.items():
        print(f"- {snippet_type}: {count}")
    
    # 显示一些示例片段
    print(f"\n示例片段:")
    for i, snippet in enumerate(result.snippets[:3]):
        print(f"片段 {i+1}:")
        print(f"  类型: {snippet.type}")
        print(f"  路径: {snippet.path}")
        print(f"  名称: {snippet.name}")
        print(f"  目录: {snippet.directory}")
        print(f"  文件名: {snippet.filename}")
        print(f"  文件类型: {snippet.file_type}")
        print(f"  代码长度: {len(snippet.code)}")
        if snippet.code:
            preview = snippet.code[:100] + "..." if len(snippet.code) > 100 else snippet.code
            print(f"  代码预览: {repr(preview)}")
        print()


def demo_custom_configuration():
    """演示自定义配置"""
    print("\n=== 自定义配置示例 ===")
    
    # 创建自定义配置
    config = DirectoryConfig()
    config.chunk_size = 1024  # 更大的切片
    config.max_depth = 2      # 较浅的递归
    config.max_files = 50     # 限制文件数量
    
    # 添加自定义忽略模式
    config.ignore_patterns.extend([
        'test_*',           # 忽略测试文件
        '*.pyc',           # 忽略编译文件
        '__pycache__',     # 忽略缓存目录
    ])
    
    # 只处理文档和配置文件
    config.only_extensions = {'md', 'txt', 'yml', 'yaml', 'json', 'toml'}
    
    # 配置文本处理选项
    config.extract_text_files = True
    config.extract_config_files = True
    config.extract_documentation = True
    config.record_binary_files = False
    
    # 解析目录
    current_project = Path(__file__).parent.parent
    parser = DirectoryParser(config)
    result = parser.parse_directory(str(current_project))
    
    print(f"自定义配置解析结果:")
    print(f"- 处理文件数: {result.processed_files}")
    print(f"- 生成片段数: {len(result.snippets)}")
    
    # 显示配置文件和文档的片段
    config_snippets = [s for s in result.snippets if s.type == SnippetType.CONFIG_FILE.value]
    doc_snippets = [s for s in result.snippets if s.type == SnippetType.DOCUMENTATION.value]
    
    print(f"- 配置文件片段: {len(config_snippets)}")
    print(f"- 文档片段: {len(doc_snippets)}")
    
    if config_snippets:
        print(f"\n配置文件示例:")
        snippet = config_snippets[0]
        print(f"  文件: {snippet.path}")
        print(f"  内容预览: {snippet.code[:200]}...")


def demo_filtering_and_chunking():
    """演示过滤和切片功能"""
    print("\n=== 过滤和切片功能示例 ===")
    
    config = DirectoryConfig()
    config.chunk_size = 200    # 小切片用于演示
    config.chunk_overlap = 20  # 重叠区域
    config.min_chunk_size = 50 # 最小切片大小
    
    # 只处理 README 文件
    config.only_extensions = {'md'}
    
    current_project = Path(__file__).parent.parent
    result = parse_directory(str(current_project), config)
    
    print(f"过滤结果:")
    print(f"- 处理文件数: {result.processed_files}")
    print(f"- 生成片段数: {len(result.snippets)}")
    
    # 查找 README 文件的切片
    readme_snippets = [s for s in result.snippets if 'readme' in s.filename.lower()]
    
    if readme_snippets:
        print(f"\nREADME 文件切片示例:")
        for i, snippet in enumerate(readme_snippets[:2]):
            print(f"切片 {i+1}:")
            print(f"  文件: {snippet.path}")
            print(f"  切片索引: {snippet.metadata.get('chunk_index', 0)}")
            print(f"  切片大小: {snippet.metadata.get('chunk_size', 0)}")
            print(f"  内容: {snippet.code[:150]}...")
            print()


def demo_directory_structure():
    """演示目录结构功能"""
    print("\n=== 目录结构示例 ===")
    
    config = DirectoryConfig()
    config.max_depth = 2
    config.include_directory_structure = True
    config.only_extensions = {'py'}  # 只看 Python 文件
    
    current_project = Path(__file__).parent.parent
    result = parse_directory(str(current_project), config)
    
    print(f"目录结构信息:")
    if result.directory_structure:
        def print_tree(node, indent=0):
            prefix = "  " * indent
            if node['type'] == 'directory':
                print(f"{prefix}📁 {node['name']}/")
                for child in node.get('children', []):
                    print_tree(child, indent + 1)
            else:
                size = node.get('size', 0)
                ext = node.get('extension', '')
                print(f"{prefix}📄 {node['name']} ({size} bytes, .{ext})")
        
        print_tree(result.directory_structure)


def demo_error_handling():
    """演示错误处理"""
    print("\n=== 错误处理示例 ===")
    
    try:
        # 尝试解析不存在的目录
        result = parse_directory("/nonexistent/directory")
    except ValueError as e:
        print(f"预期的错误: {e}")
    
    # 解析存在的目录但可能有权限问题
    config = DirectoryConfig()
    config.max_files = 5  # 限制文件数量避免过多输出
    
    current_project = Path(__file__).parent.parent
    result = parse_directory(str(current_project), config)
    
    if result.errors:
        print(f"解析过程中的错误:")
        for error in result.errors[:3]:  # 只显示前3个错误
            print(f"  - {error}")
    else:
        print("没有发现错误")


def main():
    """运行所有示例"""
    print("CodeRepoIndex 目录解析器示例")
    print("=" * 50)
    
    demo_basic_directory_parsing()
    demo_custom_configuration()
    demo_filtering_and_chunking()
    demo_directory_structure()
    demo_error_handling()
    
    print("\n演示完成！")


if __name__ == "__main__":
    main() 