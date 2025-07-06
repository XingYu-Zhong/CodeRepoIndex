"""
向量存储组件实现
负责存储向量嵌入并提供相似性搜索功能
"""

import json
import os
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import logging

from .base import BaseVectorStore
from .utils import cosine_similarity, batch_cosine_similarity, filter_metadata

logger = logging.getLogger(__name__)


class SimpleVectorStore(BaseVectorStore):
    """
    简单的向量存储实现
    基于内存存储，使用暴力搜索进行相似性查询
    """
    
    def __init__(self, persist_path: Optional[str] = None):
        """
        初始化向量存储
        
        Args:
            persist_path: 持久化文件路径，如果提供则自动加载
        """
        # 核心存储：node_id -> embedding vector
        self._embeddings: Dict[str, List[float]] = {}
        
        # 元数据存储：node_id -> metadata
        self._metadata: Dict[str, Dict[str, Any]] = {}
        
        # 如果提供了路径，尝试加载
        if persist_path and os.path.exists(persist_path):
            try:
                self.load_from_path(persist_path)
                logger.info(f"从 {persist_path} 加载了 {len(self._embeddings)} 个向量")
            except Exception as e:
                logger.warning(f"无法从 {persist_path} 加载向量存储: {e}")
    
    def add(self, node_id: str, embedding: List[float], metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        添加向量到存储中
        
        Args:
            node_id: 节点ID
            embedding: 嵌入向量
            metadata: 可选的元数据
            
        Raises:
            ValueError: 如果向量格式无效
        """
        if not embedding:
            raise ValueError("嵌入向量不能为空")
        
        if not isinstance(embedding, list):
            raise ValueError("嵌入向量必须是列表格式")
        
        # 验证向量维度一致性
        if self._embeddings and len(embedding) != len(next(iter(self._embeddings.values()))):
            existing_dim = len(next(iter(self._embeddings.values())))
            raise ValueError(f"向量维度不一致：期望 {existing_dim}，实际 {len(embedding)}")
        
        if node_id in self._embeddings:
            logger.warning(f"向量 {node_id} 已存在，将被覆盖")
        
        self._embeddings[node_id] = embedding
        if metadata:
            self._metadata[node_id] = metadata
        
        logger.debug(f"添加向量 {node_id}，维度: {len(embedding)}")
    
    def add_batch(self, data: List[Tuple[str, List[float], Optional[Dict[str, Any]]]]) -> None:
        """
        批量添加向量
        
        Args:
            data: (node_id, embedding, metadata) 元组列表
        """
        for node_id, embedding, metadata in data:
            self.add(node_id, embedding, metadata)
        
        logger.debug(f"批量添加了 {len(data)} 个向量")
    
    def query(
        self, 
        query_embedding: List[float], 
        top_k: int = 10,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        查询最相似的向量
        
        Args:
            query_embedding: 查询向量
            top_k: 返回的结果数量
            metadata_filter: 元数据过滤条件
            
        Returns:
            结果列表，每个结果包含 node_id, score, metadata
        """
        if not query_embedding:
            raise ValueError("查询向量不能为空")
        
        if not self._embeddings:
            return []
        
        # 获取所有向量和对应的node_id
        node_ids = list(self._embeddings.keys())
        embeddings = list(self._embeddings.values())
        
        # 应用元数据过滤
        if metadata_filter:
            filtered_items = []
            for node_id in node_ids:
                metadata = self._metadata.get(node_id, {})
                match = True
                for key, value in metadata_filter.items():
                    if key not in metadata or metadata[key] != value:
                        match = False
                        break
                if match:
                    filtered_items.append({
                        'node_id': node_id,
                        'embedding': self._embeddings[node_id],
                        'metadata': metadata
                    })
            
            if not filtered_items:
                return []
            
            node_ids = [item['node_id'] for item in filtered_items]
            embeddings = [item['embedding'] for item in filtered_items]
        
        # 计算相似度
        try:
            similarities = batch_cosine_similarity(query_embedding, embeddings)
        except Exception as e:
            logger.error(f"计算相似度失败: {e}")
            # 回退到逐个计算
            similarities = []
            for embedding in embeddings:
                sim = cosine_similarity(query_embedding, embedding)
                similarities.append(sim)
        
        # 排序并获取top_k
        results = []
        for i, (node_id, similarity) in enumerate(zip(node_ids, similarities)):
            results.append({
                'node_id': node_id,
                'score': float(similarity),
                'metadata': self._metadata.get(node_id, {})
            })
        
        # 按相似度降序排序
        results.sort(key=lambda x: x['score'], reverse=True)
        
        # 返回top_k结果
        return results[:top_k]
    
    def delete(self, node_id: str) -> bool:
        """
        删除指定向量
        
        Args:
            node_id: 节点ID
            
        Returns:
            是否成功删除
        """
        deleted = False
        
        if node_id in self._embeddings:
            del self._embeddings[node_id]
            deleted = True
        
        if node_id in self._metadata:
            del self._metadata[node_id]
        
        if deleted:
            logger.debug(f"删除向量 {node_id}")
        else:
            logger.warning(f"尝试删除不存在的向量 {node_id}")
        
        return deleted
    
    def delete_batch(self, node_ids: List[str]) -> int:
        """
        批量删除向量
        
        Args:
            node_ids: 节点ID列表
            
        Returns:
            成功删除的向量数量
        """
        deleted_count = 0
        for node_id in node_ids:
            if self.delete(node_id):
                deleted_count += 1
        
        return deleted_count
    
    def get_all_node_ids(self) -> List[str]:
        """
        获取所有节点ID
        
        Returns:
            节点ID列表
        """
        return list(self._embeddings.keys())
    
    def get_embedding(self, node_id: str) -> Optional[List[float]]:
        """
        获取指定节点的嵌入向量
        
        Args:
            node_id: 节点ID
            
        Returns:
            嵌入向量，如果不存在则返回None
        """
        return self._embeddings.get(node_id)
    
    def get_metadata(self, node_id: str) -> Optional[Dict[str, Any]]:
        """
        获取指定节点的元数据
        
        Args:
            node_id: 节点ID
            
        Returns:
            元数据，如果不存在则返回None
        """
        return self._metadata.get(node_id)
    
    def update_metadata(self, node_id: str, metadata: Dict[str, Any]) -> bool:
        """
        更新节点的元数据
        
        Args:
            node_id: 节点ID
            metadata: 新的元数据
            
        Returns:
            是否成功更新
        """
        if node_id not in self._embeddings:
            logger.warning(f"节点 {node_id} 不存在，无法更新元数据")
            return False
        
        self._metadata[node_id] = metadata
        logger.debug(f"更新节点 {node_id} 的元数据")
        return True
    
    def size(self) -> int:
        """
        获取存储的向量数量
        
        Returns:
            向量数量
        """
        return len(self._embeddings)
    
    def get_dimension(self) -> Optional[int]:
        """
        获取向量维度
        
        Returns:
            向量维度，如果没有向量则返回None
        """
        if not self._embeddings:
            return None
        
        return len(next(iter(self._embeddings.values())))
    
    def clear(self) -> None:
        """清空所有向量"""
        self._embeddings.clear()
        self._metadata.clear()
        logger.info("清空了向量存储")
    
    def persist(self, filepath: str) -> None:
        """
        持久化到磁盘
        
        Args:
            filepath: 文件路径
            
        Raises:
            IOError: 如果写入失败
        """
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            data = {
                'embeddings': self._embeddings,
                'metadata': self._metadata,
                'info': {
                    'total_vectors': len(self._embeddings),
                    'dimension': self.get_dimension(),
                    'version': '1.0'
                }
            }
            
            # 写入JSON文件
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"成功保存 {len(self._embeddings)} 个向量到 {filepath}")
            
        except Exception as e:
            logger.error(f"保存向量存储失败: {e}")
            raise IOError(f"无法保存到 {filepath}: {e}")
    
    def load_from_path(self, filepath: str) -> None:
        """
        从磁盘加载
        
        Args:
            filepath: 文件路径
            
        Raises:
            IOError: 如果读取失败
            ValueError: 如果数据格式错误
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 验证数据格式
            if 'embeddings' not in data:
                raise ValueError("数据格式错误：缺少 'embeddings' 字段")
            
            # 清空当前数据
            self._embeddings.clear()
            self._metadata.clear()
            
            # 加载嵌入向量
            embeddings_data = data['embeddings']
            for node_id, embedding in embeddings_data.items():
                if not isinstance(embedding, list):
                    logger.warning(f"跳过无效向量 {node_id}: 不是列表格式")
                    continue
                self._embeddings[node_id] = embedding
            
            # 加载元数据（如果存在）
            if 'metadata' in data:
                metadata_data = data['metadata']
                for node_id, metadata in metadata_data.items():
                    if node_id in self._embeddings:  # 只保留有对应向量的元数据
                        self._metadata[node_id] = metadata
            
            logger.info(f"成功从 {filepath} 加载 {len(self._embeddings)} 个向量")
            
        except FileNotFoundError:
            logger.warning(f"文件 {filepath} 不存在")
            raise IOError(f"文件不存在: {filepath}")
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            raise ValueError(f"无效的JSON格式: {e}")
        except Exception as e:
            logger.error(f"加载向量存储失败: {e}")
            raise IOError(f"无法从 {filepath} 加载: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取向量存储统计信息
        
        Returns:
            统计信息字典
        """
        if not self._embeddings:
            return {
                'total_vectors': 0,
                'dimension': None,
                'has_metadata': 0,
                'metadata_keys': []
            }
        
        # 统计有元数据的向量数量
        has_metadata_count = len(self._metadata)
        
        # 收集所有元数据键
        metadata_keys = set()
        for metadata in self._metadata.values():
            if isinstance(metadata, dict):
                metadata_keys.update(metadata.keys())
        
        return {
            'total_vectors': len(self._embeddings),
            'dimension': self.get_dimension(),
            'has_metadata': has_metadata_count,
            'metadata_keys': list(metadata_keys)
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取向量存储统计信息（get_statistics的别名）
        
        Returns:
            统计信息字典
        """
        stats = self.get_statistics()
        return {
            'total_vectors': stats['total_vectors'],
            'storage_type': 'SimpleVectorStore',
            'dimension': stats['dimension']
        }
    
    def similarity_search_with_threshold(
        self, 
        query_embedding: List[float], 
        threshold: float = 0.7,
        max_results: int = 100,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        基于阈值的相似性搜索
        
        Args:
            query_embedding: 查询向量
            threshold: 相似度阈值
            max_results: 最大结果数量
            metadata_filter: 元数据过滤条件
            
        Returns:
            满足阈值的结果列表
        """
        # 获取更多结果然后过滤
        initial_results = self.query(
            query_embedding, 
            top_k=min(max_results * 2, len(self._embeddings)),
            metadata_filter=metadata_filter
        )
        
        # 过滤低于阈值的结果
        filtered_results = [
            result for result in initial_results 
            if result['score'] >= threshold
        ]
        
        return filtered_results[:max_results]
    
    def __len__(self) -> int:
        """返回向量数量"""
        return len(self._embeddings)
    
    def __contains__(self, node_id: str) -> bool:
        """检查向量是否存在"""
        return node_id in self._embeddings


def create_vector_store(
    store_type: str = "simple", 
    persist_path: Optional[str] = None,
    **kwargs
) -> BaseVectorStore:
    """
    创建向量存储实例
    
    Args:
        store_type: 存储类型，目前只支持 "simple"
        persist_path: 持久化路径
        **kwargs: 其他参数
        
    Returns:
        向量存储实例
        
    Raises:
        ValueError: 如果存储类型不支持
    """
    if store_type == "simple":
        return SimpleVectorStore(persist_path=persist_path, **kwargs)
    else:
        raise ValueError(f"不支持的向量存储类型: {store_type}") 