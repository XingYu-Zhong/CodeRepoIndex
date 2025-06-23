# coding: utf-8
"""
代码解析器模块

提供基于 tree-sitter 的代码解析功能，支持多种编程语言的源代码分析。

主要功能：
- 解析源代码文件，提取函数、类、方法等代码结构
- 支持多种编程语言：Python、JavaScript、TypeScript、Java、Go、C/C++ 等
- 提供灵活的配置选项和预设模板
- 支持批量处理和缓存机制
- 提供详细的错误处理和日志记录

基本用法：
    from coderepoindex.parsers import CodeParser, parse_code_file
    
    # 使用便利函数
    result = parse_code_file("example.py")
    
    # 或者使用解析器类
    parser = CodeParser()
    result = parser.parse_file("example.py")
    
    # 查看解析结果
    for snippet in result.snippets:
        print(f"{snippet.type}: {snippet.name}")
"""

from .code_parser import (
    CodeParser,
    CodeSnippet, 
    ParseResult,
    SupportedLanguage,
    NodeType,
    ParserError,
    FileReadError,
    LanguageNotSupportedError,
    parse_code_file,
    get_file_language as get_file_language_from_parser
)

from .config import (
    ParserConfig,
    ConfigTemplates,
    DEFAULT_CONFIG,
    LANGUAGE_CONFIGS,
    get_language_config,
    is_file_ignored,
    get_file_language,
    should_parse_file
)

from .test_parser import ParserTester
from .logger_config import LoggerConfig, setup_parser_logging, log_performance, log_error_with_context

# 版本信息
__version__ = "1.0.0"

# 公开的API
__all__ = [
    # 核心类
    "CodeParser",
    "CodeSnippet",
    "ParseResult",
    "ParserConfig",
    
    # 枚举类
    "SupportedLanguage", 
    "NodeType",
    
    # 异常类
    "ParserError",
    "FileReadError", 
    "LanguageNotSupportedError",
    
    # 配置相关
    "ConfigTemplates",
    "DEFAULT_CONFIG",
    "LANGUAGE_CONFIGS",
    
    # 便利函数
    "parse_code_file",
    "get_file_language",
    "get_file_language_from_parser",
    "get_language_config",
    "is_file_ignored", 
    "should_parse_file",
    
    # 测试工具
    "ParserTester",
    
    # 日志配置
    "LoggerConfig",
    "setup_parser_logging",
    "log_performance",
    "log_error_with_context",
    
    # 版本
    "__version__"
]


# 便利函数的别名
def create_parser(config: ParserConfig = None) -> CodeParser:
    """
    创建代码解析器实例
    
    Args:
        config: 解析器配置，如果为None则使用默认配置
        
    Returns:
        CodeParser 实例
    """
    if config is None:
        config = DEFAULT_CONFIG
    
    # 注意：当前实现还未完全集成配置，这是一个占位符
    return CodeParser(max_cache_size=config.max_cache_size)


def parse_files(file_paths: list, config: ParserConfig = None) -> list:
    """
    批量解析多个文件
    
    Args:
        file_paths: 文件路径列表
        config: 解析器配置
        
    Returns:
        解析结果列表
    """
    parser = create_parser(config)
    return parser.parse_multiple_files(file_paths)


def get_supported_languages() -> list:
    """
    获取支持的编程语言列表
    
    Returns:
        支持的语言名称列表
    """
    return [lang.value for lang in SupportedLanguage]


def get_supported_extensions() -> list:
    """
    获取支持的文件扩展名列表
    
    Returns:
        支持的文件扩展名列表
    """
    return list(DEFAULT_CONFIG.language_extensions.keys())


# 模块级别的便利函数
def quick_parse(file_path: str, extract_comments: bool = True) -> ParseResult:
    """
    快速解析单个文件的便利函数
    
    Args:
        file_path: 文件路径
        extract_comments: 是否提取注释
        
    Returns:
        解析结果
    """
    if extract_comments:
        config = ConfigTemplates.detailed()
    else:
        config = ConfigTemplates.minimal()
    
    parser = create_parser(config)
    return parser.parse_file(file_path)


# 打印模块信息
def print_module_info():
    """打印模块信息"""
    print(f"CodeRepoIndex 代码解析器模块 v{__version__}")
    print("支持的编程语言:")
    for lang in get_supported_languages():
        print(f"  - {lang}")
    print("\n支持的文件扩展名:")
    extensions = get_supported_extensions()
    for i in range(0, len(extensions), 8):  # 每行8个
        print(f"  {', '.join(extensions[i:i+8])}")


if __name__ == "__main__":
    print_module_info()
