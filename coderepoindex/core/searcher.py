"""
代码搜索器模块

负责在向量化的代码索引中进行语义搜索。
"""

import logging
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from ..config import CodeRepoConfig

from .storage_adapter import create_embedding_storage, EmbeddingStorageAdapter
from .models import (
    SearchResult, 
    SearchQuery, 
    CodeBlock, 
    BlockType,
    create_search_query
)

logger = logging.getLogger(__name__)


class CodeSearcher:
    """
    代码搜索器
    
    专注于纯向量语义搜索，支持自然语言查询和代码片段查询。
    """

    def __init__(
        self,
        config: Optional['CodeRepoConfig'] = None,
        embedding_provider=None,
        storage_path: str = "./storage",
        **kwargs
    ):
        """
        初始化代码搜索器

        Args:
            config: 项目配置对象
            embedding_provider: 嵌入提供商（可选）
            storage_path: 存储路径
            **kwargs: 其他配置参数
        """
        self.config = config
        
        # 创建存储适配器
        storage_config = {
            'storage_path': storage_path,
            'embedding_provider': embedding_provider,
        }
        
        if config:
            storage_config.update({
                'storage_path': config.storage.base_path,
                'provider_type': config.embedding.provider_type,
                'model_name': config.embedding.model_name,
                'api_key': config.embedding.api_key,
                'base_url': config.embedding.base_url,
                'timeout': config.embedding.timeout,
                **config.embedding.extra_params,
                **config.storage.extra_params
            })
        else:
            storage_config.update(kwargs)
        
        self.storage = create_embedding_storage(**storage_config)
        self.embedding_provider = self.storage.embedding_provider
        self._connected = False
        
        logger.info(f"向量搜索器初始化完成: {storage_config['storage_path']}")

    def connect(self) -> None:
        """连接存储后端"""
        if not self._connected:
            self.storage.connect()
            self._connected = True
            logger.info("向量搜索器连接成功")

    def disconnect(self) -> None:
        """断开存储连接"""
        if self._connected:
            self.storage.disconnect()
            self._connected = False
            logger.info("向量搜索器连接已断开")

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
        向量语义搜索

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

        logger.info(f"开始向量搜索: '{query[:50]}...', top_k={top_k}")

        if not query.strip():
            return []

        try:
            # 1. 生成查询向量
            if not self.embedding_provider:
                logger.error("embedding_provider未初始化")
                return []
                
            query_embedding = self.embedding_provider.get_embedding(query)
            logger.debug(f"生成查询向量成功，维度: {len(query_embedding)}")
            
            # 2. 构建元数据过滤条件
            metadata_filter = {}
            if repository_id:
                metadata_filter["repository_id"] = repository_id
            if language:
                metadata_filter["language"] = language
            if block_type:
                metadata_filter["block_type"] = block_type.value
            if file_path:
                metadata_filter["file_path"] = file_path
            
            # 3. 执行向量搜索
            logger.debug(f"向量搜索，过滤条件: {metadata_filter}")
            vector_results = self.storage.search_vectors(
                query_vector=query_embedding,
                top_k=top_k * 2,  # 获取更多候选，后续过滤
                metadata_filter=metadata_filter if metadata_filter else None
            )
            
            logger.info(f"向量搜索返回 {len(vector_results)} 个候选结果")
            
            if not vector_results:
                logger.info("向量搜索没有返回结果")
                return []
            
            # 4. 转换为SearchResult并应用阈值过滤
            search_results = []
            code_block_ids = []
            
            for result in vector_results:
                vector_id = result.get('id')
                score = result.get('score', 0.0)
                
                # 应用相似度阈值过滤
                if score < similarity_threshold:
                    continue
                
                if vector_id:
                    code_block_ids.append((vector_id, score))
            
            logger.debug(f"阈值过滤后的代码块ID数量: {len(code_block_ids)}")
            
            # 5. 批量获取代码块
            if code_block_ids:
                block_ids_only = [block_id for block_id, _ in code_block_ids]
                code_blocks = self.storage.query_code_blocks(
                    repository_id=repository_id,
                    code_block_ids=block_ids_only,
                    limit=len(block_ids_only)
                )
                
                # 创建代码块映射
                code_block_map = {block.block_id: block for block in code_blocks}
                
                # 6. 构建最终搜索结果
                for block_id, score in code_block_ids:
                    code_block = code_block_map.get(block_id)
                    if code_block:
                        search_result = SearchResult(
                            block=code_block,
                            score=score,
                            match_reason=f"向量相似度: {score:.4f}"
                        )
                        search_results.append(search_result)
                    else:
                        logger.warning(f"未找到代码块ID: {block_id}")
            
            # 7. 按相似度排序并限制数量
            search_results.sort(key=lambda x: x.score, reverse=True)
            final_results = search_results[:top_k]
            
            logger.info(f"最终返回 {len(final_results)} 个搜索结果")
            
            # 8. 调试信息
            for i, result in enumerate(final_results[:3]):
                logger.debug(f"结果 {i+1}: {result.block.file_path}:{result.block.line_start} - "
                           f"{result.block.name} (分数: {result.score:.4f})")
            
            return final_results
            
        except Exception as e:
            logger.error(f"向量搜索失败: {e}")
            import traceback
            logger.error(f"错误详情: {traceback.format_exc()}")
            return []

    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.disconnect()


def create_code_searcher(
    config: Optional['CodeRepoConfig'] = None,
    storage_path: str = "./storage",
    embedding_provider=None,
    **kwargs
) -> CodeSearcher:
    """
    创建代码搜索器实例

    Args:
        config: 项目配置对象
        storage_path: 存储路径
        embedding_provider: 嵌入提供商
        **kwargs: 其他配置参数

    Returns:
        CodeSearcher实例
    """
    return CodeSearcher(
        config=config,
        storage_path=storage_path,
        embedding_provider=embedding_provider,
        **kwargs
    ) 