# coding: utf-8
"""
Python代码解析器测试模块
测试Python语言的代码解析功能
"""

import tempfile
from pathlib import Path
from typing import List
import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from code_parser import CodeParser, ParseResult
from loguru import logger


class PythonParserTester:
    """Python解析器测试类"""
    
    def __init__(self):
        self.parser = CodeParser()
        self.test_files = []
    
    def create_python_test_file(self) -> Path:
        """创建Python测试文件"""
        python_code = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Python测试文件
包含类、函数、异步函数、装饰器等Python特性
"""

import os
import sys
import asyncio
from typing import List, Dict, Optional, Union, Tuple
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from functools import wraps, lru_cache
import logging

# 全局常量
VERSION = "1.0.0"
DEBUG_MODE = True

# 全局变量
global_counter = 0


@dataclass
class Person:
    """人员数据类"""
    name: str
    age: int
    email: Optional[str] = None
    skills: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """初始化后处理"""
        if self.email is None:
            self.email = f"{self.name.lower()}@example.com"


class Animal(ABC):
    """抽象动物基类"""
    
    def __init__(self, name: str, species: str):
        """初始化动物"""
        self.name = name
        self.species = species
        self._age = 0
    
    @property
    def age(self) -> int:
        """获取年龄属性"""
        return self._age
    
    @age.setter
    def age(self, value: int):
        """设置年龄属性"""
        if value < 0:
            raise ValueError("年龄不能为负数")
        self._age = value
    
    @abstractmethod
    def make_sound(self) -> str:
        """抽象方法：发出声音"""
        pass
    
    @classmethod
    def create_default(cls, name: str):
        """类方法：创建默认动物"""
        return cls(name, "unknown")
    
    @staticmethod
    def is_valid_age(age: int) -> bool:
        """静态方法：验证年龄是否有效"""
        return 0 <= age <= 200


class Dog(Animal):
    """狗类"""
    
    def __init__(self, name: str, breed: str = "未知"):
        """初始化狗"""
        super().__init__(name, "犬科")
        self.breed = breed
        self.is_trained = False
    
    def make_sound(self) -> str:
        """狗叫声"""
        return "汪汪！"
    
    def train(self, skill: str) -> bool:
        """训练技能"""
        if skill in ["坐下", "握手", "装死"]:
            self.is_trained = True
            logger.info(f"{self.name} 学会了 {skill}")
            return True
        return False
    
    def play_fetch(self, distance: float) -> str:
        """玩接球游戏"""
        if distance > 50:
            return f"{self.name} 跑得太远了，累坏了！"
        return f"{self.name} 成功接到了球！"


class Cat(Animal):
    """猫类"""
    
    def __init__(self, name: str, color: str = "白色"):
        super().__init__(name, "猫科")
        self.color = color
        self.lives = 9
    
    def make_sound(self) -> str:
        """猫叫声"""
        return "喵~"
    
    def climb_tree(self, height: float) -> bool:
        """爬树"""
        return height <= 10.0


def timing_decorator(func):
    """计时装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        import time
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f"{func.__name__} 执行时间: {end - start:.4f}秒")
        return result
    return wrapper


@lru_cache(maxsize=128)
def fibonacci(n: int) -> int:
    """斐波那契数列（带缓存）"""
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)


@timing_decorator
def calculate_statistics(numbers: List[float]) -> Dict[str, float]:
    """计算数字列表的统计信息"""
    if not numbers:
        return {}
    
    result = {
        'count': len(numbers),
        'sum': sum(numbers),
        'mean': sum(numbers) / len(numbers),
        'min': min(numbers),
        'max': max(numbers)
    }
    
    # 计算方差
    mean_val = result['mean']
    variance = sum((x - mean_val) ** 2 for x in numbers) / len(numbers)
    result['variance'] = variance
    result['std_dev'] = variance ** 0.5
    
    return result


async def async_fetch_data(url: str, timeout: int = 30) -> Dict:
    """异步获取数据"""
    try:
        # 模拟异步请求
        await asyncio.sleep(0.1)
        return {
            'url': url,
            'status': 200,
            'data': f"从 {url} 获取的数据",
            'timestamp': asyncio.get_event_loop().time()
        }
    except Exception as e:
        logger.error(f"获取数据失败: {e}")
        return {'error': str(e)}


async def async_process_urls(urls: List[str]) -> List[Dict]:
    """异步处理多个URL"""
    tasks = [async_fetch_data(url) for url in urls]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return [r for r in results if not isinstance(r, Exception)]


def generator_function(limit: int):
    """生成器函数"""
    for i in range(limit):
        if i % 2 == 0:
            yield i * i
        else:
            yield i


def context_manager_function():
    """上下文管理器函数"""
    class FileManager:
        def __init__(self, filename):
            self.filename = filename
            self.file = None
        
        def __enter__(self):
            self.file = open(self.filename, 'w')
            return self.file
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            if self.file:
                self.file.close()
    
    return FileManager


def lambda_examples():
    """Lambda表达式示例"""
    # 简单lambda
    square = lambda x: x ** 2
    
    # 带条件的lambda
    is_even = lambda x: x % 2 == 0
    
    # 用于排序的lambda
    people = [('Alice', 25), ('Bob', 30), ('Charlie', 20)]
    sorted_by_age = sorted(people, key=lambda person: person[1])
    
    return square, is_even, sorted_by_age


def error_handling_example():
    """错误处理示例"""
    try:
        # 可能出错的代码
        result = 10 / 0
    except ZeroDivisionError as e:
        logger.error(f"除零错误: {e}")
        return None
    except Exception as e:
        logger.error(f"未知错误: {e}")
        return None
    else:
        return result
    finally:
        logger.info("清理资源")


class MetaclassExample(type):
    """元类示例"""
    def __new__(cls, name, bases, attrs):
        # 为所有方法添加日志
        for key, value in attrs.items():
            if callable(value) and not key.startswith('_'):
                attrs[key] = cls.add_logging(value)
        return super().__new__(cls, name, bases, attrs)
    
    @staticmethod
    def add_logging(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger.info(f"调用方法: {func.__name__}")
            return func(*args, **kwargs)
        return wrapper


class ExampleClass(metaclass=MetaclassExample):
    """使用元类的示例类"""
    
    def method_one(self):
        return "方法一"
    
    def method_two(self, x: int) -> int:
        return x * 2


# 模块级别函数
def main():
    """主函数"""
    print("Python解析器测试")
    
    # 创建实例
    dog = Dog("旺财", "金毛")
    cat = Cat("咪咪", "橘色")
    
    # 测试方法
    print(dog.make_sound())
    print(cat.make_sound())
    
    # 测试异步函数
    urls = ["http://example1.com", "http://example2.com"]
    loop = asyncio.new_event_loop()
    results = loop.run_until_complete(async_process_urls(urls))
    print(f"异步结果: {results}")
    
    # 测试统计函数
    numbers = [1.0, 2.5, 3.7, 4.2, 5.1]
    stats = calculate_statistics(numbers)
    print(f"统计结果: {stats}")


if __name__ == "__main__":
    main()
'''
        
        # 创建临时文件
        temp_file = Path(tempfile.mktemp(suffix=".py"))
        with temp_file.open('w', encoding='utf-8') as f:
            f.write(python_code)
        
        self.test_files.append(temp_file)
        return temp_file
    
    def test_python_parsing(self):
        """测试Python解析功能"""
        logger.info("开始Python解析测试")
        print("=== Python解析测试 ===")
        
        test_file = self.create_python_test_file()
        logger.info(f"创建测试文件: {test_file}")
        
        # 解析文件
        result = self.parser.parse_file(str(test_file))
        
        # 验证结果
        print(f"语言: {result.language.value if result.language else 'Unknown'}")
        print(f"文件路径: {result.file_path}")
        print(f"代码片段数量: {len(result.snippets)}")
        print(f"处理时间: {result.processing_time:.4f}s")
        print(f"是否成功: {result.is_successful}")
        
        if result.errors:
            print(f"错误信息: {result.errors}")
        
        # 分析代码片段
        classes = [s for s in result.snippets if s.type == 'class']
        functions = [s for s in result.snippets if s.type in ['function', 'method']]
        
        print(f"\n发现的类: {len(classes)}")
        for cls in classes:
            print(f"  - {cls.name} (行 {cls.line_start}-{cls.line_end})")
        
        print(f"\n发现的函数/方法: {len(functions)}")
        for func in functions[:10]:  # 只显示前10个
            print(f"  - {func.name}({func.args}) (行 {func.line_start}-{cls.line_end})")
            if func.class_name:
                print(f"    所属类: {func.class_name}")
        
        logger.success("Python解析测试完成")
        return result
    
    def cleanup_test_files(self):
        """清理测试文件"""
        for file_path in self.test_files:
            try:
                if file_path.exists():
                    file_path.unlink()
            except Exception as e:
                logger.error(f"清理文件失败: {file_path}, 错误: {e}")
    
    def run_test(self):
        """运行Python解析测试"""
        try:
            result = self.test_python_parsing()
            return result
        finally:
            self.cleanup_test_files()


def main():
    """主函数"""
    tester = PythonParserTester()
    tester.run_test()


if __name__ == "__main__":
    main() 