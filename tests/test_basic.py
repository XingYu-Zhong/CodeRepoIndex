"""
基础测试模块

测试项目的基本功能和导入。
"""

import pytest
from coderepoindex import CodeIndexer, CodeSearcher, __version__


def test_version():
    """测试版本号"""
    assert __version__ == "0.1.0"


def test_code_indexer_import():
    """测试 CodeIndexer 导入"""
    indexer = CodeIndexer()
    assert indexer is not None
    assert indexer.embedding_model == "sentence-transformers/all-MiniLM-L6-v2"
    assert indexer.storage_backend == "chroma"


def test_code_searcher_import():
    """测试 CodeSearcher 导入"""
    searcher = CodeSearcher()
    assert searcher is not None
    assert searcher.embedding_model == "sentence-transformers/all-MiniLM-L6-v2"
    assert searcher.storage_backend == "chroma"


def test_indexer_initialization():
    """测试索引器初始化"""
    indexer = CodeIndexer(
        embedding_model="test-model",
        storage_backend="test-backend"
    )
    assert indexer.embedding_model == "test-model"
    assert indexer.storage_backend == "test-backend"


def test_searcher_initialization():
    """测试搜索器初始化"""
    searcher = CodeSearcher(
        embedding_model="test-model",
        storage_backend="test-backend"
    )
    assert searcher.embedding_model == "test-model"
    assert searcher.storage_backend == "test-backend"


def test_indexer_get_stats():
    """测试索引器统计信息"""
    indexer = CodeIndexer()
    stats = indexer.get_stats()
    
    assert isinstance(stats, dict)
    assert "total_vectors" in stats
    assert "total_repositories" in stats
    assert "total_files" in stats
    assert "storage_size" in stats


def test_searcher_get_stats():
    """测试搜索器统计信息"""
    searcher = CodeSearcher()
    stats = searcher.get_stats()
    
    assert isinstance(stats, dict)
    assert "total_indexed_blocks" in stats
    assert "available_languages" in stats
    assert "index_size" in stats
    assert "last_updated" in stats


def test_empty_search():
    """测试空查询搜索"""
    searcher = CodeSearcher()
    results = searcher.search("")
    
    assert isinstance(results, list)
    assert len(results) == 0 