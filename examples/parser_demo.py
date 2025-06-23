#!/usr/bin/env python3
# coding: utf-8
"""
代码解析器使用示例

演示如何使用优化后的代码解析器来分析源代码文件。
"""

import sys
import json
from pathlib import Path
from loguru import logger

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from coderepoindex.parsers import (
    CodeParser, 
    parse_code_file, 
    ConfigTemplates,
    ParserTester,
    get_supported_languages,
    get_supported_extensions,
    quick_parse,
    print_module_info
)

# 配置日志格式
logger.remove()  # 移除默认的handler
logger.add(
    sys.stdout, 
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO"
)


def demo_basic_usage():
    """演示基本用法"""
    print("=== 基本使用示例 ===")
    
    # 创建一个简单的Python测试文件
    test_code = '''
# -*- coding: utf-8 -*-
"""
示例Python文件
包含类和函数的演示代码
"""

class Calculator:
    """简单的计算器类"""
    
    def __init__(self):
        """初始化计算器"""
        self.history = []
    
    def add(self, a, b):
        """加法运算"""
        result = a + b
        self.history.append(f"{a} + {b} = {result}")
        return result
    
    def multiply(self, a, b):
        """乘法运算"""
        result = a * b
        self.history.append(f"{a} * {b} = {result}")
        return result


def fibonacci(n):
    """计算斐波那契数列"""
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)


# 全局变量
MAX_VALUE = 100
'''
    
    # 写入临时文件
    temp_file = Path("temp_example.py")
    temp_file.write_text(test_code, encoding='utf-8')
    
    try:
        # 方法1：使用便利函数
        print("方法1：使用便利函数")
        result = parse_code_file(str(temp_file))
        print(f"解析结果：{result.language.value if result.language else 'Unknown'} 语言")
        print(f"提取到 {len(result.snippets)} 个代码片段")
        
        # 方法2：使用解析器类
        print("\n方法2：使用解析器类")
        parser = CodeParser()
        result2 = parser.parse_file(str(temp_file))
        
        # 显示详细信息
        for i, snippet in enumerate(result2.snippets):
            print(f"\n片段 {i+1}:")
            print(f"  类型: {snippet.type}")
            print(f"  名称: {snippet.name}")
            print(f"  行数: {snippet.line_start}-{snippet.line_end}")
            if snippet.class_name:
                print(f"  所属类: {snippet.class_name}")
            if snippet.args:
                print(f"  参数: {snippet.args}")
            print(f"  代码片段 (前100字符): {snippet.code[:100]}...")
        
    finally:
        # 清理临时文件
        if temp_file.exists():
            temp_file.unlink()


def demo_configuration():
    """演示配置选项"""
    print("\n=== 配置选项示例 ===")
    
    # 创建测试文件
    test_code = '''
def test_function(x, y):
    """这是一个测试函数"""
    # 执行一些计算
    result = x + y
    return result

class TestClass:
    def method1(self):
        pass
    
    def method2(self):
        pass
'''
    
    temp_file = Path("temp_config_test.py")
    temp_file.write_text(test_code, encoding='utf-8')
    
    try:
        configs = {
            "最小配置": ConfigTemplates.minimal(),
            "详细配置": ConfigTemplates.detailed(),
            "性能配置": ConfigTemplates.performance(),
            "中文优化": ConfigTemplates.chinese_optimized()
        }
        
        for config_name, config in configs.items():
            print(f"\n--- {config_name} ---")
            result = quick_parse(str(temp_file), extract_comments=(config_name == "详细配置"))
            print(f"提取的代码片段数量: {len(result.snippets)}")
            print(f"处理时间: {result.processing_time:.4f}s")
            
            # 显示配置的一些关键参数
            print(f"配置参数:")
            print(f"  提取注释: {config.extract_comments}")
            print(f"  提取文档字符串: {config.extract_docstrings}")
            print(f"  最大文件大小: {config.max_file_size / 1024 / 1024:.1f}MB")
    
    finally:
        if temp_file.exists():
            temp_file.unlink()


def demo_batch_processing():
    """演示批量处理"""
    print("\n=== 批量处理示例 ===")
    
    # 创建多个测试文件
    test_files = []
    
    # Python文件
    py_code = '''
def hello_python():
    print("Hello from Python!")
    return "python"
'''
    
    # JavaScript文件
    js_code = '''
function helloJavaScript() {
    console.log("Hello from JavaScript!");
    return "javascript";
}

const arrowFunction = () => {
    return "arrow function";
};
'''
    
    files_to_create = [
        ("test1.py", py_code),
        ("test2.js", js_code)
    ]
    
    try:
        # 创建测试文件
        for filename, content in files_to_create:
            file_path = Path(filename)
            file_path.write_text(content, encoding='utf-8')
            test_files.append(file_path)
        
        # 批量解析
        parser = CodeParser()
        file_paths = [str(f) for f in test_files]
        results = parser.parse_multiple_files(file_paths)
        
        print(f"批量解析了 {len(results)} 个文件:")
        for result in results:
            file_name = Path(result.file_path).name
            print(f"\n文件: {file_name}")
            print(f"  语言: {result.language.value if result.language else 'Unknown'}")
            print(f"  代码片段数量: {len(result.snippets)}")
            print(f"  是否成功: {result.is_successful}")
            
            if result.snippets:
                print("  函数列表:")
                for snippet in result.snippets:
                    if snippet.type == "function":
                        print(f"    - {snippet.name}()")
    
    finally:
        # 清理测试文件
        for file_path in test_files:
            if file_path.exists():
                file_path.unlink()


def demo_error_handling():
    """演示错误处理"""
    print("\n=== 错误处理示例 ===")
    
    parser = CodeParser()
    
    # 测试1：不存在的文件
    print("测试1：解析不存在的文件")
    result = parser.parse_file("nonexistent_file.py")
    print(f"是否成功: {result.is_successful}")
    if result.errors:
        print(f"错误信息: {result.errors[0]}")
    
    # 测试2：不支持的文件类型
    print("\n测试2：解析不支持的文件类型")
    unsupported_file = Path("test.unknown")
    unsupported_file.write_text("some content")
    
    try:
        result = parser.parse_file(str(unsupported_file))
        print(f"是否成功: {result.is_successful}")
        if result.errors:
            print(f"错误信息: {result.errors[0]}")
    finally:
        if unsupported_file.exists():
            unsupported_file.unlink()
    
    # 测试3：语法错误的文件
    print("\n测试3：解析有语法错误的文件")
    syntax_error_file = Path("syntax_error.py")
    syntax_error_file.write_text("def invalid_syntax(\n    # 缺少参数和闭合括号")
    
    try:
        result = parser.parse_file(str(syntax_error_file))
        print(f"是否成功: {result.is_successful}")
        print(f"代码片段数量: {len(result.snippets)}")
        # 即使有语法错误，tree-sitter也可能提取到部分信息
    finally:
        if syntax_error_file.exists():
            syntax_error_file.unlink()


def demo_advanced_features():
    """演示高级功能"""
    print("\n=== 高级功能示例 ===")
    
    # 显示模块信息
    print("模块信息:")
    print_module_info()
    
    # 显示支持的语言和扩展名
    print(f"\n支持的语言: {', '.join(get_supported_languages())}")
    print(f"支持的扩展名: {', '.join(get_supported_extensions())}")
    
    # 创建复杂的测试文件
    complex_code = '''
"""
复杂的Python示例文件
包含多种代码结构
"""

from typing import List, Dict, Optional
import asyncio

class DataProcessor:
    """数据处理器类"""
    
    def __init__(self, name: str):
        self.name = name
        self._cache: Dict[str, int] = {}
    
    @property
    def cache_size(self) -> int:
        """获取缓存大小"""
        return len(self._cache)
    
    @staticmethod
    def validate_data(data: List[int]) -> bool:
        """静态方法：验证数据"""
        return all(isinstance(x, int) for x in data)
    
    @classmethod
    def from_config(cls, config: Dict) -> 'DataProcessor':
        """类方法：从配置创建实例"""
        return cls(config.get('name', 'default'))
    
    async def process_async(self, data: List[int]) -> Dict[str, int]:
        """异步处理方法"""
        await asyncio.sleep(0.1)
        result = {}
        for i, value in enumerate(data):
            result[f"item_{i}"] = value * 2
        return result

def decorator_example(func):
    """装饰器示例"""
    def wrapper(*args, **kwargs):
        print(f"调用函数: {func.__name__}")
        return func(*args, **kwargs)
    return wrapper

@decorator_example
def decorated_function(x: int) -> int:
    """被装饰的函数"""
    return x ** 2

# 全局常量
CONFIG = {
    'debug': True,
    'max_items': 1000
}
'''
    
    complex_file = Path("complex_example.py")
    complex_file.write_text(complex_code, encoding='utf-8')
    
    try:
        # 使用详细配置解析
        result = quick_parse(str(complex_file), extract_comments=True)
        
        print(f"\n复杂文件解析结果:")
        print(f"文件大小: {result.metadata.get('file_size', 0)} bytes")
        print(f"处理时间: {result.processing_time:.4f}s")
        print(f"代码片段数量: {len(result.snippets)}")
        
        # 按类型分组显示
        snippets_by_type = {}
        for snippet in result.snippets:
            if snippet.type not in snippets_by_type:
                snippets_by_type[snippet.type] = []
            snippets_by_type[snippet.type].append(snippet)
        
        for snippet_type, snippets in snippets_by_type.items():
            print(f"\n{snippet_type.upper()} ({len(snippets)} 个):")
            for snippet in snippets:
                name = snippet.name
                if snippet.class_name:
                    name = f"{snippet.class_name}.{name}"
                print(f"  - {name}")
                if snippet.args:
                    print(f"    参数: {snippet.args}")
    
    finally:
        if complex_file.exists():
            complex_file.unlink()


def demo_testing():
    """演示测试功能"""
    print("\n=== 测试功能演示 ===")
    
    # 使用内置的测试器
    print("运行内置测试套件:")
    tester = ParserTester()
    tester.run_all_tests()


def main():
    """主函数"""
    logger.info("启动代码解析器演示程序")
    print("CodeRepoIndex 代码解析器示例")
    print("=" * 50)
    
    demos = [
        ("基本用法", demo_basic_usage),
        ("配置选项", demo_configuration),
        ("批量处理", demo_batch_processing),
        ("错误处理", demo_error_handling),
        ("高级功能", demo_advanced_features),
        ("测试功能", demo_testing)
    ]
    
    try:
        for demo_name, demo_func in demos:
            logger.info(f"开始演示: {demo_name}")
            try:
                demo_func()
                logger.success(f"演示 {demo_name} 完成")
            except Exception as e:
                logger.error(f"演示 {demo_name} 失败: {e}")
                raise
        
    except KeyboardInterrupt:
        logger.warning("用户中断了演示")
        print("\n\n用户中断了演示")
    except Exception as e:
        logger.error(f"演示过程中出现错误: {e}")
        print(f"\n演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 50)
    print("演示完成！")
    logger.info("代码解析器演示程序结束")


if __name__ == "__main__":
    main() 