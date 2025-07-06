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
from ..embeddings import EmbeddingIndexer, create_indexer, create_retriever
from .storage_adapter import create_embedding_storage, EmbeddingStorageAdapter
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
        
        # 创建嵌入提供商
        if embedding_provider is None:
            try:
                from ..models import create_embedding_provider
                if self.config:
                    # 使用配置中心的嵌入配置
                    logger.info(f"使用配置中心的嵌入配置: model={self.config.embedding.model_name}, api_key={self.config.embedding.api_key[:10] if self.config.embedding.api_key else 'None'}..., base_url={self.config.embedding.base_url}")
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

        # 根据配置创建embedding存储适配器
        storage_config = {}
        if self.config:
            storage_config = {
                'storage_path': self.config.storage.base_path,
                'embedding_provider': embedding_provider,
                # 传递embedding配置（如果embedding_provider为None）
                'provider_type': self.config.embedding.provider_type,
                'model_name': self.config.embedding.model_name,
                'api_key': self.config.embedding.api_key,
                'base_url': self.config.embedding.base_url,
                'timeout': self.config.embedding.timeout,
                'batch_size': self.config.embedding.batch_size,
                **self.config.embedding.extra_params,
                **self.config.storage.extra_params
            }
        else:
            storage_config = {
                'storage_path': storage_path,
                'embedding_provider': embedding_provider,
                **kwargs
            }
        
        self.storage = create_embedding_storage(**storage_config)
        
        # 直接使用storage的embedding组件
        self.embedding_indexer = self.storage.indexer
        
        # 创建解析器
        self.code_parser = CodeParser()
        
        # 初始化组件
        self._connected = False
        
        logger.info(f"代码索引器初始化完成: storage_path={storage_config['storage_path']}")

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
        repository_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        为指定的代码仓库创建索引

        Args:
            repo_config: 仓库配置
            progress_callback: 进度回调函数
            repository_id: 仓库ID（可选，不提供则自动生成）
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
            
            # 如果外部指定了repository_id，覆盖自动生成的
            if repository_id:
                repository_index.repository_id = repository_id
                logger.info(f"使用外部指定的仓库ID: {repository_id}")
            
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
        
        # 创建目录解析器配置
        from ..parsers import create_directory_config
        
        dir_config = create_directory_config(
            only_extensions={"py", "js", "ts", "java", "go", "cpp", "c", "h"},
            ignore_patterns=[
                "__pycache__", "node_modules", ".git", "*.pyc", "*.min.js"
            ]
        )
        
        dir_parser = DirectoryParser(dir_config)
        
        # 解析目录
        result = dir_parser.parse_directory(repo_path)
        
        # 更新进度
        progress.total_files = result.total_files
        
        # 转换为CodeBlock
        code_blocks = []
        
        for snippet in result.snippets:
            progress.processed_files += 1
            
            if progress_callback:
                progress_callback(progress)
            
            # 转换代码片段
            try:
                code_block = CodeBlock.from_code_snippet(snippet, repository_id)
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
        """为代码块生成向量嵌入并存储到embedding模块"""
        
        print(f"🔥🔥🔥 _generate_embeddings被调用了！代码块数量: {len(code_blocks)}")
        logger.info(f"开始使用embedding模块生成向量嵌入，共 {len(code_blocks)} 个代码块")
        
        if not code_blocks:
            print("🔥 代码块为空，直接返回")
            return
        
        try:
            print("🔥 第1步：开始转换为文档格式")
            # 1. 将CodeBlock转换为embedding模块所需的文档格式
            documents = []
            code_block_map = {}  # 用于反向查找
            
            for code_block in code_blocks:
                # 组合代码和元数据作为文档内容
                content = f"{code_block.name}\n{code_block.content}"
                if code_block.signature:
                    content = f"{code_block.signature}\n{content}"
                
                # 构建文档元数据
                metadata = {
                    "code_block_id": code_block.block_id,
                    "repository_id": code_block.repository_id,
                    "file_path": code_block.file_path,
                    "name": code_block.name,
                    "signature": code_block.signature,
                    "block_type": code_block.block_type.value if code_block.block_type else "unknown",
                    "language": code_block.language or "unknown",
                    "line_start": code_block.line_start,
                    "line_end": code_block.line_end,
                    "class_name": code_block.class_name,
                    "namespace": code_block.namespace,
                    "keywords": code_block.keywords,
                    "search_text": code_block.search_text
                }
                
                # 创建文档
                doc = {
                    "text": content,
                    "metadata": metadata
                }
                documents.append(doc)
                
                # 建立映射关系
                code_block_map[len(documents) - 1] = code_block
            
            print(f"🔥 第1步完成：转换了 {len(documents)} 个文档")
            
            print("🔥 第2步：开始使用EmbeddingIndexer构建索引")
            # 2. 使用EmbeddingIndexer构建索引
            logger.info(f"使用EmbeddingIndexer构建索引，文档数: {len(documents)}")
            self.embedding_indexer.build_index(documents, clear_existing=False)
            print("🔥 第2步完成：EmbeddingIndexer构建索引成功")
            
        except Exception as e:
            print(f"🔥 第1-2步出现异常: {e}")
            print(f"🔥 异常类型: {type(e)}")
            import traceback
            print(f"🔥 完整堆栈: {traceback.format_exc()}")
            logger.error(f"使用EmbeddingIndexer生成嵌入失败: {e}")
            raise
        
        try:
            print("🔥 第3步：开始检查EmbeddingIndexer内部状态")
            # 调试：检查EmbeddingIndexer的内部状态
            logger.info(f"EmbeddingIndexer索引构建完成")
            logger.info(f"DocumentStore中的节点数: {len(self.embedding_indexer.document_store._nodes)}")
            logger.info(f"VectorStore中的向量数: {len(self.embedding_indexer.vector_store._embeddings)}")
            print(f"🔥 第3步完成：DocumentStore节点数={len(self.embedding_indexer.document_store._nodes)}, VectorStore向量数={len(self.embedding_indexer.vector_store._embeddings)}")
            
        except Exception as e:
            print(f"🔥 第3步异常: {e}")
            logger.error(f"检查EmbeddingIndexer状态失败: {e}")
        
        try:
            print("🔥 第4步：开始关联向量到代码块")
            # 调试：显示前几个节点的metadata
            sample_nodes = list(self.embedding_indexer.document_store._nodes.values())[:3]
            for i, node in enumerate(sample_nodes):
                logger.info(f"节点 {i+1}: ID={node.node_id[:20]}...")
                logger.info(f"  文本长度: {len(node.text) if node.text else 0}")
                logger.info(f"  有嵌入: {'是' if node.embedding else '否'}")
                logger.info(f"  元数据: {node.metadata}")
                logger.info(f"  元数据中的code_block_id: {node.metadata.get('code_block_id') if node.metadata else 'None'}")
            
            # 3. 从embedding模块获取生成的向量并关联到代码块
            embedded_count = 0
            
            # 首先调试：检查我们要查找的code_block_id
            logger.info(f"要查找的代码块ID列表:")
            for i, (doc_index, code_block) in enumerate(list(code_block_map.items())[:5]):  # 只显示前5个
                logger.info(f"  {i+1}. {code_block.block_id}")
            
            print(f"🔥 第4步：开始遍历 {len(code_block_map)} 个代码块进行向量关联")
            
            # 方法1：通过node_id直接查找（更可靠）
            for doc_index, code_block in code_block_map.items():
                try:
                    # 查找对应的节点 - 改进查找逻辑
                    found_node = None
                    
                    logger.debug(f"正在查找代码块 {code_block.block_id} 对应的节点...")
                    
                    # 遍历document_store中的所有节点
                    nodes_checked = 0
                    for node in self.embedding_indexer.document_store._nodes.values():
                        nodes_checked += 1
                        node_metadata = node.metadata or {}
                        node_code_block_id = node_metadata.get("code_block_id")
                        
                        if nodes_checked <= 3:  # 调试前3个节点
                            logger.debug(f"  检查节点 {node.node_id[:15]}..., 其code_block_id: {node_code_block_id}")
                        
                        if node_code_block_id == code_block.block_id:
                            found_node = node
                            logger.debug(f"  找到匹配节点: {node.node_id[:20]}...")
                            break
                    
                    logger.debug(f"  共检查了 {nodes_checked} 个节点")
                    
                    if found_node and found_node.embedding:
                        code_block.embedding = found_node.embedding
                        embedded_count += 1
                        logger.debug(f"为代码块 {code_block.block_id} 设置嵌入向量，维度: {len(found_node.embedding)}")
                    else:
                        # 如果通过code_block_id找不到，尝试通过其他方式
                        logger.warning(f"通过code_block_id未找到代码块 {code_block.block_id} 对应的节点，尝试其他方式")
                        
                        # 方法2：通过文本内容模糊匹配
                        target_content = f"{code_block.name}\n{code_block.content}"
                        if code_block.signature:
                            target_content = f"{code_block.signature}\n{target_content}"
                        
                        logger.debug(f"尝试通过文本匹配，目标内容前100字符: {target_content[:100]}")
                        
                        for node in self.embedding_indexer.document_store._nodes.values():
                            # 检查文本是否匹配
                            if node.text and target_content[:100] in node.text[:100]:
                                if node.embedding:
                                    code_block.embedding = node.embedding
                                    embedded_count += 1
                                    logger.debug(f"通过文本匹配为代码块 {code_block.block_id} 设置嵌入向量")
                                    break
                        else:
                            logger.warning(f"完全未找到代码块 {code_block.block_id} 对应的节点")
                        
                except Exception as e:
                    print(f"🔥 处理代码块 {code_block.block_id} 时出现异常: {e}")
                    logger.error(f"为代码块 {code_block.block_id} 关联嵌入失败: {e}")
            
            print(f"🔥 第4步完成：成功为 {embedded_count}/{len(code_blocks)} 个代码块生成嵌入向量")
            logger.info(f"成功为 {embedded_count}/{len(code_blocks)} 个代码块生成嵌入向量")
            
        except Exception as e:
            print(f"🔥 第4步异常: {e}")
            logger.error(f"关联向量到代码块失败: {e}")
        
        try:
            print("🔥 第5步：开始保存到存储")
            # 4. 保存代码块到本地存储（包含嵌入向量）
            saved_count = 0
            saved_with_vector_count = 0
            
            for code_block in code_blocks:
                try:
                    # 保存到本地存储和向量存储
                    self.storage.save_code_block_with_vector(code_block)
                    saved_count += 1
                    
                    if code_block.embedding:
                        saved_with_vector_count += 1
                        logger.debug(f"保存代码块 {code_block.block_id} 及其向量到存储")
                    else:
                        logger.warning(f"代码块 {code_block.block_id} 没有向量，仅保存元数据")
                        
                except Exception as e:
                    print(f"🔥 保存代码块 {code_block.block_id} 失败: {e}")
                    logger.error(f"保存代码块 {code_block.block_id} 失败: {e}")
            
            print(f"🔥 第5步完成：成功保存 {saved_count} 个代码块到存储，其中 {saved_with_vector_count} 个包含向量")
            logger.info(f"成功保存 {saved_count} 个代码块到存储，其中 {saved_with_vector_count} 个包含向量")
            
        except Exception as e:
            print(f"🔥 第5步异常: {e}")
            logger.error(f"保存到存储失败: {e}")
        
        try:
            print("🔥 第6步：验证向量存储")
            # 5. 验证向量是否正确保存
            vector_stats = self.storage.vector_storage.get_stats()
            logger.info(f"存储后向量统计: {vector_stats}")
            
            # 额外调试：检查向量存储中是否有数据
            if hasattr(self.storage.vector_storage, 'vectors'):
                actual_vector_count = len(self.storage.vector_storage.vectors)
                logger.info(f"实际向量存储中的向量数: {actual_vector_count}")
            elif hasattr(self.storage.vector_storage, 'collection'):
                try:
                    actual_vector_count = self.storage.vector_storage.collection.count()
                    logger.info(f"ChromaDB中的向量数: {actual_vector_count}")
                except:
                    pass
            
            print("🔥 第6步完成：向量存储验证完成")
                    
        except Exception as e:
            print(f"🔥 第6步异常: {e}")
            logger.warning(f"获取向量统计失败: {e}")
        
        try:
            print("🔥 第7步：更新进度")
            # 6. 更新进度
            if progress_callback:
                progress.processed_blocks = len(code_blocks)
                progress.current_stage = "embedding_complete"
                progress_callback(progress)
            print("🔥 第7步完成：进度更新完成")
                
        except Exception as e:
            print(f"🔥 第7步异常: {e}")
        
        print("🔥🔥🔥 _generate_embeddings方法完成！")

    def _generate_embeddings_for_blocks(self, code_blocks: List[CodeBlock]) -> None:
        """为代码块生成嵌入（简化版）"""
        logger.info(f"为 {len(code_blocks)} 个代码块生成嵌入")
        
        for code_block in code_blocks:
            try:
                content = f"{code_block.name}\n{code_block.content}"
                if code_block.signature:
                    content = f"{code_block.signature}\n{content}"
                
                # 生成嵌入并设置到代码块
                embedding = self.embedding_indexer.embedding_provider.get_embedding(content)
                code_block.embedding = embedding
                logger.debug(f"为代码块 {code_block.block_id} 生成嵌入成功")
                
            except Exception as e:
                logger.error(f"为代码块 {code_block.block_id} 生成嵌入失败: {e}")
                # 继续处理其他块
                continue

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
    storage_path: str = "./storage",
    config: Optional['CodeRepoConfig'] = None,
    embedding_provider=None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    **kwargs
) -> CodeIndexer:
    """
    创建代码索引器
    
    Args:
        storage_path: 存储路径
        config: 项目配置对象
        embedding_provider: 嵌入提供商
        api_key: API密钥
        base_url: API基础URL
        **kwargs: 其他配置参数
        
    Returns:
        CodeIndexer实例
    """
    return CodeIndexer(
        storage_path=storage_path,
        config=config,
        embedding_provider=embedding_provider,
        api_key=api_key,
        base_url=base_url,
        **kwargs
    ) 