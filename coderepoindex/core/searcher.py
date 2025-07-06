"""
代码搜索器模块

负责在向量化的代码索引中进行语义搜索。
"""

import logging
from typing import List, Optional, Dict, Any, Union, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from ..config import CodeRepoConfig

from ..storage import create_storage_backend, CompositeStorage
from ..embeddings import create_indexer, EmbeddingIndexer
from .models import (
    SearchResult, 
    SearchQuery, 
    CodeBlock, 
    RepositoryIndex, 
    BlockType,
    create_search_query
)

logger = logging.getLogger(__name__)


class CodeSearcher:
    """
    代码搜索器

    在已创建的代码索引中进行语义相似度搜索，
    支持自然语言查询和代码片段查询。
    """

    def __init__(
        self,
        storage_backend: str = "local",
        vector_backend: str = "chromadb",
        embedding_provider=None,
        storage_path: str = "./storage",
        config: Optional['CodeRepoConfig'] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        **kwargs
    ):
        """
        初始化代码搜索器

        Args:
            storage_backend: 存储后端类型
            vector_backend: 向量存储后端类型
            embedding_provider: 嵌入提供商
            storage_path: 存储路径
            config: 项目配置对象
            api_key: API密钥
            base_url: API基础URL
            **kwargs: 其他配置参数
        """
        # 使用配置中心
        if config is not None:
            self.config = config
        else:
            # 从配置中心获取配置或创建默认配置
            try:
                from ..config import get_current_config, load_config
                self.config = get_current_config()
                if self.config is None:
                    # 如果没有配置，创建一个临时配置
                    config_data = {}
                    if api_key:
                        config_data['api_key'] = api_key
                    if base_url:
                        config_data['base_url'] = base_url
                    if storage_backend:
                        config_data['storage_backend'] = storage_backend
                    if vector_backend:
                        config_data['vector_backend'] = vector_backend
                    if storage_path:
                        config_data['storage_base_path'] = storage_path
                    config_data.update(kwargs)
                    
                    self.config = load_config(config_dict=config_data)
                    logger.info("使用临时配置创建搜索器")
                else:
                    logger.info("使用配置中心的配置")
            except ImportError:
                logger.warning("配置中心模块未找到，使用传统配置方式")
                self.config = None
        
        # 根据配置创建存储后端
        storage_config = {}
        if self.config:
            storage_config = {
                'storage_type': self.config.storage.storage_backend,
                'vector_backend': self.config.storage.vector_backend,
                'base_path': self.config.storage.base_path,
                **self.config.storage.extra_params
            }
        else:
            storage_config = {
                'storage_type': storage_backend,
                'vector_backend': vector_backend,
                'base_path': storage_path,
                **kwargs
            }
        
        self.storage = create_storage_backend(**storage_config)
        
        # 创建嵌入索引器
        if embedding_provider is None:
            try:
                from ..models import create_embedding_provider
                if self.config:
                    # 使用配置中心的嵌入配置
                    embedding_provider = create_embedding_provider(
                        provider_type=self.config.embedding.provider_type,
                        model_name=self.config.embedding.model_name,
                        api_key=self.config.embedding.api_key,
                        base_url=self.config.embedding.base_url,
                        timeout=self.config.embedding.timeout,
                        **self.config.embedding.extra_params
                    )
                else:
                    # 使用传统方式
                    embedding_provider = create_embedding_provider(
                        api_key=api_key,
                        base_url=base_url,
                        **kwargs
                    )
            except ImportError:
                logger.warning("models模块未找到，将使用默认嵌入配置")
                embedding_provider = None
        
        # 设置嵌入索引器的存储路径
        embed_storage_path = f"{storage_config['base_path']}/embeddings"
        
        self.embedding_indexer = create_indexer(
            embedding_provider=embedding_provider,
            persist_dir=embed_storage_path,
            **kwargs
        )
        
        # 初始化组件
        self._connected = False
        
        logger.info(f"代码搜索器初始化完成: storage={storage_config['storage_type']}, vector={storage_config['vector_backend']}")

    def connect(self) -> None:
        """连接所有存储后端"""
        if not self._connected:
            self.storage.connect()
            self._connected = True
            logger.info("代码搜索器连接成功")

    def disconnect(self) -> None:
        """断开所有存储连接"""
        if self._connected:
            self.storage.disconnect()
            self._connected = False
            logger.info("代码搜索器连接已断开")

    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        return {
            "connected": self._connected,
            "storage": self.storage.health_check() if self._connected else {},
            "timestamp": datetime.now().isoformat()
        }

    def search(
        self,
        query: str,
        top_k: int = 10,
        repository_id: Optional[str] = None,
        language: Optional[str] = None,
        block_type: Optional[BlockType] = None,
        file_path: Optional[str] = None,
        similarity_threshold: float = 0.0,
        **kwargs
    ) -> List[SearchResult]:
        """
        根据查询内容搜索相似代码块

        Args:
            query: 搜索查询（自然语言或代码片段）
            top_k: 返回结果数量
            repository_id: 限制搜索的仓库ID
            language: 限制搜索的编程语言
            block_type: 限制搜索的代码块类型
            file_path: 限制搜索的文件路径
            similarity_threshold: 相似度阈值
            **kwargs: 其他搜索参数

        Returns:
            搜索结果列表
        """
        if not self._connected:
            self.connect()

        logger.info(f"开始搜索: '{query[:50]}...', top_k={top_k}")

        if not query.strip():
            return []

        try:
            # 1. 创建搜索查询对象
            search_query = create_search_query(
                query=query,
                query_type="semantic",
                repository_id=repository_id,
                language=language,
                block_type=block_type,
                file_path=file_path,
                top_k=top_k,
                similarity_threshold=similarity_threshold,
                **kwargs
            )
            
            # 2. 记录搜索查询
            self.storage.save_search_query(search_query)
            
            # 3. 执行向量搜索
            search_results = self._perform_vector_search(search_query)
            
            # 4. 应用元数据过滤
            filtered_results = self._apply_metadata_filters(search_results, search_query)
            
            # 5. 排序和限制结果数量
            final_results = self._rank_and_limit_results(filtered_results, search_query)
            
            logger.info(f"搜索完成，找到 {len(final_results)} 个结果")
            return final_results
            
        except Exception as e:
            logger.error(f"搜索失败: {e}")
            return []

    def search_by_code(
        self,
        code_snippet: str,
        top_k: int = 10,
        language: Optional[str] = None,
        similarity_threshold: float = 0.0,
        **kwargs
    ) -> List[SearchResult]:
        """
        根据代码片段搜索相似代码

        Args:
            code_snippet: 代码片段
            top_k: 返回结果数量
            language: 限制搜索的编程语言
            similarity_threshold: 相似度阈值
            **kwargs: 其他搜索参数

        Returns:
            搜索结果列表
        """
        logger.info(f"开始代码搜索，代码长度: {len(code_snippet)}")
        
        return self.search(
            query=code_snippet,
            top_k=top_k,
            language=language,
            similarity_threshold=similarity_threshold,
            **kwargs
        )

    def search_similar_functions(
        self,
        function_name: str,
        top_k: int = 10,
        repository_id: Optional[str] = None,
        language: Optional[str] = None,
        **kwargs
    ) -> List[SearchResult]:
        """
        搜索相似的函数

        Args:
            function_name: 函数名称
            top_k: 返回结果数量
            repository_id: 限制搜索的仓库ID
            language: 限制搜索的编程语言
            **kwargs: 其他搜索参数

        Returns:
            搜索结果列表
        """
        logger.info(f"搜索相似函数: {function_name}")
        
        return self.search(
            query=f"function {function_name}",
            top_k=top_k,
            repository_id=repository_id,
            language=language,
            block_type=BlockType.FUNCTION,
            **kwargs
        )

    def search_by_metadata(
        self,
        metadata_filters: Dict[str, Any],
        top_k: int = 10,
        repository_id: Optional[str] = None,
        **kwargs
    ) -> List[SearchResult]:
        """
        根据元数据搜索代码块

        Args:
            metadata_filters: 元数据过滤条件
            top_k: 返回结果数量
            repository_id: 限制搜索的仓库ID
            **kwargs: 其他搜索参数

        Returns:
            搜索结果列表
        """
        if not self._connected:
            self.connect()

        logger.info(f"元数据搜索: {metadata_filters}")
        
        try:
            # 从存储中获取匹配的代码块
            blocks = self.storage.get_blocks_by_metadata(
                metadata_filters=metadata_filters,
                repository_id=repository_id,
                limit=top_k
            )
            
            # 转换为搜索结果
            results = []
            for block in blocks:
                result = SearchResult(
                    block=block,
                    score=1.0,  # 元数据搜索给予满分
                    match_reason="元数据匹配"
                )
                results.append(result)
            
            logger.info(f"元数据搜索完成，找到 {len(results)} 个结果")
            return results
            
        except Exception as e:
            logger.error(f"元数据搜索失败: {e}")
            return []

    def get_recommendations(
        self,
        file_path: str,
        top_k: int = 5,
        repository_id: Optional[str] = None
    ) -> List[SearchResult]:
        """
        基于文件获取相关代码推荐

        Args:
            file_path: 目标文件路径
            top_k: 返回结果数量
            repository_id: 限制搜索的仓库ID

        Returns:
            推荐结果列表
        """
        if not self._connected:
            self.connect()

        logger.info(f"获取文件推荐: {file_path}")
        
        try:
            # 1. 获取目标文件的代码块
            target_blocks = self.storage.get_blocks_by_file(
                file_path=file_path,
                repository_id=repository_id
            )
            
            if not target_blocks:
                logger.warning(f"未找到文件的代码块: {file_path}")
                return []
            
            # 2. 基于文件中的代码块内容进行搜索
            recommendations = []
            for block in target_blocks[:3]:  # 最多使用前3个代码块
                if block.content:
                    similar_results = self.search(
                        query=block.content,
                        top_k=top_k,
                        repository_id=repository_id,
                        similarity_threshold=0.3
                    )
                    
                    # 过滤掉来自同一文件的结果
                    for result in similar_results:
                        if result.block.file_path != file_path:
                            result.match_reason = f"基于文件 {file_path} 的推荐"
                            recommendations.append(result)
            
            # 3. 去重和排序
            seen_blocks = set()
            unique_recommendations = []
            
            for rec in recommendations:
                if rec.block.block_id not in seen_blocks:
                    seen_blocks.add(rec.block.block_id)
                    unique_recommendations.append(rec)
            
            # 按分数排序并限制数量
            unique_recommendations.sort(key=lambda x: x.score, reverse=True)
            final_recommendations = unique_recommendations[:top_k]
            
            logger.info(f"推荐完成，找到 {len(final_recommendations)} 个结果")
            return final_recommendations
            
        except Exception as e:
            logger.error(f"获取推荐失败: {e}")
            return []

    def get_stats(self) -> Dict[str, Any]:
        """
        获取搜索统计信息

        Returns:
            统计信息字典
        """
        if not self._connected:
            self.connect()

        try:
            storage_stats = self.storage.get_stats()
            repositories = self.storage.list_repository_indexes()
            
            return {
                "total_repositories": len(repositories),
                "total_indexed_blocks": storage_stats.get("total_blocks", 0),
                "storage_size": storage_stats.get("storage_size", "0 MB"),
                "available_languages": list(set(
                    lang for repo in repositories 
                    for lang in repo.language_distribution.keys()
                )),
                "last_indexed": max(
                    (repo.indexed_at for repo in repositories if repo.indexed_at),
                    default=None
                ),
                "storage_backend": self.storage.__class__.__name__,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def _perform_vector_search(self, search_query: SearchQuery) -> List[SearchResult]:
        """执行向量搜索"""
        try:
            # 1. 生成查询向量
            query_vector = self.embedding_indexer.embed_query(search_query.query)
            
            # 2. 在向量存储中搜索
            search_results = self.storage.vector_search(
                query_vector=query_vector,
                top_k=search_query.top_k * 2,  # 搜索更多结果用于后续过滤
                similarity_threshold=search_query.similarity_threshold
            )
            
            # 3. 转换为SearchResult对象
            results = []
            for vector_result in search_results:
                # 从存储中获取完整的代码块信息
                block = self.storage.get_block(vector_result.node_id)
                if block:
                    result = SearchResult(
                        block=block,
                        score=vector_result.score,
                        match_reason="向量相似度匹配"
                    )
                    results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"向量搜索失败: {e}")
            return []

    def _apply_metadata_filters(
        self, 
        results: List[SearchResult], 
        search_query: SearchQuery
    ) -> List[SearchResult]:
        """应用元数据过滤"""
        filtered_results = []
        
        for result in results:
            block = result.block
            
            # 仓库过滤
            if search_query.repository_id and block.repository_id != search_query.repository_id:
                continue
                
            # 语言过滤
            if search_query.language and block.language != search_query.language:
                continue
                
            # 代码块类型过滤
            if search_query.block_type and block.block_type != search_query.block_type:
                continue
                
            # 文件路径过滤
            if search_query.file_path and search_query.file_path not in block.file_path:
                continue
                
            # 元数据过滤
            if search_query.metadata_filters:
                match = True
                for key, value in search_query.metadata_filters.items():
                    if key not in block.metadata or block.metadata[key] != value:
                        match = False
                        break
                if not match:
                    continue
                    
            # 时间范围过滤
            if search_query.created_after and block.created_at < search_query.created_after:
                continue
            if search_query.created_before and block.created_at > search_query.created_before:
                continue
                
            filtered_results.append(result)
        
        return filtered_results

    def _rank_and_limit_results(
        self, 
        results: List[SearchResult], 
        search_query: SearchQuery
    ) -> List[SearchResult]:
        """排序和限制结果数量"""
        # 按分数排序
        results.sort(key=lambda x: x.score, reverse=True)
        
        # 限制数量
        return results[:search_query.top_k]

    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.disconnect()


def create_code_searcher(
    storage_backend: str = "local",
    vector_backend: str = "chromadb",
    storage_path: str = "./storage",
    config: Optional['CodeRepoConfig'] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    **kwargs
) -> CodeSearcher:
    """
    创建代码搜索器实例

    Args:
        storage_backend: 存储后端类型
        vector_backend: 向量存储后端类型
        storage_path: 存储路径
        config: 项目配置对象
        api_key: API密钥
        base_url: API基础URL
        **kwargs: 其他配置参数

    Returns:
        CodeSearcher实例
    """
    return CodeSearcher(
        storage_backend=storage_backend,
        vector_backend=vector_backend,
        storage_path=storage_path,
        config=config,
        api_key=api_key,
        base_url=base_url,
        **kwargs
    ) 