"""
Core数据模型模块

定义代码仓库索引的核心数据结构和模型。
"""

import hashlib
import json
import time
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional, List, Union, Tuple
from pathlib import Path
from datetime import datetime
from enum import Enum

from ..parsers.code_parser import CodeSnippet, SnippetType
from ..embeddings.node import Node


class BlockType(Enum):
    """代码块类型枚举"""
    FUNCTION = "function"
    CLASS = "class"
    METHOD = "method"
    PROPERTY = "property"
    VARIABLE = "variable"
    IMPORT = "import"
    COMMENT = "comment"
    DOCUMENTATION = "documentation"
    CONFIG = "config"
    TEXT_CHUNK = "text_chunk"
    BINARY_FILE = "binary_file"
    UNKNOWN = "unknown"


@dataclass
class CodeBlock:
    """
    代码块数据结构
    
    统一的代码块表示，整合了parser和embedding的数据结构
    """
    
    # 基本标识
    block_id: str = ""
    repository_id: str = ""
    
    # 代码内容
    content: str = ""
    content_hash: str = ""
    
    # 位置信息
    file_path: str = ""
    line_start: int = 0
    line_end: int = 0
    char_start: Optional[int] = None
    char_end: Optional[int] = None
    
    # 代码结构信息
    block_type: BlockType = BlockType.UNKNOWN
    language: Optional[str] = None
    name: str = ""
    full_name: str = ""
    signature: str = ""
    class_name: str = ""
    namespace: str = ""
    
    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # 关键词和搜索信息
    keywords: List[str] = field(default_factory=list)
    search_text: str = ""
    
    # 关系信息
    parent_block_id: Optional[str] = None
    child_block_ids: List[str] = field(default_factory=list)
    related_block_ids: List[str] = field(default_factory=list)
    
    # 向量嵌入
    embedding: Optional[List[float]] = None
    embedding_model: Optional[str] = None
    
    # 时间戳
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """初始化后处理"""
        if not self.block_id:
            self.block_id = self.generate_block_id()
        
        if not self.content_hash:
            self.content_hash = self.calculate_content_hash()
    
    def generate_block_id(self) -> str:
        """生成代码块ID"""
        # 使用文件路径、行号、内容哈希生成唯一ID
        base_info = f"{self.file_path}:{self.line_start}-{self.line_end}"
        content_hash = hashlib.md5(self.content.encode('utf-8')).hexdigest()[:8]
        return f"{base_info}:{content_hash}"
    
    def calculate_content_hash(self) -> str:
        """计算内容哈希"""
        return hashlib.md5(self.content.encode('utf-8')).hexdigest()
    
    def update_timestamp(self):
        """更新时间戳"""
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        # 处理特殊字段
        data['block_type'] = self.block_type.value
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CodeBlock':
        """从字典创建实例"""
        # 处理特殊字段
        if 'block_type' in data:
            data['block_type'] = BlockType(data['block_type'])
        if 'created_at' in data:
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if 'updated_at' in data:
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        return cls(**data)
    
    @classmethod
    def from_code_snippet(cls, snippet: CodeSnippet, repository_id: str = "") -> 'CodeBlock':
        """从CodeSnippet创建CodeBlock"""
        # 映射代码片段类型到块类型
        type_mapping = {
            "function": BlockType.FUNCTION,
            "class": BlockType.CLASS,
            "method": BlockType.METHOD,
            "text_chunk": BlockType.TEXT_CHUNK,
            "config_file": BlockType.CONFIG,
            "documentation": BlockType.DOCUMENTATION,
            "binary_file": BlockType.BINARY_FILE,
        }
        
        block_type = type_mapping.get(snippet.type, BlockType.UNKNOWN)
        
        # 提取关键词
        keywords = []
        if snippet.key_msg:
            keywords = [word.strip() for word in snippet.key_msg.split() if word.strip()]
        
        # 生成搜索文本
        search_text = f"{snippet.name} {snippet.comment} {snippet.key_msg}".strip()
        
        return cls(
            repository_id=repository_id,
            content=snippet.code,
            file_path=snippet.path,
            line_start=snippet.line_start,
            line_end=snippet.line_end,
            block_type=block_type,
            language=getattr(snippet, 'language', None),
            name=snippet.name,
            full_name=snippet.func_name or snippet.name,
            signature=snippet.args,
            class_name=snippet.class_name,
            keywords=keywords,
            search_text=search_text,
            metadata={
                "comment": snippet.comment,
                "key_msg": snippet.key_msg,
                "md5": snippet.md5,
                "original_type": snippet.type,
            }
        )
    
    def to_node(self) -> Node:
        """转换为embedding Node"""
        return Node(
            node_id=self.block_id,
            text=self.content,
            metadata={
                "repository_id": self.repository_id,
                "file_path": self.file_path,
                "line_start": self.line_start,
                "line_end": self.line_end,
                "block_type": self.block_type.value,
                "language": self.language,
                "name": self.name,
                "full_name": self.full_name,
                "signature": self.signature,
                "class_name": self.class_name,
                "namespace": self.namespace,
                "keywords": self.keywords,
                "search_text": self.search_text,
                "created_at": self.created_at.isoformat(),
                **self.metadata
            },
            embedding=self.embedding,
            start_char_idx=self.char_start,
            end_char_idx=self.char_end,
        )
    
    @classmethod
    def from_node(cls, node: Node, repository_id: str = "") -> 'CodeBlock':
        """从Node创建CodeBlock"""
        metadata = node.metadata or {}
        
        return cls(
            block_id=node.node_id,
            repository_id=repository_id,
            content=node.text,
            file_path=metadata.get("file_path", ""),
            line_start=metadata.get("line_start", 0),
            line_end=metadata.get("line_end", 0),
            char_start=node.start_char_idx,
            char_end=node.end_char_idx,
            block_type=BlockType(metadata.get("block_type", "unknown")),
            language=metadata.get("language"),
            name=metadata.get("name", ""),
            full_name=metadata.get("full_name", ""),
            signature=metadata.get("signature", ""),
            class_name=metadata.get("class_name", ""),
            namespace=metadata.get("namespace", ""),
            keywords=metadata.get("keywords", []),
            search_text=metadata.get("search_text", ""),
            embedding=node.embedding,
            metadata={k: v for k, v in metadata.items() if k not in {
                "repository_id", "file_path", "line_start", "line_end", "block_type",
                "language", "name", "full_name", "signature", "class_name", "namespace",
                "keywords", "search_text", "created_at"
            }},
            created_at=datetime.fromisoformat(metadata.get("created_at", datetime.now().isoformat())),
        )


@dataclass
class RepositoryIndex:
    """
    代码仓库索引信息
    """
    
    repository_id: str = ""
    name: str = ""
    url: str = ""
    local_path: str = ""
    branch: str = ""
    commit_hash: str = ""
    
    # 统计信息
    total_files: int = 0
    indexed_files: int = 0
    total_blocks: int = 0
    total_lines: int = 0
    
    # 语言分布
    language_distribution: Dict[str, int] = field(default_factory=dict)
    
    # 索引配置
    index_config: Dict[str, Any] = field(default_factory=dict)
    
    # 时间戳
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    indexed_at: Optional[datetime] = None
    
    def __post_init__(self):
        """初始化后处理"""
        if not self.repository_id:
            self.repository_id = self.generate_repository_id()
    
    def generate_repository_id(self) -> str:
        """生成仓库ID"""
        # 使用仓库URL或路径生成唯一ID
        base_info = self.url or self.local_path or self.name
        return hashlib.md5(base_info.encode('utf-8')).hexdigest()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        if self.indexed_at:
            data['indexed_at'] = self.indexed_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RepositoryIndex':
        """从字典创建实例"""
        if 'created_at' in data:
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if 'updated_at' in data:
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        if 'indexed_at' in data and data['indexed_at']:
            data['indexed_at'] = datetime.fromisoformat(data['indexed_at'])
        return cls(**data)
    
    def update_stats(self, blocks: List[CodeBlock]):
        """更新统计信息"""
        self.total_blocks = len(blocks)
        self.language_distribution.clear()
        
        for block in blocks:
            if block.language:
                self.language_distribution[block.language] = \
                    self.language_distribution.get(block.language, 0) + 1
        
        self.updated_at = datetime.now()
    
    def mark_indexed(self):
        """标记为已索引"""
        self.indexed_at = datetime.now()
        self.updated_at = datetime.now()


@dataclass
class SearchQuery:
    """
    搜索查询对象
    """
    
    query: str = ""
    query_type: str = "semantic"  # semantic, code, keyword, metadata
    
    # 过滤条件
    repository_id: Optional[str] = None
    language: Optional[str] = None
    block_type: Optional[BlockType] = None
    file_path: Optional[str] = None
    
    # 搜索参数
    top_k: int = 10
    similarity_threshold: float = 0.0
    
    # 元数据过滤
    metadata_filters: Dict[str, Any] = field(default_factory=dict)
    
    # 时间范围
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        if self.block_type:
            data['block_type'] = self.block_type.value
        if self.created_after:
            data['created_after'] = self.created_after.isoformat()
        if self.created_before:
            data['created_before'] = self.created_before.isoformat()
        return data


@dataclass
class SearchResult:
    """
    搜索结果对象
    """
    
    block: CodeBlock
    score: float = 0.0
    match_reason: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "block": self.block.to_dict(),
            "score": self.score,
            "match_reason": self.match_reason,
        }


# 辅助函数
def create_repository_index(
    repository_path: str,
    url: str = "",
    branch: str = "",
    commit_hash: str = "",
    **kwargs
) -> RepositoryIndex:
    """
    创建仓库索引对象
    
    Args:
        repository_path: 仓库本地路径
        url: 仓库URL
        branch: 分支名
        commit_hash: 提交哈希
        **kwargs: 其他参数
        
    Returns:
        RepositoryIndex实例
    """
    path = Path(repository_path)
    name = path.name
    
    return RepositoryIndex(
        name=name,
        url=url,
        local_path=str(path),
        branch=branch,
        commit_hash=commit_hash,
        **kwargs
    )


def create_search_query(
    query: str,
    query_type: str = "semantic",
    **kwargs
) -> SearchQuery:
    """
    创建搜索查询对象
    
    Args:
        query: 查询内容
        query_type: 查询类型
        **kwargs: 其他参数
        
    Returns:
        SearchQuery实例
    """
    return SearchQuery(
        query=query,
        query_type=query_type,
        **kwargs
    ) 