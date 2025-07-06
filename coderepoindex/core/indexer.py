"""
代码索引器模块

整合repository、parsers、embeddings、storage模块，
提供完整的代码仓库索引功能。
"""

import time
from typing import List, Optional, Dict, Any, Callable, TYPE_CHECKING
from pathlib import Path
import logging
from datetime import datetime

if TYPE_CHECKING:
    from ..config import CodeRepoConfig

from ..repository import RepositoryFetcher, RepoConfig
from ..parsers import DirectoryParser, CodeParser, DirectoryConfig
from ..embeddings import EmbeddingIndexer, create_indexer
from ..storage import create_storage_backend, CompositeStorage
from .models import (
    CodeBlock, 
    RepositoryIndex, 
    create_repository_index,
    BlockType
)

logger = logging.getLogger(__name__)


class IndexingProgress:
    """索引进度跟踪"""
    
    def __init__(self):
        self.total_files = 0
        self.processed_files = 0
        self.total_blocks = 0
        self.processed_blocks = 0
        self.start_time = None
        self.current_file = ""
        self.errors = []
    
    @property
    def progress_percent(self) -> float:
        """文件处理进度百分比"""
        if self.total_files == 0:
            return 0.0
        return (self.processed_files / self.total_files) * 100
    
    @property
    def elapsed_time(self) -> float:
        """已用时间（秒）"""
        if self.start_time is None:
            return 0.0
        return time.time() - self.start_time
    
    @property
    def estimated_total_time(self) -> float:
        """预计总时间（秒）"""
        if self.processed_files == 0 or self.elapsed_time == 0:
            return 0.0
        return (self.elapsed_time / self.processed_files) * self.total_files
    
    @property
    def eta(self) -> float:
        """预计剩余时间（秒）"""
        return max(0, self.estimated_total_time - self.elapsed_time)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "total_files": self.total_files,
            "processed_files": self.processed_files,
            "total_blocks": self.total_blocks,
            "processed_blocks": self.processed_blocks,
            "progress_percent": self.progress_percent,
            "elapsed_time": self.elapsed_time,
            "eta": self.eta,
            "current_file": self.current_file,
            "error_count": len(self.errors)
        }


class CodeIndexer:
    """
    代码索引器

    整合多个模块，提供完整的代码仓库索引功能。
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
        初始化代码索引器

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
                    logger.info("使用临时配置创建索引器")
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
        
        # 创建解析器
        self.code_parser = CodeParser()
        
        # 初始化组件
        self._connected = False
        
        logger.info(f"代码索引器初始化完成: storage={storage_config['storage_type']}, vector={storage_config['vector_backend']}")

    def connect(self) -> None:
        """连接所有存储后端"""
        if not self._connected:
            self.storage.connect()
            self._connected = True
            logger.info("代码索引器连接成功")

    def disconnect(self) -> None:
        """断开所有存储连接"""
        if self._connected:
            self.storage.disconnect()
            self._connected = False
            logger.info("代码索引器连接已断开")

    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        return {
            "connected": self._connected,
            "storage": self.storage.health_check() if self._connected else {},
            "timestamp": datetime.now().isoformat()
        }

    def get_stats(self) -> Dict[str, Any]:
        """获取索引统计信息"""
        if not self._connected:
            return {"error": "未连接"}
        
        storage_stats = self.storage.get_stats()
        
        return {
            "repositories": len(self.storage.list_repository_indexes()),
            "storage": storage_stats,
            "timestamp": datetime.now().isoformat()
        }

    def index_repository(
        self,
        repo_config: RepoConfig,
        progress_callback: Optional[Callable[[IndexingProgress], None]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        为指定的代码仓库创建索引

        Args:
            repo_config: 仓库配置
            progress_callback: 进度回调函数
            **kwargs: 其他配置参数

        Returns:
            索引统计信息
        """
        if not self._connected:
            self.connect()

        progress = IndexingProgress()
        progress.start_time = time.time()
        
        try:
            logger.info(f"开始索引仓库: {repo_config.path}")
            
            # 1. 获取代码仓库
            with RepositoryFetcher() as fetcher:
                repo_path = fetcher.fetch(repo_config)
                logger.info(f"仓库获取成功: {repo_path}")
            
            # 2. 创建仓库索引记录
            repository_index = create_repository_index(
                repository_path=repo_path,
                url=repo_config.path if repo_config.source.value == "git" else "",
                branch=repo_config.branch or "",
                commit_hash=repo_config.commit or "",
                **kwargs
            )
            
            # 3. 解析代码文件
            code_blocks = self._parse_repository(
                repo_path, 
                repository_index.repository_id,
                progress,
                progress_callback
            )
            
            if not code_blocks:
                logger.warning("未找到任何代码块")
                return {"error": "未找到任何代码块"}
            
            logger.info(f"解析完成，共找到 {len(code_blocks)} 个代码块")
            
            # 4. 生成向量嵌入
            self._generate_embeddings(code_blocks, progress, progress_callback)
            
            # 5. 保存到存储
            self._save_to_storage(code_blocks, repository_index, progress, progress_callback)
            
            # 6. 更新仓库索引
            repository_index.update_stats(code_blocks)
            repository_index.mark_indexed()
            self.storage.save_repository_index(repository_index)
            
            # 7. 生成统计信息
            stats = {
                "repository_id": repository_index.repository_id,
                "total_files": progress.total_files,
                "processed_files": progress.processed_files,
                "total_blocks": len(code_blocks),
                "language_distribution": repository_index.language_distribution,
                "elapsed_time": progress.elapsed_time,
                "errors": progress.errors
            }
            
            logger.info(f"仓库索引完成: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"索引仓库失败: {e}")
            progress.errors.append(str(e))
            raise

    def index_file(
        self,
        file_path: str,
        repository_id: str = "",
        **kwargs
    ) -> Dict[str, Any]:
        """
        为单个代码文件创建索引

        Args:
            file_path: 代码文件路径
            repository_id: 仓库ID
            **kwargs: 其他配置参数

        Returns:
            索引统计信息
        """
        if not self._connected:
            self.connect()

        try:
            logger.info(f"开始索引文件: {file_path}")
            
            # 1. 解析文件
            result = self.code_parser.parse_file(file_path)
            
            if result.errors:
                logger.warning(f"解析文件时出现错误: {result.errors}")
            
            if not result.snippets:
                logger.warning("文件中未找到代码块")
                return {"error": "未找到代码块"}
            
            # 2. 转换为CodeBlock
            code_blocks = []
            for snippet in result.snippets:
                code_block = CodeBlock.from_code_snippet(snippet, repository_id)
                code_blocks.append(code_block)
            
            # 3. 生成向量嵌入
            self._generate_embeddings_for_blocks(code_blocks)
            
            # 4. 保存到存储
            for code_block in code_blocks:
                self.storage.save_code_block_with_vector(code_block)
            
            stats = {
                "file_path": file_path,
                "repository_id": repository_id,
                "code_blocks": len(code_blocks),
                "language": result.language.value if result.language else None
            }
            
            logger.info(f"文件索引完成: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"索引文件失败: {e}")
            raise

    def delete_repository_index(self, repository_id: str) -> Dict[str, Any]:
        """
        删除仓库索引

        Args:
            repository_id: 仓库ID

        Returns:
            删除统计信息
        """
        if not self._connected:
            self.connect()

        try:
            logger.info(f"开始删除仓库索引: {repository_id}")
            
            # 删除所有相关数据
            result = self.storage.delete_repository_data(repository_id)
            
            logger.info(f"仓库索引删除完成: {result}")
            return result
            
        except Exception as e:
            logger.error(f"删除仓库索引失败: {e}")
            raise

    def list_repositories(self) -> List[RepositoryIndex]:
        """列出所有已索引的仓库"""
        if not self._connected:
            self.connect()
        
        return self.storage.list_repository_indexes()

    def get_repository_info(self, repository_id: str) -> Optional[RepositoryIndex]:
        """获取仓库信息"""
        if not self._connected:
            self.connect()
        
        return self.storage.get_repository_index(repository_id)

    def _parse_repository(
        self,
        repo_path: str,
        repository_id: str,
        progress: IndexingProgress,
        progress_callback: Optional[Callable[[IndexingProgress], None]] = None
    ) -> List[CodeBlock]:
        """解析仓库中的所有代码文件"""
        
        # 创建目录解析器
        dir_config = DirectoryConfig(
            target_directory=repo_path,
            include_patterns=["*.py", "*.js", "*.ts", "*.java", "*.go", "*.cpp", "*.c", "*.h"],
            exclude_patterns=[
                "__pycache__", "node_modules", ".git", "*.pyc", "*.min.js"
            ]
        )
        
        dir_parser = DirectoryParser(dir_config)
        
        # 解析目录
        result = dir_parser.parse_directory()
        
        # 更新进度
        progress.total_files = len(result.file_results)
        
        # 转换为CodeBlock
        code_blocks = []
        
        for file_result in result.file_results:
            progress.current_file = file_result.file_path
            progress.processed_files += 1
            
            if progress_callback:
                progress_callback(progress)
            
            # 跳过有错误的文件
            if file_result.errors:
                progress.errors.extend(file_result.errors)
                continue
            
            # 转换代码片段
            for snippet in file_result.snippets:
                try:
                    code_block = CodeBlock.from_code_snippet(snippet, repository_id)
                    # 设置语言信息
                    if file_result.language:
                        code_block.language = file_result.language.value
                    code_blocks.append(code_block)
                    progress.total_blocks += 1
                    
                except Exception as e:
                    error_msg = f"转换代码片段失败 {snippet.path}: {e}"
                    progress.errors.append(error_msg)
                    logger.error(error_msg)
        
        return code_blocks

    def _generate_embeddings(
        self,
        code_blocks: List[CodeBlock],
        progress: IndexingProgress,
        progress_callback: Optional[Callable[[IndexingProgress], None]] = None
    ) -> None:
        """为代码块生成向量嵌入"""
        
        logger.info(f"开始生成向量嵌入，共 {len(code_blocks)} 个代码块")
        
        # 批量生成嵌入
        batch_size = 10
        for i in range(0, len(code_blocks), batch_size):
            batch = code_blocks[i:i + batch_size]
            
            try:
                # 准备文档数据
                documents = []
                for code_block in batch:
                    # 组合代码和元数据作为文档内容
                    content = f"{code_block.name}\n{code_block.content}"
                    if code_block.signature:
                        content = f"{code_block.signature}\n{content}"
                    
                    documents.append({
                        "text": content,
                        "metadata": {
                            "block_id": code_block.block_id,
                            "repository_id": code_block.repository_id,
                            "file_path": code_block.file_path,
                            "block_type": code_block.block_type.value,
                            "language": code_block.language,
                            "name": code_block.name
                        }
                    })
                
                # 生成嵌入
                self.embedding_indexer.build_index(documents)
                
                # 获取嵌入并设置到code_block
                for j, code_block in enumerate(batch):
                    # 这里简化处理，实际应该从embedding_indexer获取具体的向量
                    # code_block.embedding = embedding_vector
                    pass
                
                progress.processed_blocks += len(batch)
                
                if progress_callback:
                    progress_callback(progress)
                    
            except Exception as e:
                error_msg = f"生成嵌入失败 批次 {i//batch_size + 1}: {e}"
                progress.errors.append(error_msg)
                logger.error(error_msg)

    def _generate_embeddings_for_blocks(self, code_blocks: List[CodeBlock]) -> None:
        """为代码块生成嵌入（简化版）"""
        documents = []
        
        for code_block in code_blocks:
            content = f"{code_block.name}\n{code_block.content}"
            if code_block.signature:
                content = f"{code_block.signature}\n{content}"
            
            documents.append({
                "text": content,
                "metadata": {
                    "block_id": code_block.block_id,
                    "repository_id": code_block.repository_id,
                    "file_path": code_block.file_path,
                    "block_type": code_block.block_type.value,
                    "language": code_block.language,
                    "name": code_block.name
                }
            })
        
        try:
            self.embedding_indexer.build_index(documents)
        except Exception as e:
            logger.error(f"生成嵌入失败: {e}")

    def _save_to_storage(
        self,
        code_blocks: List[CodeBlock],
        repository_index: RepositoryIndex,
        progress: IndexingProgress,
        progress_callback: Optional[Callable[[IndexingProgress], None]] = None
    ) -> None:
        """保存数据到存储"""
        
        logger.info(f"开始保存数据，共 {len(code_blocks)} 个代码块")
        
        try:
            # 批量保存代码块
            batch_size = 100
            for i in range(0, len(code_blocks), batch_size):
                batch = code_blocks[i:i + batch_size]
                
                # 保存代码块和向量
                for code_block in batch:
                    self.storage.save_code_block_with_vector(code_block)
                
                if progress_callback:
                    progress_callback(progress)
            
            # 保存仓库索引
            self.storage.save_repository_index(repository_index)
            
            logger.info("数据保存完成")
            
        except Exception as e:
            error_msg = f"保存数据失败: {e}"
            progress.errors.append(error_msg)
            logger.error(error_msg)
            raise

    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.disconnect()


# 便利函数
def create_code_indexer(
    storage_backend: str = "local",
    vector_backend: str = "chromadb",
    storage_path: str = "./storage",
    config: Optional['CodeRepoConfig'] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    **kwargs
) -> CodeIndexer:
    """
    创建代码索引器
    
    Args:
        storage_backend: 存储后端类型
        vector_backend: 向量存储后端类型
        storage_path: 存储路径
        config: 项目配置对象
        api_key: API密钥
        base_url: API基础URL
        **kwargs: 其他配置参数
        
    Returns:
        CodeIndexer实例
    """
    return CodeIndexer(
        storage_backend=storage_backend,
        vector_backend=vector_backend,
        storage_path=storage_path,
        config=config,
        api_key=api_key,
        base_url=base_url,
        **kwargs
    ) 