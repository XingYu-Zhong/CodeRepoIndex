"""
Storage适配器模块

将embedding模块适配成storage接口，使现有代码可以无缝切换到embedding模块。
"""

import logging
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from pathlib import Path

from ..embeddings import (
    create_indexer, 
    create_retriever, 
    EmbeddingIndexer, 
    EmbeddingRetriever
)
from ..models import create_embedding_provider
from .models import CodeBlock, RepositoryIndex, SearchQuery, SearchResult

logger = logging.getLogger(__name__)


class EmbeddingStorageAdapter:
    """
    Embedding存储适配器
    
    将embedding模块的EmbeddingIndexer和EmbeddingRetriever包装成storage接口，
    使现有的searcher和indexer代码可以无缝切换到embedding模块。
    """
    
    def __init__(
        self,
        storage_path: str = "./storage",
        embedding_provider=None,
        **kwargs
    ):
        """
        初始化适配器
        
        Args:
            storage_path: 存储路径
            embedding_provider: 嵌入提供商
            **kwargs: 其他配置参数
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # 创建嵌入提供商
        if embedding_provider is None:
            try:
                # 只传递ModelConfig支持的参数
                model_params = {}
                supported_params = [
                    'provider_type', 'model_name', 'api_key', 'base_url', 
                    'max_tokens', 'temperature', 'timeout', 'extra_params'
                ]
                
                for param in supported_params:
                    if param in kwargs:
                        model_params[param] = kwargs[param]
                
                # 将不支持的参数放入extra_params
                extra_params = model_params.get('extra_params', {})
                for key, value in kwargs.items():
                    if key not in supported_params:
                        extra_params[key] = value
                
                if extra_params:
                    model_params['extra_params'] = extra_params
                
                self.embedding_provider = create_embedding_provider(**model_params)
                logger.info("使用默认嵌入提供商")
            except Exception as e:
                logger.error(f"无法创建嵌入提供商: {e}")
                raise ValueError("必须提供有效的嵌入提供商")
        else:
            self.embedding_provider = embedding_provider
        
        # 创建索引器和检索器
        self.indexer = create_indexer(
            embedding_provider=self.embedding_provider,
            persist_dir=str(self.storage_path),
            **kwargs
        )
        
        self.retriever = create_retriever(
            embedding_provider=self.embedding_provider,
            persist_dir=str(self.storage_path),
            document_store=self.indexer.document_store,
            vector_store=self.indexer.vector_store,
            **kwargs
        )
        
        # 兼容性属性（为了支持旧代码）
        self.code_block_storage = self  # 自身就是code_block_storage
        self.vector_storage = self.indexer.vector_store  # 向量存储
        
        # 仓库索引缓存
        self._repository_indexes: Dict[str, RepositoryIndex] = {}
        self._search_history: List[SearchQuery] = []
        
        # 元数据存储（简单的JSON文件存储）
        self._metadata: Dict[str, Any] = {}
        self.metadata_storage = self._create_metadata_storage()
        
        # 加载持久化数据
        self._load_repository_indexes()
        self._load_search_history()
        self._load_metadata()
        
        logger.info(f"Embedding存储适配器初始化完成: {storage_path}")
    
    def _create_metadata_storage(self):
        """创建元数据存储对象"""
        class MetadataStorage:
            def __init__(self, adapter):
                self.adapter = adapter
            
            def set_metadata(self, key: str, value: Any) -> None:
                """设置元数据"""
                self.adapter._metadata[key] = value
                self.adapter._persist_metadata()
            
            def get_metadata(self, key: str, default=None) -> Any:
                """获取元数据"""
                return self.adapter._metadata.get(key, default)
            
            def delete_metadata(self, key: str) -> bool:
                """删除元数据"""
                if key in self.adapter._metadata:
                    del self.adapter._metadata[key]
                    self.adapter._persist_metadata()
                    return True
                return False
            
            def list_metadata_keys(self) -> List[str]:
                """列出所有元数据键"""
                return list(self.adapter._metadata.keys())
        
        return MetadataStorage(self)
    
    def connect(self) -> None:
        """连接存储后端"""
        # embedding模块不需要显式连接
        logger.info("Embedding存储适配器连接成功")
    
    def disconnect(self) -> None:
        """断开存储连接"""
        # embedding模块不需要显式断开连接
        logger.info("Embedding存储适配器连接已断开")
    
    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        return {
            "storage_path": str(self.storage_path),
            "indexer_ready": self.indexer is not None,
            "retriever_ready": self.retriever is not None,
            "embedding_provider_ready": self.embedding_provider is not None,
            "documents_count": len(self.indexer.document_store),
            "vectors_count": len(self.indexer.vector_store),
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """获取存储统计信息"""
        return {
            "total_blocks": len(self.indexer.document_store),
            "total_vectors": len(self.indexer.vector_store),
            "storage_size": "由embedding模块管理",
            "storage_path": str(self.storage_path),
            "embedding_model": self.embedding_provider.get_model_name() if self.embedding_provider else "未知",
        }
    
    # ========== 代码块相关方法 ==========
    
    def save_code_block(self, code_block: CodeBlock) -> None:
        """保存代码块"""
        # 转换为Node并添加到embedding存储
        node = code_block.to_node()
        self.indexer.document_store.add_node(node)
        
        # 如果有embedding，也添加到向量存储
        if code_block.embedding:
            self.indexer.vector_store.add(
                node_id=node.node_id,
                embedding=code_block.embedding,
                metadata=node.metadata
            )
    
    def save_code_blocks(self, code_blocks: List[CodeBlock]) -> None:
        """批量保存代码块"""
        nodes = [block.to_node() for block in code_blocks]
        self.indexer.document_store.add_nodes(nodes)
        
        # 添加向量
        vector_data = []
        for block in code_blocks:
            if block.embedding:
                vector_data.append((
                    block.block_id,
                    block.embedding,
                    block.to_node().metadata
                ))
        
        if vector_data:
            self.indexer.vector_store.add_batch(vector_data)
    
    def save_code_block_with_vector(self, code_block: CodeBlock) -> None:
        """保存代码块及其向量（与原storage接口兼容）"""
        self.save_code_block(code_block)
    
    def get_code_block(self, block_id: str) -> Optional[CodeBlock]:
        """获取单个代码块"""
        node = self.indexer.document_store.get_node(block_id)
        if node:
            return CodeBlock.from_node(node)
        return None
    
    def query_code_blocks(
        self,
        repository_id: Optional[str] = None,
        language: Optional[str] = None,
        file_path: Optional[str] = None,
        code_block_ids: Optional[List[str]] = None,
        limit: int = 100
    ) -> List[CodeBlock]:
        """查询代码块"""
        if code_block_ids:
            # 根据ID列表查询
            nodes = self.indexer.document_store.get_nodes(code_block_ids)
        else:
            # 根据元数据过滤查询
            metadata_filter = {}
            if repository_id:
                metadata_filter["repository_id"] = repository_id
            if language:
                metadata_filter["language"] = language
            if file_path:
                metadata_filter["file_path"] = file_path
            
            nodes = self.retriever.retrieve_by_metadata(metadata_filter, top_k=limit)
        
        return [CodeBlock.from_node(node) for node in nodes]
    
    def delete_code_block(self, block_id: str) -> bool:
        """删除代码块"""
        # 从文档存储中删除
        doc_deleted = self.indexer.document_store.delete_node(block_id)
        # 从向量存储中删除
        vec_deleted = self.indexer.vector_store.delete(block_id)
        return doc_deleted or vec_deleted
    
    def get_blocks_by_file(
        self,
        file_path: str,
        repository_id: Optional[str] = None,
        limit: int = 100
    ) -> List[CodeBlock]:
        """根据文件路径获取代码块"""
        metadata_filter = {"file_path": file_path}
        if repository_id:
            metadata_filter["repository_id"] = repository_id
        
        nodes = self.retriever.retrieve_by_metadata(metadata_filter, top_k=limit)
        return [CodeBlock.from_node(node) for node in nodes]
    
    def get_blocks_by_metadata(
        self,
        metadata_filters: Dict[str, Any],
        repository_id: Optional[str] = None,
        limit: int = 100
    ) -> List[CodeBlock]:
        """根据元数据获取代码块"""
        if repository_id:
            metadata_filters = {**metadata_filters, "repository_id": repository_id}
        
        nodes = self.retriever.retrieve_by_metadata(metadata_filters, top_k=limit)
        return [CodeBlock.from_node(node) for node in nodes]
    
    def count_code_blocks(self, repository_id: Optional[str] = None) -> int:
        """统计代码块数量"""
        if repository_id:
            # 按仓库ID统计
            blocks = self.query_code_blocks(repository_id=repository_id, limit=10000)
            return len(blocks)
        else:
            # 统计所有代码块
            return len(self.indexer.document_store)
    
    # ========== 向量搜索相关方法 ==========
    
    def search_vectors(
        self,
        query_vector: List[float],
        top_k: int = 10,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """向量搜索"""
        results = self.indexer.vector_store.query(
            query_embedding=query_vector,
            top_k=top_k,
            metadata_filter=metadata_filter
        )
        
        # 转换结果格式以匹配原storage接口
        formatted_results = []
        for result in results:
            formatted_results.append({
                'id': result['node_id'],
                'score': result['score'],
                'metadata': result.get('metadata', {})
            })
        
        return formatted_results
    
    # ========== 仓库索引相关方法 ==========
    
    def save_repository_index(self, repository_index: RepositoryIndex) -> None:
        """保存仓库索引"""
        self._repository_indexes[repository_index.repository_id] = repository_index
        self._persist_repository_indexes()
    
    def get_repository_index(self, repository_id: str) -> Optional[RepositoryIndex]:
        """获取仓库索引"""
        return self._repository_indexes.get(repository_id)
    
    def list_repository_indexes(self) -> List[RepositoryIndex]:
        """列出所有仓库索引"""
        return list(self._repository_indexes.values())
    
    def delete_repository_index(self, repository_id: str) -> bool:
        """删除仓库索引"""
        if repository_id in self._repository_indexes:
            del self._repository_indexes[repository_id]
            self._persist_repository_indexes()
            return True
        return False
    
    def delete_repository_data(self, repository_id: str) -> bool:
        """删除仓库的所有数据（包括代码块和向量）"""
        # 删除代码块
        blocks = self.query_code_blocks(repository_id=repository_id, limit=10000)
        deleted_count = 0
        
        for block in blocks:
            if self.delete_code_block(block.block_id):
                deleted_count += 1
        
        # 删除仓库索引
        self.delete_repository_index(repository_id)
        
        logger.info(f"删除仓库 {repository_id} 的数据：{deleted_count} 个代码块")
        return deleted_count > 0
    
    # ========== 搜索历史相关方法 ==========
    
    def save_search_query(self, query: SearchQuery) -> None:
        """保存搜索查询"""
        self._search_history.append(query)
        # 保持最近100条记录
        if len(self._search_history) > 100:
            self._search_history = self._search_history[-100:]
        self._persist_search_history()
    
    def get_search_history(self, limit: int = 100) -> List[SearchQuery]:
        """获取搜索历史"""
        return self._search_history[-limit:]
    
    # ========== 持久化辅助方法 ==========
    
    def persist(self) -> None:
        """持久化数据"""
        self.indexer.persist()
        self._persist_repository_indexes()
        self._persist_search_history()
        self._persist_metadata()
    
    def _persist_repository_indexes(self) -> None:
        """持久化仓库索引"""
        repo_file = self.storage_path / "repositories.json"
        repo_data = [repo.to_dict() for repo in self._repository_indexes.values()]
        
        import json
        with open(repo_file, 'w', encoding='utf-8') as f:
            json.dump(repo_data, f, ensure_ascii=False, indent=2)
    
    def _persist_search_history(self) -> None:
        """持久化搜索历史"""
        history_file = self.storage_path / "search_history.json"
        history_data = [query.to_dict() for query in self._search_history]
        
        import json
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(history_data, f, ensure_ascii=False, indent=2)
    
    def _load_repository_indexes(self) -> None:
        """加载仓库索引"""
        repo_file = self.storage_path / "repositories.json"
        if repo_file.exists():
            try:
                import json
                with open(repo_file, 'r', encoding='utf-8') as f:
                    repo_data = json.load(f)
                
                for data in repo_data:
                    repo = RepositoryIndex.from_dict(data)
                    self._repository_indexes[repo.repository_id] = repo
                
                logger.info(f"加载了 {len(self._repository_indexes)} 个仓库索引")
            except Exception as e:
                logger.error(f"加载仓库索引失败: {e}")
    
    def _load_search_history(self) -> None:
        """加载搜索历史"""
        history_file = self.storage_path / "search_history.json"
        if history_file.exists():
            try:
                import json
                with open(history_file, 'r', encoding='utf-8') as f:
                    history_data = json.load(f)
                
                for data in history_data:
                    query = SearchQuery(**data)
                    self._search_history.append(query)
                
                logger.info(f"加载了 {len(self._search_history)} 条搜索历史")
            except Exception as e:
                logger.error(f"加载搜索历史失败: {e}")
    
    def _load_metadata(self) -> None:
        """加载元数据"""
        metadata_file = self.storage_path / "metadata.json"
        if metadata_file.exists():
            try:
                import json
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    self._metadata = json.load(f)
                
                logger.info(f"加载了 {len(self._metadata)} 个元数据项")
            except Exception as e:
                logger.error(f"加载元数据失败: {e}")
    
    def _persist_metadata(self) -> None:
        """持久化元数据"""
        metadata_file = self.storage_path / "metadata.json"
        
        import json
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(self._metadata, f, ensure_ascii=False, indent=2)
    
    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        # 加载持久化数据
        self._load_repository_indexes()
        self._load_search_history()
        self._load_metadata()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        # 持久化数据
        self.persist()
        self.disconnect()


def create_embedding_storage(
    storage_path: str = "./storage",
    embedding_provider=None,
    **kwargs
) -> EmbeddingStorageAdapter:
    """
    创建embedding存储适配器
    
    Args:
        storage_path: 存储路径
        embedding_provider: 嵌入提供商
        **kwargs: 其他配置参数
        
    Returns:
        EmbeddingStorageAdapter实例
    """
    return EmbeddingStorageAdapter(
        storage_path=storage_path,
        embedding_provider=embedding_provider,
        **kwargs
    ) 