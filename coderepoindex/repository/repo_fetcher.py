"""
代码仓库获取器

支持从多种源获取代码仓库：
1. Git 仓库 - 支持指定分支、标签、提交等
2. 本地路径 - 直接使用本地代码仓库
3. ZIP 文件 - 解压 ZIP 包到临时目录
"""

import os
import shutil
import tempfile
import zipfile
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any, Union
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

try:
    import git
    HAS_GITPYTHON = True
except ImportError:
    HAS_GITPYTHON = False
    logger.warning("GitPython 未安装，Git 功能将不可用")


class RepoSource(Enum):
    """仓库源类型"""
    GIT = "git"
    LOCAL = "local"
    ZIP = "zip"


@dataclass
class RepoConfig:
    """仓库配置"""
    source: RepoSource
    path: str
    branch: Optional[str] = None
    tag: Optional[str] = None
    commit: Optional[str] = None
    auth_token: Optional[str] = None
    target_dir: Optional[str] = None
    cleanup_on_error: bool = True


class RepositoryFetcher:
    """
    代码仓库获取器
    
    提供统一的接口来获取不同来源的代码仓库
    """
    
    def __init__(self, temp_dir: Optional[str] = None):
        """
        初始化仓库获取器
        
        Args:
            temp_dir: 临时目录路径，用于存放克隆的仓库
        """
        self.temp_dir = temp_dir or tempfile.gettempdir()
        self.temp_repos = []  # 跟踪创建的临时仓库，用于清理
        
    def fetch(self, config: RepoConfig) -> str:
        """
        根据配置获取代码仓库
        
        Args:
            config: 仓库配置
            
        Returns:
            本地仓库路径
            
        Raises:
            ValueError: 配置错误
            RuntimeError: 获取失败
        """
        logger.info(f"开始获取仓库: {config.source.value} - {config.path}")
        
        try:
            if config.source == RepoSource.GIT:
                return self._fetch_git_repo(config)
            elif config.source == RepoSource.LOCAL:
                return self._fetch_local_repo(config)
            elif config.source == RepoSource.ZIP:
                return self._fetch_zip_repo(config)
            else:
                raise ValueError(f"不支持的仓库源类型: {config.source}")
                
        except Exception as e:
            logger.error(f"获取仓库失败: {e}")
            if config.cleanup_on_error:
                self._cleanup_temp_repo(config.target_dir)
            raise RuntimeError(f"获取仓库失败: {e}") from e
    
    def _fetch_git_repo(self, config: RepoConfig) -> str:
        """获取 Git 仓库"""
        if not HAS_GITPYTHON:
            raise RuntimeError("需要安装 GitPython 来支持 Git 功能: pip install GitPython")
            
        # 确定目标目录
        if config.target_dir:
            target_path = Path(config.target_dir)
        else:
            # 使用当前目录下的 .coderepo 目录
            coderepo_dir = Path.cwd() / ".coderepo"
            coderepo_dir.mkdir(exist_ok=True)  # 如果不存在就创建
            
            # 根据仓库URL生成基础目录名
            repo_name = self._extract_repo_name(config.path)
            
            # 如果指定了commit，获取完整的commit hash用于目录命名
            commit_hash = None
            if config.commit:
                commit_hash = self._resolve_commit_hash(config.path, config.commit, config)
            elif config.tag:
                # 对于tag，也解析为commit hash
                commit_hash = self._resolve_tag_to_commit(config.path, config.tag, config)
            elif config.branch:
                # 对于分支，获取最新的commit hash
                commit_hash = self._resolve_branch_to_commit(config.path, config.branch, config)
                
            # 根据commit hash生成目录名
            if commit_hash:
                # 使用仓库名_commit前8位作为目录名
                target_dir_name = f"{repo_name}_{commit_hash[:8]}"
            else:
                # 如果无法获取commit信息，使用默认名称
                target_dir_name = repo_name
                
            target_path = coderepo_dir / target_dir_name
            
            # 如果目录已存在且是相同的commit，直接返回
            if target_path.exists() and commit_hash:
                existing_commit = self._get_existing_commit(target_path)
                if existing_commit and existing_commit.startswith(commit_hash[:8]):
                    logger.info(f"目录 {target_path} 已存在相同commit，直接使用")
                    return str(target_path)
                    
        target_path.mkdir(parents=True, exist_ok=True)
        
        try:
            # 克隆仓库
            logger.info(f"克隆 Git 仓库到: {target_path}")
            
            # 设置克隆选项
            clone_kwargs = {}
            if config.auth_token:
                # 如果提供了认证令牌，修改 URL
                if config.path.startswith("https://github.com"):
                    clone_url = config.path.replace("https://", f"https://{config.auth_token}@")
                else:
                    clone_url = config.path
                clone_kwargs['url'] = clone_url
            else:
                clone_kwargs['url'] = config.path
                
            # 如果指定了分支，只克隆该分支
            if config.branch:
                clone_kwargs['branch'] = config.branch
                clone_kwargs['single_branch'] = True
                
            repo = git.Repo.clone_from(
                to_path=str(target_path),
                **clone_kwargs
            )
            
            # 检出指定的提交或标签
            if config.commit:
                logger.info(f"检出提交: {config.commit}")
                repo.git.checkout(config.commit)
            elif config.tag:
                logger.info(f"检出标签: {config.tag}")
                repo.git.checkout(config.tag)
            elif config.branch and config.branch != "master" and config.branch != "main":
                logger.info(f"检出分支: {config.branch}")
                repo.git.checkout(config.branch)
                
            logger.info(f"Git 仓库获取成功: {target_path}")
            return str(target_path)
            
        except git.exc.GitError as e:
            raise RuntimeError(f"Git 操作失败: {e}")
    
    def _extract_repo_name(self, repo_url: str) -> str:
        """从 Git URL 中提取仓库名称"""
        # 移除 .git 后缀
        if repo_url.endswith('.git'):
            repo_url = repo_url[:-4]
        
        # 提取最后一部分作为仓库名
        repo_name = repo_url.rstrip('/').split('/')[-1]
        
        # 清理特殊字符，只保留字母、数字、连字符和下划线
        import re
        repo_name = re.sub(r'[^\w\-_]', '_', repo_name)
        
        return repo_name or "unknown_repo"
    
    def _resolve_commit_hash(self, repo_url: str, commit_ref: str, config: RepoConfig) -> Optional[str]:
        """解析commit引用为完整的commit hash"""
        try:
            # 创建一个临时目录进行轻量级克隆
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_repo_path = Path(temp_dir) / "temp_repo"
                
                # 设置克隆选项
                clone_kwargs = {'url': repo_url, 'to_path': str(temp_repo_path)}
                if config.auth_token and repo_url.startswith("https://github.com"):
                    clone_kwargs['url'] = repo_url.replace("https://", f"https://{config.auth_token}@")
                
                # 轻量级克隆（只获取元数据）
                repo = git.Repo.clone_from(**clone_kwargs)
                
                # 解析commit hash
                commit_obj = repo.commit(commit_ref)
                return commit_obj.hexsha
                
        except Exception as e:
            logger.warning(f"无法解析commit hash {commit_ref}: {e}")
            return commit_ref  # 返回原始引用
    
    def _resolve_tag_to_commit(self, repo_url: str, tag: str, config: RepoConfig) -> Optional[str]:
        """解析tag为commit hash"""
        return self._resolve_commit_hash(repo_url, tag, config)
    
    def _resolve_branch_to_commit(self, repo_url: str, branch: str, config: RepoConfig) -> Optional[str]:
        """解析分支为最新的commit hash"""
        try:
            # 创建一个临时目录进行轻量级克隆
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_repo_path = Path(temp_dir) / "temp_repo"
                
                # 设置克隆选项
                clone_kwargs = {
                    'url': repo_url, 
                    'to_path': str(temp_repo_path),
                    'branch': branch,
                    'single_branch': True,
                    'depth': 1  # 只克隆最新的commit
                }
                if config.auth_token and repo_url.startswith("https://github.com"):
                    clone_kwargs['url'] = repo_url.replace("https://", f"https://{config.auth_token}@")
                
                repo = git.Repo.clone_from(**clone_kwargs)
                return repo.head.commit.hexsha
                
        except Exception as e:
            logger.warning(f"无法解析分支 {branch} 的commit hash: {e}")
            return None
    
    def _get_existing_commit(self, repo_path: Path) -> Optional[str]:
        """获取现有仓库的当前commit hash"""
        try:
            if not (repo_path / ".git").exists():
                return None
                
            repo = git.Repo(str(repo_path))
            return repo.head.commit.hexsha
            
        except Exception as e:
            logger.warning(f"无法获取现有仓库的commit hash: {e}")
            return None
    
    def _fetch_local_repo(self, config: RepoConfig) -> str:
        """获取本地仓库"""
        repo_path = Path(config.path)
        
        if not repo_path.exists():
            raise ValueError(f"本地路径不存在: {repo_path}")
            
        if not repo_path.is_dir():
            raise ValueError(f"路径不是目录: {repo_path}")
            
        logger.info(f"使用本地仓库: {repo_path}")
        return str(repo_path.resolve())
    
    def _fetch_zip_repo(self, config: RepoConfig) -> str:
        """获取 ZIP 仓库"""
        zip_path = Path(config.path)
        
        if not zip_path.exists():
            raise ValueError(f"ZIP 文件不存在: {zip_path}")
            
        if not zip_path.suffix.lower() == '.zip':
            raise ValueError(f"文件不是 ZIP 格式: {zip_path}")
            
        # 确定解压目录
        if config.target_dir:
            extract_path = Path(config.target_dir)
        else:
            extract_path = Path(self.temp_dir) / f"zip_repo_{len(self.temp_repos)}"
            self.temp_repos.append(str(extract_path))
            
        extract_path.mkdir(parents=True, exist_ok=True)
        
        try:
            logger.info(f"解压 ZIP 文件到: {extract_path}")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)
                
            # 检查是否有单个根目录（常见的 ZIP 结构）
            extracted_items = list(extract_path.iterdir())
            if len(extracted_items) == 1 and extracted_items[0].is_dir():
                repo_path = extracted_items[0]
            else:
                repo_path = extract_path
                
            logger.info(f"ZIP 仓库解压成功: {repo_path}")
            return str(repo_path)
            
        except zipfile.BadZipFile as e:
            raise RuntimeError(f"无效的 ZIP 文件: {e}")
    
    def _cleanup_temp_repo(self, repo_path: Optional[str]):
        """清理临时仓库"""
        if repo_path and Path(repo_path).exists():
            try:
                shutil.rmtree(repo_path)
                logger.info(f"清理临时仓库: {repo_path}")
            except Exception as e:
                logger.warning(f"清理临时仓库失败: {e}")
    
    def cleanup_all(self):
        """清理所有临时仓库"""
        for repo_path in self.temp_repos:
            self._cleanup_temp_repo(repo_path)
        self.temp_repos.clear()
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口，自动清理"""
        self.cleanup_all()


def create_git_config(
    repo_url: str,
    branch: Optional[str] = None,
    tag: Optional[str] = None,
    commit: Optional[str] = None,
    auth_token: Optional[str] = None,
    target_dir: Optional[str] = None
) -> RepoConfig:
    """
    创建 Git 仓库配置的便捷函数
    
    Args:
        repo_url: Git 仓库 URL
        branch: 分支名（默认为仓库默认分支）
        tag: 标签名
        commit: 提交哈希
        auth_token: 认证令牌
        target_dir: 目标目录
        
    Returns:
        仓库配置对象
    """
    return RepoConfig(
        source=RepoSource.GIT,
        path=repo_url,
        branch=branch,
        tag=tag,
        commit=commit,
        auth_token=auth_token,
        target_dir=target_dir
    )


def create_local_config(repo_path: str) -> RepoConfig:
    """
    创建本地仓库配置的便捷函数
    
    Args:
        repo_path: 本地仓库路径
        
    Returns:
        仓库配置对象
    """
    return RepoConfig(
        source=RepoSource.LOCAL,
        path=repo_path
    )


def create_zip_config(
    zip_path: str,
    target_dir: Optional[str] = None
) -> RepoConfig:
    """
    创建 ZIP 仓库配置的便捷函数
    
    Args:
        zip_path: ZIP 文件路径
        target_dir: 解压目标目录
        
    Returns:
        仓库配置对象
    """
    return RepoConfig(
        source=RepoSource.ZIP,
        path=zip_path,
        target_dir=target_dir
    ) 