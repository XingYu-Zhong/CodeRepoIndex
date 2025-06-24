# 代码解析器模块

一个基于 tree-sitter 的强大代码解析器，用于提取源代码的结构信息，支持多种编程语言。

## 📖 目录

- [主要特性](#🚀-主要特性)
- [处理思路与架构](#🏗️-处理思路与架构)
- [安装依赖](#📦-安装依赖)
- [快速开始](#🔧-快速开始)
- [核心机制详解](#⚙️-核心机制详解)
- [解析结果](#📋-解析结果)
- [配置选项](#⚙️-配置选项)
- [支持的编程语言](#🌐-支持的编程语言)
- [高级功能](#🛠️-高级功能)
- [测试和调试](#🧪-测试和调试)
- [故障排查](#🔧-故障排查)
- [示例输出](#📝-示例输出)
- [贡献指南](#🤝-贡献指南)

## 🚀 主要特性

- **多语言支持**: 支持 Python、JavaScript、TypeScript、Java、Go、C/C++、Kotlin、Lua 等主流编程语言
- **结构化提取**: 自动识别和提取函数、类、方法、注释等代码结构
- **智能关键词提取**: 提取中英文关键词，支持代码搜索和索引
- **灵活配置**: 提供多种预设配置模板，支持自定义解析选项
- **批量处理**: 支持同时处理多个文件，提供高效的批量解析功能
- **错误处理**: 完善的错误处理机制，优雅地处理各种异常情况
- **性能优化**: 内置缓存机制和性能监控，适用于大型代码库
- **中文支持**: 优化的中文编码处理和关键词提取

## 🏗️ 处理思路与架构

### 整体架构设计

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   输入文件      │───▶│  语言检测器      │───▶│  Tree-sitter    │
│                 │    │  文件读取器      │    │  解析器         │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
┌─────────────────┐    ┌──────────────────┐             │
│   代码片段      │◀───│  结构提取器      │◀────────────┘
│   数据结构      │    │  关键词提取器    │
└─────────────────┘    └──────────────────┘
```

### 核心处理流程

#### 1. 文件预处理阶段
```python
文件路径 → 语言检测 → 文件读取 → 编码识别 → 内容解码
```

- **语言检测**: 根据文件扩展名映射到支持的编程语言
- **文件读取**: 安全读取文件，检查文件大小限制（默认10MB）
- **编码识别**: 优先尝试UTF-8，失败时使用chardet自动检测
- **内容解码**: 将字节流转换为字符串，处理编码错误

#### 2. AST解析阶段
```python
源代码 → Tree-sitter解析器 → AST树 → 节点遍历
```

- **解析器获取**: 为特定语言创建Tree-sitter解析器（带缓存）
- **AST生成**: 将源代码解析为抽象语法树
- **节点识别**: 根据语言特性识别函数、类、方法等节点类型

#### 3. 结构提取阶段
```python
AST节点 → 类型判断 → 信息提取 → 代码片段创建
```

**类解析流程**:
```python
def _parse_classes(self, root_node, source_code, language, file_path):
    # 1. 遍历AST查找类节点
    # 2. 提取类名和类代码
    # 3. 创建类代码片段
    # 4. 递归解析类中的方法
    # 5. 返回类和方法的完整列表
```

**函数解析流程**:
```python
def _parse_functions(self, root_node, source_code, language, file_path, class_name):
    # 1. 遍历AST查找函数节点
    # 2. 收集函数前的注释
    # 3. 提取函数名、参数、返回类型
    # 4. 生成关键词信息
    # 5. 创建函数代码片段
```

#### 4. 关键词提取机制

`key_msg`生成是代码搜索的核心功能：

```python
def _extract_key_messages(self, code: str, comment: str, file_path: Path) -> str:
    # 步骤1: 提取中文关键词 - 正则: [\u4e00-\u9fa5]+
    chinese_words = re.findall(r'[\u4e00-\u9fa5]+', code + comment)
    
    # 步骤2: 提取英文标识符 - 正则: [a-zA-Z_][a-zA-Z0-9_]*
    english_words = re.findall(r'[a-zA-Z_][a-zA-Z0-9_]*', code)
    
    # 步骤3: 添加文件名（去除扩展名）
    key_words = chinese_words + english_words + [file_path.stem]
    
    # 步骤4: 去重、过滤、连接
    unique_words = list(set(word for word in key_words if len(word) > 1))
    return ' '.join(unique_words)
```

**示例**:
```python
# 输入代码
def calculate_user_score(user_id: int) -> float:
    """计算用户分数"""
    return user_id * 1.5

# 文件: /project/utils/score_manager.py
# 生成的key_msg: "计算 用户 分数 def calculate_user_score user_id int float return score_manager"
```

### 语言特定处理策略

#### Python特殊处理
- **节点类型**: `function_definition`, `async_function_definition`
- **方法识别**: 根据是否在类内部区分函数和方法
- **装饰器处理**: 自动识别`@classmethod`, `@staticmethod`等
- **类型注解**: 提取参数和返回值的类型信息

#### JavaScript/TypeScript特殊处理
- **节点类型**: `function_declaration`, `arrow_function`, `method_definition`
- **ES6支持**: 箭头函数、类语法
- **TypeScript接口**: 识别接口声明

#### Java特殊处理
- **节点类型**: `method_declaration`, `constructor_declaration`
- **访问修饰符**: 自动提取public/private/protected
- **泛型支持**: 处理泛型参数

### 性能优化策略

#### 1. 缓存机制
- **解析器缓存**: LRU缓存，避免重复创建Tree-sitter解析器
- **文件级缓存**: 对于相同文件避免重复解析
- **语言检测缓存**: 缓存文件扩展名到语言的映射

#### 2. 内存管理
- **懒加载**: 按需加载特定语言的解析器
- **资源释放**: 及时释放大型AST树的内存
- **批处理优化**: 批量处理时复用解析器实例

#### 3. 并发处理
- **线程安全**: 解析器创建使用线程锁
- **异步友好**: 支持异步文件处理框架

## 📦 安装依赖

### 基础安装
```bash
# 安装必要的依赖
pip install tree-sitter tree-sitter-languages chardet loguru
```

### 版本兼容性
推荐的版本组合：
```bash
pip install tree-sitter==0.21.3 tree-sitter-languages==1.10.2 chardet==3.0.4 loguru
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
   - 解决方案：
   ```bash
   pip install tree-sitter==0.21.3 --force-reinstall
   pip install tree-sitter-languages==1.10.2 --force-reinstall
   ```

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
    if snippet.key_msg:
        print(f"  关键词: {snippet.key_msg}")
```

### 批量处理

```python
from coderepoindex.parsers import CodeParser

parser = CodeParser()
file_paths = ["file1.py", "file2.js", "file3.java"]
results = parser.parse_multiple_files(file_paths)

# 统计处理结果
successful = sum(1 for r in results if r.is_successful)
total_snippets = sum(len(r.snippets) for r in results)
total_time = sum(r.processing_time for r in results)

print(f"成功处理: {successful}/{len(file_paths)} 个文件")
print(f"总代码片段: {total_snippets}")
print(f"总处理时间: {total_time:.4f}s")
```

### 使用配置模板

```python
from coderepoindex.parsers import ConfigTemplates, CodeParser

# 最小配置：只提取基本结构，不包含注释
config = ConfigTemplates.minimal()
parser = CodeParser()
result = parser.parse_file("example.py")

# 详细配置：提取所有可能的信息
config = ConfigTemplates.detailed()

# 性能配置：适用于大型代码库
config = ConfigTemplates.performance()

# 中文优化配置：针对中文项目
config = ConfigTemplates.chinese_optimized()
```

## ⚙️ 核心机制详解

### 代码片段分类逻辑

解析器根据以下规则对代码片段进行分类：

```python
# 类型判断逻辑
if node_type in class_node_types:
    snippet_type = "class"
elif node_type in function_node_types:
    if inside_class:
        snippet_type = "method"
    else:
        snippet_type = "function"
```

### 关键词提取详解

`key_msg`字段是搜索功能的核心，包含：

1. **中文关键词**: 从代码和注释中提取的中文词汇
2. **英文标识符**: 变量名、函数名、类名等标识符
3. **文件上下文**: 文件名（去除扩展名）

**提取示例**:
```python
# 源代码
class UserManager:
    """用户管理器"""
    
    def get_user_info(self, user_id: int) -> dict:
        """获取用户信息"""
        return {"id": user_id}

# 生成的key_msg包含:
# 中文: ["用户", "管理器", "获取", "信息"]  
# 英文: ["UserManager", "get_user_info", "user_id", "int", "dict", "id"]
# 文件: ["user_manager"] (假设文件名为user_manager.py)
```

### 编码处理机制

支持多种编码格式，处理流程：

```python
def _decode_content(self, raw_bytes, file_path):
    # 1. 优先尝试UTF-8
    try:
        return raw_bytes.decode('utf-8')
    except UnicodeDecodeError:
        # 2. 使用chardet自动检测
        detected = chardet.detect(raw_bytes)
        if detected['confidence'] > 0.7:
            return raw_bytes.decode(detected['encoding'], errors='replace')
        # 3. 返回None，标记解码失败
        return None
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
    metadata: Dict[str, Any]              # 元数据（文件大小等）
    processing_time: float                # 处理时间(秒)
    
    @property
    def is_successful(self) -> bool:      # 是否解析成功
        return self.language is not None and not self.errors
    
    @property
    def suffix(self) -> str:              # 文件后缀
        return Path(self.file_path).suffix[1:]
```

### CodeSnippet 类

```python
@dataclass
class CodeSnippet:
    type: str          # 类型: "function", "class", "method"
    path: str          # 文件路径
    name: str          # 代码片段名称
    code: str          # 完整代码内容
    md5: str           # MD5哈希值（用于去重）
    func_name: str     # 函数完整名称
    args: str          # 参数列表
    class_name: str    # 所属类名（方法专用）
    comment: str       # 关联注释
    key_msg: str       # 搜索关键词
    line_start: int    # 起始行号
    line_end: int      # 结束行号
    metadata: Dict     # 额外元数据
```

**代码片段示例**:
```python
# 输入代码
class Calculator:
    def add(self, a: int, b: int) -> int:
        """执行加法运算"""
        return a + b

# 生成的CodeSnippet
CodeSnippet(
    type="method",
    name="add", 
    func_name="add",
    args="(self, a: int, b: int)",
    class_name="Calculator",
    comment="执行加法运算",
    key_msg="执行 加法 运算 add self int Calculator",
    line_start=2,
    line_end=4,
    # ... 其他字段
)
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
from coderepoindex.parsers import ConfigTemplates

# 最小配置：只解析基本结构，适用于快速浏览
config = ConfigTemplates.minimal()
# 特点：不提取注释、不提取关键词、最大性能

# 性能配置：适用于大型代码库
config = ConfigTemplates.performance() 
# 特点：小缓存、忽略测试文件、限制函数大小

# 详细配置：提取所有信息，适用于代码分析
config = ConfigTemplates.detailed()
# 特点：提取所有内容、包括导入语句和变量

# 中文优化：针对中文项目
config = ConfigTemplates.chinese_optimized()
# 特点：优化中文编码处理、增强中文关键词提取
```

## 🌐 支持的编程语言

| 语言 | 扩展名 | 支持的结构 | Tree-sitter语法 |
|------|--------|------------|-----------------|
| Python | `.py` | 函数、类、方法、异步函数 | `function_definition`, `class_definition` |
| JavaScript | `.js`, `.jsx` | 函数、类、箭头函数、方法 | `function_declaration`, `arrow_function` |
| TypeScript | `.ts`, `.tsx` | 函数、类、接口、方法 | `interface_declaration`, `type_alias` |
| Java | `.java` | 类、方法、构造函数、接口 | `method_declaration`, `constructor_declaration` |
| Go | `.go` | 函数、方法、类型声明 | `function_declaration`, `method_declaration` |
| C | `.c`, `.h` | 函数、结构体 | `function_definition`, `struct_specifier` |
| C++ | `.cpp`, `.cc`, `.cxx`, `.hpp` | 函数、类、结构体 | `class_specifier`, `function_definition` |
| Kotlin | `.kt`, `.kts` | 函数、类、方法 | `function_declaration`, `class_declaration` |
| Lua | `.lua` | 函数 | `function_declaration` |

### 语言特性支持详情

#### Python
- ✅ 普通函数和异步函数
- ✅ 类、方法（实例、类、静态）
- ✅ 装饰器识别
- ✅ 类型注解提取
- ✅ 文档字符串处理

#### JavaScript/TypeScript  
- ✅ ES6+ 语法支持
- ✅ 箭头函数
- ✅ 类和继承
- ✅ 接口声明（TypeScript）
- ✅ 泛型支持（TypeScript）

#### Java
- ✅ 访问修饰符识别
- ✅ 泛型方法
- ✅ 接口和抽象类
- ✅ 注解处理
- ✅ 内部类支持

## 🛠️ 高级功能

### 错误处理与恢复

```python
parser = CodeParser()
result = parser.parse_file("example.py")

# 检查解析结果
if not result.is_successful:
    print("解析失败:")
    for error in result.errors:
        print(f"  - {error}")
        
    # 部分成功的情况
    if result.snippets:
        print(f"但仍提取到 {len(result.snippets)} 个代码片段")
else:
    print(f"解析成功，提取 {len(result.snippets)} 个代码片段")
```

### 性能监控

```python
# 单文件性能监控
result = parser.parse_file("large_file.py")
print(f"处理时间: {result.processing_time:.4f}s")
print(f"文件大小: {result.metadata.get('file_size', 0)} bytes")
print(f"平均速度: {result.metadata['file_size'] / result.processing_time / 1024:.2f} KB/s")

# 批量处理性能统计
results = parser.parse_multiple_files(file_paths)
total_time = sum(r.processing_time for r in results)
total_size = sum(r.metadata.get('file_size', 0) for r in results)
print(f"总处理时间: {total_time:.4f}s")
print(f"总文件大小: {total_size / 1024 / 1024:.2f} MB")
print(f"平均处理速度: {total_size / total_time / 1024 / 1024:.2f} MB/s")
```

### 缓存管理

```python
# 查看缓存状态
parser = CodeParser(max_cache_size=256)
print(f"支持的扩展名: {parser.get_supported_extensions()}")

# 处理大量文件后清除缓存
parser.parse_multiple_files(large_file_list)
parser.clear_cache()  # 释放内存
```

### 自定义过滤

```python
def filter_code_snippets(snippets, min_lines=5, include_types=None):
    """自定义过滤代码片段"""
    if include_types is None:
        include_types = ["function", "method", "class"]
    
    filtered = []
    for snippet in snippets:
        # 按行数过滤
        if snippet.line_end - snippet.line_start + 1 < min_lines:
            continue
        # 按类型过滤  
        if snippet.type not in include_types:
            continue
        # 按关键词过滤（示例：包含特定关键词）
        if "test" in snippet.name.lower():
            continue
        filtered.append(snippet)
    
    return filtered

# 使用示例
result = parser.parse_file("example.py")
important_snippets = filter_code_snippets(
    result.snippets, 
    min_lines=10, 
    include_types=["function", "class"]
)
```

## 🧪 测试和调试

### 运行内置测试

```python
from coderepoindex.parsers.tests import test_all_parsers

# 运行所有语言的测试
test_all_parsers.main()

# 或者运行特定语言测试
from coderepoindex.parsers.tests.test_python_parser import PythonParserTester
tester = PythonParserTester()
tester.run_test()
```

### 调试AST结构

```python
def debug_ast_structure(file_path):
    """调试AST结构的工具函数"""
    parser = CodeParser()
    
    # 获取Tree-sitter解析器
    language = parser._detect_language(Path(file_path))
    tree_parser = parser._get_parser(language)
    
    # 解析文件
    raw_bytes, source_code = parser._read_file_safely(Path(file_path))
    tree = tree_parser.parse(raw_bytes)
    
    def print_ast(node, indent=0):
        text = parser._extract_node_text(node, source_code)[:50].replace('\n', '\\n')
        print('  ' * indent + f'{node.type}: "{text}"')
        for child in node.children:
            print_ast(child, indent + 1)
    
    print_ast(tree.root_node)

# 使用示例
debug_ast_structure("example.py")
```

### 使用示例脚本

```bash
# 运行完整演示
python examples/parser_demo.py

# 解析特定文件并显示详细信息
python -m coderepoindex.parsers.code_parser example.py

# 运行依赖检查
python coderepoindex/parsers/check_dependencies.py

# 运行所有解析器测试
python coderepoindex/parsers/tests/test_all_parsers.py
```

## 🔧 故障排查

### 常见问题解决

#### 1. Tree-sitter版本兼容性
**问题**: `__init__() takes exactly 1 argument (2 given)`
```bash
# 解决方案：降级到兼容版本
pip install tree-sitter==0.21.3 --force-reinstall
```

#### 2. 编码问题
**问题**: 文件编码识别失败
```python
# 解决方案：手动指定编码
parser = CodeParser()
with open("problem_file.py", "r", encoding="gbk") as f:
    content = f.read()
# 然后使用字符串解析功能
```

#### 3. 内存问题
**问题**: 处理大文件时内存不足
```python
# 解决方案：
# 1. 增加文件大小限制检查
# 2. 及时清除缓存
# 3. 使用性能配置

config = ConfigTemplates.performance()
parser = CodeParser(max_cache_size=64)  # 减小缓存
```

#### 4. 解析失败问题
**问题**: 特定文件解析失败
```python
# 调试步骤：
result = parser.parse_file("problem_file.py")
if not result.is_successful:
    print("错误信息:", result.errors)
    print("语言检测:", result.language)
    print("文件大小:", result.metadata.get('file_size'))
```

### 性能调优建议

1. **大型项目处理**:
   ```python
   # 使用性能配置
   config = ConfigTemplates.performance()
   # 增加缓存大小
   parser = CodeParser(max_cache_size=512)
   # 过滤测试文件
   files = [f for f in all_files if not f.endswith('_test.py')]
   ```

2. **内存优化**:
   ```python
   # 分批处理文件
   def process_files_in_batches(files, batch_size=100):
       for i in range(0, len(files), batch_size):
           batch = files[i:i+batch_size]
           results = parser.parse_multiple_files(batch)
           yield results
           parser.clear_cache()  # 释放内存
   ```

3. **并发处理**:
   ```python
   from concurrent.futures import ThreadPoolExecutor
   
   def parse_file_safe(file_path):
       parser = CodeParser()  # 每个线程独立的解析器
       return parser.parse_file(file_path)
   
   with ThreadPoolExecutor(max_workers=4) as executor:
       results = list(executor.map(parse_file_safe, file_paths))
   ```

## 📝 示例输出

### 详细解析结果示例

```
=== 解析结果 ===
文件: src/utils/user_manager.py
语言: python
代码片段数量: 8
处理时间: 0.0156s
文件大小: 2.3 KB
是否成功: True

=== 代码片段详情 ===

片段 1: [class]
  名称: UserManager  
  行数: 12-45
  关键词: UserManager 用户 管理器 类 数据库 操作 user manager database

片段 2: [method]  
  名称: __init__
  所属类: UserManager
  参数: (self, db_connection)
  行数: 15-18
  注释: 初始化用户管理器
  关键词: init 初始化 用户 管理器 self db_connection

片段 3: [method]
  名称: get_user_by_id  
  所属类: UserManager
  参数: (self, user_id: int) -> Optional[User]
  行数: 20-28
  注释: 根据ID获取用户信息
  关键词: get_user_by_id 获取 用户 信息 ID user_id int Optional User

片段 4: [method]
  名称: create_user
  所属类: UserManager  
  参数: (self, username: str, email: str) -> User
  行数: 30-38
  注释: 创建新用户
  关键词: create_user 创建 新用户 username str email User

片段 5: [function]
  名称: validate_email
  参数: (email: str) -> bool  
  行数: 47-52
  注释: 验证邮箱格式
  关键词: validate_email 验证 邮箱 格式 email str bool

=== 统计信息 ===
- 类: 1 个
- 方法: 3 个  
- 函数: 1 个
- 平均每个片段: 6.2 行
- 关键词总数: 35 个
- 中文关键词: 12 个
- 英文关键词: 23 个
```

### 批量处理结果示例

```
=== 批量处理结果 ===
处理文件数: 156
成功: 152 (97.4%)
失败: 4 (2.6%)
总处理时间: 2.347s
平均每文件: 15.0ms

=== 语言分布 ===
Python: 89 文件 (1,234 个代码片段)
JavaScript: 45 文件 (567 个代码片段)  
TypeScript: 18 文件 (234 个代码片段)
Java: 4 文件 (89 个代码片段)

=== 代码片段统计 ===
总代码片段: 2,124
- 函数: 1,245 (58.6%)
- 方法: 678 (31.9%) 
- 类: 201 (9.5%)

=== 性能统计 ===
总文件大小: 15.6 MB
处理速度: 6.64 MB/s
最大单文件: 2.1 MB (config.py)
最慢单文件: 156ms (large_utils.py)
```

## 🔄 优化内容

相比原始版本，此优化版本包含以下改进：

### 1. 架构优化
- ✅ 使用 `dataclass` 替代 `TypedDict`，提供更好的类型检查
- ✅ 引入枚举类型，提高代码可维护性  
- ✅ 模块化设计，分离配置、测试和核心逻辑
- ✅ 统一的错误处理机制

### 2. 性能优化  
- ✅ LRU缓存机制，避免重复创建解析器
- ✅ 优化文件读取和编码检测流程
- ✅ 引入计时装饰器，便于性能分析
- ✅ 线程安全的解析器管理
- ✅ 内存使用优化

### 3. 错误处理
- ✅ 自定义异常类型体系
- ✅ 优雅的错误恢复机制  
- ✅ 详细的错误信息记录和分类
- ✅ 部分失败时的容错处理

### 4. 功能增强
- ✅ 支持更多编程语言（9种主流语言）
- ✅ 改进的关键词提取算法
- ✅ 灵活的配置系统和预设模板
- ✅ 批量处理和并发支持
- ✅ Python函数/方法正确区分

### 5. 开发体验
- ✅ 完整的类型注解
- ✅ 丰富的文档和示例
- ✅ 内置测试套件，覆盖所有语言
- ✅ 便利函数和模块级API  
- ✅ 调试工具和故障排查指南

### 6. 日志和监控
- ✅ 使用 loguru 替代标准 logging
- ✅ 支持中文日志信息  
- ✅ 性能监控和统计
- ✅ 可配置的日志级别

## 🤝 贡献指南

欢迎贡献代码！请确保：

1. **代码质量**
   - 遵循现有的代码风格
   - 添加完整的类型注解
   - 使用中文注释和文档字符串

2. **测试要求**  
   - 为新功能添加测试用例
   - 确保所有现有测试通过
   - 测试覆盖边界情况

3. **文档更新**
   - 更新相关文档
   - 添加使用示例
   - 更新配置说明

4. **性能考虑**
   - 避免引入性能回归
   - 优化内存使用
   - 考虑大文件处理场景

### 开发设置

```bash
# 克隆项目
git clone <repository-url>
cd CodeRepoIndex

# 安装开发依赖
pip install -r requirements-dev.txt

# 运行测试
python -m pytest coderepoindex/parsers/tests/

# 运行代码质量检查
flake8 coderepoindex/parsers/
mypy coderepoindex/parsers/
```

## 📄 许可证

MIT License - 详见项目根目录的 LICENSE 文件。

---

**注意**: 此模块需要安装 `tree-sitter-languages` 包才能正常工作。如果遇到语言解析器不可用的问题，请参考[故障排查](#🔧-故障排查)部分的解决方案。

**维护状态**: 积极维护中 🟢 | **最后更新**: 2024年6月 | **版本**: 1.2.0 