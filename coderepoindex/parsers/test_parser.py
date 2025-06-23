# coding: utf-8
"""
代码解析器测试模块

用于测试和演示代码解析器的功能。
"""

from pathlib import Path
from typing import List
import tempfile
import os
from loguru import logger

from code_parser import CodeParser, ParseResult
from config import ParserConfig, ConfigTemplates


class ParserTester:
    """解析器测试类"""
    
    def __init__(self):
        self.parser = CodeParser()
        self.test_files = []
    
    def create_test_files(self) -> List[Path]:
        """创建测试用的代码文件"""
        test_files = []
        
        # Python 测试文件
        python_code = '''
# -*- coding: utf-8 -*-
"""
这是一个Python测试文件
包含类和函数的示例代码
"""

import os
import sys
from typing import List, Dict


class TestClass:
    """测试类：演示类的解析"""
    
    def __init__(self, name: str):
        """初始化方法"""
        self.name = name
    
    def get_name(self) -> str:
        """获取名称的方法"""
        return self.name
    
    def process_data(self, data: List[int]) -> Dict[str, int]:
        """处理数据的方法"""
        result = {}
        for i, value in enumerate(data):
            result[f"item_{i}"] = value * 2
        return result


def standalone_function(x: int, y: int) -> int:
    """独立函数：计算两个数的和"""
    return x + y


async def async_function():
    """异步函数示例"""
    import asyncio
    await asyncio.sleep(1)
    return "completed"


# 全局变量
GLOBAL_CONSTANT = "测试常量"
'''
        
        # JavaScript 测试文件
        js_code = '''
/**
 * JavaScript测试文件
 * 包含类、函数和箭头函数的示例
 */

// 导入模块
import { Component } from 'react';
import utils from './utils';

/**
 * 测试类
 */
class TestComponent extends Component {
    constructor(props) {
        super(props);
        this.state = { count: 0 };
    }
    
    /**
     * 增加计数器
     */
    increment() {
        this.setState({ count: this.state.count + 1 });
    }
    
    render() {
        return `<div>Count: ${this.state.count}</div>`;
    }
}

/**
 * 普通函数
 */
function calculateSum(a, b) {
    return a + b;
}

/**
 * 箭头函数
 */
const calculateProduct = (a, b) => {
    return a * b;
};

// 异步函数
async function fetchData(url) {
    const response = await fetch(url);
    return response.json();
}

// 导出
export { TestComponent, calculateSum, calculateProduct };
'''
        
        # 创建临时文件
        temp_dir = Path(tempfile.mkdtemp())
        
        python_file = temp_dir / "test_file.py"
        with python_file.open('w', encoding='utf-8') as f:
            f.write(python_code)
        test_files.append(python_file)
        
        js_file = temp_dir / "test_file.js"
        with js_file.open('w', encoding='utf-8') as f:
            f.write(js_code)
        test_files.append(js_file)
        
        self.test_files = test_files
        return test_files
    
    def cleanup_test_files(self):
        """清理测试文件"""
        for file_path in self.test_files:
            try:
                if file_path.exists():
                    file_path.unlink()
                # 删除空目录
                if file_path.parent.exists() and not any(file_path.parent.iterdir()):
                    file_path.parent.rmdir()
            except Exception as e:
                print(f"清理文件失败: {file_path}, 错误: {e}")
    
    def test_basic_parsing(self):
        """测试基本解析功能"""
        logger.info("开始基本解析功能测试")
        print("=== 基本解析功能测试 ===")
        
        test_files = self.create_test_files()
        logger.info(f"创建了 {len(test_files)} 个测试文件")
        
        for file_path in test_files:
            logger.debug(f"测试解析文件: {file_path.name}")
            print(f"\n解析文件: {file_path.name}")
            result = self.parser.parse_file(str(file_path))
            
            self.print_parse_result(result)
            
        logger.success("基本解析功能测试完成")
    
    def test_config_templates(self):
        """测试不同的配置模板"""
        logger.info("开始配置模板测试")
        print("\n=== 配置模板测试 ===")
        
        test_files = self.create_test_files()
        python_file = test_files[0]  # 使用Python文件测试
        logger.debug(f"使用测试文件: {python_file.name}")
        
        configs = {
            "默认配置": ParserConfig(),
            "最小配置": ConfigTemplates.minimal(),
            "性能配置": ConfigTemplates.performance(),
            "详细配置": ConfigTemplates.detailed(),
            "中文优化": ConfigTemplates.chinese_optimized()
        }
        
        for config_name, config in configs.items():
            logger.debug(f"测试配置: {config_name}")
            print(f"\n--- {config_name} ---")
            parser = CodeParser()
            # 这里可以将config传递给parser，但当前实现还未集成config
            result = parser.parse_file(str(python_file))
            print(f"提取的代码片段数量: {len(result.snippets)}")
            print(f"处理时间: {result.processing_time:.4f}s")
            logger.debug(f"{config_name} 测试完成: {len(result.snippets)} 个片段, {result.processing_time:.4f}s")
            
        logger.success("配置模板测试完成")
    
    def test_error_handling(self):
        """测试错误处理"""
        print("\n=== 错误处理测试 ===")
        
        # 测试不存在的文件
        print("测试不存在的文件:")
        result = self.parser.parse_file("/nonexistent/file.py")
        print(f"是否成功: {result.is_successful}")
        print(f"错误信息: {result.errors}")
        
        # 测试不支持的文件类型
        print("\n测试不支持的文件类型:")
        temp_file = Path(tempfile.mktemp(suffix=".unknown"))
        temp_file.write_text("some content")
        
        result = self.parser.parse_file(str(temp_file))
        print(f"是否成功: {result.is_successful}")
        print(f"错误信息: {result.errors}")
        
        temp_file.unlink()
    
    def test_batch_parsing(self):
        """测试批量解析"""
        print("\n=== 批量解析测试 ===")
        
        test_files = self.create_test_files()
        file_paths = [str(f) for f in test_files]
        
        results = self.parser.parse_multiple_files(file_paths)
        
        print(f"批量解析了 {len(results)} 个文件")
        for result in results:
            print(f"文件: {Path(result.file_path).name}")
            print(f"  语言: {result.language.value if result.language else 'Unknown'}")
            print(f"  代码片段: {len(result.snippets)}")
            print(f"  是否成功: {result.is_successful}")
    
    def print_parse_result(self, result: ParseResult):
        """打印解析结果"""
        print(f"  语言: {result.language.value if result.language else 'Unknown'}")
        print(f"  文件大小: {result.metadata.get('file_size', 0)} bytes")
        print(f"  处理时间: {result.processing_time:.4f}s")
        print(f"  代码片段数量: {len(result.snippets)}")
        print(f"  是否成功: {result.is_successful}")
        
        if result.errors:
            print(f"  错误: {result.errors}")
        
        # 显示前3个代码片段的详细信息
        for i, snippet in enumerate(result.snippets[:3]):
            print(f"\n  片段 {i+1}:")
            print(f"    类型: {snippet.type}")
            print(f"    名称: {snippet.name}")
            print(f"    行数: {snippet.line_start}-{snippet.line_end}")
            if snippet.class_name:
                print(f"    所属类: {snippet.class_name}")
            if snippet.args:
                print(f"    参数: {snippet.args}")
            if snippet.comment:
                print(f"    注释: {snippet.comment[:100]}...")
            print(f"    关键词: {snippet.key_msg[:100]}...")
    
    def run_all_tests(self):
        """运行所有测试"""
        logger.info("开始运行完整测试套件")
        
        try:
            print("开始代码解析器测试")
            print("=" * 50)
            
            test_methods = [
                ("基本解析", self.test_basic_parsing),
                ("配置模板", self.test_config_templates),
                ("错误处理", self.test_error_handling),
                ("批量处理", self.test_batch_parsing)
            ]
            
            for test_name, test_method in test_methods:
                logger.info(f"开始执行测试: {test_name}")
                try:
                    test_method()
                    logger.success(f"测试 {test_name} 通过")
                except Exception as e:
                    logger.error(f"测试 {test_name} 失败: {e}")
                    raise
            
            print("\n" + "=" * 50)
            print("所有测试完成")
            logger.success("完整测试套件执行完成")
            
        except Exception as e:
            logger.error(f"测试执行过程中出现错误: {e}")
            raise
        finally:
            logger.debug("开始清理测试文件")
            self.cleanup_test_files()
            logger.debug("测试文件清理完成")


def main():
    """主函数：运行测试"""
    tester = ParserTester()
    tester.run_all_tests()


if __name__ == "__main__":
    main() 