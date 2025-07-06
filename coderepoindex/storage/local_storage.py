"""
本地文件系统存储实现

基于本地文件系统的存储后端，支持代码块、元数据的持久化存储。
"""

import json
import os
import shutil
from pathlib import Path
from typing import List, Optional, Dict, Any, Iterator
from datetime import datetime
import sqlite3
from contextlib import contextmanager
import logging

from .base import (
    BaseCodeBlockStorage, 
    BaseMetadataStorage, 
    StorageConfig,
    StorageError,
    StorageNotFoundError,
    StorageConnectionError
)
from ..core.models import CodeBlock, RepositoryIndex, SearchQuery, BlockType

logger = logging.getLogger(__name__)


class LocalCodeBlockStorage(BaseCodeBlockStorage):
    """
    本地代码块存储实现
    
    使用SQLite数据库存储代码块的结构化信息，
    使用文件系统存储代码块的完整内容。
    """
    
    def __init__(self, config: StorageConfig):
        super().__init__(config)
        self.base_path = Path(config.base_path)
        self.db_path = self.base_path / "code_blocks.db"
        self.content_path = self.base_path / "content"
        self._connection = None
        
    def connect(self) -> None:
        """连接存储后端"""
        try:
            # 创建目录
            self.base_path.mkdir(parents=True, exist_ok=True)
            self.content_path.mkdir(parents=True, exist_ok=True)
            
            # 连接数据库
            self._connection = sqlite3.connect(str(self.db_path), check_same_thread=False)
            self._connection.row_factory = sqlite3.Row
            
            # 创建表
            self._create_tables()
            
            logger.info(f"本地代码块存储连接成功: {self.base_path}")
            
        except Exception as e:
            logger.error(f"连接本地代码块存储失败: {e}")
            raise StorageConnectionError(f"连接失败: {e}")
    
    def disconnect(self) -> None:
        """断开存储连接"""
        if self._connection:
            self._connection.close()
            self._connection = None
            logger.info("本地代码块存储连接已断开")
    
    def health_check(self) -> bool:
        """健康检查"""
        try:
            if not self._connection:
                return False
            
            # 检查数据库连接
            cursor = self._connection.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            
            # 检查目录
            return self.base_path.exists() and self.content_path.exists()
            
        except Exception:
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """获取存储统计信息"""
        try:
            cursor = self._connection.cursor()
            
            # 统计代码块数量
            cursor.execute("SELECT COUNT(*) FROM code_blocks")
            total_blocks = cursor.fetchone()[0]
            
            # 统计仓库数量
            cursor.execute("SELECT COUNT(DISTINCT repository_id) FROM code_blocks")
            total_repositories = cursor.fetchone()[0]
            
            # 统计语言分布
            cursor.execute("""
                SELECT language, COUNT(*) as count 
                FROM code_blocks 
                WHERE language IS NOT NULL 
                GROUP BY language
            """)
            language_distribution = {row[0]: row[1] for row in cursor.fetchall()}
            
            # 计算存储大小
            storage_size = self._calculate_storage_size()
            
            return {
                "total_blocks": total_blocks,
                "total_repositories": total_repositories,
                "language_distribution": language_distribution,
                "storage_size": storage_size,
                "db_path": str(self.db_path),
                "content_path": str(self.content_path)
            }
            
        except Exception as e:
            logger.error(f"获取存储统计信息失败: {e}")
            return {}
    
    def _create_tables(self) -> None:
        """创建数据库表"""
        cursor = self._connection.cursor()
        
        # 创建代码块表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS code_blocks (
                block_id TEXT PRIMARY KEY,
                repository_id TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                file_path TEXT NOT NULL,
                line_start INTEGER NOT NULL,
                line_end INTEGER NOT NULL,
                char_start INTEGER,
                char_end INTEGER,
                block_type TEXT NOT NULL,
                language TEXT,
                name TEXT NOT NULL,
                full_name TEXT,
                signature TEXT,
                class_name TEXT,
                namespace TEXT,
                keywords TEXT,
                search_text TEXT,
                parent_block_id TEXT,
                metadata TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (parent_block_id) REFERENCES code_blocks(block_id)
            )
        """)
        
        # 创建索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_repository_id ON code_blocks(repository_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_language ON code_blocks(language)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_block_type ON code_blocks(block_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_file_path ON code_blocks(file_path)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_name ON code_blocks(name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_search_text ON code_blocks(search_text)")
        
        # 创建关系表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS code_block_relations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                parent_block_id TEXT NOT NULL,
                child_block_id TEXT NOT NULL,
                relation_type TEXT NOT NULL,
                FOREIGN KEY (parent_block_id) REFERENCES code_blocks(block_id),
                FOREIGN KEY (child_block_id) REFERENCES code_blocks(block_id),
                UNIQUE(parent_block_id, child_block_id, relation_type)
            )
        """)
        
        self._connection.commit()
    
    def _calculate_storage_size(self) -> str:
        """计算存储大小"""
        try:
            total_size = 0
            
            # 计算数据库大小
            if self.db_path.exists():
                total_size += self.db_path.stat().st_size
            
            # 计算内容文件大小
            for root, dirs, files in os.walk(self.content_path):
                for file in files:
                    file_path = Path(root) / file
                    total_size += file_path.stat().st_size
            
            # 转换为可读格式
            for unit in ['B', 'KB', 'MB', 'GB']:
                if total_size < 1024.0:
                    return f"{total_size:.1f} {unit}"
                total_size /= 1024.0
            
            return f"{total_size:.1f} TB"
            
        except Exception:
            return "未知"
    
    def save_code_block(self, code_block: CodeBlock) -> None:
        """保存代码块"""
        try:
            # 保存到数据库
            cursor = self._connection.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO code_blocks (
                    block_id, repository_id, content_hash, file_path, line_start, line_end,
                    char_start, char_end, block_type, language, name, full_name, signature,
                    class_name, namespace, keywords, search_text, parent_block_id,
                    metadata, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                code_block.block_id,
                code_block.repository_id,
                code_block.content_hash,
                code_block.file_path,
                code_block.line_start,
                code_block.line_end,
                code_block.char_start,
                code_block.char_end,
                code_block.block_type.value,
                code_block.language,
                code_block.name,
                code_block.full_name,
                code_block.signature,
                code_block.class_name,
                code_block.namespace,
                json.dumps(code_block.keywords),
                code_block.search_text,
                code_block.parent_block_id,
                json.dumps(code_block.metadata),
                code_block.created_at.isoformat(),
                code_block.updated_at.isoformat()
            ))
            
            # 保存内容到文件
            content_file = self.content_path / f"{code_block.block_id}.txt"
            content_file.write_text(code_block.content, encoding='utf-8')
            
            # 保存关系
            self._save_relations(code_block)
            
            self._connection.commit()
            
        except Exception as e:
            self._connection.rollback()
            logger.error(f"保存代码块失败: {e}")
            raise StorageError(f"保存代码块失败: {e}")
    
    def save_code_blocks(self, code_blocks: List[CodeBlock]) -> None:
        """批量保存代码块"""
        try:
            for code_block in code_blocks:
                self.save_code_block(code_block)
                
        except Exception as e:
            logger.error(f"批量保存代码块失败: {e}")
            raise StorageError(f"批量保存代码块失败: {e}")
    
    def get_code_block(self, block_id: str) -> Optional[CodeBlock]:
        """获取代码块"""
        try:
            cursor = self._connection.cursor()
            cursor.execute("""
                SELECT * FROM code_blocks WHERE block_id = ?
            """, (block_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            # 读取内容
            content_file = self.content_path / f"{block_id}.txt"
            if content_file.exists():
                content = content_file.read_text(encoding='utf-8')
            else:
                content = ""
            
            # 构造CodeBlock对象
            return self._row_to_code_block(row, content)
            
        except Exception as e:
            logger.error(f"获取代码块失败: {e}")
            return None
    
    def get_code_blocks(self, block_ids: List[str]) -> List[CodeBlock]:
        """批量获取代码块"""
        result = []
        for block_id in block_ids:
            code_block = self.get_code_block(block_id)
            if code_block:
                result.append(code_block)
        return result
    
    def query_code_blocks(
        self,
        repository_id: Optional[str] = None,
        language: Optional[str] = None,
        block_type: Optional[str] = None,
        file_path: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[CodeBlock]:
        """查询代码块"""
        try:
            cursor = self._connection.cursor()
            
            # 构建查询条件
            conditions = []
            params = []
            
            if repository_id:
                conditions.append("repository_id = ?")
                params.append(repository_id)
            
            if language:
                conditions.append("language = ?")
                params.append(language)
            
            if block_type:
                conditions.append("block_type = ?")
                params.append(block_type)
            
            if file_path:
                conditions.append("file_path LIKE ?")
                params.append(f"%{file_path}%")
            
            # 构建SQL语句
            sql = "SELECT * FROM code_blocks"
            if conditions:
                sql += " WHERE " + " AND ".join(conditions)
            sql += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            
            # 转换为CodeBlock对象
            result = []
            for row in rows:
                # 读取内容
                content_file = self.content_path / f"{row['block_id']}.txt"
                if content_file.exists():
                    content = content_file.read_text(encoding='utf-8')
                else:
                    content = ""
                
                code_block = self._row_to_code_block(row, content)
                result.append(code_block)
            
            return result
            
        except Exception as e:
            logger.error(f"查询代码块失败: {e}")
            return []
    
    def delete_code_block(self, block_id: str) -> bool:
        """删除代码块"""
        try:
            cursor = self._connection.cursor()
            
            # 删除关系
            cursor.execute("""
                DELETE FROM code_block_relations 
                WHERE parent_block_id = ? OR child_block_id = ?
            """, (block_id, block_id))
            
            # 删除代码块
            cursor.execute("DELETE FROM code_blocks WHERE block_id = ?", (block_id,))
            
            # 删除内容文件
            content_file = self.content_path / f"{block_id}.txt"
            if content_file.exists():
                content_file.unlink()
            
            self._connection.commit()
            
            return cursor.rowcount > 0
            
        except Exception as e:
            self._connection.rollback()
            logger.error(f"删除代码块失败: {e}")
            return False
    
    def delete_code_blocks(self, repository_id: str) -> int:
        """删除仓库的所有代码块"""
        try:
            cursor = self._connection.cursor()
            
            # 获取要删除的代码块ID
            cursor.execute("SELECT block_id FROM code_blocks WHERE repository_id = ?", (repository_id,))
            block_ids = [row[0] for row in cursor.fetchall()]
            
            # 删除关系
            for block_id in block_ids:
                cursor.execute("""
                    DELETE FROM code_block_relations 
                    WHERE parent_block_id = ? OR child_block_id = ?
                """, (block_id, block_id))
            
            # 删除代码块
            cursor.execute("DELETE FROM code_blocks WHERE repository_id = ?", (repository_id,))
            deleted_count = cursor.rowcount
            
            # 删除内容文件
            for block_id in block_ids:
                content_file = self.content_path / f"{block_id}.txt"
                if content_file.exists():
                    content_file.unlink()
            
            self._connection.commit()
            
            return deleted_count
            
        except Exception as e:
            self._connection.rollback()
            logger.error(f"删除仓库代码块失败: {e}")
            return 0
    
    def update_code_block(self, code_block: CodeBlock) -> bool:
        """更新代码块"""
        try:
            # 更新时间戳
            code_block.update_timestamp()
            
            # 保存（使用INSERT OR REPLACE）
            self.save_code_block(code_block)
            
            return True
            
        except Exception as e:
            logger.error(f"更新代码块失败: {e}")
            return False
    
    def count_code_blocks(
        self,
        repository_id: Optional[str] = None,
        language: Optional[str] = None,
        block_type: Optional[str] = None
    ) -> int:
        """统计代码块数量"""
        try:
            cursor = self._connection.cursor()
            
            # 构建查询条件
            conditions = []
            params = []
            
            if repository_id:
                conditions.append("repository_id = ?")
                params.append(repository_id)
            
            if language:
                conditions.append("language = ?")
                params.append(language)
            
            if block_type:
                conditions.append("block_type = ?")
                params.append(block_type)
            
            # 构建SQL语句
            sql = "SELECT COUNT(*) FROM code_blocks"
            if conditions:
                sql += " WHERE " + " AND ".join(conditions)
            
            cursor.execute(sql, params)
            return cursor.fetchone()[0]
            
        except Exception as e:
            logger.error(f"统计代码块数量失败: {e}")
            return 0
    
    def iter_code_blocks(
        self,
        repository_id: Optional[str] = None,
        batch_size: int = 100
    ) -> Iterator[CodeBlock]:
        """迭代代码块"""
        try:
            offset = 0
            
            while True:
                blocks = self.query_code_blocks(
                    repository_id=repository_id,
                    limit=batch_size,
                    offset=offset
                )
                
                if not blocks:
                    break
                
                for block in blocks:
                    yield block
                
                offset += batch_size
                
        except Exception as e:
            logger.error(f"迭代代码块失败: {e}")
    
    def _save_relations(self, code_block: CodeBlock) -> None:
        """保存代码块关系"""
        cursor = self._connection.cursor()
        
        # 保存子块关系
        for child_id in code_block.child_block_ids:
            cursor.execute("""
                INSERT OR IGNORE INTO code_block_relations 
                (parent_block_id, child_block_id, relation_type) 
                VALUES (?, ?, ?)
            """, (code_block.block_id, child_id, "child"))
        
        # 保存相关块关系
        for related_id in code_block.related_block_ids:
            cursor.execute("""
                INSERT OR IGNORE INTO code_block_relations 
                (parent_block_id, child_block_id, relation_type) 
                VALUES (?, ?, ?)
            """, (code_block.block_id, related_id, "related"))
    
    def _row_to_code_block(self, row: sqlite3.Row, content: str) -> CodeBlock:
        """将数据库行转换为CodeBlock对象"""
        return CodeBlock(
            block_id=row['block_id'],
            repository_id=row['repository_id'],
            content=content,
            content_hash=row['content_hash'],
            file_path=row['file_path'],
            line_start=row['line_start'],
            line_end=row['line_end'],
            char_start=row['char_start'],
            char_end=row['char_end'],
            block_type=BlockType(row['block_type']),
            language=row['language'],
            name=row['name'],
            full_name=row['full_name'],
            signature=row['signature'],
            class_name=row['class_name'],
            namespace=row['namespace'],
            keywords=json.loads(row['keywords']) if row['keywords'] else [],
            search_text=row['search_text'],
            parent_block_id=row['parent_block_id'],
            metadata=json.loads(row['metadata']) if row['metadata'] else {},
            created_at=datetime.fromisoformat(row['created_at']),
            updated_at=datetime.fromisoformat(row['updated_at'])
        )


class LocalMetadataStorage(BaseMetadataStorage):
    """
    本地元数据存储实现
    
    使用JSON文件存储元数据信息。
    """
    
    def __init__(self, config: StorageConfig):
        super().__init__(config)
        self.base_path = Path(config.base_path)
        self.metadata_path = self.base_path / "metadata"
        self.repositories_file = self.metadata_path / "repositories.json"
        self.search_history_file = self.metadata_path / "search_history.json"
        self.general_metadata_file = self.metadata_path / "general.json"
    
    def connect(self) -> None:
        """连接存储后端"""
        try:
            # 创建目录
            self.metadata_path.mkdir(parents=True, exist_ok=True)
            
            # 初始化文件
            self._init_files()
            
            logger.info(f"本地元数据存储连接成功: {self.metadata_path}")
            
        except Exception as e:
            logger.error(f"连接本地元数据存储失败: {e}")
            raise StorageConnectionError(f"连接失败: {e}")
    
    def disconnect(self) -> None:
        """断开存储连接"""
        logger.info("本地元数据存储连接已断开")
    
    def health_check(self) -> bool:
        """健康检查"""
        return self.metadata_path.exists()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取存储统计信息"""
        try:
            stats = {
                "metadata_path": str(self.metadata_path),
                "repositories_count": 0,
                "search_history_count": 0,
                "general_metadata_count": 0
            }
            
            # 统计仓库数量
            if self.repositories_file.exists():
                repos_data = json.loads(self.repositories_file.read_text(encoding='utf-8'))
                stats["repositories_count"] = len(repos_data)
            
            # 统计搜索历史数量
            if self.search_history_file.exists():
                history_data = json.loads(self.search_history_file.read_text(encoding='utf-8'))
                stats["search_history_count"] = len(history_data)
            
            # 统计一般元数据数量
            if self.general_metadata_file.exists():
                general_data = json.loads(self.general_metadata_file.read_text(encoding='utf-8'))
                stats["general_metadata_count"] = len(general_data)
            
            return stats
            
        except Exception as e:
            logger.error(f"获取元数据存储统计信息失败: {e}")
            return {}
    
    def _init_files(self) -> None:
        """初始化文件"""
        if not self.repositories_file.exists():
            self.repositories_file.write_text("[]", encoding='utf-8')
        
        if not self.search_history_file.exists():
            self.search_history_file.write_text("[]", encoding='utf-8')
        
        if not self.general_metadata_file.exists():
            self.general_metadata_file.write_text("{}", encoding='utf-8')
    
    def save_repository_index(self, repository_index: RepositoryIndex) -> None:
        """保存仓库索引"""
        try:
            # 读取现有数据
            repos_data = json.loads(self.repositories_file.read_text(encoding='utf-8'))
            
            # 查找现有仓库
            found = False
            for i, repo in enumerate(repos_data):
                if repo["repository_id"] == repository_index.repository_id:
                    repos_data[i] = repository_index.to_dict()
                    found = True
                    break
            
            if not found:
                repos_data.append(repository_index.to_dict())
            
            # 写入文件
            self.repositories_file.write_text(
                json.dumps(repos_data, ensure_ascii=False, indent=2),
                encoding='utf-8'
            )
            
        except Exception as e:
            logger.error(f"保存仓库索引失败: {e}")
            raise StorageError(f"保存仓库索引失败: {e}")
    
    def get_repository_index(self, repository_id: str) -> Optional[RepositoryIndex]:
        """获取仓库索引"""
        try:
            repos_data = json.loads(self.repositories_file.read_text(encoding='utf-8'))
            
            for repo in repos_data:
                if repo["repository_id"] == repository_id:
                    return RepositoryIndex.from_dict(repo)
            
            return None
            
        except Exception as e:
            logger.error(f"获取仓库索引失败: {e}")
            return None
    
    def list_repository_indexes(self) -> List[RepositoryIndex]:
        """列出所有仓库索引"""
        try:
            repos_data = json.loads(self.repositories_file.read_text(encoding='utf-8'))
            return [RepositoryIndex.from_dict(repo) for repo in repos_data]
            
        except Exception as e:
            logger.error(f"列出仓库索引失败: {e}")
            return []
    
    def delete_repository_index(self, repository_id: str) -> bool:
        """删除仓库索引"""
        try:
            repos_data = json.loads(self.repositories_file.read_text(encoding='utf-8'))
            
            # 过滤掉要删除的仓库
            new_repos_data = [repo for repo in repos_data if repo["repository_id"] != repository_id]
            
            if len(new_repos_data) < len(repos_data):
                self.repositories_file.write_text(
                    json.dumps(new_repos_data, ensure_ascii=False, indent=2),
                    encoding='utf-8'
                )
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"删除仓库索引失败: {e}")
            return False
    
    def update_repository_index(self, repository_index: RepositoryIndex) -> bool:
        """更新仓库索引"""
        try:
            # 更新时间戳
            repository_index.updated_at = datetime.now()
            
            # 保存
            self.save_repository_index(repository_index)
            return True
            
        except Exception as e:
            logger.error(f"更新仓库索引失败: {e}")
            return False
    
    def save_search_query(self, query: SearchQuery) -> None:
        """保存搜索查询"""
        try:
            # 读取现有数据
            history_data = json.loads(self.search_history_file.read_text(encoding='utf-8'))
            
            # 添加查询记录
            query_record = query.to_dict()
            query_record["timestamp"] = datetime.now().isoformat()
            history_data.append(query_record)
            
            # 保持最近1000条记录
            if len(history_data) > 1000:
                history_data = history_data[-1000:]
            
            # 写入文件
            self.search_history_file.write_text(
                json.dumps(history_data, ensure_ascii=False, indent=2),
                encoding='utf-8'
            )
            
        except Exception as e:
            logger.error(f"保存搜索查询失败: {e}")
    
    def get_search_history(self, limit: int = 100, offset: int = 0) -> List[SearchQuery]:
        """获取搜索历史"""
        try:
            history_data = json.loads(self.search_history_file.read_text(encoding='utf-8'))
            
            # 反向排序（最新在前）
            history_data.reverse()
            
            # 分页
            start = offset
            end = offset + limit
            page_data = history_data[start:end]
            
            # 转换为SearchQuery对象
            result = []
            for record in page_data:
                query = SearchQuery(
                    query=record.get("query", ""),
                    query_type=record.get("query_type", "semantic"),
                    repository_id=record.get("repository_id"),
                    language=record.get("language"),
                    block_type=BlockType(record["block_type"]) if record.get("block_type") else None,
                    file_path=record.get("file_path"),
                    top_k=record.get("top_k", 10),
                    similarity_threshold=record.get("similarity_threshold", 0.0),
                    metadata_filters=record.get("metadata_filters", {}),
                    created_after=datetime.fromisoformat(record["created_after"]) if record.get("created_after") else None,
                    created_before=datetime.fromisoformat(record["created_before"]) if record.get("created_before") else None
                )
                result.append(query)
            
            return result
            
        except Exception as e:
            logger.error(f"获取搜索历史失败: {e}")
            return []
    
    def get_metadata(self, key: str) -> Optional[Any]:
        """获取元数据"""
        try:
            general_data = json.loads(self.general_metadata_file.read_text(encoding='utf-8'))
            return general_data.get(key)
            
        except Exception as e:
            logger.error(f"获取元数据失败: {e}")
            return None
    
    def set_metadata(self, key: str, value: Any) -> None:
        """设置元数据"""
        try:
            general_data = json.loads(self.general_metadata_file.read_text(encoding='utf-8'))
            general_data[key] = value
            
            self.general_metadata_file.write_text(
                json.dumps(general_data, ensure_ascii=False, indent=2),
                encoding='utf-8'
            )
            
        except Exception as e:
            logger.error(f"设置元数据失败: {e}")
            raise StorageError(f"设置元数据失败: {e}")
    
    def delete_metadata(self, key: str) -> bool:
        """删除元数据"""
        try:
            general_data = json.loads(self.general_metadata_file.read_text(encoding='utf-8'))
            
            if key in general_data:
                del general_data[key]
                
                self.general_metadata_file.write_text(
                    json.dumps(general_data, ensure_ascii=False, indent=2),
                    encoding='utf-8'
                )
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"删除元数据失败: {e}")
            return False
    
    def list_metadata_keys(self) -> List[str]:
        """列出所有元数据键"""
        try:
            general_data = json.loads(self.general_metadata_file.read_text(encoding='utf-8'))
            return list(general_data.keys())
            
        except Exception as e:
            logger.error(f"列出元数据键失败: {e}")
            return []


class LocalFileStorage:
    """
    本地文件存储的复合实现
    
    整合代码块存储和元数据存储。
    """
    
    def __init__(self, config: StorageConfig):
        self.config = config
        self.code_block_storage = LocalCodeBlockStorage(config)
        self.metadata_storage = LocalMetadataStorage(config)
    
    def connect(self) -> None:
        """连接存储后端"""
        self.code_block_storage.connect()
        self.metadata_storage.connect()
    
    def disconnect(self) -> None:
        """断开存储连接"""
        self.code_block_storage.disconnect()
        self.metadata_storage.disconnect()
    
    def health_check(self) -> bool:
        """健康检查"""
        return (
            self.code_block_storage.health_check() and 
            self.metadata_storage.health_check()
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """获取存储统计信息"""
        stats = {
            "storage_type": "local",
            "base_path": self.config.base_path,
            "code_blocks": self.code_block_storage.get_stats(),
            "metadata": self.metadata_storage.get_stats()
        }
        return stats
    
    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.disconnect() 