"""
版本管理模块

负责：
1. 检测文件内容变化（基于MD5）
2. 管理代码片段版本
3. 支持增量更新
4. 提供变化差异分析
"""

import hashlib
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum

from .code_parser import CodeSnippet, SnippetType


class ChangeType(Enum):
    """变化类型"""
    ADDED = "added"       # 新增文件/切块
    MODIFIED = "modified" # 修改文件/切块
    DELETED = "deleted"   # 删除文件/切块
    UNCHANGED = "unchanged" # 无变化


@dataclass
class FileSnapshot:
    """文件快照"""
    file_path: str
    file_md5: str
    file_size: int
    modified_time: float
    repo_commit: str
    chunks_count: int
    chunk_hashes: List[str]  # 该文件所有切块的hash
    created_at: str
    updated_at: str


@dataclass
class ChangeRecord:
    """变化记录"""
    file_path: str
    change_type: ChangeType
    old_md5: Optional[str] = None
    new_md5: Optional[str] = None
    old_chunks: List[str] = None    # 旧切块hash列表
    new_chunks: List[str] = None    # 新切块hash列表
    added_chunks: List[str] = None  # 新增切块
    modified_chunks: List[str] = None # 修改切块
    deleted_chunks: List[str] = None  # 删除切块


class VersionManager:
    """版本管理器"""
    
    def __init__(self, storage_dir: str = ".coderepo_index"):
        """
        初始化版本管理器
        
        Args:
            storage_dir: 存储版本信息的目录
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        
        # 版本数据存储文件
        self.snapshots_file = self.storage_dir / "file_snapshots.json"
        self.chunks_index_file = self.storage_dir / "chunks_index.json"
        
        # 加载现有数据
        self.file_snapshots: Dict[str, FileSnapshot] = self._load_snapshots()
        self.chunks_index: Dict[str, Dict] = self._load_chunks_index()
    
    def calculate_file_md5(self, file_path: Path) -> str:
        """计算文件MD5"""
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
                return hashlib.md5(content).hexdigest()
        except Exception as e:
            print(f"计算文件MD5失败 {file_path}: {e}")
            return ""
    
    def calculate_chunk_hash(self, content: str) -> str:
        """计算切块内容hash"""
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def detect_file_changes(self, 
                          repo_path: str, 
                          repo_commit: str,
                          file_paths: List[str]) -> List[ChangeRecord]:
        """
        检测文件变化
        
        Args:
            repo_path: 仓库路径
            repo_commit: 仓库commit hash
            file_paths: 要检测的文件路径列表
            
        Returns:
            变化记录列表
        """
        changes = []
        repo_path = Path(repo_path)
        current_time = datetime.now().isoformat()
        
        # 检查现有文件的变化
        for file_path in file_paths:
            full_path = repo_path / file_path
            if not full_path.exists():
                # 文件被删除
                if file_path in self.file_snapshots:
                    old_snapshot = self.file_snapshots[file_path]
                    changes.append(ChangeRecord(
                        file_path=file_path,
                        change_type=ChangeType.DELETED,
                        old_md5=old_snapshot.file_md5,
                        old_chunks=old_snapshot.chunk_hashes
                    ))
                continue
            
            # 计算当前文件MD5
            current_md5 = self.calculate_file_md5(full_path)
            file_stat = full_path.stat()
            
            if file_path in self.file_snapshots:
                old_snapshot = self.file_snapshots[file_path]
                if old_snapshot.file_md5 != current_md5:
                    # 文件已修改
                    changes.append(ChangeRecord(
                        file_path=file_path,
                        change_type=ChangeType.MODIFIED,
                        old_md5=old_snapshot.file_md5,
                        new_md5=current_md5,
                        old_chunks=old_snapshot.chunk_hashes
                    ))
                else:
                    # 文件无变化
                    changes.append(ChangeRecord(
                        file_path=file_path,
                        change_type=ChangeType.UNCHANGED,
                        old_md5=current_md5,
                        new_md5=current_md5
                    ))
            else:
                # 新文件
                changes.append(ChangeRecord(
                    file_path=file_path,
                    change_type=ChangeType.ADDED,
                    new_md5=current_md5
                ))
        
        return changes
    
    def update_file_snapshot(self, 
                           file_path: str,
                           file_md5: str,
                           repo_commit: str,
                           chunk_hashes: List[str],
                           repo_path: str):
        """更新文件快照"""
        full_path = Path(repo_path) / file_path
        file_stat = full_path.stat()
        current_time = datetime.now().isoformat()
        
        if file_path in self.file_snapshots:
            # 更新现有快照
            snapshot = self.file_snapshots[file_path]
            snapshot.file_md5 = file_md5
            snapshot.file_size = file_stat.st_size
            snapshot.modified_time = file_stat.st_mtime
            snapshot.repo_commit = repo_commit
            snapshot.chunks_count = len(chunk_hashes)
            snapshot.chunk_hashes = chunk_hashes
            snapshot.updated_at = current_time
        else:
            # 创建新快照
            self.file_snapshots[file_path] = FileSnapshot(
                file_path=file_path,
                file_md5=file_md5,
                file_size=file_stat.st_size,
                modified_time=file_stat.st_mtime,
                repo_commit=repo_commit,
                chunks_count=len(chunk_hashes),
                chunk_hashes=chunk_hashes,
                created_at=current_time,
                updated_at=current_time
            )
    
    def detect_chunk_changes(self, 
                           old_chunks: List[str], 
                           new_chunks: List[CodeSnippet]) -> Tuple[List[str], List[str], List[str]]:
        """
        检测切块级别的变化
        
        Args:
            old_chunks: 旧切块hash列表
            new_chunks: 新切块列表
            
        Returns:
            (新增切块hash, 修改切块hash, 删除切块hash)
        """
        old_chunk_set = set(old_chunks) if old_chunks else set()
        new_chunk_hashes = [self.calculate_chunk_hash(chunk.content) for chunk in new_chunks]
        new_chunk_set = set(new_chunk_hashes)
        
        added = list(new_chunk_set - old_chunk_set)
        deleted = list(old_chunk_set - new_chunk_set)
        unchanged = list(old_chunk_set & new_chunk_set)
        
        return added, unchanged, deleted
    
    def update_chunks_index(self, chunks: List[CodeSnippet]):
        """更新切块索引"""
        for chunk in chunks:
            chunk_hash = self.calculate_chunk_hash(chunk.content)
            chunk.chunk_hash = chunk_hash
            
            # 更新切块索引
            if chunk_hash in self.chunks_index:
                # 更新现有切块
                existing = self.chunks_index[chunk_hash]
                existing['version'] += 1
                existing['updated_at'] = datetime.now().isoformat()
                existing['file_path'] = chunk.file_path
                existing['repo_commit'] = chunk.repo_commit
            else:
                # 新切块
                self.chunks_index[chunk_hash] = {
                    'chunk_hash': chunk_hash,
                    'content': chunk.content,
                    'file_path': chunk.file_path,
                    'repo_commit': chunk.repo_commit,
                    'version': 1,
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat(),
                    'snippet_type': chunk.snippet_type.value if chunk.snippet_type else None,
                    'language': chunk.language,
                    'start_line': chunk.start_line,
                    'end_line': chunk.end_line
                }
    
    def get_incremental_update_plan(self, 
                                  repo_path: str,
                                  repo_commit: str,
                                  file_paths: List[str]) -> Dict[str, Any]:
        """
        生成增量更新计划
        
        Returns:
            包含需要处理的文件和预期变化的更新计划
        """
        changes = self.detect_file_changes(repo_path, repo_commit, file_paths)
        
        plan = {
            'repo_commit': repo_commit,
            'total_files': len(file_paths),
            'changes_summary': {
                'added': len([c for c in changes if c.change_type == ChangeType.ADDED]),
                'modified': len([c for c in changes if c.change_type == ChangeType.MODIFIED]),
                'deleted': len([c for c in changes if c.change_type == ChangeType.DELETED]),
                'unchanged': len([c for c in changes if c.change_type == ChangeType.UNCHANGED])
            },
            'files_to_process': [c.file_path for c in changes 
                               if c.change_type in [ChangeType.ADDED, ChangeType.MODIFIED]],
            'files_to_delete': [c.file_path for c in changes 
                              if c.change_type == ChangeType.DELETED],
            'unchanged_files': [c.file_path for c in changes 
                              if c.change_type == ChangeType.UNCHANGED],
            'detailed_changes': [asdict(c) for c in changes]
        }
        
        return plan
    
    def save_state(self):
        """保存版本状态到磁盘"""
        # 保存文件快照
        snapshots_data = {
            path: asdict(snapshot) 
            for path, snapshot in self.file_snapshots.items()
        }
        with open(self.snapshots_file, 'w', encoding='utf-8') as f:
            json.dump(snapshots_data, f, ensure_ascii=False, indent=2)
        
        # 保存切块索引
        with open(self.chunks_index_file, 'w', encoding='utf-8') as f:
            json.dump(self.chunks_index, f, ensure_ascii=False, indent=2)
    
    def _load_snapshots(self) -> Dict[str, FileSnapshot]:
        """加载文件快照"""
        if not self.snapshots_file.exists():
            return {}
        
        try:
            with open(self.snapshots_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {
                    path: FileSnapshot(**snapshot_data)
                    for path, snapshot_data in data.items()
                }
        except Exception as e:
            print(f"加载文件快照失败: {e}")
            return {}
    
    def _load_chunks_index(self) -> Dict[str, Dict]:
        """加载切块索引"""
        if not self.chunks_index_file.exists():
            return {}
        
        try:
            with open(self.chunks_index_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载切块索引失败: {e}")
            return {}
    
    def cleanup_orphaned_chunks(self):
        """清理孤儿切块（不再属于任何文件的切块）"""
        # 获取所有当前文件的切块hash
        current_chunks = set()
        for snapshot in self.file_snapshots.values():
            current_chunks.update(snapshot.chunk_hashes)
        
        # 找出孤儿切块
        orphaned_chunks = set(self.chunks_index.keys()) - current_chunks
        
        # 删除孤儿切块
        for chunk_hash in orphaned_chunks:
            del self.chunks_index[chunk_hash]
        
        if orphaned_chunks:
            print(f"清理了 {len(orphaned_chunks)} 个孤儿切块")
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取版本管理统计信息"""
        return {
            'total_files': len(self.file_snapshots),
            'total_chunks': len(self.chunks_index),
            'storage_size': {
                'snapshots_file': self.snapshots_file.stat().st_size if self.snapshots_file.exists() else 0,
                'chunks_index_file': self.chunks_index_file.stat().st_size if self.chunks_index_file.exists() else 0
            },
            'latest_commits': list(set(snapshot.repo_commit for snapshot in self.file_snapshots.values()))
        } 