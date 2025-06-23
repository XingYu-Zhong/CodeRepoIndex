# 代码解析器测试套件

本目录包含了针对所有支持编程语言的代码解析器测试脚本。

## 支持的编程语言

- **Python** - `test_python_parser.py`
- **JavaScript** - `test_javascript_parser.py` 
- **TypeScript** - `test_typescript_parser.py`
- **Go** - `test_go_parser.py`
- **Java** - `test_java_parser.py`
- **C** - `test_c_parser.py`
- **C++** - `test_cpp_parser.py`
- **Kotlin** - `test_kotlin_parser.py`
- **Lua** - `test_lua_parser.py`

## 使用方法

### 运行所有测试

```bash
# 运行所有语言的解析器测试
python tests/test_all_parsers.py

# 或者
cd tests && python test_all_parsers.py
```

### 运行特定语言测试

```bash
# 运行特定语言的测试
python tests/test_all_parsers.py --language Python

# 或者直接运行对应的测试文件
python tests/test_python_parser.py
```

### 列出支持的语言

```bash
python tests/test_all_parsers.py --list
```

## 测试内容

每个语言的测试脚本都包含：

1. **完整的示例代码** - 包含该语言的典型特性和语法结构
2. **解析功能测试** - 验证代码解析器能正确识别和提取代码结构
3. **结果分析** - 显示解析出的类、函数、方法等信息
4. **性能测试** - 测量解析所需的时间
5. **错误处理** - 测试解析失败时的错误信息

## 测试示例代码特性

### Python
- 类和继承
- 装饰器
- 异步函数
- 上下文管理器
- 元类
- 数据类

### JavaScript
- ES6+ 语法
- 类和继承
- 箭头函数
- 异步/await
- React 组件
- 模块导入/导出

### TypeScript
- 类型注解
- 接口和泛型
- 装饰器
- 抽象类
- 命名空间

### Go
- 结构体和方法
- 接口
- 协程和通道
- 包管理
- 错误处理

### Java
- 类和继承
- 接口实现
- 注解
- 泛型
- 枚举
- Spring 注解

### C
- 结构体
- 函数指针
- 宏定义
- 内存管理
- 多线程

### C++
- 类和继承
- 模板
- STL 容器
- 智能指针
- 命名空间
- 现代C++特性

### Kotlin
- 数据类
- 扩展函数
- 协程
- 密封类
- 伴生对象

### Lua
- 函数和闭包
- 表和元表
- 协程
- 模块系统
- 面向对象编程

## 输出示例

运行测试后会显示类似以下的信息：

```
=== Python解析测试 ===
语言: python
代码片段数量: 25
处理时间: 0.0234s
是否成功: True

发现的类: 6
  - Person (行 45-49)
  - Animal (行 52-80)
  - Dog (行 83-112)
  - Cat (行 115-128)

发现的函数/方法: 19
  - __post_init__(self) (行 47-49)
  - __init__(self, name: str, species: str) (行 55-58)
  - age(self) -> int (行 61-63)
  - make_sound(self) -> str (行 73-75)
```

## 依赖要求

确保安装了必要的依赖：

```bash
pip install loguru tree-sitter tree-sitter-languages
```

## 故障排除

如果遇到解析失败的情况：

1. 检查是否安装了 `tree-sitter-languages`
2. 确保代码解析器模块路径正确
3. 查看错误日志了解具体失败原因

## 扩展测试

要添加新的测试用例：

1. 在相应的测试文件中修改示例代码
2. 或者创建新的测试方法
3. 运行测试验证新功能 