"""
Node类定义，表示文本块和相关元数据
"""

import uuid
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field


@dataclass
class Node:
    """
    表示文本块及其元数据的节点类
    类似于LlamaIndex中的Node概念
    """
    
    # 核心属性
    node_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    text: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # 关系属性
    relationships: Dict[str, str] = field(default_factory=dict)
    
    # 嵌入相关
    embedding: Optional[List[float]] = None
    
    # 其他属性
    start_char_idx: Optional[int] = None
    end_char_idx: Optional[int] = None
    
    def __post_init__(self):
        """初始化后处理"""
        if not self.node_id:
            self.node_id = str(uuid.uuid4())
    
    @classmethod
    def from_text(
        cls,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
        node_id: Optional[str] = None,
        **kwargs
    ) -> 'Node':
        """
        从文本创建节点
        
        Args:
            text: 文本内容
            metadata: 元数据
            node_id: 节点ID，如果不提供则自动生成
            **kwargs: 其他参数
            
        Returns:
            Node实例
        """
        return cls(
            node_id=node_id or str(uuid.uuid4()),
            text=text,
            metadata=metadata or {},
            **kwargs
        )
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Node':
        """
        从字典创建节点
        
        Args:
            data: 包含节点数据的字典
            
        Returns:
            Node实例
        """
        return cls(
            node_id=data.get('node_id', str(uuid.uuid4())),
            text=data.get('text', ''),
            metadata=data.get('metadata', {}),
            relationships=data.get('relationships', {}),
            embedding=data.get('embedding'),
            start_char_idx=data.get('start_char_idx'),
            end_char_idx=data.get('end_char_idx')
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        将节点转换为字典
        
        Returns:
            包含节点数据的字典
        """
        return {
            'node_id': self.node_id,
            'text': self.text,
            'metadata': self.metadata,
            'relationships': self.relationships,
            'embedding': self.embedding,
            'start_char_idx': self.start_char_idx,
            'end_char_idx': self.end_char_idx
        }
    
    def get_content(self, metadata_mode: str = "all") -> str:
        """
        获取节点内容（可包含元数据）
        
        Args:
            metadata_mode: 元数据模式 ("all", "embed", "llm", "none")
            
        Returns:
            节点内容字符串
        """
        if metadata_mode == "none":
            return self.text
        
        # 简单实现，可以根据需要扩展
        metadata_str = ""
        if metadata_mode in ["all", "embed", "llm"] and self.metadata:
            # 过滤一些常用的元数据字段
            important_keys = ["title", "source", "file_name", "page", "section"]
            relevant_metadata = {
                k: v for k, v in self.metadata.items() 
                if k in important_keys
            }
            if relevant_metadata:
                metadata_str = f"Metadata: {relevant_metadata}\n"
        
        return f"{metadata_str}{self.text}".strip()
    
    def get_text_embedding_with_metadata(self) -> str:
        """获取包含元数据的文本用于嵌入"""
        return self.get_content(metadata_mode="embed")
    
    def set_content(self, text: str) -> None:
        """设置节点文本内容"""
        self.text = text
    
    def add_metadata(self, key: str, value: Any) -> None:
        """添加元数据"""
        self.metadata[key] = value
    
    def remove_metadata(self, key: str) -> Any:
        """移除元数据"""
        return self.metadata.pop(key, None)
    
    def add_relationship(self, relationship_type: str, node_id: str) -> None:
        """添加关系"""
        self.relationships[relationship_type] = node_id
    
    def get_relationship(self, relationship_type: str) -> Optional[str]:
        """获取关系"""
        return self.relationships.get(relationship_type)
    
    def __len__(self) -> int:
        """返回文本长度"""
        return len(self.text)
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"Node(id={self.node_id[:8]}..., text_len={len(self.text)})"
    
    def __repr__(self) -> str:
        """详细字符串表示"""
        return (f"Node(node_id='{self.node_id}', text='{self.text[:50]}...', "
                f"metadata={self.metadata})")


class Document(Node):
    """
    文档类，继承自Node
    用于表示完整的文档，在分块之前使用
    """
    
    def __init__(self, text: str = "", metadata: Optional[Dict[str, Any]] = None, **kwargs):
        """
        初始化文档
        
        Args:
            text: 文档文本
            metadata: 文档元数据
            **kwargs: 其他参数
        """
        super().__init__(text=text, metadata=metadata or {}, **kwargs)
        # 为文档添加默认的doc_id（如果metadata中没有的话）
        if "doc_id" not in self.metadata:
            self.metadata["doc_id"] = self.node_id
    
    @classmethod
    def from_file(cls, file_path: str, **kwargs) -> 'Document':
        """
        从文件创建文档
        
        Args:
            file_path: 文件路径
            **kwargs: 其他参数
            
        Returns:
            Document实例
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            metadata = kwargs.get('metadata', {})
            metadata.update({
                'file_path': file_path,
                'file_name': file_path.split('/')[-1]
            })
            
            return cls(text=text, metadata=metadata, **kwargs)
        except Exception as e:
            raise ValueError(f"无法读取文件 {file_path}: {e}")
    
    def get_doc_id(self) -> str:
        """获取文档ID"""
        return self.metadata.get("doc_id", self.node_id) 