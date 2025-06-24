# 目录解析器使用说明

## 概述

新增的目录解析器 (`DirectoryParser`) 提供了处理整个代码仓库目录的能力，满足了以下核心需求：

✅ **直接处理文件夹路径** - 提供 `parse_directory()` 函数  
✅ **目录信息记录** - CodeSnippet 包含完整的目录和文件信息  
✅ **全文件处理** - 递归处理目录下所有文件  
✅ **智能文件过滤** - 内置常见忽略文件列表  
✅ **通用切割策略** - 对不支持的文件进行文本切割  
✅ **统一片段格式** - 用 type 字段区分不同类型的代码片段  

## 快速开始

```python
from coderepoindex.parsers import parse_directory, create_directory_config

# 基础用法
result = parse_directory("/path/to/repository")

# 自定义配置
config = create_directory_config(
    chunk_size=512,           # 文本切割大小
    max_depth=5,              # 最大递归深度
    only_extensions={'py', 'js', 'md'}  # 只处理特定扩展名
)
result = parse_directory("/path/to/repository", config)

# 查看结果
print(f"处理了 {result.processed_files} 个文件")
print(f"生成了 {len(result.snippets)} 个代码片段")

# 检查不同类型的片段
for snippet in result.snippets:
    print(f"{snippet.type}: {snippet.path} ({snippet.filename})")
```

## 片段类型

新的解析器支持以下代码片段类型：

- `code_function` - 代码函数
- `code_class` - 代码类  
- `code_method` - 代码方法
- `text_chunk` - 文本切片
- `config_file` - 配置文件
- `documentation` - 文档文件
- `binary_file` - 二进制文件记录

## 忽略文件列表

默认忽略以下文件和目录：

**Git 相关**: `.git`, `.gitignore`, `.gitmodules`  
**编辑器**: `.vscode`, `.idea`, `*.swp`, `.DS_Store`  
**CI/CD**: `.github`, `.travis.yml`, `.pre-commit-config.yaml`  
**依赖管理**: `node_modules`, `__pycache__`, `*.pyc`, `venv`  
**构建产物**: `build`, `dist`, `target`, `*.min.js`  
**媒体文件**: `*.jpg`, `*.png`, `*.mp4`, `*.pdf`  

## 配置选项

主要配置参数：

```python
config = DirectoryConfig(
    # 文本切割
    chunk_size=512,           # 文本切割大小（字符数）
    chunk_overlap=50,         # 切片重叠大小
    min_chunk_size=100,       # 最小切片大小
    
    # 目录遍历
    max_depth=10,             # 最大递归深度
    max_files=10000,          # 最大处理文件数
    follow_symlinks=False,    # 是否跟随符号链接
    
    # 文件过滤
    ignore_patterns=[...],    # 忽略模式列表
    only_extensions=set(),    # 只处理的扩展名（None=全部）
    
    # 内容处理
    extract_text_files=True,      # 处理文本文件
    extract_config_files=True,    # 处理配置文件
    extract_documentation=True,   # 处理文档文件
    record_binary_files=False,    # 记录二进制文件
    
    # 目录结构
    include_directory_structure=True  # 包含目录结构信息
)
```

## CodeSnippet 字段说明

新的 CodeSnippet 包含以下字段：

```python
@dataclass
class CodeSnippet:
    # 基础信息
    type: str              # 片段类型
    path: str              # 文件相对路径
    name: str              # 片段名称
    code: str              # 代码内容
    
    # 目录和文件信息（新增）
    directory: str         # 所在目录
    filename: str          # 文件名
    file_type: str         # 文件类型：code/text/binary
    language: str          # 编程语言
    
    # 代码结构信息
    func_name: str         # 函数名
    class_name: str        # 类名
    line_start: int        # 起始行号
    line_end: int          # 结束行号
    
    # 扩展信息
    metadata: Dict[str, Any]  # 扩展元数据
```

## 示例输出

处理结果示例：

```
解析结果:
- 根目录: /path/to/project
- 总文件数: 42
- 已处理文件数: 38
- 代码文件数: 25
- 文本文件数: 13
- 生成片段数: 156

片段类型统计:
- code_function: 45
- code_class: 12
- text_chunk: 89
- documentation: 10
```

## 性能优化

- 使用文件大小和扩展名进行预过滤
- 支持递归深度限制避免过深遍历
- 提供文件数量限制防止处理过多文件
- 智能文本切割避免过大片段
- 缓存机制减少重复解析

更多详细示例请查看 `examples/directory_parser_demo.py`。 