#!/usr/bin/env python3
# coding: utf-8
"""
依赖检查脚本

检查代码解析器所需的依赖是否正确安装，并提供安装建议。
"""

import sys
import subprocess
from pathlib import Path


def check_basic_dependencies():
    """检查基础依赖"""
    print("=== 检查基础依赖 ===")
    
    dependencies = [
        "tree_sitter",
        "loguru", 
        "chardet"
    ]
    
    missing = []
    
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"✅ {dep}")
        except ImportError:
            print(f"❌ {dep} - 未安装")
            missing.append(dep)
    
    if missing:
        print(f"\n缺少依赖: {', '.join(missing)}")
        print("安装命令: pip install " + " ".join(missing))
        return False
    
    return True


def check_tree_sitter_languages():
    """检查 tree-sitter-languages 依赖"""
    print("\n=== 检查 tree-sitter-languages ===")
    
    try:
        from tree_sitter_languages import get_language
        print("✅ tree_sitter_languages 已安装")
        
        # 测试获取语言
        languages_to_test = ["python", "javascript", "java"]
        supported = []
        
        for lang in languages_to_test:
            try:
                lang_obj = get_language(lang)
                supported.append(lang)
                print(f"✅ {lang} 语言支持: {type(lang_obj)}")
            except Exception as e:
                print(f"❌ {lang} 语言不支持: {e}")
        
        if supported:
            print(f"支持的语言: {', '.join(supported)}")
            return True
        else:
            print("❌ 没有支持的语言")
            return False
            
    except ImportError as e:
        print(f"❌ tree_sitter_languages 未安装: {e}")
        print("安装命令: pip install tree-sitter-languages")
        return False


def check_tree_sitter_compatibility():
    """检查 tree-sitter 版本兼容性"""
    print("\n=== 检查 tree-sitter 版本兼容性 ===")
    
    try:
        import tree_sitter
        print(f"✅ tree-sitter 版本: {tree_sitter.__version__ if hasattr(tree_sitter, '__version__') else 'unknown'}")
        
        # 测试基本功能
        from tree_sitter import Language, Parser
        parser = Parser()
        print("✅ Parser 类可以实例化")
        
        return True
        
    except Exception as e:
        print(f"❌ tree-sitter 兼容性问题: {e}")
        return False


def test_parser_creation():
    """测试解析器创建"""
    print("\n=== 测试解析器创建 ===")
    
    try:
        # 尝试导入我们的解析器
        sys.path.insert(0, str(Path(__file__).parent))
        from code_parser import CodeParser
        
        print("✅ CodeParser 类导入成功")
        
        # 尝试创建解析器实例
        parser = CodeParser()
        print("✅ CodeParser 实例创建成功")
        
        # 测试获取支持的扩展名
        extensions = parser.get_supported_extensions()
        print(f"✅ 支持的扩展名: {extensions}")
        
        return True
        
    except Exception as e:
        print(f"❌ 解析器创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_simple_parsing():
    """测试简单解析功能"""
    print("\n=== 测试简单解析 ===")
    
    try:
        import tempfile
        from pathlib import Path
        
        # 导入解析器
        sys.path.insert(0, str(Path(__file__).parent))
        from code_parser import CodeParser
        
        # 创建简单的测试文件
        test_code = '''def hello():
    """简单的测试函数"""
    return "Hello, World!"
'''
        
        # 写入临时文件
        temp_file = Path(tempfile.mktemp(suffix=".py"))
        temp_file.write_text(test_code, encoding='utf-8')
        
        try:
            # 尝试解析
            parser = CodeParser()
            result = parser.parse_file(str(temp_file))
            
            if result.is_successful:
                print(f"✅ 解析成功，提取 {len(result.snippets)} 个代码片段")
                
                # 显示片段信息
                for snippet in result.snippets:
                    print(f"  - {snippet.type}: {snippet.name}")
                
                return True
            else:
                print(f"❌ 解析失败: {result.errors}")
                return False
                
        finally:
            if temp_file.exists():
                temp_file.unlink()
        
    except Exception as e:
        print(f"❌ 解析测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def provide_installation_guide():
    """提供安装指南"""
    print("\n=== 安装指南 ===")
    
    print("1. 安装基础依赖:")
    print("   pip install tree-sitter loguru chardet")
    
    print("\n2. 安装 tree-sitter-languages:")
    print("   pip install tree-sitter-languages")
    
    print("\n3. 如果遇到编译问题，可以尝试:")
    print("   pip install --upgrade pip setuptools wheel")
    print("   pip install tree-sitter-languages --no-cache-dir")
    
    print("\n4. 检查 Python 版本兼容性:")
    print(f"   当前 Python 版本: {sys.version}")
    print("   推荐 Python 3.8+")
    
    print("\n5. 在某些系统上，可能需要安装编译工具:")
    print("   - Ubuntu/Debian: sudo apt-get install build-essential")
    print("   - CentOS/RHEL: sudo yum groupinstall 'Development Tools'")
    print("   - macOS: xcode-select --install")
    print("   - Windows: 安装 Visual Studio Build Tools")


def main():
    """主函数"""
    print("代码解析器依赖检查工具")
    print("=" * 50)
    
    checks = [
        ("基础依赖", check_basic_dependencies),
        ("tree-sitter-languages", check_tree_sitter_languages),
        ("tree-sitter兼容性", check_tree_sitter_compatibility),
        ("解析器创建", test_parser_creation),
        ("简单解析测试", test_simple_parsing)
    ]
    
    results = []
    
    for name, check_func in checks:
        print(f"\n{'='*20} {name} {'='*20}")
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ 检查 {name} 时出错: {e}")
            results.append((name, False))
    
    # 总结
    print("\n" + "=" * 50)
    print("检查结果总结:")
    
    passed = 0
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {name}: {status}")
        if result:
            passed += 1
    
    print(f"\n通过率: {passed}/{len(results)} ({passed/len(results)*100:.1f}%)")
    
    if passed < len(results):
        provide_installation_guide()
    else:
        print("\n🎉 所有检查都通过了！代码解析器已准备就绪。")
        
        print("\n快速测试:")
        print("from coderepoindex.parsers import parse_code_file")
        print("result = parse_code_file('your_file.py')")


if __name__ == "__main__":
    main() 