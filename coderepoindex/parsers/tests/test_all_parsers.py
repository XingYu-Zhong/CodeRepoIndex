# coding: utf-8
"""
所有语言解析器测试统一脚本
运行所有支持语言的解析器测试
"""

import sys
import os
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from loguru import logger
from test_python_parser import PythonParserTester
from test_javascript_parser import JavaScriptParserTester
from test_typescript_parser import TypeScriptParserTester
from test_go_parser import GoParserTester
from test_java_parser import JavaParserTester
from test_c_parser import CParserTester
from test_cpp_parser import CppParserTester
from test_kotlin_parser import KotlinParserTester
from test_lua_parser import LuaParserTester


class AllParsersTester:
    """所有解析器测试类"""
    
    def __init__(self):
        self.testers = {
            "Python": PythonParserTester(),
            "JavaScript": JavaScriptParserTester(),
            "TypeScript": TypeScriptParserTester(),
            "Go": GoParserTester(),
            "Java": JavaParserTester(),
            "C": CParserTester(),
            "C++": CppParserTester(),
            "Kotlin": KotlinParserTester(),
            "Lua": LuaParserTester()
        }
        self.results = {}
    
    def run_all_tests(self):
        """运行所有语言的解析器测试"""
        logger.info("开始运行所有语言的解析器测试")
        print("=" * 60)
        print("代码解析器测试套件")
        print("=" * 60)
        
        total_tests = len(self.testers)
        passed_tests = 0
        failed_tests = 0
        
        for language, tester in self.testers.items():
            try:
                print(f"\n正在测试 {language} 解析器...")
                result = tester.run_test()
                
                self.results[language] = {
                    'success': result.is_successful,
                    'snippets_count': len(result.snippets),
                    'processing_time': result.processing_time,
                    'errors': result.errors
                }
                
                if result.is_successful:
                    passed_tests += 1
                    logger.success(f"{language} 解析器测试通过")
                else:
                    failed_tests += 1
                    logger.error(f"{language} 解析器测试失败: {result.errors}")
                    
            except Exception as e:
                failed_tests += 1
                self.results[language] = {
                    'success': False,
                    'error': str(e)
                }
                logger.error(f"{language} 解析器测试出现异常: {e}")
        
        # 显示汇总结果
        print("\n" + "=" * 60)
        print("测试结果汇总")
        print("=" * 60)
        
        for language, result in self.results.items():
            status = "✅ 通过" if result.get('success', False) else "❌ 失败"
            print(f"{language:<12} {status}")
            
            if result.get('success', False):
                print(f"{'':>14} 代码片段: {result['snippets_count']}")
                print(f"{'':>14} 处理时间: {result['processing_time']:.4f}s")
            elif 'error' in result:
                print(f"{'':>14} 错误: {result['error']}")
            elif result.get('errors'):
                print(f"{'':>14} 错误: {result['errors']}")
        
        print(f"\n总计: {total_tests} 个测试")
        print(f"通过: {passed_tests} 个")
        print(f"失败: {failed_tests} 个")
        print(f"成功率: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            logger.warning(f"有 {failed_tests} 个测试失败")
        else:
            logger.success("所有测试都通过了!")
        
        return failed_tests == 0
    
    def run_specific_test(self, language: str):
        """运行特定语言的测试"""
        if language not in self.testers:
            available = ", ".join(self.testers.keys())
            print(f"不支持的语言: {language}")
            print(f"可用的语言: {available}")
            return False
        
        print(f"运行 {language} 解析器测试...")
        tester = self.testers[language]
        
        try:
            result = tester.run_test()
            return result.is_successful
        except Exception as e:
            logger.error(f"测试失败: {e}")
            return False


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="代码解析器测试套件")
    parser.add_argument(
        '--language', '-l',
        choices=['Python', 'JavaScript', 'TypeScript', 'Go', 'Java', 'C', 'C++', 'Kotlin', 'Lua'],
        help="只测试指定的语言"
    )
    parser.add_argument(
        '--list', action='store_true',
        help="列出所有支持的语言"
    )
    
    args = parser.parse_args()
    
    tester = AllParsersTester()
    
    if args.list:
        print("支持的编程语言:")
        for language in tester.testers.keys():
            print(f"  - {language}")
        return
    
    if args.language:
        success = tester.run_specific_test(args.language)
        sys.exit(0 if success else 1)
    else:
        success = tester.run_all_tests()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main() 