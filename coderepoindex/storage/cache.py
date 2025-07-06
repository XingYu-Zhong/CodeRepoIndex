"""
缓存存储实现

提供多级缓存以提高存储性能。
"""

import json
import pickle
from typing import Any, Optional, Dict
from pathlib import Path
import time
import threading
import logging

logger = logging.getLogger(__name__)


class CacheStorage:
    """缓存存储基础类"""
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存项"""
        raise NotImplementedError
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """设置缓存项"""
        raise NotImplementedError
    
    def delete(self, key: str) -> bool:
        """删除缓存项"""
        raise NotImplementedError
    
    def clear(self) -> None:
        """清空缓存"""
        raise NotImplementedError


class MemoryCache(CacheStorage):
    """内存缓存实现"""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.access_times: Dict[str, float] = {}
        self.lock = threading.RLock()
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存项"""
        with self.lock:
            if key not in self.cache:
                return None
            
            # 检查是否过期
            entry = self.cache[key]
            if entry["expires_at"] and time.time() > entry["expires_at"]:
                del self.cache[key]
                del self.access_times[key]
                return None
            
            # 更新访问时间
            self.access_times[key] = time.time()
            return entry["value"]
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """设置缓存项"""
        with self.lock:
            # 计算过期时间
            if ttl is None:
                ttl = self.default_ttl
            
            expires_at = time.time() + ttl if ttl > 0 else None
            
            # 如果缓存已满，删除最久未访问的项
            if len(self.cache) >= self.max_size and key not in self.cache:
                self._evict_lru()
            
            # 保存缓存项
            self.cache[key] = {
                "value": value,
                "expires_at": expires_at,
                "created_at": time.time()
            }
            self.access_times[key] = time.time()
    
    def delete(self, key: str) -> bool:
        """删除缓存项"""
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                del self.access_times[key]
                return True
            return False
    
    def clear(self) -> None:
        """清空缓存"""
        with self.lock:
            self.cache.clear()
            self.access_times.clear()
    
    def _evict_lru(self) -> None:
        """删除最久未访问的项"""
        if not self.access_times:
            return
        
        lru_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
        del self.cache[lru_key]
        del self.access_times[lru_key]
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        with self.lock:
            return {
                "size": len(self.cache),
                "max_size": self.max_size,
                "hit_ratio": 0.0,  # 需要实现命中率统计
                "memory_usage": len(str(self.cache))  # 简单估算
            }


class FileCache(CacheStorage):
    """文件缓存实现"""
    
    def __init__(self, cache_dir: str, max_files: int = 10000, default_ttl: int = 86400):
        self.cache_dir = Path(cache_dir)
        self.max_files = max_files
        self.default_ttl = default_ttl
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存项"""
        cache_file = self._get_cache_file(key)
        
        try:
            if not cache_file.exists():
                return None
            
            with open(cache_file, 'rb') as f:
                data = pickle.load(f)
            
            # 检查是否过期
            if data["expires_at"] and time.time() > data["expires_at"]:
                cache_file.unlink()
                return None
            
            # 更新访问时间
            cache_file.touch()
            return data["value"]
            
        except Exception as e:
            logger.error(f"读取文件缓存失败: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """设置缓存项"""
        try:
            with self.lock:
                # 检查文件数量限制
                if self._count_files() >= self.max_files:
                    self._evict_oldest()
                
                # 计算过期时间
                if ttl is None:
                    ttl = self.default_ttl
                
                expires_at = time.time() + ttl if ttl > 0 else None
                
                # 保存到文件
                cache_file = self._get_cache_file(key)
                data = {
                    "value": value,
                    "expires_at": expires_at,
                    "created_at": time.time()
                }
                
                with open(cache_file, 'wb') as f:
                    pickle.dump(data, f)
                    
        except Exception as e:
            logger.error(f"写入文件缓存失败: {e}")
    
    def delete(self, key: str) -> bool:
        """删除缓存项"""
        try:
            cache_file = self._get_cache_file(key)
            if cache_file.exists():
                cache_file.unlink()
                return True
            return False
            
        except Exception as e:
            logger.error(f"删除文件缓存失败: {e}")
            return False
    
    def clear(self) -> None:
        """清空缓存"""
        try:
            import shutil
            shutil.rmtree(self.cache_dir)
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            
        except Exception as e:
            logger.error(f"清空文件缓存失败: {e}")
    
    def _get_cache_file(self, key: str) -> Path:
        """获取缓存文件路径"""
        import hashlib
        key_hash = hashlib.md5(key.encode('utf-8')).hexdigest()
        return self.cache_dir / f"{key_hash}.cache"
    
    def _count_files(self) -> int:
        """统计缓存文件数量"""
        return len(list(self.cache_dir.glob("*.cache")))
    
    def _evict_oldest(self) -> None:
        """删除最旧的缓存文件"""
        cache_files = list(self.cache_dir.glob("*.cache"))
        if cache_files:
            oldest_file = min(cache_files, key=lambda f: f.stat().st_mtime)
            oldest_file.unlink()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        try:
            file_count = self._count_files()
            total_size = sum(f.stat().st_size for f in self.cache_dir.glob("*.cache"))
            
            return {
                "file_count": file_count,
                "max_files": self.max_files,
                "total_size": total_size,
                "cache_dir": str(self.cache_dir)
            }
            
        except Exception as e:
            logger.error(f"获取文件缓存统计失败: {e}")
            return {} 