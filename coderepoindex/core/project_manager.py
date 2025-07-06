"""
项目管理器模块

提供多项目的统一管理功能，确保不同项目的数据隔离和独立管理。
"""

import hashlib
import uuid
from typing import List, Optional, Dict, Any, Set
from pathlib import Path
from datetime import datetime
import logging
import re

from .models import RepositoryIndex, CodeBlock
from .storage_adapter import create_embedding_storage, EmbeddingStorageAdapter
from ..config import CodeRepoConfig

logger = logging.getLogger(__name__)


class ProjectInfo:
    """项目信息类"""
    
    def __init__(
        self,
        project_id: str,
        name: str,
        description: str = "",
        local_path: str = "",
        repository_url: str = "",
        created_at: Optional[datetime] = None,
        last_indexed_at: Optional[datetime] = None,
        **metadata
    ):
        self.project_id = project_id
        self.name = name
        self.description = description
        self.local_path = local_path
        self.repository_url = repository_url
        self.created_at = created_at or datetime.now()
        self.last_indexed_at = last_indexed_at
        self.metadata = metadata
        
        # 统计信息
        self._stats_cache = None
        self._stats_cache_time = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "project_id": self.project_id,
            "name": self.name,
            "description": self.description,
            "local_path": self.local_path,
            "repository_url": self.repository_url,
            "created_at": self.created_at.isoformat(),
            "last_indexed_at": self.last_indexed_at.isoformat() if self.last_indexed_at else None,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProjectInfo':
        """从字典创建实例"""
        created_at = datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None
        last_indexed_at = datetime.fromisoformat(data["last_indexed_at"]) if data.get("last_indexed_at") else None
        
        return cls(
            project_id=data["project_id"],
            name=data["name"],
            description=data.get("description", ""),
            local_path=data.get("local_path", ""),
            repository_url=data.get("repository_url", ""),
            created_at=created_at,
            last_indexed_at=last_indexed_at,
            **data.get("metadata", {})
        )


class ProjectManager:
    """
    项目管理器
    
    提供多项目的统一管理，包括项目创建、切换、数据隔离等功能。
    """
    
    def __init__(
        self,
        storage: Optional[EmbeddingStorageAdapter] = None,
        config: Optional[CodeRepoConfig] = None,
        **kwargs
    ):
        """
        初始化项目管理器
        
        Args:
            storage: 存储后端
            config: 配置对象
            **kwargs: 其他配置参数
        """
        self.config = config
        
        # 创建存储后端
        if storage is None:
            storage_config = {}
            if config:
                storage_config = {
                    'storage_path': config.storage.base_path,
                    # 传递embedding配置
                    'provider_type': config.embedding.provider_type,
                    'model_name': config.embedding.model_name,
                    'api_key': config.embedding.api_key,
                    'base_url': config.embedding.base_url,
                    'timeout': config.embedding.timeout,
                    'batch_size': config.embedding.batch_size,
                    **config.embedding.extra_params,
                    **config.storage.extra_params
                }
            else:
                storage_config = {
                    'storage_path': kwargs.get('storage_path', './storage'),
                    **kwargs
                }
            
            self.storage = create_embedding_storage(**storage_config)
        else:
            self.storage = storage
        
        # 当前活跃的项目
        self._current_project: Optional[str] = None
        self._connected = False
        
        logger.info("项目管理器初始化完成")
    
    def connect(self) -> None:
        """连接存储后端"""
        if not self._connected:
            self.storage.connect()
            self._connected = True
            logger.info("项目管理器连接成功")
    
    def disconnect(self) -> None:
        """断开存储连接"""
        if self._connected:
            self.storage.disconnect()
            self._connected = False
            logger.info("项目管理器连接已断开")
    
    def create_project(
        self,
        name: str,
        description: str = "",
        local_path: str = "",
        repository_url: str = "",
        project_id: Optional[str] = None,
        **metadata
    ) -> ProjectInfo:
        """
        创建新项目
        
        Args:
            name: 项目名称
            description: 项目描述
            local_path: 本地路径
            repository_url: 仓库URL
            project_id: 项目ID（可选，不提供则自动生成）
            **metadata: 其他元数据
            
        Returns:
            ProjectInfo: 项目信息对象
        """
        if not self._connected:
            self.connect()
        
        # 生成项目ID
        if project_id is None:
            if repository_url:
                # 基于仓库URL生成ID
                project_id = hashlib.md5(repository_url.encode('utf-8')).hexdigest()
            elif local_path:
                # 基于本地路径生成ID
                project_id = hashlib.md5(local_path.encode('utf-8')).hexdigest()
            else:
                # 生成随机ID
                project_id = str(uuid.uuid4()).replace('-', '')
        
        # 检查项目是否已存在
        if self.get_project(project_id):
            raise ValueError(f"项目ID已存在: {project_id}")
        
        # 创建项目信息
        project_info = ProjectInfo(
            project_id=project_id,
            name=name,
            description=description,
            local_path=local_path,
            repository_url=repository_url,
            **metadata
        )
        
        # 保存项目信息
        self._save_project_info(project_info)
        
        logger.info(f"项目创建成功: {name} ({project_id})")
        return project_info
    
    def get_project(self, project_id: str) -> Optional[ProjectInfo]:
        """获取项目信息"""
        if not self._connected:
            self.connect()
        
        try:
            # 从存储中获取项目元数据（适配器接口不同）
            metadata_key = f"project:{project_id}"
            if hasattr(self.storage, '_repository_indexes') and project_id in self.storage._repository_indexes:
                repo_index = self.storage._repository_indexes[project_id]
                return ProjectInfo(
                    project_id=repo_index.repository_id,
                    name=repo_index.name,
                    description="",
                    local_path=repo_index.local_path,
                    repository_url=repo_index.url,
                    created_at=repo_index.created_at,
                    last_indexed_at=repo_index.indexed_at
                )
            
            # 尝试从仓库索引中获取
            repo_index = self.storage.get_repository_index(project_id)
            if repo_index:
                return ProjectInfo(
                    project_id=repo_index.repository_id,
                    name=repo_index.name,
                    description="",
                    local_path=repo_index.local_path,
                    repository_url=repo_index.url,
                    created_at=repo_index.created_at,
                    last_indexed_at=repo_index.indexed_at
                )
            
            return None
            
        except Exception as e:
            logger.error(f"获取项目信息失败: {e}")
            return None
    
    def list_projects(self) -> List[ProjectInfo]:
        """列出所有项目"""
        if not self._connected:
            self.connect()
        
        projects = []
        
        try:
            # 从项目元数据获取
            project_keys = [key for key in self.storage.metadata_storage.list_metadata_keys() 
                          if key.startswith("project:")]
            
            for key in project_keys:
                project_id = key.replace("project:", "")
                project_info = self.get_project(project_id)
                if project_info:
                    projects.append(project_info)
            
            # 从仓库索引补充
            repo_indexes = self.storage.list_repository_indexes()
            existing_ids = {p.project_id for p in projects}
            
            for repo_index in repo_indexes:
                if repo_index.repository_id not in existing_ids:
                    project_info = ProjectInfo(
                        project_id=repo_index.repository_id,
                        name=repo_index.name,
                        description="",
                        local_path=repo_index.local_path,
                        repository_url=repo_index.url,
                        created_at=repo_index.created_at,
                        last_indexed_at=repo_index.indexed_at
                    )
                    projects.append(project_info)
            
            # 按创建时间排序
            projects.sort(key=lambda x: x.created_at, reverse=True)
            return projects
            
        except Exception as e:
            logger.error(f"列出项目失败: {e}")
            return []
    
    def delete_project(self, project_id: str, delete_data: bool = True) -> bool:
        """
        删除项目
        
        Args:
            project_id: 项目ID
            delete_data: 是否删除项目相关的所有数据
            
        Returns:
            bool: 是否删除成功
        """
        if not self._connected:
            self.connect()
        
        try:
            # 删除项目相关数据
            if delete_data:
                result = self.storage.delete_repository_data(project_id)
                logger.info(f"删除项目数据: {result}")
            
            # 删除项目元数据
            self.storage.metadata_storage.delete_metadata(f"project:{project_id}")
            
            # 如果当前项目被删除，清空当前项目
            if self._current_project == project_id:
                self._current_project = None
            
            logger.info(f"项目删除成功: {project_id}")
            return True
            
        except Exception as e:
            logger.error(f"删除项目失败: {e}")
            return False
    
    def set_current_project(self, project_id: str) -> bool:
        """设置当前活跃项目"""
        if not self._connected:
            self.connect()
        
        # 验证项目是否存在
        project = self.get_project(project_id)
        if not project:
            logger.error(f"项目不存在: {project_id}")
            return False
        
        self._current_project = project_id
        
        # 保存到元数据
        self.storage.metadata_storage.set_metadata("current_project", project_id)
        
        logger.info(f"当前项目设置为: {project.name} ({project_id})")
        return True
    
    def get_current_project(self) -> Optional[ProjectInfo]:
        """获取当前活跃项目"""
        if not self._connected:
            self.connect()
        
        if self._current_project is None:
            # 从存储中恢复当前项目
            current_id = self.storage.metadata_storage.get_metadata("current_project")
            if current_id:
                self._current_project = current_id
        
        if self._current_project:
            return self.get_project(self._current_project)
        
        return None
    
    def get_project_stats(self, project_id: str) -> Dict[str, Any]:
        """获取项目统计信息"""
        if not self._connected:
            self.connect()
        
        try:
            # 获取代码块统计
            total_blocks = self.storage.code_block_storage.count_code_blocks(repository_id=project_id)
            
            # 获取语言分布
            blocks = self.storage.query_code_blocks(repository_id=project_id, limit=1000)
            language_distribution = {}
            for block in blocks:
                if block.language:
                    language_distribution[block.language] = language_distribution.get(block.language, 0) + 1
            
            # 获取文件数量
            file_paths = set(block.file_path for block in blocks)
            total_files = len(file_paths)
            
            return {
                "project_id": project_id,
                "total_blocks": total_blocks,
                "total_files": total_files,
                "language_distribution": language_distribution,
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取项目统计失败: {e}")
            return {}
    
    def search_in_project(
        self,
        query: str,
        project_id: Optional[str] = None,
        **kwargs
    ) -> List[Any]:
        """
        在指定项目中搜索
        
        Args:
            query: 搜索查询
            project_id: 项目ID，为None时使用当前项目
            **kwargs: 其他搜索参数
            
        Returns:
            搜索结果列表
        """
        if not self._connected:
            self.connect()
        
        # 确定搜索的项目
        target_project_id = project_id
        if target_project_id is None:
            current_project = self.get_current_project()
            if current_project:
                target_project_id = current_project.project_id
            else:
                logger.warning("没有指定项目ID，且没有当前活跃项目")
                return []
        
        # 验证项目存在
        if not self.get_project(target_project_id):
            logger.error(f"项目不存在: {target_project_id}")
            return []
        
        # 在查询参数中添加项目ID过滤
        kwargs['repository_id'] = target_project_id
        
        logger.info(f"在项目 {target_project_id} 中搜索: {query}")
        
        # 获取项目中的所有代码块
        blocks = self.storage.query_code_blocks(repository_id=target_project_id)
        
        if not blocks:
            logger.warning(f"项目 {target_project_id} 中没有找到任何代码块")
            return []
        
        # 智能搜索逻辑
        results = []
        query_lower = query.lower()
        
        # 提取查询中的关键词（简单的分词）
        keywords = re.findall(r'\b\w+\b', query_lower)
        keywords = [kw for kw in keywords if len(kw) > 2]  # 过滤短词
        
        logger.info(f"提取的关键词: {keywords}")
        
        for block in blocks:
            score = 0
            reasons = []
            
            # 1. 精确匹配（最高分）
            if query_lower in block.content.lower():
                score += 10
                reasons.append("内容精确匹配")
            
            if query_lower in block.name.lower():
                score += 8
                reasons.append("名称精确匹配")
            
            if query_lower in block.search_text.lower():
                score += 6
                reasons.append("搜索文本匹配")
            
            # 2. 关键词匹配
            if keywords:
                content_lower = block.content.lower()
                name_lower = block.name.lower()
                search_text_lower = block.search_text.lower()
                
                for keyword in keywords:
                    if keyword in content_lower:
                        score += 2
                        reasons.append(f"关键词'{keyword}'在内容中")
                    
                    if keyword in name_lower:
                        score += 3
                        reasons.append(f"关键词'{keyword}'在名称中")
                    
                    if keyword in search_text_lower:
                        score += 1
                        reasons.append(f"关键词'{keyword}'在搜索文本中")
                    
                    # 检查关键词和注释
                    for block_keyword in block.keywords:
                        if keyword in block_keyword.lower():
                            score += 1
                            reasons.append(f"关键词匹配")
            
            # 3. 特殊模式匹配（针对编程相关查询）
            programming_patterns = {
                'post request': ['post', 'request', 'http'],
                'json data': ['json', 'data'],
                'send': ['send', 'transmit', 'post'],
                'api': ['api', 'endpoint', 'service'],
                'function': ['def ', 'function', 'method'],
                'class': ['class ', 'object'],
            }
            
            query_patterns = []
            for pattern, terms in programming_patterns.items():
                if pattern in query_lower:
                    query_patterns.extend(terms)
            
            if query_patterns:
                content_lower = block.content.lower()
                for pattern_term in query_patterns:
                    if pattern_term in content_lower:
                        score += 1
                        reasons.append(f"模式匹配: {pattern_term}")
            
            # 如果有分数，则添加到结果中
            if score > 0:
                # 创建简单的结果对象（模拟SearchResult）
                result = type('SearchResult', (), {
                    'block': block,
                    'score': score,
                    'match_reason': '; '.join(reasons),
                    'file_path': block.file_path,
                    'name': block.name,
                    'content': block.content
                })()
                results.append(result)
        
        # 按分数排序
        results.sort(key=lambda x: x.score, reverse=True)
        
        # 限制结果数量
        max_results = kwargs.get('top_k', 10)
        final_results = results[:max_results]
        
        logger.info(f"搜索完成，找到 {len(final_results)} 个结果")
        
        return final_results
    
    def _save_project_info(self, project_info: ProjectInfo) -> None:
        """保存项目信息到存储"""
        self.storage.metadata_storage.set_metadata(
            f"project:{project_info.project_id}",
            project_info.to_dict()
        )
    
    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.disconnect()


def create_project_manager(
    storage_path: str = "./storage",
    config: Optional[CodeRepoConfig] = None,
    **kwargs
) -> ProjectManager:
    """
    创建项目管理器实例
    
    Args:
        storage_path: 存储路径
        config: 配置对象
        **kwargs: 其他配置参数
        
    Returns:
        ProjectManager实例
    """
    return ProjectManager(
        storage=None,  # 让ProjectManager自己创建存储
        config=config,
        storage_path=storage_path,
        **kwargs
    ) 