# 代码解析器模块

一个基于 tree-sitter 的强大代码解析器，用于提取源代码的结构信息，支持多种编程语言。

## 🚀 主要特性

- **多语言支持**: 支持 Python、JavaScript、TypeScript、Java、Go、C/C++、Kotlin、Lua 等主流编程语言
- **结构化提取**: 自动识别和提取函数、类、方法、注释等代码结构
- **灵活配置**: 提供多种预设配置模板，支持自定义解析选项
- **批量处理**: 支持同时处理多个文件，提供高效的批量解析功能
- **错误处理**: 完善的错误处理机制，优雅地处理各种异常情况
- **性能优化**: 内置缓存机制和性能监控，适用于大型代码库
- **中文支持**: 优化的中文编码处理和关键词提取

## 📦 安装依赖

```bash
# 安装必要的依赖
pip install tree-sitter tree-sitter-languages chardet loguru
```

### 依赖问题排查

如果遇到依赖问题，可以运行依赖检查脚本：

```bash
# 检查依赖是否正确安装
python coderepoindex/parsers/check_dependencies.py
```

常见问题解决：

1. **ImportError: tree_sitter_languages**
   ```bash
   pip install tree-sitter-languages
   ```

2. **"Argument to set_language must be a Language" 错误**
   - 这通常是由于 `tree-sitter-languages` 版本问题
   - 尝试重新安装：`pip install --upgrade tree-sitter-languages`

3. **编译错误**
   ```bash
   # 升级构建工具
   pip install --upgrade pip setuptools wheel
   
   # 清除缓存重新安装
   pip install tree-sitter-languages --no-cache-dir
   ```

4. **在某些系统上需要编译工具**
   - Ubuntu/Debian: `sudo apt-get install build-essential`
   - CentOS/RHEL: `sudo yum groupinstall 'Development Tools'`
   - macOS: `xcode-select --install`
   - Windows: 安装 Visual Studio Build Tools

## 🔧 快速开始

### 基本用法

```python
from coderepoindex.parsers import CodeParser, parse_code_file

# 方法1: 使用便利函数
result = parse_code_file("example.py")
print(f"语言: {result.language.value}")
print(f"代码片段数量: {len(result.snippets)}")

# 方法2: 使用解析器类
parser = CodeParser()
result = parser.parse_file("example.py")

# 查看解析结果
for snippet in result.snippets:
    print(f"{snippet.type}: {snippet.name}")
    if snippet.class_name:
        print(f"  所属类: {snippet.class_name}")
    if snippet.args:
        print(f"  参数: {snippet.args}")
```

### 批量处理

```python
from coderepoindex.parsers import CodeParser

parser = CodeParser()
file_paths = ["file1.py", "file2.js", "file3.java"]
results = parser.parse_multiple_files(file_paths)

for result in results:
    print(f"文件: {result.file_path}")
    print(f"成功: {result.is_successful}")
    print(f"代码片段: {len(result.snippets)}")
```

### 使用配置模板

```python
from coderepoindex.parsers import ConfigTemplates, quick_parse

# 最小配置：只提取基本结构，不包含注释
result = quick_parse("example.py", extract_comments=False)

# 详细配置：提取所有可能的信息
config = ConfigTemplates.detailed()
parser = CodeParser()
result = parser.parse_file("example.py")

# 性能配置：适用于大型代码库
config = ConfigTemplates.performance()

# 中文优化配置：针对中文项目
config = ConfigTemplates.chinese_optimized()
```

## 📋 解析结果

### ParseResult 类

```python
@dataclass
class ParseResult:
    language: Optional[SupportedLanguage]  # 检测到的编程语言
    file_path: str                         # 文件路径
    snippets: List[CodeSnippet]           # 提取的代码片段列表
    errors: List[str]                     # 错误信息列表
    metadata: Dict[str, Any]              # 元数据
    processing_time: float                # 处理时间(秒)
    
    @property
    def is_successful(self) -> bool:      # 是否解析成功
    @property
    def suffix(self) -> str:              # 文件后缀
```

### CodeSnippet 类

```python
@dataclass
class CodeSnippet:
    type: str          # 类型: "function", "class", "method" 等
    path: str          # 文件路径
    name: str          # 名称
    code: str          # 代码内容
    md5: str           # MD5 哈希值
    func_name: str     # 函数全名
    args: str          # 参数列表
    class_name: str    # 所属类名
    comment: str       # 关联注释
    key_msg: str       # 关键信息(用于搜索)
    line_start: int    # 起始行号
    line_end: int      # 结束行号
    metadata: Dict     # 额外元数据
```

## ⚙️ 配置选项

### ParserConfig 类

```python
@dataclass
class ParserConfig:
    # 文件处理
    max_file_size: int = 10 * 1024 * 1024  # 最大文件大小(10MB)
    max_cache_size: int = 128               # 缓存大小
    
    # 编码处理
    encoding_confidence_threshold: float = 0.7  # 编码检测置信度阈值
    default_encoding: str = 'utf-8'             # 默认编码
    fallback_encoding: str = 'gbk'              # 备用编码
    
    # 解析选项
    extract_comments: bool = True               # 提取注释
    extract_docstrings: bool = True             # 提取文档字符串
    extract_imports: bool = False               # 提取导入语句
    extract_variables: bool = False             # 提取变量
    
    # 过滤选项
    min_function_lines: int = 1                 # 最小函数行数
    max_function_lines: int = 1000              # 最大函数行数
    ignore_private_methods: bool = False        # 忽略私有方法
    ignore_test_files: bool = False             # 忽略测试文件
    
    # 关键词提取
    extract_chinese_keywords: bool = True       # 提取中文关键词
    extract_english_keywords: bool = True       # 提取英文关键词
    min_keyword_length: int = 2                 # 最小关键词长度
    max_keywords_per_snippet: int = 50          # 每个片段最大关键词数
```

### 预设配置模板

```python
# 最小配置：只解析基本结构
config = ConfigTemplates.minimal()

# 性能配置：适用于大型代码库
config = ConfigTemplates.performance()

# 详细配置：提取所有信息
config = ConfigTemplates.detailed()

# 中文优化：针对中文项目
config = ConfigTemplates.chinese_optimized()
```

## 🌐 支持的编程语言

| 语言 | 扩展名 | 支持的结构 |
|------|--------|------------|
| Python | `.py` | 函数、类、方法、异步函数 |
| JavaScript | `.js`, `.jsx` | 函数、类、箭头函数、方法 |
| TypeScript | `.ts`, `.tsx` | 函数、类、接口、方法 |
| Java | `.java` | 类、方法、构造函数、接口 |
| Go | `.go` | 函数、方法、类型声明 |
| C | `.c`, `.h` | 函数、结构体 |
| C++ | `.cpp`, `.cc`, `.cxx`, `.hpp` | 函数、类、结构体 |
| Kotlin | `.kt`, `.kts` | 函数、类、方法 |
| Lua | `.lua` | 函数 |

## 🛠️ 高级功能

### 错误处理

```python
parser = CodeParser()
result = parser.parse_file("example.py")

if not result.is_successful:
    print("解析失败:")
    for error in result.errors:
        print(f"  - {error}")
else:
    print(f"解析成功，提取 {len(result.snippets)} 个代码片段")
```

### 性能监控

```python
result = parser.parse_file("large_file.py")
print(f"处理时间: {result.processing_time:.4f}s")
print(f"文件大小: {result.metadata.get('file_size', 0)} bytes")
```

### 缓存管理

```python
# 清除解析器缓存
parser.clear_cache()

# 获取支持的扩展名
extensions = parser.get_supported_extensions()
print(f"支持的扩展名: {extensions}")
```

## 🧪 测试和调试

### 运行内置测试

```python
from coderepoindex.parsers import ParserTester

# 运行所有测试
tester = ParserTester()
tester.run_all_tests()

# 或者运行特定测试
tester.test_basic_parsing()
tester.test_error_handling()
```

### 使用示例脚本

```bash
# 运行完整演示
python examples/parser_demo.py

# 解析特定文件
python -m coderepoindex.parsers.code_parser example.py
```

## 🔧 优化内容

相比原始版本，此优化版本包含以下改进：

### 1. 架构优化
- 使用 `dataclass` 替代 `TypedDict`，提供更好的类型检查
- 引入枚举类型，提高代码可维护性
- 模块化设计，分离配置、测试和核心逻辑

### 2. 性能优化
- 添加 LRU 缓存机制
- 优化文件读取和编码检测
- 引入计时装饰器，便于性能分析
- 线程安全的解析器管理

### 3. 错误处理
- 自定义异常类型
- 优雅的错误恢复机制
- 详细的错误信息记录

### 4. 功能增强
- 支持更多编程语言
- 改进的关键词提取算法
- 灵活的配置系统
- 批量处理支持

### 5. 开发体验
- 完整的类型注解
- 丰富的文档和示例
- 内置测试套件
- 便利函数和模块级API

### 6. 日志和监控
- 使用 loguru 替代标准 logging
- 支持中文日志信息
- 性能监控和统计

## 📝 示例输出

```
文件: example.py
语言: python
代码片段数量: 5
处理时间: 0.0123s

片段 1:
  类型: class
  名称: Calculator
  行数: 8-25
  关键词: Calculator 计算器 类 init add multiply history

片段 2:
  类型: function
  名称: __init__
  行数: 11-13
  所属类: Calculator
  参数: (self)
  注释: 初始化计算器

片段 3:
  类型: function
  名称: add
  行数: 15-19
  所属类: Calculator
  参数: (self, a, b)
  注释: 加法运算
```

## 🤝 贡献指南

欢迎贡献代码！请确保：

1. 遵循现有的代码风格
2. 添加适当的测试用例
3. 更新相关文档
4. 使用中文注释和文档字符串

## 📄 许可证

MIT License - 详见项目根目录的 LICENSE 文件。

---

**注意**: 此模块需要安装 `tree-sitter-languages` 包才能正常工作。如果遇到语言解析器不可用的问题，请检查相关依赖是否正确安装。 