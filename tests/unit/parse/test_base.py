import sys
from pathlib import Path
from loguru import logger
logger.remove()  # 移除默认handler
logger.add(sys.stderr, level="INFO")  # 只显示INFO及以上级别的日志

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from coderepoindex.parsers import CodeParser, parse_code_file

# 方法1: 使用便利函数
result = parse_code_file("example.py")
print(f"语言: {result.language.value}")
print(f"代码片段数量: {len(result.snippets)}")
print(result.snippets)   

# # 方法2: 使用解析器类
# parser = CodeParser()
# result = parser.parse_file("example.py")

# # 查看解析结果
# for snippet in result.snippets:
#     print(f"{snippet.type}: {snippet.name}")
#     if snippet.class_name:
#         print(f"  所属类: {snippet.class_name}")
#     if snippet.args:
#         print(f"  参数: {snippet.args}")