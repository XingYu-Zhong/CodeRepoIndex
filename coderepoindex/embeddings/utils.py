"""
Embedding模块的工具函数
包括文本分块、相似度计算、向量操作等
"""

import re
import math
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from .base import BaseSplitter
from .node import Node, Document


class SimpleTextSplitter(BaseSplitter):
    """
    简单的文本分块器
    基于字符数量进行分块，支持重叠
    """
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        separator: str = "\n\n",
        keep_separator: bool = True
    ):
        """
        初始化文本分块器
        
        Args:
            chunk_size: 每个块的最大字符数
            chunk_overlap: 块之间的重叠字符数
            separator: 分割符
            keep_separator: 是否保留分割符
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separator = separator
        self.keep_separator = keep_separator
    
    def split_text(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[Node]:
        """
        将文本分割成节点
        
        Args:
            text: 输入文本
            metadata: 元数据
            
        Returns:
            节点列表
        """
        if not text.strip():
            return []
        
        # 首先按分割符分割
        if self.separator in text:
            splits = text.split(self.separator)
            if self.keep_separator and self.separator:
                # 重新添加分割符
                splits = [split + self.separator for split in splits[:-1]] + [splits[-1]]
        else:
            splits = [text]
        
        # 合并小段落，分割大段落
        chunks = []
        current_chunk = ""
        
        for split in splits:
            # 如果当前split太长，需要强制分割
            if len(split) > self.chunk_size:
                # 先保存当前chunk（如果不为空）
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""
                
                # 强制分割长文本
                force_chunks = self._force_split_text(split)
                chunks.extend(force_chunks)
            else:
                # 检查加入后是否超长
                if len(current_chunk) + len(split) <= self.chunk_size:
                    current_chunk += split
                else:
                    # 保存当前chunk，开始新chunk
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = split
        
        # 保存最后一个chunk
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        # 处理重叠
        if self.chunk_overlap > 0:
            chunks = self._add_overlap(chunks)
        
        # 创建节点
        nodes = []
        base_metadata = metadata or {}
        
        for i, chunk in enumerate(chunks):
            if not chunk.strip():
                continue
                
            node_metadata = base_metadata.copy()
            node_metadata.update({
                'chunk_index': i,
                'total_chunks': len(chunks)
            })
            
            node = Node.from_text(
                text=chunk,
                metadata=node_metadata
            )
            nodes.append(node)
        
        return nodes
    
    def split_documents(self, documents: List[Dict[str, Any]]) -> List[Node]:
        """
        批量分割文档
        
        Args:
            documents: 文档列表，每个文档是包含'text'和可选'metadata'的字典
            
        Returns:
            节点列表
        """
        all_nodes = []
        
        for doc in documents:
            text = doc.get('text', '')
            metadata = doc.get('metadata', {})
            
            nodes = self.split_text(text, metadata)
            all_nodes.extend(nodes)
        
        return all_nodes
    
    def _force_split_text(self, text: str) -> List[str]:
        """强制分割过长的文本"""
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            # 如果不是最后一段，尝试在合适的位置断开
            if end < len(text):
                # 寻找最近的句号、换行符等
                break_chars = ['.', '!', '?', '\n', '。', '！', '？']
                best_break = end
                
                for i in range(end - 100, end):  # 在最后100个字符中寻找
                    if i > start and text[i] in break_chars:
                        best_break = i + 1
                        break
                
                chunk = text[start:best_break]
            else:
                chunk = text[start:]
            
            if chunk.strip():
                chunks.append(chunk)
            
            start = best_break if end < len(text) else end
        
        return chunks
    
    def _add_overlap(self, chunks: List[str]) -> List[str]:
        """为块添加重叠"""
        if len(chunks) <= 1:
            return chunks
        
        overlapped_chunks = [chunks[0]]
        
        for i in range(1, len(chunks)):
            prev_chunk = chunks[i-1]
            curr_chunk = chunks[i]
            
            # 从前一个chunk的末尾取重叠部分
            overlap_start = max(0, len(prev_chunk) - self.chunk_overlap)
            overlap_text = prev_chunk[overlap_start:]
            
            # 添加重叠到当前chunk
            overlapped_chunk = overlap_text + curr_chunk
            overlapped_chunks.append(overlapped_chunk)
        
        return overlapped_chunks


class SentenceSplitter(BaseSplitter):
    """
    基于句子的文本分块器
    尝试在句子边界处分割文本
    """
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ):
        """
        初始化句子分块器
        
        Args:
            chunk_size: 每个块的最大字符数
            chunk_overlap: 块之间的重叠字符数
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # 句子结束标点
        self.sentence_endings = r'[.!?。！？]+'
    
    def split_text(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[Node]:
        """
        将文本按句子分割成节点
        
        Args:
            text: 输入文本
            metadata: 元数据
            
        Returns:
            节点列表
        """
        if not text.strip():
            return []
        
        # 按句子分割
        sentences = self._split_into_sentences(text)
        
        # 合并句子到合适的块大小
        chunks = self._group_sentences(sentences)
        
        # 创建节点
        nodes = []
        base_metadata = metadata or {}
        
        for i, chunk in enumerate(chunks):
            if not chunk.strip():
                continue
                
            node_metadata = base_metadata.copy()
            node_metadata.update({
                'chunk_index': i,
                'total_chunks': len(chunks)
            })
            
            node = Node.from_text(
                text=chunk,
                metadata=node_metadata
            )
            nodes.append(node)
        
        return nodes
    
    def split_documents(self, documents: List[Dict[str, Any]]) -> List[Node]:
        """批量分割文档"""
        all_nodes = []
        
        for doc in documents:
            text = doc.get('text', '')
            metadata = doc.get('metadata', {})
            
            nodes = self.split_text(text, metadata)
            all_nodes.extend(nodes)
        
        return all_nodes
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """将文本分割成句子"""
        # 使用正则表达式分割句子
        sentences = re.split(self.sentence_endings, text)
        
        # 清理并过滤空句子
        cleaned_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence:
                cleaned_sentences.append(sentence)
        
        return cleaned_sentences
    
    def _group_sentences(self, sentences: List[str]) -> List[str]:
        """将句子组合成合适大小的块"""
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            # 检查加入当前句子后是否超长
            test_chunk = current_chunk + " " + sentence if current_chunk else sentence
            
            if len(test_chunk) <= self.chunk_size:
                current_chunk = test_chunk
            else:
                # 保存当前chunk，开始新chunk
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence
        
        # 保存最后一个chunk
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    计算两个向量的余弦相似度
    
    Args:
        vec1: 向量1
        vec2: 向量2
        
    Returns:
        余弦相似度值 (0-1)
    """
    if not vec1 or not vec2:
        return 0.0
    
    # 转换为numpy数组
    v1 = np.array(vec1)
    v2 = np.array(vec2)
    
    # 计算点积
    dot_product = np.dot(v1, v2)
    
    # 计算模长
    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)
    
    # 避免除零
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    # 计算余弦相似度
    similarity = dot_product / (norm1 * norm2)
    
    # 确保结果在[0, 1]范围内
    return max(0.0, min(1.0, similarity))


def euclidean_distance(vec1: List[float], vec2: List[float]) -> float:
    """
    计算两个向量的欧几里得距离
    
    Args:
        vec1: 向量1
        vec2: 向量2
        
    Returns:
        欧几里得距离
    """
    if not vec1 or not vec2:
        return float('inf')
    
    v1 = np.array(vec1)
    v2 = np.array(vec2)
    
    return float(np.linalg.norm(v1 - v2))


def batch_cosine_similarity(query_vec: List[float], vectors: List[List[float]]) -> List[float]:
    """
    批量计算查询向量与多个向量的余弦相似度
    
    Args:
        query_vec: 查询向量
        vectors: 向量列表
        
    Returns:
        相似度列表
    """
    if not query_vec or not vectors:
        return []
    
    query = np.array(query_vec).reshape(1, -1)
    matrix = np.array(vectors)
    
    # 计算余弦相似度
    similarities = np.dot(query, matrix.T) / (
        np.linalg.norm(query, axis=1, keepdims=True) * 
        np.linalg.norm(matrix, axis=1, keepdims=True).T
    )
    
    return similarities[0].tolist()


def normalize_vector(vector: List[float]) -> List[float]:
    """
    归一化向量
    
    Args:
        vector: 输入向量
        
    Returns:
        归一化后的向量
    """
    if not vector:
        return vector
    
    vec = np.array(vector)
    norm = np.linalg.norm(vec)
    
    if norm == 0:
        return vector
    
    return (vec / norm).tolist()


def filter_metadata(
    items: List[Dict[str, Any]], 
    metadata_filter: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    根据元数据过滤项目
    
    Args:
        items: 项目列表
        metadata_filter: 过滤条件
        
    Returns:
        过滤后的项目列表
    """
    if not metadata_filter:
        return items
    
    filtered_items = []
    
    for item in items:
        metadata = item.get('metadata', {})
        match = True
        
        for key, value in metadata_filter.items():
            if key not in metadata or metadata[key] != value:
                match = False
                break
        
        if match:
            filtered_items.append(item)
    
    return filtered_items


def create_default_splitter(splitter_type: str = "simple", **kwargs) -> BaseSplitter:
    """
    创建默认的文本分块器
    
    Args:
        splitter_type: 分块器类型 ("simple", "sentence")
        **kwargs: 分块器参数
        
    Returns:
        文本分块器实例
    """
    if splitter_type == "simple":
        return SimpleTextSplitter(**kwargs)
    elif splitter_type == "sentence":
        return SentenceSplitter(**kwargs)
    else:
        raise ValueError(f"不支持的分块器类型: {splitter_type}")


def get_vector_dimension(vectors: List[List[float]]) -> Optional[int]:
    """
    获取向量的维度
    
    Args:
        vectors: 向量列表
        
    Returns:
        向量维度，如果列表为空则返回None
    """
    if not vectors:
        return None
    
    return len(vectors[0]) if vectors[0] else None


def validate_vector_dimensions(vectors: List[List[float]]) -> bool:
    """
    验证向量列表中所有向量的维度是否一致
    
    Args:
        vectors: 向量列表
        
    Returns:
        是否所有向量维度一致
    """
    if not vectors:
        return True
    
    if not vectors[0]:
        return True
    
    expected_dim = len(vectors[0])
    
    for vec in vectors:
        if not vec or len(vec) != expected_dim:
            return False
    
    return True 