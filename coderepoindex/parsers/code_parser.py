# coding: utf-8
"""
代码解析器模块

使用 tree-sitter 解析源代码文件，提取类、函数等代码结构。
支持多种编程语言，包括 Python、JavaScript、TypeScript、Go、Java 等。
"""

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Tuple, Union, Callable
from enum import Enum
import threading
from functools import lru_cache, wraps
import time

# 第三方库
import chardet
from tree_sitter import Language, Node, Parser as TreeSitterParser
from loguru import logger

try:
    from tree_sitter_languages import get_language
except ImportError:
    logger.warning("tree_sitter_languages not available, falling back to manual language loading")
    get_language = None


class NodeType(Enum):
    """AST 节点类型枚举"""
    FUNCTION = "function"
    METHOD = "method"
    CLASS = "class"
    INTERFACE = "interface"
    COMMENT = "comment"
    IMPORT = "import"
    VARIABLE = "variable"


class SupportedLanguage(Enum):
    """支持的编程语言"""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    GO = "go"
    JAVA = "java"
    C = "c"
    CPP = "cpp"
    KOTLIN = "kotlin"
    LUA = "lua"


# 语言映射配置
LANGUAGE_MAPPING: Dict[str, SupportedLanguage] = {
    'py': SupportedLanguage.PYTHON,
    'java': SupportedLanguage.JAVA,
    'js': SupportedLanguage.JAVASCRIPT,
    'jsx': SupportedLanguage.JAVASCRIPT,
    'ts': SupportedLanguage.TYPESCRIPT,
    'tsx': SupportedLanguage.TYPESCRIPT,
    'go': SupportedLanguage.GO,
    'c': SupportedLanguage.C,
    'h': SupportedLanguage.C,
    'cc': SupportedLanguage.CPP,
    'cpp': SupportedLanguage.CPP,
    'cxx': SupportedLanguage.CPP,
    'kt': SupportedLanguage.KOTLIN,
    'lua': SupportedLanguage.LUA,
}

# 文件大小限制 (10MB)
MAX_FILE_SIZE = 10 * 1024 * 1024


@dataclass
class CodeSnippet:
    """代码片段数据结构"""
    type: str
    path: str
    name: str
    code: str
    md5: str
    func_name: str = ""
    args: str = ""
    class_name: str = ""
    comment: str = ""
    key_msg: str = ""
    line_start: int = 0
    line_end: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """后处理，计算 MD5 如果未提供"""
        if not self.md5:
            self.md5 = self._calculate_md5()

    def _calculate_md5(self) -> str:
        """计算代码片段的 MD5 哈希值"""
        content = f"{self.path}{self.class_name}{self.code}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()


@dataclass
class ParseResult:
    """解析结果数据结构"""
    language: Optional[SupportedLanguage]
    file_path: str
    snippets: List[CodeSnippet] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    processing_time: float = 0.0

    @property
    def is_successful(self) -> bool:
        """判断解析是否成功"""
        return self.language is not None and not self.errors

    @property
    def suffix(self) -> str:
        """获取文件后缀"""
        return Path(self.file_path).suffix[1:] if Path(self.file_path).suffix else ""


class ParserError(Exception):
    """解析器异常类"""
    pass


class FileReadError(ParserError):
    """文件读取异常"""
    pass


class LanguageNotSupportedError(ParserError):
    """语言不支持异常"""
    pass


def timing_decorator(func: Callable) -> Callable:
    """计时装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        # 如果返回结果是 ParseResult，则设置处理时间
        if isinstance(result, ParseResult):
            result.processing_time = end_time - start_time
            
        logger.debug(f"{func.__name__} 执行时间: {end_time - start_time:.4f}s")
        return result
    return wrapper


class CodeParser:
    """
    代码解析器主类
    
    使用 tree-sitter 解析源代码文件，提取代码结构信息。
    支持多种编程语言，提供缓存机制以提高性能。
    """

    def __init__(self, max_cache_size: int = 128):
        """
        初始化解析器
        
        Args:
            max_cache_size: 解析器缓存的最大大小
        """
        self._parsers: Dict[SupportedLanguage, TreeSitterParser] = {}
        self._parser_lock = threading.Lock()
        self._max_cache_size = max_cache_size
        
        # 设置日志
        logger.info(f"初始化代码解析器，缓存大小: {max_cache_size}")
        logger.debug(f"支持的语言: {[lang.value for lang in SupportedLanguage]}")

    @lru_cache(maxsize=128)
    def _get_parser(self, language: SupportedLanguage) -> Optional[TreeSitterParser]:
        """
        获取或创建指定语言的 tree-sitter 解析器
        
        Args:
            language: 目标编程语言
            
        Returns:
            TreeSitterParser 实例或 None
        """
        with self._parser_lock:
            if language not in self._parsers:
                try:
                    if get_language is None:
                        logger.error(f"tree_sitter_languages 不可用，无法创建 {language.value} 解析器")
                        logger.info("请安装: pip install tree-sitter-languages")
                        return None
                        
                    logger.debug(f"正在获取 {language.value} 语言定义...")
                    tree_sitter_lang = get_language(language.value)
                    logger.debug(f"语言定义类型: {type(tree_sitter_lang)}")
                    
                    parser = TreeSitterParser()
                    parser.set_language(tree_sitter_lang)
                    self._parsers[language] = parser
                    logger.debug(f"成功创建 {language.value} 语言解析器")
                    
                except Exception as e:
                    logger.error(f"创建 {language.value} 解析器失败: {e}")
                    logger.debug(f"错误详情: {type(e).__name__}: {e}")
                    
                    # 提供安装建议
                    if "tree_sitter_languages" in str(e) or "get_language" in str(e):
                        logger.info("建议安装: pip install tree-sitter-languages")
                    elif "Language" in str(e):
                        logger.info("tree-sitter 版本可能不兼容，建议检查版本")
                    
                    return None
                    
            return self._parsers[language]

    def _detect_language(self, file_path: Path) -> Optional[SupportedLanguage]:
        """
        根据文件扩展名检测编程语言
        
        Args:
            file_path: 文件路径
            
        Returns:
            检测到的语言或 None
        """
        suffix = file_path.suffix[1:].lower() if file_path.suffix else ""
        return LANGUAGE_MAPPING.get(suffix)

    def _read_file_safely(self, file_path: Path) -> Tuple[Optional[bytes], Optional[str]]:
        """
        安全地读取文件内容
        
        Args:
            file_path: 文件路径
            
        Returns:
            (原始字节, 解码后的字符串) 或 (None, None)
        """
        logger.debug(f"开始读取文件: {file_path}")
        
        try:
            file_size = file_path.stat().st_size
            logger.debug(f"文件大小: {file_size} bytes")
            
            # 检查文件大小
            if file_size > MAX_FILE_SIZE:
                logger.warning(f"文件 {file_path} 过大 ({file_size} bytes)，跳过解析")
                return None, None
                
            with file_path.open('rb') as f:
                raw_bytes = f.read()
                
            logger.debug(f"成功读取文件: {file_path}, 大小: {len(raw_bytes)} bytes")
                
        except (IOError, OSError) as e:
            logger.error(f"读取文件 {file_path} 失败: {e}")
            return None, None

        # 尝试解码
        return self._decode_content(raw_bytes, file_path)

    def _decode_content(self, raw_bytes: bytes, file_path: Path) -> Tuple[bytes, Optional[str]]:
        """
        解码文件内容
        
        Args:
            raw_bytes: 原始字节内容
            file_path: 文件路径（用于日志）
            
        Returns:
            (原始字节, 解码后的字符串)
        """
        # 首先尝试 UTF-8
        try:
            return raw_bytes, raw_bytes.decode('utf-8')
        except UnicodeDecodeError:
            logger.debug(f"UTF-8 解码失败，尝试检测编码: {file_path}")
            
        # 使用 chardet 检测编码
        try:
            detected = chardet.detect(raw_bytes)
            encoding = detected.get('encoding')
            confidence = detected.get('confidence', 0)
            
            if encoding and confidence > 0.7:
                decoded_str = raw_bytes.decode(encoding, errors='replace')
                logger.debug(f"使用 {encoding} 编码解码文件: {file_path} (置信度: {confidence:.2f})")
                return raw_bytes, decoded_str
            else:
                logger.warning(f"无法可靠地检测文件编码: {file_path}")
                return raw_bytes, None
                
        except (UnicodeDecodeError, TypeError) as e:
            logger.error(f"解码文件失败: {file_path}, 错误: {e}")
            return raw_bytes, None

    def _extract_node_text(self, node: Node, source_code: str) -> str:
        """
        从源代码中提取节点的文本内容
        
        Args:
            node: AST 节点
            source_code: 源代码字符串
            
        Returns:
            节点对应的文本内容
        """
        if node.start_byte >= len(source_code.encode('utf-8')):
            return ""
        return source_code[node.start_byte:node.end_byte]

    def _extract_function_details(self, node: Node, source_code: str, language: SupportedLanguage) -> Tuple[str, str, str]:
        """
        提取函数详细信息
        
        Args:
            node: 函数节点
            source_code: 源代码
            language: 编程语言
            
        Returns:
            (函数全名, 函数简名, 参数列表)
        """
        if language == SupportedLanguage.PYTHON:
            return self._extract_python_function_details(node, source_code)
        elif language in (SupportedLanguage.JAVASCRIPT, SupportedLanguage.TYPESCRIPT):
            return self._extract_js_function_details(node, source_code)
        elif language == SupportedLanguage.JAVA:
            return self._extract_java_function_details(node, source_code)
        elif language == SupportedLanguage.KOTLIN:
            return self._extract_kotlin_function_details(node, source_code)
        elif language == SupportedLanguage.LUA:
            return self._extract_lua_function_details(node, source_code)
        else:
            return self._extract_generic_function_details(node, source_code)

    def _extract_python_function_details(self, node: Node, source_code: str) -> Tuple[str, str, str]:
        """提取 Python 函数详细信息"""
        func_name = ""
        args = ""
        
        for child in node.children:
            if child.type == "identifier":
                func_name = self._extract_node_text(child, source_code)
            elif child.type == "parameters":
                args = self._extract_node_text(child, source_code)
                
        return func_name, func_name, args

    def _extract_js_function_details(self, node: Node, source_code: str) -> Tuple[str, str, str]:
        """提取 JavaScript/TypeScript 函数详细信息"""
        func_name = ""
        args = ""
        
        for child in node.children:
            if child.type in ("identifier", "property_identifier"):
                func_name = self._extract_node_text(child, source_code)
            elif child.type == "formal_parameters":
                args = self._extract_node_text(child, source_code)
                
        return func_name, func_name, args

    def _extract_java_function_details(self, node: Node, source_code: str) -> Tuple[str, str, str]:
        """提取 Java 函数详细信息"""
        func_name = ""
        args = ""
        
        for child in node.children:
            if child.type == "identifier":
                func_name = self._extract_node_text(child, source_code)
            elif child.type == "formal_parameters":
                args = self._extract_node_text(child, source_code)
                
        return func_name, func_name, args

    def _extract_kotlin_function_details(self, node: Node, source_code: str) -> Tuple[str, str, str]:
        """提取 Kotlin 函数详细信息"""
        func_name = ""
        args = ""
        
        for child in node.children:
            if child.type == "simple_identifier":
                func_name = self._extract_node_text(child, source_code)
            elif child.type == "function_value_parameters":
                args = self._extract_node_text(child, source_code)
                
        return func_name, func_name, args

    def _extract_lua_function_details(self, node: Node, source_code: str) -> Tuple[str, str, str]:
        """提取 Lua 函数详细信息"""
        func_name = ""
        args = ""
        
        for child in node.children:
            if child.type == "identifier":
                func_name = self._extract_node_text(child, source_code)
            elif child.type == "parameters":
                args = self._extract_node_text(child, source_code)
                
        return func_name, func_name, args

    def _extract_generic_function_details(self, node: Node, source_code: str) -> Tuple[str, str, str]:
        """提取通用函数详细信息"""
        func_name = self._extract_node_text(node, source_code).split('(')[0].strip()
        args = ""
        
        # 尝试提取参数
        try:
            full_text = self._extract_node_text(node, source_code)
            if '(' in full_text and ')' in full_text:
                start = full_text.find('(')
                end = full_text.find(')', start)
                args = full_text[start:end+1] if end != -1 else ""
        except Exception:
            pass
            
        return func_name, func_name, args

    def _extract_key_messages(self, code: str, comment: str, file_path: Path) -> str:
        """
        提取关键信息用于搜索
        
        Args:
            code: 代码内容
            comment: 注释内容
            file_path: 文件路径
            
        Returns:
            关键信息字符串
        """
        # 提取中文关键词
        chinese_words = re.findall(r'[\u4e00-\u9fa5]+', code + comment)
        
        # 提取英文标识符
        english_words = re.findall(r'[a-zA-Z_][a-zA-Z0-9_]*', code)
        
        # 添加文件名
        key_words = chinese_words + english_words + [file_path.stem]
        
        # 去重并连接
        unique_words = list(set(word for word in key_words if len(word) > 1))
        return ' '.join(unique_words)

    def _parse_functions(self, root_node: Node, source_code: str, 
                        language: SupportedLanguage, file_path: Path,
                        class_name: str = "") -> List[CodeSnippet]:
        """
        解析函数节点
        
        Args:
            root_node: 根节点
            source_code: 源代码
            language: 编程语言
            file_path: 文件路径
            class_name: 所属类名
            
        Returns:
            函数代码片段列表
        """
        logger.debug(f"开始解析函数节点，语言: {language.value}, 类名: {class_name or '无'}")
        functions = []
        
        def traverse_node(node: Node, current_comment: str = ""):
            nonlocal functions
            
            # 收集注释
            if 'comment' in node.type.lower():
                current_comment += self._extract_node_text(node, source_code) + "\n"
                return current_comment
            
            # 处理函数节点
            if self._is_function_node(node, language):
                func_code = self._extract_node_text(node, source_code)
                full_name, short_name, args = self._extract_function_details(node, source_code, language)
                
                # 计算行号
                line_start = source_code[:node.start_byte].count('\n') + 1
                line_end = source_code[:node.end_byte].count('\n') + 1
                
                # 提取关键信息
                key_msg = self._extract_key_messages(func_code, current_comment, file_path)
                
                logger.debug(f"发现函数: {short_name}, 行数: {line_start}-{line_end}, 参数: {args}")
                
                # 创建代码片段
                snippet = CodeSnippet(
                    type="function",
                    path=str(file_path),
                    name=short_name,
                    func_name=full_name,
                    args=args,
                    class_name=class_name,
                    comment=current_comment.strip(),
                    code=current_comment + func_code,
                    key_msg=key_msg,
                    line_start=line_start,
                    line_end=line_end,
                    md5=""  # 将在 __post_init__ 中计算
                )
                
                functions.append(snippet)
                current_comment = ""  # 重置注释
            
            # 递归遍历子节点
            comment = current_comment
            for child in node.children:
                comment = traverse_node(child, comment)
            
            return comment
        
        traverse_node(root_node)
        
        logger.debug(f"函数解析完成，共找到 {len(functions)} 个函数")
        return functions

    def _is_function_node(self, node: Node, language: SupportedLanguage) -> bool:
        """
        判断节点是否为函数节点
        
        Args:
            node: AST 节点
            language: 编程语言
            
        Returns:
            是否为函数节点
        """
        function_types = {
            SupportedLanguage.PYTHON: ('function_definition', 'method_definition'),
            SupportedLanguage.JAVASCRIPT: ('function_declaration', 'method_definition', 'arrow_function'),
            SupportedLanguage.TYPESCRIPT: ('function_declaration', 'method_definition', 'arrow_function'),
            SupportedLanguage.JAVA: ('method_declaration', 'constructor_declaration'),
            SupportedLanguage.GO: ('function_declaration', 'method_declaration'),
            SupportedLanguage.C: ('function_definition',),
            SupportedLanguage.CPP: ('function_definition',),
            SupportedLanguage.KOTLIN: ('function_declaration', 'anonymous_function'),
            SupportedLanguage.LUA: ('function_declaration', 'function_definition'),
        }
        
        return node.type in function_types.get(language, ())

    def _parse_classes(self, root_node: Node, source_code: str,
                      language: SupportedLanguage, file_path: Path) -> List[CodeSnippet]:
        """
        解析类节点
        
        Args:
            root_node: 根节点
            source_code: 源代码
            language: 编程语言
            file_path: 文件路径
            
        Returns:
            类代码片段列表
        """
        classes = []
        
        def traverse_node(node: Node):
            if self._is_class_node(node, language):
                class_name = self._extract_class_name(node, source_code, language)
                class_code = self._extract_node_text(node, source_code)
                
                # 计算行号
                line_start = source_code[:node.start_byte].count('\n') + 1
                line_end = source_code[:node.end_byte].count('\n') + 1
                
                # 提取关键信息
                key_msg = self._extract_key_messages(class_code, "", file_path)
                
                # 创建类代码片段
                snippet = CodeSnippet(
                    type="class",
                    path=str(file_path),
                    name=class_name,
                    class_name=class_name,
                    code=class_code,
                    key_msg=key_msg,
                    line_start=line_start,
                    line_end=line_end,
                    md5=""
                )
                
                classes.append(snippet)
                
                # 解析类中的方法
                methods = self._parse_functions(node, source_code, language, file_path, class_name)
                classes.extend(methods)
            
            # 递归遍历子节点
            for child in node.children:
                traverse_node(child)
        
        traverse_node(root_node)
        return classes

    def _is_class_node(self, node: Node, language: SupportedLanguage) -> bool:
        """判断节点是否为类节点"""
        class_types = {
            SupportedLanguage.PYTHON: ('class_definition',),
            SupportedLanguage.JAVASCRIPT: ('class_declaration',),
            SupportedLanguage.TYPESCRIPT: ('class_declaration', 'interface_declaration'),
            SupportedLanguage.JAVA: ('class_declaration', 'interface_declaration'),
            SupportedLanguage.GO: ('type_declaration',),
            SupportedLanguage.CPP: ('class_specifier',),
            SupportedLanguage.KOTLIN: ('class_declaration', 'object_declaration', 'interface_declaration'),
            SupportedLanguage.LUA: ('table_constructor',),  # Lua使用table实现面向对象
        }
        
        return node.type in class_types.get(language, ())

    def _extract_class_name(self, node: Node, source_code: str, language: SupportedLanguage) -> str:
        """提取类名"""
        for child in node.children:
            if child.type in ("identifier", "type_identifier"):
                return self._extract_node_text(child, source_code)
        return "Unknown"

    def _handle_special_files(self, file_path: Path, source_code: str) -> Optional[List[CodeSnippet]]:
        """
        处理特殊文件（如配置文件等）
        
        Args:
            file_path: 文件路径
            source_code: 源代码
            
        Returns:
            特殊处理的代码片段列表或 None
        """
        # 处理特定的 GMCommandData.py 文件
        if file_path.name == 'GMCommandData.py':
            return self._parse_gm_command_data(source_code, file_path)
        
        return None

    def _parse_gm_command_data(self, source_code: str, file_path: Path) -> List[CodeSnippet]:
        """解析 GM 命令数据文件"""
        logger.info(f"应用特殊解析逻辑: {file_path}")
        
        # 这里可以实现特定的解析逻辑
        # 暂时返回空列表
        return []

    @timing_decorator
    def parse_file(self, file_path_str: str) -> ParseResult:
        """
        解析源代码文件
        
        Args:
            file_path_str: 文件路径字符串
            
        Returns:
            解析结果
        """
        file_path = Path(file_path_str)
        logger.info(f"开始解析文件: {file_path}")
        
        result = ParseResult(
            language=None,
            file_path=str(file_path),
            snippets=[],
            errors=[],
            metadata={"file_size": 0}
        )
        
        try:
            # 检查文件是否存在
            if not file_path.exists():
                raise FileReadError(f"文件不存在: {file_path}")
            
            # 检测语言
            language = self._detect_language(file_path)
            if not language:
                raise LanguageNotSupportedError(f"不支持的文件类型: {file_path.suffix}")
            
            logger.debug(f"检测到语言: {language.value}")
            result.language = language
            
            # 获取解析器
            parser = self._get_parser(language)
            if not parser:
                raise ParserError(f"无法获取 {language.value} 解析器")
            
            logger.debug(f"获取到 {language.value} 解析器")
            
            # 读取文件
            raw_bytes, source_code = self._read_file_safely(file_path)
            if raw_bytes is None or source_code is None:
                raise FileReadError(f"无法读取或解码文件: {file_path}")
            
            result.metadata["file_size"] = len(raw_bytes)
            logger.debug(f"文件内容长度: {len(source_code)} 字符")
            
            # 检查特殊文件
            special_snippets = self._handle_special_files(file_path, source_code)
            if special_snippets is not None:
                logger.info(f"应用特殊文件处理逻辑: {file_path.name}")
                result.snippets = special_snippets
                return result
            
            # 解析 AST
            logger.debug("开始解析 AST")
            tree = parser.parse(raw_bytes)
            if not tree or not tree.root_node:
                raise ParserError("AST 解析失败")
            
            root_node = tree.root_node
            logger.debug(f"AST 根节点类型: {root_node.type}, 子节点数: {len(root_node.children)}")
            
            # 提取代码片段
            if language in (SupportedLanguage.JAVASCRIPT, SupportedLanguage.TYPESCRIPT):
                # 前端语言特殊处理
                logger.debug("使用前端语言解析逻辑")
                result.snippets = self._parse_frontend_code(root_node, source_code, language, file_path)
            else:
                # 后端语言通用处理
                logger.debug("使用后端语言解析逻辑")
                result.snippets = self._parse_backend_code(root_node, source_code, language, file_path)
            
            logger.success(f"成功解析文件 {file_path}，提取 {len(result.snippets)} 个代码片段")
            
            # 打印代码片段统计
            if result.snippets:
                snippet_stats = {}
                for snippet in result.snippets:
                    snippet_type = snippet.type
                    if snippet_type not in snippet_stats:
                        snippet_stats[snippet_type] = 0
                    snippet_stats[snippet_type] += 1
                
                stats_str = ", ".join([f"{k}: {v}" for k, v in snippet_stats.items()])
                logger.info(f"代码片段统计 - {stats_str}")
            
        except Exception as e:
            error_msg = f"解析文件 {file_path} 时出错: {str(e)}"
            logger.error(error_msg)
            result.errors.append(error_msg)
        
        return result

    def _parse_frontend_code(self, root_node: Node, source_code: str,
                            language: SupportedLanguage, file_path: Path) -> List[CodeSnippet]:
        """解析前端代码"""
        snippets = []
        
        # 解析函数
        functions = self._parse_functions(root_node, source_code, language, file_path)
        snippets.extend(functions)
        
        # 解析类和接口
        classes = self._parse_classes(root_node, source_code, language, file_path)
        snippets.extend(classes)
        
        return snippets

    def _parse_backend_code(self, root_node: Node, source_code: str,
                           language: SupportedLanguage, file_path: Path) -> List[CodeSnippet]:
        """解析后端代码"""
        snippets = []
        
        # 解析类
        classes = self._parse_classes(root_node, source_code, language, file_path)
        snippets.extend(classes)
        
        # 解析顶级函数
        functions = self._parse_functions(root_node, source_code, language, file_path)
        snippets.extend(functions)
        
        return snippets

    def parse_multiple_files(self, file_paths: List[str]) -> List[ParseResult]:
        """
        批量解析多个文件
        
        Args:
            file_paths: 文件路径列表
            
        Returns:
            解析结果列表
        """
        logger.info(f"开始批量解析 {len(file_paths)} 个文件")
        
        results = []
        successful_count = 0
        failed_count = 0
        
        for i, file_path in enumerate(file_paths, 1):
            logger.debug(f"处理第 {i}/{len(file_paths)} 个文件: {file_path}")
            
            try:
                result = self.parse_file(file_path)
                results.append(result)
                
                if result.is_successful:
                    successful_count += 1
                    logger.debug(f"文件 {file_path} 解析成功")
                else:
                    failed_count += 1
                    logger.warning(f"文件 {file_path} 解析失败: {result.errors}")
                    
            except Exception as e:
                failed_count += 1
                logger.error(f"批量解析时处理文件 {file_path} 失败: {e}")
                error_result = ParseResult(
                    language=None,
                    file_path=file_path,
                    errors=[str(e)]
                )
                results.append(error_result)
        
        logger.success(f"批量解析完成: 成功 {successful_count} 个, 失败 {failed_count} 个")
        return results

    def get_supported_extensions(self) -> List[str]:
        """获取支持的文件扩展名列表"""
        return list(LANGUAGE_MAPPING.keys())

    def clear_cache(self):
        """清除解析器缓存"""
        with self._parser_lock:
            self._parsers.clear()
        self._get_parser.cache_clear()
        logger.info("解析器缓存已清除")


# 便利函数
def parse_code_file(file_path: str) -> ParseResult:
    """
    便利函数：解析单个代码文件
    
    Args:
        file_path: 文件路径
        
    Returns:
        解析结果
    """
    parser = CodeParser()
    return parser.parse_file(file_path)


def get_file_language(file_path: str) -> Optional[SupportedLanguage]:
    """
    便利函数：获取文件的编程语言
    
    Args:
        file_path: 文件路径
        
    Returns:
        编程语言或 None
    """
    parser = CodeParser()
    return parser._detect_language(Path(file_path))


if __name__ == '__main__':
    # 示例用法
    import sys
    
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        parser = CodeParser()
        result = parser.parse_file(file_path)
        
        print(f"文件: {result.file_path}")
        print(f"语言: {result.language.value if result.language else 'Unknown'}")
        print(f"代码片段数量: {len(result.snippets)}")
        print(f"处理时间: {result.processing_time:.4f}s")
        
        if result.errors:
            print(f"错误: {result.errors}")
        
        for i, snippet in enumerate(result.snippets[:5]):  # 只显示前5个
            print(f"\n片段 {i+1}:")
            print(f"  类型: {snippet.type}")
            print(f"  名称: {snippet.name}")
            print(f"  行数: {snippet.line_start}-{snippet.line_end}")
            if snippet.class_name:
                print(f"  所属类: {snippet.class_name}")
    else:
        print("用法: python code_parser.py <file_path>")