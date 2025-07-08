# 贡献指南

感谢您对 CodeRepoIndex 项目的关注！我们欢迎所有形式的贡献。

## 如何贡献

### 报告问题

如果您发现了 bug 或有功能建议，请通过 [GitHub Issues](https://github.com/XingYu-Zhong/CodeRepoIndex/issues) 报告。

提交 issue 时，请：
- 使用清晰、描述性的标题
- 详细描述问题或功能请求
- 提供复现步骤（如果是 bug）
- 包含相关的环境信息

### 代码贡献

1. **Fork 项目**
   ```bash
   git clone https://github.com/XingYu-Zhong/CodeRepoIndex.git
   cd CodeRepoIndex
   ```

2. **创建开发环境**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -e ".[dev]"
   ```

3. **安装预提交钩子**
   ```bash
   pre-commit install
   ```

4. **创建功能分支**
   ```bash
   git checkout -b feature/your-feature-name
   ```

5. **编写代码**
   - 遵循项目的编码风格
   - 为新功能添加测试
   - 更新相关文档

6. **运行测试**
   ```bash
   pytest tests/
   ```

7. **检查代码质量**
   ```bash
   black coderepoindex/
   isort coderepoindex/
   flake8 coderepoindex/
   mypy coderepoindex/
   ```

8. **提交更改**
   ```bash
   git add .
   git commit -m "feat: 添加新功能描述"
   ```

9. **推送分支**
   ```bash
   git push origin feature/your-feature-name
   ```

10. **创建 Pull Request**

## 开发规范

### 代码风格

- 使用 [Black](https://black.readthedocs.io/) 进行代码格式化
- 使用 [isort](https://pycqa.github.io/isort/) 进行导入排序
- 遵循 [PEP 8](https://www.python.org/dev/peps/pep-0008/) 编码规范
- 使用类型注解（Type Hints）

### 提交信息规范

我们使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

- `feat:` 新功能
- `fix:` 修复 bug
- `docs:` 文档更新
- `style:` 代码风格调整
- `refactor:` 代码重构
- `test:` 添加或修改测试
- `chore:` 构建或辅助工具的变动

示例：
```
feat: 添加向量相似度搜索功能
fix: 修复代码解析器在处理复杂语法时的问题
docs: 更新 API 文档
```

### 测试

- 所有新功能都必须有相应的测试
- 确保测试覆盖率不低于 80%
- 运行所有测试并确保通过

### 文档

- 为公共 API 添加 docstring
- 更新相关的 README 或文档
- 使用中文注释和文档

## 项目结构

```
CodeRepoIndex/
├── coderepoindex/          # 主要源代码
│   ├── core/              # 核心功能模块 (Indexer, Searcher)
│   ├── parsers/           # 代码解析器 (CodeParser, DirectoryParser)
│   ├── embeddings/        # 向量嵌入与存储模块
│   ├── repository/        # 仓库获取模块
│   ├── models/            # 外部模型接口
│   ├── config/            # 配置管理
│   └── cli.py             # 命令行接口
├── tests/                 # 测试文件
│   ├── unit/              # 单元测试
│   └── integration/       # 集成测试
├── docs/                  # 文档
├── examples/              # 示例代码
└── scripts/               # 脚本文件
```

## 开发流程

1. 从 issue 或功能需求开始
2. 创建功能分支
3. 编写代码和测试
4. 运行代码质量检查
5. 提交 Pull Request
6. 代码审查
7. 合并到主分支

## 获得帮助

如果您在贡献过程中遇到问题，可以：

- 查看现有的 [Issues](https://github.com/XingYu-Zhong/CodeRepoIndex/issues)
- 创建新的 issue 寻求帮助
- 联系维护者：zhongxingyuemail@gmail.com

## 行为准则

请遵循我们的 [行为准则](CODE_OF_CONDUCT.md)，营造一个友好、包容的社区环境。

感谢您的贡献！🎉 