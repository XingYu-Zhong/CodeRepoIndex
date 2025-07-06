"""
查询检索器实现
负责从嵌入索引中检索相关文档
"""

import os
from typing import List, Dict, Any, Optional, Tuple, Union
import logging

from ..models import BaseEmbeddingProvider, create_embedding_provider
from .base import BaseRetriever
from .node import Node
from .document_store import BaseDocumentStore, create_document_store
from .vector_store import BaseVectorStore, create_vector_store

logger = logging.getLogger(__name__)


class EmbeddingRetriever(BaseRetriever):
    """
    嵌入检索器
    使用向量相似性搜索来检索相关文档
    """
    
    def __init__(
        self,
        embedding_provider: Optional[BaseEmbeddingProvider] = None,
        document_store: Optional[BaseDocumentStore] = None,
        vector_store: Optional[BaseVectorStore] = None,
        persist_dir: Optional[str] = None,
        metadata_only: bool = False,
        **kwargs
    ):
        """
        初始化检索器
        
        Args:
            embedding_provider: 嵌入模型提供商
            document_store: 文档存储
            vector_store: 向量存储
            persist_dir: 持久化目录
            metadata_only: 是否仅用于元数据检索，不需要嵌入提供商
            **kwargs: 其他参数
        """
        # 初始化嵌入提供商
        if embedding_provider is None and not metadata_only:
            try:
                self.embedding_provider = create_embedding_provider()
                logger.info("使用默认嵌入提供商")
            except Exception as e:
                logger.error(f"无法创建默认嵌入提供商: {e}")
                if not metadata_only:
                    raise ValueError("必须提供有效的嵌入提供商或正确配置默认提供商")
                else:
                    self.embedding_provider = None
                    logger.info("元数据检索模式，不需要嵌入提供商")
        else:
            self.embedding_provider = embedding_provider
            if metadata_only and embedding_provider is None:
                logger.info("元数据检索模式，不使用嵌入提供商")
        
        # 初始化存储组件
        self.persist_dir = persist_dir
        if persist_dir:
            doc_store_path = os.path.join(persist_dir, "document_store.json")
            vector_store_path = os.path.join(persist_dir, "vector_store.json")
        else:
            doc_store_path = vector_store_path = None
        
        self.document_store = document_store if document_store is not None else create_document_store(
            persist_path=doc_store_path
        )
        self.vector_store = vector_store if vector_store is not None else create_vector_store(
            persist_path=vector_store_path
        )
        
        logger.info(f"初始化检索器，持久化目录: {persist_dir}")
    
    def retrieve(self, query: str, top_k: int = 10, **kwargs) -> List[Dict[str, Any]]:
        """
        检索相关文档
        
        Args:
            query: 查询文本
            top_k: 返回的结果数量
            **kwargs: 其他参数
            
        Returns:
            检索结果列表，每个结果包含节点信息和相似度分数
        """
        logger.debug(f"检索查询: {query[:100]}...")
        
        if not query.strip():
            logger.warning("查询为空")
            return []
        
        # 生成查询向量
        try:
            query_embedding = self.embedding_provider.get_embedding(query)
        except Exception as e:
            logger.error(f"生成查询向量失败: {e}")
            raise
        
        # 向量搜索
        try:
            vector_results = self.vector_store.query(
                query_embedding=query_embedding,
                top_k=top_k,
                metadata_filter=kwargs.get('metadata_filter')
            )
        except Exception as e:
            logger.error(f"向量搜索失败: {e}")
            raise
        
        if not vector_results:
            logger.debug("向量搜索没有返回结果")
            return []
        
        # 获取对应的文档节点
        node_ids = [result['node_id'] for result in vector_results]
        try:
            nodes = self.document_store.get_nodes(node_ids)
        except Exception as e:
            logger.error(f"获取文档节点失败: {e}")
            raise
        
        # 构建最终结果
        results = []
        node_dict = {node.node_id: node for node in nodes}
        
        for vector_result in vector_results:
            node_id = vector_result['node_id']
            node = node_dict.get(node_id)
            
            if node:
                result = {
                    'node_id': node_id,
                    'text': node.text,
                    'metadata': node.metadata,
                    'score': vector_result['score'],
                    'node': node  # 包含完整的节点对象
                }
                results.append(result)
            else:
                logger.warning(f"节点 {node_id} 在文档存储中不存在")
        
        logger.debug(f"检索完成，返回 {len(results)} 个结果")
        return results
    
    def retrieve_with_scores(self, query: str, top_k: int = 10, **kwargs) -> List[Tuple[Dict[str, Any], float]]:
        """
        检索相关文档并返回相似度分数
        
        Args:
            query: 查询文本
            top_k: 返回的结果数量
            **kwargs: 其他参数
            
        Returns:
            (结果, 分数) 元组列表
        """
        results = self.retrieve(query, top_k, **kwargs)
        return [(result, result['score']) for result in results]
    
    def retrieve_nodes(self, query: str, top_k: int = 10, **kwargs) -> List[Node]:
        """
        检索相关节点对象
        
        Args:
            query: 查询文本
            top_k: 返回的结果数量
            **kwargs: 其他参数
            
        Returns:
            节点对象列表
        """
        results = self.retrieve(query, top_k, **kwargs)
        return [result['node'] for result in results if 'node' in result]
    
    def retrieve_with_threshold(
        self, 
        query: str, 
        threshold: float = 0.7,
        max_results: int = 100,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        基于阈值的检索
        
        Args:
            query: 查询文本
            threshold: 相似度阈值
            max_results: 最大结果数量
            **kwargs: 其他参数
            
        Returns:
            满足阈值的检索结果
        """
        logger.debug(f"阈值检索: {query[:100]}..., 阈值: {threshold}")
        
        # 生成查询向量
        try:
            query_embedding = self.embedding_provider.get_embedding(query)
        except Exception as e:
            logger.error(f"生成查询向量失败: {e}")
            raise
        
        # 使用向量存储的阈值搜索
        try:
            vector_results = self.vector_store.similarity_search_with_threshold(
                query_embedding=query_embedding,
                threshold=threshold,
                max_results=max_results,
                metadata_filter=kwargs.get('metadata_filter')
            )
        except Exception as e:
            logger.error(f"阈值向量搜索失败: {e}")
            raise
        
        if not vector_results:
            logger.debug("阈值搜索没有返回结果")
            return []
        
        # 获取对应的文档节点
        node_ids = [result['node_id'] for result in vector_results]
        try:
            nodes = self.document_store.get_nodes(node_ids)
        except Exception as e:
            logger.error(f"获取文档节点失败: {e}")
            raise
        
        # 构建最终结果
        results = []
        node_dict = {node.node_id: node for node in nodes}
        
        for vector_result in vector_results:
            node_id = vector_result['node_id']
            node = node_dict.get(node_id)
            
            if node:
                result = {
                    'node_id': node_id,
                    'text': node.text,
                    'metadata': node.metadata,
                    'score': vector_result['score'],
                    'node': node
                }
                results.append(result)
        
        logger.debug(f"阈值检索完成，返回 {len(results)} 个结果")
        return results
    
    def retrieve_by_doc_id(self, doc_id: str) -> List[Node]:
        """
        根据文档ID检索所有相关节点
        
        Args:
            doc_id: 文档ID
            
        Returns:
            属于该文档的节点列表
        """
        try:
            return self.document_store.get_nodes_by_doc_id(doc_id)
        except Exception as e:
            logger.error(f"根据文档ID检索失败: {e}")
            raise
    
    def retrieve_by_node_id(self, node_id: str) -> Optional[Node]:
        """
        根据节点ID检索单个节点
        
        Args:
            node_id: 节点ID
            
        Returns:
            检索到的节点，如果不存在则返回None
        """
        try:
            return self.document_store.get_node(node_id)
        except Exception as e:
            logger.error(f"根据节点ID检索失败: {e}")
            return None
    
    def retrieve_by_node_ids(self, node_ids: List[str]) -> List[Node]:
        """
        根据节点ID列表批量检索节点
        
        Args:
            node_ids: 节点ID列表
            
        Returns:
            检索到的节点列表
        """
        try:
            return self.document_store.get_nodes(node_ids)
        except Exception as e:
            logger.error(f"批量检索节点失败: {e}")
            return []
    
    def retrieve_by_metadata(self, metadata_filter: Dict[str, Any], top_k: int = 10) -> List[Node]:
        """
        纯元数据检索（不涉及向量搜索）
        
        Args:
            metadata_filter: 元数据过滤条件
            top_k: 返回的节点数量
            
        Returns:
            匹配的节点列表
        """
        try:
            matching_nodes = self.document_store.search_by_metadata(metadata_filter)
            return matching_nodes[:top_k]
        except Exception as e:
            logger.error(f"元数据检索失败: {e}")
            return []
    
    def retrieve_metadata_contains(self, metadata_key: str, search_value: Any, top_k: int = 10) -> List[Node]:
        """
        搜索元数据包含指定值的节点
        
        Args:
            metadata_key: 元数据键
            search_value: 搜索值
            top_k: 返回的节点数量
            
        Returns:
            匹配的节点列表
        """
        try:
            matching_nodes = self.document_store.search_metadata_contains(metadata_key, search_value)
            return matching_nodes[:top_k]
        except Exception as e:
            logger.error(f"元数据包含检索失败: {e}")
            return []
    
    def retrieve_metadata_range(self, metadata_key: str, min_value=None, max_value=None, top_k: int = 10) -> List[Node]:
        """
        搜索元数据在指定范围内的节点
        
        Args:
            metadata_key: 元数据键
            min_value: 最小值（可选）
            max_value: 最大值（可选）
            top_k: 返回的节点数量
            
        Returns:
            匹配的节点列表
        """
        try:
            matching_nodes = self.document_store.search_metadata_range(metadata_key, min_value, max_value)
            return matching_nodes[:top_k]
        except Exception as e:
            logger.error(f"元数据范围检索失败: {e}")
            return []
    
    def retrieve_by_metadata_exists(self, metadata_keys: List[str], require_all: bool = True, top_k: int = 10) -> List[Node]:
        """
        搜索包含指定元数据键的节点
        
        Args:
            metadata_keys: 元数据键列表
            require_all: 是否要求包含所有键（True）还是任意一个键（False）
            top_k: 返回的节点数量
            
        Returns:
            匹配的节点列表
        """
        try:
            matching_nodes = self.document_store.search_metadata_exists(metadata_keys, require_all)
            return matching_nodes[:top_k]
        except Exception as e:
            logger.error(f"元数据存在性检索失败: {e}")
            return []
    
    def retrieve_hybrid(
        self, 
        query: str, 
        metadata_filter: Optional[Dict[str, Any]] = None,
        top_k: int = 10,
        metadata_weight: float = 0.3,
        vector_weight: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        混合检索：结合向量搜索和元数据过滤
        
        Args:
            query: 查询文本
            metadata_filter: 元数据过滤条件
            top_k: 返回的节点数量
            metadata_weight: 元数据匹配权重
            vector_weight: 向量相似度权重
            
        Returns:
            混合检索结果列表
        """
        try:
            # 先进行向量搜索
            vector_results = self.retrieve(query, top_k * 2, metadata_filter=metadata_filter)
            
            if not metadata_filter:
                return vector_results[:top_k]
            
            # 进行元数据搜索
            metadata_nodes = self.document_store.search_by_metadata(metadata_filter)
            metadata_node_ids = {node.node_id for node in metadata_nodes}
            
            # 为结果重新计算分数
            final_results = []
            for result in vector_results:
                node_id = result['node_id']
                vector_score = result['score']
                
                # 如果节点也匹配元数据，给予额外分数
                metadata_score = 1.0 if node_id in metadata_node_ids else 0.0
                
                # 计算混合分数
                hybrid_score = vector_weight * vector_score + metadata_weight * metadata_score
                
                result_copy = result.copy()
                result_copy['hybrid_score'] = hybrid_score
                result_copy['vector_score'] = vector_score
                result_copy['metadata_score'] = metadata_score
                
                final_results.append(result_copy)
            
            # 按混合分数排序
            final_results.sort(key=lambda x: x['hybrid_score'], reverse=True)
            
            return final_results[:top_k]
            
        except Exception as e:
            logger.error(f"混合检索失败: {e}")
            return []
    
    def get_metadata_values(self, metadata_key: str) -> List[Any]:
        """
        获取指定元数据键的所有唯一值
        
        Args:
            metadata_key: 元数据键
            
        Returns:
            唯一值列表
        """
        try:
            return self.document_store.get_metadata_values(metadata_key)
        except Exception as e:
            logger.error(f"获取元数据值失败: {e}")
            return []
    
    def get_metadata_statistics(self) -> Dict[str, Dict[str, Any]]:
        """
        获取元数据统计信息
        
        Returns:
            元数据统计字典
        """
        try:
            return self.document_store.get_metadata_statistics()
        except Exception as e:
            logger.error(f"获取元数据统计失败: {e}")
            return {}
    
    def retrieve_similar_to_node(self, node_id: str, top_k: int = 10, **kwargs) -> List[Dict[str, Any]]:
        """
        检索与指定节点相似的其他节点
        
        Args:
            node_id: 参考节点ID
            top_k: 返回的结果数量
            **kwargs: 其他参数
            
        Returns:
            相似节点列表
        """
        logger.debug(f"检索与节点 {node_id} 相似的节点")
        
        # 获取参考节点的嵌入向量
        reference_embedding = self.vector_store.get_embedding(node_id)
        if reference_embedding is None:
            logger.error(f"节点 {node_id} 的嵌入向量不存在")
            raise ValueError(f"节点 {node_id} 不存在或没有嵌入向量")
        
        # 执行向量搜索
        try:
            vector_results = self.vector_store.query(
                query_embedding=reference_embedding,
                top_k=top_k + 1,  # +1 因为会包含自己
                metadata_filter=kwargs.get('metadata_filter')
            )
        except Exception as e:
            logger.error(f"相似性搜索失败: {e}")
            raise
        
        # 过滤掉自己
        filtered_results = [
            result for result in vector_results 
            if result['node_id'] != node_id
        ][:top_k]
        
        if not filtered_results:
            logger.debug("没有找到相似的节点")
            return []
        
        # 获取对应的文档节点
        node_ids = [result['node_id'] for result in filtered_results]
        try:
            nodes = self.document_store.get_nodes(node_ids)
        except Exception as e:
            logger.error(f"获取文档节点失败: {e}")
            raise
        
        # 构建最终结果
        results = []
        node_dict = {node.node_id: node for node in nodes}
        
        for vector_result in filtered_results:
            node_id = vector_result['node_id']
            node = node_dict.get(node_id)
            
            if node:
                result = {
                    'node_id': node_id,
                    'text': node.text,
                    'metadata': node.metadata,
                    'score': vector_result['score'],
                    'node': node
                }
                results.append(result)
        
        logger.debug(f"找到 {len(results)} 个相似节点")
        return results
    
    def retrieve_with_context(
        self, 
        query: str, 
        top_k: int = 10,
        context_window: int = 1,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        检索时包含上下文节点
        
        Args:
            query: 查询文本
            top_k: 返回的结果数量
            context_window: 上下文窗口大小（前后各取多少个节点）
            **kwargs: 其他参数
            
        Returns:
            包含上下文的检索结果
        """
        logger.debug(f"上下文检索: {query[:100]}..., 上下文窗口: {context_window}")
        
        # 先进行正常检索
        primary_results = self.retrieve(query, top_k, **kwargs)
        
        if not primary_results or context_window <= 0:
            return primary_results
        
        # 收集需要获取上下文的节点
        context_node_ids = set()
        
        for result in primary_results:
            node = result.get('node')
            if not node or 'chunk_index' not in node.metadata:
                continue
            
            doc_id = node.metadata.get('doc_id')
            chunk_index = node.metadata.get('chunk_index')
            total_chunks = node.metadata.get('total_chunks', 0)
            
            if doc_id is None or chunk_index is None:
                continue
            
            # 添加前后的节点
            for offset in range(-context_window, context_window + 1):
                if offset == 0:
                    continue  # 跳过自己
                
                target_index = chunk_index + offset
                if 0 <= target_index < total_chunks:
                    # 这里需要根据实际的节点ID规则来构造
                    # 简化处理：尝试从同一文档的所有节点中找到对应的chunk_index
                    doc_nodes = self.document_store.get_nodes_by_doc_id(doc_id)
                    for doc_node in doc_nodes:
                        if doc_node.metadata.get('chunk_index') == target_index:
                            context_node_ids.add(doc_node.node_id)
                            break
        
        # 获取上下文节点
        if context_node_ids:
            context_nodes = self.document_store.get_nodes(list(context_node_ids))
            
            # 将上下文添加到结果中
            for result in primary_results:
                node = result.get('node')
                if not node:
                    continue
                
                doc_id = node.metadata.get('doc_id')
                chunk_index = node.metadata.get('chunk_index')
                
                if doc_id and chunk_index is not None:
                    # 收集该节点的上下文
                    node_context = []
                    for ctx_node in context_nodes:
                        if (ctx_node.metadata.get('doc_id') == doc_id and
                            ctx_node.metadata.get('chunk_index') is not None):
                            ctx_index = ctx_node.metadata.get('chunk_index')
                            if abs(ctx_index - chunk_index) <= context_window:
                                node_context.append(ctx_node)
                    
                    # 按chunk_index排序
                    node_context.sort(key=lambda x: x.metadata.get('chunk_index', 0))
                    result['context_nodes'] = node_context
        
        logger.debug(f"上下文检索完成，返回 {len(primary_results)} 个结果")
        return primary_results
    
    def load_index(self, persist_dir: Optional[str] = None) -> None:
        """
        加载索引
        
        Args:
            persist_dir: 持久化目录，如果不提供则使用初始化时的目录
        """
        load_dir = persist_dir or self.persist_dir
        if not load_dir:
            raise ValueError("没有指定持久化目录")
        
        try:
            doc_store_path = os.path.join(load_dir, "document_store.json")
            vector_store_path = os.path.join(load_dir, "vector_store.json")
            
            self.document_store.load_from_path(doc_store_path)
            self.vector_store.load_from_path(vector_store_path)
            
            logger.info(f"索引已从 {load_dir} 加载到检索器")
        except Exception as e:
            logger.error(f"加载索引失败: {e}")
            raise
    
    def refresh(self) -> None:
        """
        刷新检索器，重新加载最新的索引数据
        
        当indexer构建了新的索引但retriever使用独立存储时，
        可以调用此方法来同步最新数据。
        
        注意：如果retriever和indexer共享存储实例，则不需要调用此方法。
        """
        if self.persist_dir:
            logger.info("刷新检索器索引数据")
            self.load_index(self.persist_dir)
        else:
            logger.warning("没有配置持久化目录，无法刷新索引")
    
    def sync_with_indexer(self, indexer) -> None:
        """
        与指定的indexer同步存储实例
        
        Args:
            indexer: 要同步的索引构建器
        """
        logger.info("与indexer同步存储实例")
        self.document_store = indexer.document_store
        self.vector_store = indexer.vector_store
        logger.info("存储实例同步完成")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取检索器统计信息
        
        Returns:
            统计信息字典
        """
        doc_stats = self.document_store.get_statistics()
        vector_stats = self.vector_store.get_statistics()
        
        return {
            'documents': doc_stats,
            'vectors': vector_stats,
            'embedding_model': self.embedding_provider.get_model_name(),
            'persist_dir': self.persist_dir
        }
    
    def is_ready(self) -> bool:
        """
        检查检索器是否准备就绪
        
        Returns:
            是否可以进行检索
        """
        return (len(self.document_store) > 0 and 
                len(self.vector_store) > 0 and
                self.embedding_provider.is_available())


def create_retriever(
    embedding_provider: Optional[BaseEmbeddingProvider] = None,
    persist_dir: Optional[str] = None,
    **kwargs
) -> EmbeddingRetriever:
    """
    创建检索器
    
    Args:
        embedding_provider: 嵌入提供商
        persist_dir: 持久化目录
        **kwargs: 其他参数
        
    Returns:
        检索器实例
    """
    return EmbeddingRetriever(
        embedding_provider=embedding_provider,
        persist_dir=persist_dir,
        **kwargs
    ) 