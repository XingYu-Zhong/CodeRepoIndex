"""
目录解析器模块

提供处理整个代码仓库目录的功能，支持：
- 递归处理目录下所有文件
- 智能文件过滤和忽略规则
- 对不支持的文件进行通用切割
- 统一的代码片段格式
- 目录结构信息记录
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
import fnmatch
import mimetypes
import time

from .code_parser import CodeParser, CodeSnippet, ParseResult, SupportedLanguage, SnippetType
from .config import ParserConfig, DEFAULT_CONFIG, is_file_ignored, get_file_language
from .version_manager import VersionManager, ChangeType
from loguru import logger


# 默认忽略的文件和目录模式
DEFAULT_IGNORE_PATTERNS = [
    # Git 相关
    '.git',
    '.gitignore',
    '.gitmodules',
    '.gitattributes',
    
    # 编辑器和IDE
    '.vscode',
    '.idea',
    '*.swp',
    '*.swo',
    '*~',
    '.DS_Store',
    'Thumbs.db',
    
    # CI/CD 配置
    '.github',
    '.gitlab-ci.yml',
    '.travis.yml',
    '.circleci',
    '.pre-commit-config.yaml',
    '.pre-commit-hooks.yaml',
    'azure-pipelines.yml',
    'Jenkinsfile',
    
    # 包管理和依赖
    'node_modules',
    '__pycache__',
    '*.pyc',
    '*.pyo',
    '*.pyd',
    '.pytest_cache',
    'venv',
    'env',
    '.venv',
    '.env',
    'vendor',
    'Pipfile.lock',
    'poetry.lock',
    'yarn.lock',
    'package-lock.json',
    'composer.lock',
    'Gemfile.lock',
    
    # 构建产物
    'build',
    'dist',
    'target',
    'bin',
    'obj',
    'out',
    '*.min.js',
    '*.min.css',
    '*.bundle.js',
    '*.chunk.js',
    
    # 日志和临时文件
    '*.log',
    '*.tmp',
    '*.temp',
    '*.cache',
    
    # 数据库文件
    '*.db',
    '*.sqlite',
    '*.sqlite3',
    
    # 压缩文件
    '*.zip',
    '*.tar.gz',
    '*.rar',
    '*.7z',
    
    # 图片和媒体文件
    '*.jpg',
    '*.jpeg',
    '*.png',
    '*.gif',
    '*.bmp',
    '*.svg',
    '*.ico',
    '*.mp3',
    '*.mp4',
    '*.avi',
    '*.mov',
    '*.pdf',
    
    # 字体文件
    '*.ttf',
    '*.woff',
    '*.woff2',
    '*.eot',
]

# 文档文件扩展名
DOCUMENTATION_EXTENSIONS = {
    'md', 'txt', 'rst', 'adoc', 'org',
    'textile', 'creole', 'wiki', 'confluence'
}

# 配置文件扩展名
CONFIG_EXTENSIONS = {
    'json', 'yaml', 'yml', 'toml', 'ini', 'cfg',
    'conf', 'config', 'properties', 'env'
}

# 文本文件扩展名（可以进行文本切割）
TEXT_EXTENSIONS = DOCUMENTATION_EXTENSIONS | CONFIG_EXTENSIONS | {
    'xml', 'html', 'htm', 'css', 'scss', 'less',
    'sql', 'sh', 'bash', 'zsh', 'fish', 'ps1',
    'dockerfile', 'makefile', 'cmake'
}


@dataclass
class DirectoryConfig:
    """目录解析配置"""
    
    # 基础解析配置
    parser_config: ParserConfig = field(default_factory=lambda: DEFAULT_CONFIG)
    
    # 目录遍历配置
    max_depth: int = 10                  # 最大递归深度
    follow_symlinks: bool = False        # 是否跟随符号链接
    max_files: int = 10000              # 最大处理文件数
    
    # 文件过滤配置
    ignore_patterns: List[str] = field(default_factory=lambda: DEFAULT_IGNORE_PATTERNS.copy())
    only_extensions: Optional[Set[str]] = None  # 如果指定，则只处理这些扩展名
    
    # 文本切割配置
    chunk_size: int = 512               # 文本切割大小（字符数）
    chunk_overlap: int = 50             # 切片重叠大小
    min_chunk_size: int = 100           # 最小切片大小
    max_text_file_size: int = 1024 * 1024  # 最大文本文件大小 (1MB)
    
    # 内容处理配置
    extract_text_files: bool = True     # 是否处理文本文件
    extract_config_files: bool = True   # 是否处理配置文件
    extract_documentation: bool = True  # 是否处理文档文件
    record_binary_files: bool = False   # 是否记录二进制文件信息
    
    # 目录结构配置
    include_directory_structure: bool = True  # 是否包含目录结构信息
    max_path_length: int = 260          # 最大路径长度限制
    
    # 版本管理配置
    enable_incremental_update: bool = False  # 是否启用增量更新
    version_storage_dir: str = ".coderepo_index"  # 版本信息存储目录
    repo_commit: Optional[str] = None    # 仓库commit hash


@dataclass
class DirectoryParseResult:
    """目录解析结果"""
    
    root_path: str                                    # 根目录路径
    snippets: List[CodeSnippet] = field(default_factory=list)  # 所有代码片段
    file_results: Dict[str, ParseResult] = field(default_factory=dict)  # 文件解析结果
    errors: List[str] = field(default_factory=list)  # 错误信息
    
    # 统计信息
    total_files: int = 0                 # 总文件数
    processed_files: int = 0             # 已处理文件数
    skipped_files: int = 0               # 跳过的文件数
    code_files: int = 0                  # 代码文件数
    text_files: int = 0                  # 文本文件数
    binary_files: int = 0                # 二进制文件数
    
    # 性能信息
    processing_time: float = 0.0         # 处理时间
    directory_structure: Dict[str, Any] = field(default_factory=dict)  # 目录结构
    
    # 版本管理信息
    incremental_update_used: bool = False  # 是否使用了增量更新
    update_plan: Optional[Dict[str, Any]] = None  # 增量更新计划
    files_changed: int = 0               # 变化的文件数
    files_added: int = 0                 # 新增的文件数
    files_deleted: int = 0               # 删除的文件数
    chunks_changed: int = 0              # 变化的切块数
    
    @property
    def success_rate(self) -> float:
        """计算成功率"""
        if self.total_files == 0:
            return 0.0
        return self.processed_files / self.total_files


class DirectoryParser:
    """目录解析器"""
    
    def __init__(self, config: Optional[DirectoryConfig] = None):
        """
        初始化目录解析器
        
        Args:
            config: 目录解析配置
        """
        self.config = config or DirectoryConfig()
        self.code_parser = CodeParser(max_cache_size=self.config.parser_config.max_cache_size)
        
        # 初始化版本管理器
        if self.config.enable_incremental_update:
            self.version_manager = VersionManager(self.config.version_storage_dir)
        else:
            self.version_manager = None
        
        logger.info(f"初始化目录解析器，最大深度: {self.config.max_depth}，增量更新: {self.config.enable_incremental_update}")
        
    def parse_directory(self, directory_path: str) -> DirectoryParseResult:
        """
        解析整个目录
        
        Args:
            directory_path: 目录路径
            
        Returns:
            目录解析结果
        """
        start_time = time.time()
        directory_path = Path(directory_path).resolve()
        
        if not directory_path.exists():
            raise ValueError(f"目录不存在: {directory_path}")
        if not directory_path.is_dir():
            raise ValueError(f"路径不是目录: {directory_path}")
            
        logger.info(f"开始解析目录: {directory_path}")
        
        result = DirectoryParseResult(root_path=str(directory_path))
        
        try:
            # 获取所有文件
            all_files = self._scan_directory(directory_path)
            result.total_files = len(all_files)
            
            logger.info(f"发现 {result.total_files} 个文件")
            
            # 处理增量更新
            files_to_process = all_files
            if self.version_manager and self.config.repo_commit:
                result.incremental_update_used = True
                
                # 生成文件路径列表（相对路径）
                relative_file_paths = [str(f.relative_to(directory_path)) for f in all_files]
                
                # 获取增量更新计划
                update_plan = self.version_manager.get_incremental_update_plan(
                    str(directory_path), 
                    self.config.repo_commit, 
                    relative_file_paths
                )
                result.update_plan = update_plan
                result.files_added = update_plan['changes_summary']['added']
                result.files_changed = update_plan['changes_summary']['modified']
                result.files_deleted = update_plan['changes_summary']['deleted']
                
                # 只处理需要更新的文件
                files_to_process_paths = set(update_plan['files_to_process'])
                files_to_process = [f for f in all_files 
                                  if str(f.relative_to(directory_path)) in files_to_process_paths]
                
                logger.info(f"增量更新: 需要处理 {len(files_to_process)} 个文件 "
                           f"(新增: {result.files_added}, 修改: {result.files_changed}, 删除: {result.files_deleted})")
            
            # 构建目录结构
            if self.config.include_directory_structure:
                result.directory_structure = self._build_directory_structure(directory_path)
            
            # 处理每个文件
            for file_path in files_to_process:
                try:
                    self._process_file(file_path, directory_path, result)
                except Exception as e:
                    error_msg = f"处理文件失败 {file_path}: {e}"
                    logger.error(error_msg)
                    result.errors.append(error_msg)
                    result.skipped_files += 1
            
            # 更新版本信息
            if self.version_manager and self.config.repo_commit:
                self._update_version_info(directory_path, result)
                    
            result.processing_time = time.time() - start_time
            
            logger.info(f"目录解析完成，处理 {result.processed_files}/{result.total_files} 个文件，"
                       f"生成 {len(result.snippets)} 个代码片段，用时 {result.processing_time:.2f}s")
            
            return result
            
        except Exception as e:
            result.processing_time = time.time() - start_time
            error_msg = f"目录解析失败: {e}"
            logger.error(error_msg)
            result.errors.append(error_msg)
            return result
    
    def _scan_directory(self, directory_path: Path) -> List[Path]:
        """扫描目录，获取所有需要处理的文件"""
        all_files = []
        
        def scan_recursive(current_path: Path, depth: int = 0):
            if depth > self.config.max_depth:
                return
            if len(all_files) >= self.config.max_files:
                return
                
            try:
                for item in current_path.iterdir():
                    if item.is_file():
                        if not self._should_ignore_file(item, directory_path):
                            all_files.append(item)
                    elif item.is_dir():
                        if not self._should_ignore_directory(item):
                            if item.is_symlink() and not self.config.follow_symlinks:
                                continue
                            scan_recursive(item, depth + 1)
            except PermissionError:
                logger.warning(f"无权限访问目录: {current_path}")
            except Exception as e:
                logger.error(f"扫描目录时出错 {current_path}: {e}")
        
        scan_recursive(directory_path)
        return all_files
    
    def _should_ignore_file(self, file_path: Path, root_path: Path) -> bool:
        """判断是否应该忽略文件"""
        relative_path = file_path.relative_to(root_path)
        file_str = str(relative_path)
        file_name = file_path.name
        
        # 检查忽略模式
        for pattern in self.config.ignore_patterns:
            if fnmatch.fnmatch(file_name, pattern) or fnmatch.fnmatch(file_str, pattern):
                return True
        
        # 检查文件大小
        try:
            if file_path.stat().st_size > self.config.max_text_file_size:
                return True
        except (OSError, PermissionError):
            return True
        
        # 检查扩展名过滤
        if self.config.only_extensions:
            ext = file_path.suffix.lstrip('.').lower()
            if ext not in self.config.only_extensions:
                return True
        
        return False
    
    def _should_ignore_directory(self, dir_path: Path) -> bool:
        """判断是否应该忽略目录"""
        dir_name = dir_path.name
        
        for pattern in self.config.ignore_patterns:
            if fnmatch.fnmatch(dir_name, pattern):
                return True
        
        return False
    
    def _process_file(self, file_path: Path, root_path: Path, result: DirectoryParseResult):
        """处理单个文件"""
        relative_path = file_path.relative_to(root_path)
        file_ext = file_path.suffix.lstrip('.').lower()
        
        logger.debug(f"处理文件: {relative_path}")
        
        # 判断文件类型
        if self._is_code_file(file_ext):
            self._process_code_file(file_path, relative_path, result)
            result.code_files += 1
        elif self._is_text_file(file_ext):
            self._process_text_file(file_path, relative_path, result)
            result.text_files += 1
        elif self.config.record_binary_files:
            self._record_binary_file(file_path, relative_path, result)
            result.binary_files += 1
        else:
            result.skipped_files += 1
            return
            
        result.processed_files += 1
    
    def _is_code_file(self, extension: str) -> bool:
        """判断是否为代码文件"""
        return extension in self.config.parser_config.language_extensions
    
    def _is_text_file(self, extension: str) -> bool:
        """判断是否为文本文件"""
        return extension in TEXT_EXTENSIONS
    
    def _process_code_file(self, file_path: Path, relative_path: Path, result: DirectoryParseResult):
        """处理代码文件"""
        try:
            parse_result = self.code_parser.parse_file(str(file_path))
            result.file_results[str(relative_path)] = parse_result
            
            if parse_result.is_successful:
                # 更新代码片段的路径信息
                for snippet in parse_result.snippets:
                    snippet.path = str(relative_path)
                    # 更新目录和文件信息
                    snippet.directory = str(relative_path.parent)
                    snippet.filename = relative_path.name
                    snippet.file_type = 'code'
                    snippet.language = parse_result.language.value if parse_result.language else 'unknown'
                    
                    # 添加版本管理字段
                    if self.config.repo_commit:
                        snippet.repo_commit = self.config.repo_commit
                        snippet.created_at = snippet.updated_at = result.processing_time
                    
                    # 添加目录信息到metadata
                    snippet.metadata.update({
                        'directory': str(relative_path.parent),
                        'filename': relative_path.name,
                        'file_type': 'code',
                        'language': parse_result.language.value if parse_result.language else 'unknown'
                    })
                
                result.snippets.extend(parse_result.snippets)
                logger.debug(f"代码文件解析成功: {relative_path}, 生成 {len(parse_result.snippets)} 个片段")
            else:
                logger.warning(f"代码文件解析失败: {relative_path}")
                
        except Exception as e:
            logger.error(f"处理代码文件时出错 {relative_path}: {e}")
            raise
    
    def _process_text_file(self, file_path: Path, relative_path: Path, result: DirectoryParseResult):
        """处理文本文件"""
        try:
            # 读取文件内容
            content = self._read_text_file(file_path)
            if not content:
                return
            
            # 确定文件类型
            file_ext = file_path.suffix.lstrip('.').lower()
            if file_ext in DOCUMENTATION_EXTENSIONS:
                snippet_type = SnippetType.DOCUMENTATION
            elif file_ext in CONFIG_EXTENSIONS:
                snippet_type = SnippetType.CONFIG_FILE
            else:
                snippet_type = SnippetType.TEXT_CHUNK
            
            # 切割文本
            chunks = self._chunk_text(content)
            
            for i, chunk in enumerate(chunks):
                snippet = CodeSnippet(
                    type=snippet_type.value,
                    path=str(relative_path),
                    name=f"{relative_path.name}_chunk_{i}" if len(chunks) > 1 else relative_path.name,
                    code=chunk,
                    md5="",  # 会在 __post_init__ 中计算
                    directory=str(relative_path.parent),
                    filename=relative_path.name,
                    file_type='text',
                    metadata={
                        'directory': str(relative_path.parent),
                        'filename': relative_path.name,
                        'file_type': 'text',
                        'chunk_index': i,
                        'total_chunks': len(chunks),
                        'original_size': len(content),
                        'chunk_size': len(chunk)
                    }
                )
                result.snippets.append(snippet)
            
            logger.debug(f"文本文件处理成功: {relative_path}, 生成 {len(chunks)} 个片段")
            
        except Exception as e:
            logger.error(f"处理文本文件时出错 {relative_path}: {e}")
            raise
    
    def _record_binary_file(self, file_path: Path, relative_path: Path, result: DirectoryParseResult):
        """记录二进制文件信息"""
        try:
            file_stat = file_path.stat()
            
            snippet = CodeSnippet(
                type=SnippetType.BINARY_FILE.value,
                path=str(relative_path),
                name=relative_path.name,
                code="",  # 二进制文件不存储内容
                md5="",
                directory=str(relative_path.parent),
                filename=relative_path.name,
                file_type='binary',
                metadata={
                    'directory': str(relative_path.parent),
                    'filename': relative_path.name,
                    'file_type': 'binary',
                    'file_size': file_stat.st_size,
                    'extension': file_path.suffix.lstrip('.').lower(),
                    'mime_type': mimetypes.guess_type(str(file_path))[0]
                }
            )
            result.snippets.append(snippet)
            
        except Exception as e:
            logger.error(f"记录二进制文件时出错 {relative_path}: {e}")
            raise
    
    def _read_text_file(self, file_path: Path) -> Optional[str]:
        """安全读取文本文件"""
        try:
            # 尝试不同的编码
            encodings = ['utf-8', 'gbk', 'cp1252', 'iso-8859-1']
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        return f.read()
                except UnicodeDecodeError:
                    continue
            
            logger.warning(f"无法解码文件: {file_path}")
            return None
            
        except Exception as e:
            logger.error(f"读取文件时出错 {file_path}: {e}")
            return None
    
    def _chunk_text(self, text: str) -> List[str]:
        """将文本切分成块"""
        if len(text) <= self.config.chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.config.chunk_size
            
            # 如果不是最后一块，尝试在合适的位置断开
            if end < len(text):
                # 寻找合适的断点（换行符、句号、逗号等）
                for sep in ['\n\n', '\n', '. ', '。', ', ', '，', ' ']:
                    last_sep = text.rfind(sep, start, end)
                    if last_sep > start + self.config.min_chunk_size:
                        end = last_sep + len(sep)
                        break
            
            chunk = text[start:end].strip()
            if len(chunk) >= self.config.min_chunk_size:
                chunks.append(chunk)
            
            # 计算下一个开始位置，考虑重叠
            start = max(start + 1, end - self.config.chunk_overlap)
        
        return chunks
    
    def _build_directory_structure(self, root_path: Path) -> Dict[str, Any]:
        """构建目录结构信息"""
        def build_tree(path: Path) -> Dict[str, Any]:
            tree = {
                'type': 'directory' if path.is_dir() else 'file',
                'name': path.name,
                'path': str(path.relative_to(root_path))
            }
            
            if path.is_dir() and not self._should_ignore_directory(path):
                children = []
                try:
                    for child in sorted(path.iterdir()):
                        if not (child.is_file() and self._should_ignore_file(child, root_path)):
                            children.append(build_tree(child))
                    tree['children'] = children
                except (PermissionError, OSError):
                    pass
            elif path.is_file():
                try:
                    stat = path.stat()
                    tree.update({
                        'size': stat.st_size,
                        'extension': path.suffix.lstrip('.').lower()
                    })
                except (PermissionError, OSError):
                    pass
            
            return tree
        
        return build_tree(root_path)
    
    def _update_version_info(self, directory_path: Path, result: DirectoryParseResult):
        """更新版本管理信息"""
        if not self.version_manager or not self.config.repo_commit:
            return
            
        try:
            # 计算所有处理文件的MD5并更新切块信息
            for file_path, parse_result in result.file_results.items():
                full_path = directory_path / file_path
                if full_path.exists():
                    file_md5 = self.version_manager.calculate_file_md5(full_path)
                    
                    # 收集该文件的所有切块
                    file_chunks = [snippet for snippet in result.snippets 
                                 if snippet.file_path == file_path]
                    
                    # 更新切块的版本信息
                    for snippet in file_chunks:
                        snippet.file_md5 = file_md5
                        if not snippet.created_at:
                            from datetime import datetime
                            snippet.created_at = snippet.updated_at = datetime.now().isoformat()
                    
                    # 更新切块索引
                    self.version_manager.update_chunks_index(file_chunks)
                    
                    # 更新文件快照
                    chunk_hashes = [snippet.chunk_hash for snippet in file_chunks if snippet.chunk_hash]
                    self.version_manager.update_file_snapshot(
                        file_path=file_path,
                        file_md5=file_md5,
                        repo_commit=self.config.repo_commit,
                        chunk_hashes=chunk_hashes,
                        repo_path=str(directory_path)
                    )
            
            # 处理文本文件（非代码文件）
            for snippet in result.snippets:
                if snippet.file_path not in result.file_results:
                    # 这是文本文件的切块
                    full_path = directory_path / snippet.file_path
                    if full_path.exists():
                        file_md5 = self.version_manager.calculate_file_md5(full_path)
                        snippet.file_md5 = file_md5
                        snippet.repo_commit = self.config.repo_commit
                        if not snippet.created_at:
                            from datetime import datetime
                            snippet.created_at = snippet.updated_at = datetime.now().isoformat()
            
            # 统计变化的切块数
            if result.update_plan:
                for change in result.update_plan['detailed_changes']:
                    if change['change_type'] in ['added', 'modified']:
                        # 估算切块变化数（这里简化处理，实际可以更精确）
                        result.chunks_changed += 1
            
            # 清理孤儿切块
            self.version_manager.cleanup_orphaned_chunks()
            
            # 保存版本状态
            self.version_manager.save_state()
            
            logger.info(f"版本信息更新完成，切块变化: {result.chunks_changed}")
            
        except Exception as e:
            logger.error(f"更新版本信息时出错: {e}")
            result.errors.append(f"版本管理更新失败: {e}")


# 便利函数
def parse_directory(directory_path: str, config: Optional[DirectoryConfig] = None) -> DirectoryParseResult:
    """
    解析目录的便利函数
    
    Args:
        directory_path: 目录路径
        config: 解析配置
        
    Returns:
        目录解析结果
    """
    parser = DirectoryParser(config)
    return parser.parse_directory(directory_path)


def create_directory_config(
    chunk_size: int = 512,
    max_depth: int = 10,
    ignore_patterns: Optional[List[str]] = None,
    only_extensions: Optional[Set[str]] = None,
    enable_incremental_update: bool = False,
    repo_commit: Optional[str] = None,
    version_storage_dir: str = ".coderepo_index"
) -> DirectoryConfig:
    """
    创建目录配置的便利函数
    
    Args:
        chunk_size: 文本切割大小
        max_depth: 最大递归深度
        ignore_patterns: 忽略模式列表
        only_extensions: 只处理的扩展名集合
        enable_incremental_update: 是否启用增量更新
        repo_commit: 仓库commit hash
        version_storage_dir: 版本信息存储目录
        
    Returns:
        目录配置对象
    """
    config = DirectoryConfig()
    config.chunk_size = chunk_size
    config.max_depth = max_depth
    config.enable_incremental_update = enable_incremental_update
    config.repo_commit = repo_commit
    config.version_storage_dir = version_storage_dir
    
    if ignore_patterns:
        config.ignore_patterns.extend(ignore_patterns)
    
    if only_extensions:
        config.only_extensions = only_extensions
    
    return config 