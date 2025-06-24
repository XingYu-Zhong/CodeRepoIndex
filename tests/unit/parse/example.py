# coding: utf-8
"""
代码解析器单元测试示例
演示如何编写基本的解析器单元测试
"""

import unittest
import tempfile
import os
from pathlib import Path
import sys

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from coderepoindex.parsers.code_parser import (
    CodeParser, 
    ParseResult, 
    SupportedLanguage, 
    CodeSnippet,
    parse_code_file
)


class TestCodeParserBasic(unittest.TestCase):
    """代码解析器基础测试类"""
    
    def setUp(self):
        """测试前设置"""
        self.parser = CodeParser()
        self.temp_files = []
    
    