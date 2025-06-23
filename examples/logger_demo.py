#!/usr/bin/env python3
# coding: utf-8
"""
日志功能演示

展示如何使用优化后解析器的日志功能。
"""

import sys
import tempfile
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from coderepoindex.parsers import (
    CodeParser,
    LoggerConfig,
    setup_parser_logging,
    log_performance,
    log_error_with_context
)


def demo_log_levels():
    """演示不同的日志级别"""
    print("=== 日志级别演示 ===")
    
    # 设置调试模式
    LoggerConfig.setup_debug_mode()
    
    # 创建测试代码
    test_code = '''
def test_function():
    """测试函数"""
    return "hello world"

class TestClass:
    def method(self):
        pass
'''
    
    # 创建临时文件
    temp_file = Path(tempfile.mktemp(suffix=".py"))
    temp_file.write_text(test_code, encoding='utf-8')
    
    try:
        parser = CodeParser()
        result = parser.parse_file(str(temp_file))
        
        # 这会输出详细的DEBUG信息
        print(f"解析结果: {len(result.snippets)} 个代码片段")
        
    finally:
        if temp_file.exists():
            temp_file.unlink()


def demo_different_modes():
    """演示不同的日志模式"""
    print("\n=== 不同日志模式演示 ===")
    
    test_code = '''
def simple_function():
    return 42
'''
    
    temp_file = Path(tempfile.mktemp(suffix=".py"))
    temp_file.write_text(test_code, encoding='utf-8')
    
    modes = ["debug", "info", "production", "silent"]
    
    try:
        for mode in modes:
            print(f"\n--- {mode.upper()} 模式 ---")
            
            # 重置日志配置
            LoggerConfig._initialized = False
            setup_parser_logging(mode)
            
            parser = CodeParser()
            result = parser.parse_file(str(temp_file))
            
            print(f"模式 {mode}: 解析了 {len(result.snippets)} 个代码片段")
            
    finally:
        if temp_file.exists():
            temp_file.unlink()


def demo_performance_logging():
    """演示性能日志"""
    print("\n=== 性能日志演示 ===")
    
    # 设置INFO级别，显示性能日志
    LoggerConfig._initialized = False
    LoggerConfig.setup_logger(level="INFO")
    
    # 创建一个较大的测试文件
    test_code = '''
# -*- coding: utf-8 -*-
"""
大型测试文件
包含多个类和函数
"""

import os
import sys
from typing import List, Dict, Optional

class DataProcessor:
    """数据处理器"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.cache = {}
    
    def process_data(self, data: List) -> Dict:
        """处理数据"""
        result = {}
        for i, item in enumerate(data):
            result[f"item_{i}"] = self._transform_item(item)
        return result
    
    def _transform_item(self, item):
        """转换单个项目"""
        return str(item).upper()
    
    def clear_cache(self):
        """清空缓存"""
        self.cache.clear()

class DatabaseManager:
    """数据库管理器"""
    
    def connect(self):
        """连接数据库"""
        pass
    
    def disconnect(self):
        """断开连接"""
        pass
    
    def query(self, sql: str) -> List:
        """执行查询"""
        return []

def utility_function_1():
    """工具函数1"""
    return "utility1"

def utility_function_2():
    """工具函数2"""
    return "utility2"

def main():
    """主函数"""
    processor = DataProcessor({})
    db = DatabaseManager()
    
    data = [1, 2, 3, 4, 5]
    result = processor.process_data(data)
    print(result)

if __name__ == "__main__":
    main()
'''
    
    temp_file = Path(tempfile.mktemp(suffix=".py"))
    temp_file.write_text(test_code, encoding='utf-8')
    
    try:
        # 测试单文件解析性能
        parser = CodeParser()
        result = parser.parse_file(str(temp_file))
        
        # 手动记录性能指标
        log_performance(
            "parse_large_file",
            result.processing_time,
            file_size=len(test_code),
            snippets_count=len(result.snippets),
            language=result.language.value if result.language else "unknown"
        )
        
        # 测试批量解析性能
        import time
        start_time = time.time()
        
        # 创建多个文件进行批量测试
        files = [str(temp_file)] * 3
        results = parser.parse_multiple_files(files)
        
        duration = time.time() - start_time
        total_snippets = sum(len(r.snippets) for r in results)
        
        log_performance(
            "batch_parse",
            duration,
            files_count=len(files),
            total_snippets=total_snippets,
            avg_time_per_file=duration / len(files)
        )
        
    finally:
        if temp_file.exists():
            temp_file.unlink()


def demo_error_logging():
    """演示错误日志"""
    print("\n=== 错误日志演示 ===")
    
    LoggerConfig._initialized = False
    LoggerConfig.setup_logger(level="INFO")
    
    parser = CodeParser()
    
    # 1. 文件不存在错误
    try:
        result = parser.parse_file("nonexistent_file.py")
        if result.errors:
            log_error_with_context(
                Exception(result.errors[0]),
                {"file_path": "nonexistent_file.py", "operation": "parse_file"}
            )
    except Exception as e:
        log_error_with_context(e, {"operation": "demo_parse_nonexistent"})
    
    # 2. 不支持的文件类型
    temp_file = Path(tempfile.mktemp(suffix=".unknown"))
    temp_file.write_text("some content")
    
    try:
        result = parser.parse_file(str(temp_file))
        if result.errors:
            log_error_with_context(
                Exception(result.errors[0]),
                {"file_path": str(temp_file), "file_type": "unknown"}
            )
    finally:
        if temp_file.exists():
            temp_file.unlink()


def demo_file_logging():
    """演示文件日志功能"""
    print("\n=== 文件日志演示 ===")
    
    # 设置文件日志
    LoggerConfig._initialized = False
    LoggerConfig.setup_logger(
        level="DEBUG",
        enable_console=True,
        enable_file=True,
        log_file="logs/parser_demo.log"
    )
    
    # 创建测试文件
    test_code = '''
def logged_function():
    """这个函数的解析会被记录到文件中"""
    print("Hello, file logging!")
'''
    
    temp_file = Path(tempfile.mktemp(suffix=".py"))
    temp_file.write_text(test_code, encoding='utf-8')
    
    try:
        parser = CodeParser()
        result = parser.parse_file(str(temp_file))
        
        print(f"解析完成，日志已保存到 logs/parser_demo.log")
        print(f"提取了 {len(result.snippets)} 个代码片段")
        
        # 检查日志文件是否创建
        log_file = Path("logs/parser_demo.log")
        if log_file.exists():
            print(f"日志文件大小: {log_file.stat().st_size} bytes")
        
    finally:
        if temp_file.exists():
            temp_file.unlink()


def main():
    """主函数"""
    print("代码解析器日志功能演示")
    print("=" * 50)
    
    demos = [
        demo_log_levels,
        demo_different_modes,
        demo_performance_logging,
        demo_error_logging,
        demo_file_logging
    ]
    
    for demo_func in demos:
        try:
            demo_func()
        except Exception as e:
            print(f"演示 {demo_func.__name__} 时出错: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 50)
    print("日志演示完成！")
    print("\n提示:")
    print("- 查看 logs/ 目录下的日志文件")
    print("- 尝试设置不同的日志级别: DEBUG, INFO, WARNING, ERROR")
    print("- 在生产环境中使用 LoggerConfig.setup_production_mode()")


if __name__ == "__main__":
    main() 