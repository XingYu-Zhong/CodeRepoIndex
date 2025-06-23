# coding: utf-8
"""
解析器配置模块

定义解析器相关的配置项和常量。
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set
from pathlib import Path
from loguru import logger


@dataclass
class ParserConfig:
    """解析器配置类"""
    
    # 文件大小限制 (bytes)
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    
    # 解析器缓存大小
    max_cache_size: int = 128
    
    # 编码检测相关
    encoding_confidence_threshold: float = 0.7
    default_encoding: str = 'utf-8'
    fallback_encoding: str = 'gbk'
    
    # 性能相关
    enable_timing: bool = True
    enable_caching: bool = True
    max_recursion_depth: int = 100
    
    # 日志相关
    log_level: str = "INFO"
    enable_debug_logging: bool = False
    
    # 解析选项
    extract_comments: bool = True
    extract_docstrings: bool = True
    extract_imports: bool = False
    extract_variables: bool = False
    
    # 过滤选项
    min_function_lines: int = 1
    max_function_lines: int = 1000
    ignore_private_methods: bool = False
    ignore_test_files: bool = False
    
    # 关键词提取
    extract_chinese_keywords: bool = True
    extract_english_keywords: bool = True
    min_keyword_length: int = 2
    max_keywords_per_snippet: int = 50
    
    # 特殊文件处理
    special_file_patterns: Dict[str, str] = field(default_factory=lambda: {
        'GMCommandData.py': 'gm_command',
        '*.config.js': 'config',
        '*.test.py': 'test',
        '*.spec.py': 'test'
    })
    
    # 忽略的文件模式
    ignore_patterns: List[str] = field(default_factory=lambda: [
        '__pycache__',
        '*.pyc',
        '.git',
        'node_modules',
        '.DS_Store',
        '*.min.js',
        '*.min.css'
    ])
    
    # 支持的文件扩展名和对应的语言
    language_extensions: Dict[str, str] = field(default_factory=lambda: {
        'py': 'python',
        'java': 'java',
        'js': 'javascript',
        'jsx': 'javascript',
        'ts': 'typescript',
        'tsx': 'typescript',
        'go': 'go',
        'c': 'c',
        'h': 'c',
        'cc': 'cpp',
        'cpp': 'cpp',
        'cxx': 'cpp',
        'hpp': 'cpp',
        'kt': 'kotlin',
        'kts': 'kotlin',
        'lua': 'lua',
        'rs': 'rust',
        'php': 'php',
        'rb': 'ruby',
        'swift': 'swift',
        'scala': 'scala',
        'cs': 'csharp'
    })


# 默认配置实例
DEFAULT_CONFIG = ParserConfig()


# 语言特定的配置
LANGUAGE_CONFIGS = {
    'python': {
        'function_node_types': ['function_definition', 'method_definition', 'async_function_definition'],
        'class_node_types': ['class_definition'],
        'comment_node_types': ['comment'],
        'docstring_patterns': [r'""".*?"""', r"'''.*?'''"],
        'import_node_types': ['import_statement', 'import_from_statement']
    },
    'javascript': {
        'function_node_types': ['function_declaration', 'method_definition', 'arrow_function', 'function_expression'],
        'class_node_types': ['class_declaration'],
        'comment_node_types': ['comment'],
        'import_node_types': ['import_statement', 'export_statement']
    },
    'typescript': {
        'function_node_types': ['function_declaration', 'method_definition', 'arrow_function', 'function_expression'],
        'class_node_types': ['class_declaration', 'interface_declaration', 'type_alias_declaration'],
        'comment_node_types': ['comment'],
        'import_node_types': ['import_statement', 'export_statement']
    },
    'java': {
        'function_node_types': ['method_declaration', 'constructor_declaration'],
        'class_node_types': ['class_declaration', 'interface_declaration', 'enum_declaration'],
        'comment_node_types': ['line_comment', 'block_comment'],
        'import_node_types': ['import_declaration']
    },
    'go': {
        'function_node_types': ['function_declaration', 'method_declaration'],
        'class_node_types': ['type_declaration'],
        'comment_node_types': ['comment'],
        'import_node_types': ['import_declaration']
    },
    'c': {
        'function_node_types': ['function_definition', 'function_declarator'],
        'class_node_types': ['struct_specifier'],
        'comment_node_types': ['comment']
    },
    'cpp': {
        'function_node_types': ['function_definition', 'function_declarator'],
        'class_node_types': ['class_specifier', 'struct_specifier'],
        'comment_node_types': ['comment']
    }
}


def get_language_config(language: str) -> Dict:
    """
    获取特定语言的配置
    
    Args:
        language: 编程语言名称
        
    Returns:
        语言特定的配置字典
    """
    config = LANGUAGE_CONFIGS.get(language, {})
    if config:
        logger.debug(f"加载语言配置: {language}")
    else:
        logger.warning(f"未找到语言配置: {language}")
    return config


def is_file_ignored(file_path: Path, config: ParserConfig = None) -> bool:
    """
    检查文件是否应该被忽略
    
    Args:
        file_path: 文件路径
        config: 解析器配置
        
    Returns:
        是否应该忽略该文件
    """
    if config is None:
        config = DEFAULT_CONFIG
    
    file_str = str(file_path)
    
    for pattern in config.ignore_patterns:
        if pattern in file_str:
            return True
    
    return False


def get_file_language(file_path: Path, config: ParserConfig = None) -> str:
    """
    根据文件扩展名获取编程语言
    
    Args:
        file_path: 文件路径
        config: 解析器配置
        
    Returns:
        编程语言名称或空字符串
    """
    if config is None:
        config = DEFAULT_CONFIG
    
    suffix = file_path.suffix[1:].lower() if file_path.suffix else ""
    return config.language_extensions.get(suffix, "")


def should_parse_file(file_path: Path, config: ParserConfig = None) -> bool:
    """
    判断文件是否应该被解析
    
    Args:
        file_path: 文件路径
        config: 解析器配置
        
    Returns:
        是否应该解析该文件
    """
    if config is None:
        config = DEFAULT_CONFIG
    
    # 检查是否被忽略
    if is_file_ignored(file_path, config):
        return False
    
    # 检查是否支持该语言
    language = get_file_language(file_path, config)
    if not language:
        return False
    
    # 检查文件大小
    try:
        if file_path.stat().st_size > config.max_file_size:
            return False
    except OSError:
        return False
    
    return True


# 预定义的配置模板
class ConfigTemplates:
    """预定义的配置模板"""
    
    @staticmethod
    def minimal() -> ParserConfig:
        """最小配置：只解析基本的函数和类"""
        logger.debug("创建最小配置模板")
        return ParserConfig(
            extract_comments=False,
            extract_docstrings=False,
            extract_imports=False,
            extract_variables=False,
            enable_debug_logging=False
        )
    
    @staticmethod
    def performance() -> ParserConfig:
        """性能优化配置：适用于大型代码库"""
        logger.debug("创建性能优化配置模板")
        return ParserConfig(
            max_cache_size=256,
            enable_timing=False,
            max_function_lines=500,
            ignore_test_files=True,
            max_keywords_per_snippet=20
        )
    
    @staticmethod
    def detailed() -> ParserConfig:
        """详细配置：提取所有可能的信息"""
        logger.debug("创建详细配置模板")
        return ParserConfig(
            extract_comments=True,
            extract_docstrings=True,
            extract_imports=True,
            extract_variables=True,
            enable_debug_logging=True,
            min_function_lines=0,
            max_keywords_per_snippet=100
        )
    
    @staticmethod
    def chinese_optimized() -> ParserConfig:
        """中文优化配置：针对中文项目优化"""
        logger.debug("创建中文优化配置模板")
        return ParserConfig(
            extract_chinese_keywords=True,
            extract_english_keywords=True,
            fallback_encoding='gbk',
            encoding_confidence_threshold=0.6
        ) 