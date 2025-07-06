"""
存储工具函数

提供存储相关的工具函数。
"""

import os
import shutil
import tarfile
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class StoragePathUtils:
    """存储路径工具"""
    
    @staticmethod
    def ensure_directory(path: Path) -> None:
        """确保目录存在"""
        path.mkdir(parents=True, exist_ok=True)
    
    @staticmethod
    def get_size(path: Path) -> int:
        """获取路径大小"""
        if path.is_file():
            return path.stat().st_size
        elif path.is_dir():
            total_size = 0
            for root, dirs, files in os.walk(path):
                for file in files:
                    file_path = Path(root) / file
                    try:
                        total_size += file_path.stat().st_size
                    except (OSError, IOError):
                        continue
            return total_size
        return 0
    
    @staticmethod
    def format_size(size: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"
    
    @staticmethod
    def cleanup_empty_dirs(path: Path) -> int:
        """清理空目录"""
        cleaned_count = 0
        
        if not path.exists() or not path.is_dir():
            return cleaned_count
        
        for root, dirs, files in os.walk(path, topdown=False):
            for dir_name in dirs:
                dir_path = Path(root) / dir_name
                try:
                    if not any(dir_path.iterdir()):
                        dir_path.rmdir()
                        cleaned_count += 1
                except OSError:
                    continue
        
        return cleaned_count


class BackupUtils:
    """备份工具"""
    
    @staticmethod
    def create_backup(
        source_path: Path,
        backup_dir: Path,
        backup_name: Optional[str] = None
    ) -> Path:
        """创建备份"""
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        if backup_name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{timestamp}.tar.gz"
        
        backup_file = backup_dir / backup_name
        
        try:
            with tarfile.open(backup_file, "w:gz") as tar:
                tar.add(source_path, arcname=source_path.name)
            
            logger.info(f"创建备份成功: {backup_file}")
            return backup_file
            
        except Exception as e:
            logger.error(f"创建备份失败: {e}")
            raise
    
    @staticmethod
    def restore_backup(backup_file: Path, restore_path: Path) -> None:
        """恢复备份"""
        if not backup_file.exists():
            raise FileNotFoundError(f"备份文件不存在: {backup_file}")
        
        restore_path.mkdir(parents=True, exist_ok=True)
        
        try:
            with tarfile.open(backup_file, "r:gz") as tar:
                tar.extractall(restore_path)
            
            logger.info(f"恢复备份成功: {backup_file} -> {restore_path}")
            
        except Exception as e:
            logger.error(f"恢复备份失败: {e}")
            raise
    
    @staticmethod
    def list_backups(backup_dir: Path) -> List[Dict[str, Any]]:
        """列出备份文件"""
        if not backup_dir.exists():
            return []
        
        backups = []
        for backup_file in backup_dir.glob("backup_*.tar.gz"):
            try:
                stat = backup_file.stat()
                backups.append({
                    "name": backup_file.name,
                    "path": str(backup_file),
                    "size": stat.st_size,
                    "created_at": datetime.fromtimestamp(stat.st_ctime),
                    "modified_at": datetime.fromtimestamp(stat.st_mtime)
                })
            except OSError:
                continue
        
        # 按修改时间倒序排列
        backups.sort(key=lambda x: x["modified_at"], reverse=True)
        return backups
    
    @staticmethod
    def cleanup_old_backups(backup_dir: Path, max_backups: int = 10) -> int:
        """清理旧备份文件"""
        backups = BackupUtils.list_backups(backup_dir)
        
        if len(backups) <= max_backups:
            return 0
        
        # 删除超出数量的旧备份
        old_backups = backups[max_backups:]
        deleted_count = 0
        
        for backup in old_backups:
            try:
                Path(backup["path"]).unlink()
                deleted_count += 1
                logger.info(f"删除旧备份: {backup['name']}")
            except OSError as e:
                logger.error(f"删除备份失败: {e}")
        
        return deleted_count


class CleanupUtils:
    """清理工具"""
    
    @staticmethod
    def cleanup_temp_files(temp_dir: Path, max_age_hours: int = 24) -> int:
        """清理临时文件"""
        if not temp_dir.exists():
            return 0
        
        current_time = datetime.now().timestamp()
        max_age_seconds = max_age_hours * 3600
        cleaned_count = 0
        
        for item in temp_dir.rglob("*"):
            try:
                if item.is_file():
                    file_age = current_time - item.stat().st_mtime
                    if file_age > max_age_seconds:
                        item.unlink()
                        cleaned_count += 1
            except OSError:
                continue
        
        # 清理空目录
        cleaned_count += StoragePathUtils.cleanup_empty_dirs(temp_dir)
        
        return cleaned_count
    
    @staticmethod
    def cleanup_logs(log_dir: Path, max_days: int = 30) -> int:
        """清理日志文件"""
        if not log_dir.exists():
            return 0
        
        current_time = datetime.now().timestamp()
        max_age_seconds = max_days * 24 * 3600
        cleaned_count = 0
        
        for log_file in log_dir.glob("*.log*"):
            try:
                file_age = current_time - log_file.stat().st_mtime
                if file_age > max_age_seconds:
                    log_file.unlink()
                    cleaned_count += 1
                    logger.info(f"删除旧日志: {log_file.name}")
            except OSError as e:
                logger.error(f"删除日志失败: {e}")
        
        return cleaned_count
    
    @staticmethod
    def get_disk_usage(path: Path) -> Dict[str, Any]:
        """获取磁盘使用情况"""
        try:
            if not path.exists():
                return {}
            
            stat = shutil.disk_usage(path)
            
            return {
                "total": stat.total,
                "used": stat.used,
                "free": stat.free,
                "total_formatted": StoragePathUtils.format_size(stat.total),
                "used_formatted": StoragePathUtils.format_size(stat.used),
                "free_formatted": StoragePathUtils.format_size(stat.free),
                "usage_percent": (stat.used / stat.total) * 100 if stat.total > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"获取磁盘使用情况失败: {e}")
            return {}
    
    @staticmethod
    def check_storage_health(storage_path: Path) -> Dict[str, Any]:
        """检查存储健康状况"""
        health = {
            "path": str(storage_path),
            "exists": storage_path.exists(),
            "readable": False,
            "writable": False,
            "disk_usage": {},
            "issues": []
        }
        
        if not health["exists"]:
            health["issues"].append("存储路径不存在")
            return health
        
        # 检查读权限
        try:
            list(storage_path.iterdir())
            health["readable"] = True
        except PermissionError:
            health["issues"].append("没有读权限")
        except Exception as e:
            health["issues"].append(f"读取错误: {e}")
        
        # 检查写权限
        try:
            test_file = storage_path / ".write_test"
            test_file.write_text("test")
            test_file.unlink()
            health["writable"] = True
        except PermissionError:
            health["issues"].append("没有写权限")
        except Exception as e:
            health["issues"].append(f"写入错误: {e}")
        
        # 检查磁盘使用情况
        health["disk_usage"] = CleanupUtils.get_disk_usage(storage_path)
        
        # 检查磁盘空间不足
        if health["disk_usage"]:
            usage_percent = health["disk_usage"]["usage_percent"]
            if usage_percent > 95:
                health["issues"].append("磁盘空间严重不足")
            elif usage_percent > 85:
                health["issues"].append("磁盘空间不足")
        
        return health


# 导出工具类实例
storage_path_utils = StoragePathUtils()
backup_utils = BackupUtils()
cleanup_utils = CleanupUtils() 