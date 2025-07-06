"""
索引构建器实现
负责将文档转换为可搜索的嵌入索引
"""

import os
from typing import List, Dict, Any, Optional, Union, Callable
import logging

from ..models import BaseEmbeddingProvider, create_embedding_provider
from .base import BaseIndexer, BaseSplitter
from .node import Node, Document
from .document_store import BaseDocumentStore, create_document_store
from .vector_store import BaseVectorStore, create_vector_store
from .utils import create_default_splitter

logger = logging.getLogger(__name__)


class EmbeddingIndexer(BaseIndexer):
    """
    嵌入索引构建器
    集成文档存储、向量存储和嵌入模型，构建完整的可搜索索引
    """
    
    def __init__(
        self,
        embedding_provider: Optional[BaseEmbeddingProvider] = None,
        document_store: Optional[BaseDocumentStore] = None,
        vector_store: Optional[BaseVectorStore] = None,
        text_splitter: Optional[BaseSplitter] = None,
        embed_batch_size: int = 10,
        persist_dir: Optional[str] = None,
        **kwargs
    ):
        """
        初始化索引构建器
        
        Args:
            embedding_provider: 嵌入模型提供商
            document_store: 文档存储
            vector_store: 向量存储
            text_splitter: 文本分块器
            embed_batch_size: 批量嵌入大小
            persist_dir: 持久化目录
            **kwargs: 其他参数
        """
        # 初始化嵌入提供商
        if embedding_provider is None:
            # 使用默认配置创建嵌入提供商
            try:
                self.embedding_provider = create_embedding_provider()
                logger.info("使用默认嵌入提供商")
            except Exception as e:
                logger.error(f"无法创建默认嵌入提供商: {e}")
                raise ValueError("必须提供有效的嵌入提供商或正确配置默认提供商")
        else:
            self.embedding_provider = embedding_provider
        
        # 初始化存储组件
        self.persist_dir = persist_dir
        if persist_dir:
            os.makedirs(persist_dir, exist_ok=True)
            doc_store_path = os.path.join(persist_dir, "document_store.json")
            vector_store_path = os.path.join(persist_dir, "vector_store.json")
        else:
            doc_store_path = vector_store_path = None
        
        self.document_store = document_store or create_document_store(
            persist_path=doc_store_path
        )
        self.vector_store = vector_store or create_vector_store(
            persist_path=vector_store_path
        )
        
        # 初始化文本分块器
        self.text_splitter = text_splitter or create_default_splitter()
        
        # 其他配置
        self.embed_batch_size = embed_batch_size
        
        logger.info(f"初始化索引构建器，持久化目录: {persist_dir}")
    
    def build_index(self, documents: List[Dict[str, Any]], **kwargs) -> None:
        """
        构建索引
        
        Args:
            documents: 文档列表，每个文档包含 'text' 和可选的 'metadata'
            **kwargs: 其他参数
        """
        logger.info(f"开始构建索引，文档数量: {len(documents)}")
        
        if not documents:
            logger.warning("没有文档需要索引")
            return
        
        # 清空现有索引（如果指定）
        if kwargs.get('clear_existing', False):
            self.clear_index()
        
        # 处理每个文档
        total_nodes = 0
        for i, doc in enumerate(documents):
            try:
                nodes_count = self._process_document(doc, doc_index=i)
                total_nodes += nodes_count
                logger.debug(f"处理文档 {i+1}/{len(documents)}，生成 {nodes_count} 个节点")
            except Exception as e:
                logger.error(f"处理文档 {i} 失败: {e}")
                if not kwargs.get('ignore_errors', False):
                    raise
        
        logger.info(f"索引构建完成，总共生成 {total_nodes} 个节点")
        
        # 持久化（如果配置了持久化目录）
        if self.persist_dir:
            self.persist()
    
    def add_document(self, document: Dict[str, Any], **kwargs) -> None:
        """
        添加单个文档到索引
        
        Args:
            document: 文档字典，包含 'text' 和可选的 'metadata'
            **kwargs: 其他参数
        """
        logger.debug("添加单个文档到索引")
        
        try:
            nodes_count = self._process_document(document)
            logger.info(f"成功添加文档，生成 {nodes_count} 个节点")
            
            # 如果配置了持久化，立即保存
            if self.persist_dir and kwargs.get('auto_persist', True):
                self.persist()
                
        except Exception as e:
            logger.error(f"添加文档失败: {e}")
            raise
    
    def add_documents_from_files(
        self, 
        file_paths: List[str], 
        file_reader: Optional[Callable[[str], str]] = None,
        **kwargs
    ) -> None:
        """
        从文件添加文档
        
        Args:
            file_paths: 文件路径列表
            file_reader: 自定义文件读取函数
            **kwargs: 其他参数
        """
        logger.info(f"从 {len(file_paths)} 个文件构建索引")
        
        documents = []
        for file_path in file_paths:
            try:
                # 使用自定义读取器或默认读取器
                if file_reader:
                    text = file_reader(file_path)
                else:
                    text = self._default_file_reader(file_path)
                
                # 创建文档元数据
                metadata = {
                    'file_path': file_path,
                    'file_name': os.path.basename(file_path),
                    'file_extension': os.path.splitext(file_path)[1]
                }
                metadata.update(kwargs.get('metadata', {}))
                
                documents.append({
                    'text': text,
                    'metadata': metadata
                })
                
            except Exception as e:
                logger.error(f"读取文件 {file_path} 失败: {e}")
                if not kwargs.get('ignore_errors', False):
                    raise
        
        # 构建索引
        self.build_index(documents, **kwargs)
    
    def _process_document(self, document: Dict[str, Any], doc_index: Optional[int] = None) -> int:
        """
        处理单个文档
        
        Args:
            document: 文档字典
            doc_index: 文档索引
            
        Returns:
            生成的节点数量
        """
        text = document.get('text', '')
        metadata = document.get('metadata', {})
        
        if not text.strip():
            logger.warning("跳过空文档")
            return 0
        
        # 添加文档级别的元数据
        if doc_index is not None:
            metadata['doc_index'] = doc_index
        
        # 文本分块
        try:
            nodes = self.text_splitter.split_text(text, metadata)
            logger.debug(f"文档分块完成，生成 {len(nodes)} 个节点")
        except Exception as e:
            logger.error(f"文档分块失败: {e}")
            raise
        
        if not nodes:
            logger.warning("文档分块后没有生成节点")
            return 0
        
        # 批量生成嵌入向量
        try:
            self._generate_embeddings_for_nodes(nodes)
        except Exception as e:
            logger.error(f"生成嵌入向量失败: {e}")
            raise
        
        # 存储节点到文档存储
        try:
            self.document_store.add_nodes(nodes)
        except Exception as e:
            logger.error(f"存储节点到文档存储失败: {e}")
            raise
        
        # 存储向量到向量存储
        try:
            vector_data = []
            for node in nodes:
                if node.embedding:
                    vector_data.append((
                        node.node_id,
                        node.embedding,
                        {'doc_id': metadata.get('doc_id', node.node_id)}
                    ))
            
            if vector_data:
                self.vector_store.add_batch(vector_data)
                logger.debug(f"存储了 {len(vector_data)} 个向量")
            
        except Exception as e:
            logger.error(f"存储向量失败: {e}")
            raise
        
        return len(nodes)
    
    def _generate_embeddings_for_nodes(self, nodes: List[Node]) -> None:
        """
        为节点生成嵌入向量
        
        Args:
            nodes: 节点列表
        """
        if not nodes:
            return
        
        logger.debug(f"为 {len(nodes)} 个节点生成嵌入向量")
        
        # 批量处理
        for i in range(0, len(nodes), self.embed_batch_size):
            batch_nodes = nodes[i:i + self.embed_batch_size]
            
            try:
                # 准备文本列表
                texts = []
                for node in batch_nodes:
                    # 获取包含元数据的文本用于嵌入
                    embedding_text = node.get_text_embedding_with_metadata()
                    texts.append(embedding_text)
                
                # 批量生成嵌入
                embeddings = self.embedding_provider.get_embeddings_batch(texts)
                
                # 将嵌入向量分配给节点
                for node, embedding in zip(batch_nodes, embeddings):
                    node.embedding = embedding
                
                logger.debug(f"批次 {i//self.embed_batch_size + 1} 生成嵌入完成")
                
            except Exception as e:
                logger.error(f"批量生成嵌入失败: {e}")
                # 回退到单个生成
                self._generate_embeddings_single(batch_nodes)
    
    def _generate_embeddings_single(self, nodes: List[Node]) -> None:
        """
        单个生成嵌入向量（回退方案）
        
        Args:
            nodes: 节点列表
        """
        logger.debug(f"回退到单个生成嵌入，节点数: {len(nodes)}")
        
        for node in nodes:
            try:
                embedding_text = node.get_text_embedding_with_metadata()
                embedding = self.embedding_provider.get_embedding(embedding_text)
                node.embedding = embedding
            except Exception as e:
                logger.error(f"为节点 {node.node_id} 生成嵌入失败: {e}")
                # 设置为None，这样在后续处理中会被跳过
                node.embedding = None
    
    def _default_file_reader(self, file_path: str) -> str:
        """
        默认的文件读取器
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件内容
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # 尝试其他编码
            for encoding in ['gbk', 'latin-1']:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        return f.read()
                except UnicodeDecodeError:
                    continue
            raise ValueError(f"无法读取文件 {file_path}：编码错误")
    
    def clear_index(self) -> None:
        """清空索引"""
        logger.info("清空索引")
        self.document_store.clear()
        self.vector_store.clear()
    
    def persist(self) -> None:
        """持久化索引"""
        if not self.persist_dir:
            logger.warning("没有配置持久化目录，跳过持久化")
            return
        
        try:
            doc_store_path = os.path.join(self.persist_dir, "document_store.json")
            vector_store_path = os.path.join(self.persist_dir, "vector_store.json")
            
            self.document_store.persist(doc_store_path)
            self.vector_store.persist(vector_store_path)
            
            logger.info(f"索引已持久化到 {self.persist_dir}")
        except Exception as e:
            logger.error(f"持久化失败: {e}")
            raise
    
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
            
            logger.info(f"索引已从 {load_dir} 加载")
        except Exception as e:
            logger.error(f"加载索引失败: {e}")
            raise
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取索引统计信息
        
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
    
    def update_document(self, doc_id: str, new_document: Dict[str, Any]) -> None:
        """
        更新文档
        
        Args:
            doc_id: 文档ID
            new_document: 新的文档内容
        """
        logger.info(f"更新文档 {doc_id}")
        
        # 删除旧的节点
        old_nodes = self.document_store.get_nodes_by_doc_id(doc_id)
        old_node_ids = [node.node_id for node in old_nodes]
        
        # 从存储中删除
        self.document_store.delete_nodes(old_node_ids)
        self.vector_store.delete_batch(old_node_ids)
        
        # 添加新文档
        new_document['metadata'] = new_document.get('metadata', {})
        new_document['metadata']['doc_id'] = doc_id
        
        self.add_document(new_document)
        
        logger.info(f"文档 {doc_id} 更新完成")
    
    def delete_document(self, doc_id: str) -> bool:
        """
        删除文档
        
        Args:
            doc_id: 文档ID
            
        Returns:
            是否成功删除
        """
        logger.info(f"删除文档 {doc_id}")
        
        # 获取相关节点
        nodes = self.document_store.get_nodes_by_doc_id(doc_id)
        if not nodes:
            logger.warning(f"文档 {doc_id} 不存在")
            return False
        
        node_ids = [node.node_id for node in nodes]
        
        # 从存储中删除
        doc_deleted = self.document_store.delete_nodes(node_ids)
        vector_deleted = self.vector_store.delete_batch(node_ids)
        
        logger.info(f"删除文档 {doc_id}，删除了 {doc_deleted} 个文档节点，{vector_deleted} 个向量")
        
        return doc_deleted > 0


def create_indexer(
    embedding_provider: Optional[BaseEmbeddingProvider] = None,
    persist_dir: Optional[str] = None,
    **kwargs
) -> EmbeddingIndexer:
    """
    创建索引构建器
    
    Args:
        embedding_provider: 嵌入提供商
        persist_dir: 持久化目录
        **kwargs: 其他参数
        
    Returns:
        索引构建器实例
    """
    return EmbeddingIndexer(
        embedding_provider=embedding_provider,
        persist_dir=persist_dir,
        **kwargs
    ) 