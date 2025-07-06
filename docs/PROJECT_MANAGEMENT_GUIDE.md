# CodeRepoIndex 多项目管理指南

## 概述

CodeRepoIndex 现在支持完整的多项目管理功能，确保不同项目的代码索引和搜索数据完全隔离。每个项目都有唯一的标识符，可以独立管理和搜索。

## 核心功能

### 1. 项目唯一标识
- 每个项目都有唯一的 `project_id`（即 `repository_id`）
- 可以手动指定ID，也可以基于仓库URL或路径自动生成
- 所有的代码块、向量嵌入、元数据都通过此ID进行隔离

### 2. 项目信息管理
```python
from coderepoindex.core import create_project_manager

# 创建项目管理器
pm = create_project_manager()

with pm:
    # 创建项目
    project = pm.create_project(
        name="我的项目",
        description="项目描述",
        local_path="/path/to/project",
        repository_url="https://github.com/user/repo"
    )
    
    # 列出所有项目
    projects = pm.list_projects()
    
    # 获取项目信息
    project_info = pm.get_project("project_id")
```

### 3. 当前项目管理
```python
# 设置当前活跃项目
pm.set_current_project("project_id")

# 获取当前项目
current = pm.get_current_project()

# 在当前项目中搜索
results = pm.search_in_project("查询内容")
```

### 4. 项目统计信息
```python
# 获取项目统计
stats = pm.get_project_stats("project_id")
print(f"代码块: {stats['total_blocks']}")
print(f"文件数: {stats['total_files']}")
print(f"语言分布: {stats['language_distribution']}")
```

### 5. 项目删除
```python
# 删除项目及其所有数据
pm.delete_project("project_id", delete_data=True)
```

## 数据隔离机制

### 1. 存储层面
- **代码块存储**: SQLite中的 `repository_id` 字段建立索引
- **向量存储**: 每个向量都包含项目元数据
- **元数据存储**: 项目信息独立存储

### 2. 查询层面
```python
# 所有查询都支持项目过滤
blocks = storage.query_code_blocks(repository_id="project_id")
vectors = storage.search_vectors(metadata_filter={"repository_id": "project_id"})
```

### 3. 搜索层面
```python
from coderepoindex.core import create_code_searcher

searcher = create_code_searcher()
with searcher:
    # 在指定项目中搜索
    results = searcher.search(
        query="函数定义",
        repository_id="project_id"  # 项目隔离
    )
```

## 使用场景

### 1. 多仓库管理
```python
# 管理多个Git仓库
pm.create_project(
    name="前端项目",
    repository_url="https://github.com/company/frontend"
)

pm.create_project(
    name="后端项目", 
    repository_url="https://github.com/company/backend"
)
```

### 2. 版本分支管理
```python
# 同一仓库的不同分支
pm.create_project(
    name="主分支",
    repository_url="https://github.com/user/repo",
    project_id="repo_main"
)

pm.create_project(
    name="开发分支",
    repository_url="https://github.com/user/repo",
    project_id="repo_dev"
)
```

### 3. 本地项目管理
```python
# 管理本地项目
pm.create_project(
    name="私人项目",
    local_path="/home/user/my_project"
)
```

## 最佳实践

### 1. 项目命名
- 使用描述性的项目名称
- 添加详细的项目描述
- 为不同版本使用不同的project_id

### 2. 数据管理
- 定期查看项目统计信息
- 及时删除不需要的项目数据
- 备份重要项目的索引数据

### 3. 搜索优化
- 在搜索时明确指定项目范围
- 利用当前项目机制提高搜索效率
- 根据项目特点调整搜索参数

## API 参考

### ProjectManager 类
```python
class ProjectManager:
    def create_project(name, description="", local_path="", repository_url="", project_id=None) -> ProjectInfo
    def get_project(project_id: str) -> Optional[ProjectInfo]
    def list_projects() -> List[ProjectInfo]
    def delete_project(project_id: str, delete_data: bool = True) -> bool
    def set_current_project(project_id: str) -> bool
    def get_current_project() -> Optional[ProjectInfo]
    def get_project_stats(project_id: str) -> Dict[str, Any]
    def search_in_project(query: str, project_id: Optional[str] = None) -> List[Any]
```

### ProjectInfo 类
```python
class ProjectInfo:
    project_id: str           # 项目唯一标识
    name: str                # 项目名称
    description: str         # 项目描述
    local_path: str          # 本地路径
    repository_url: str      # 仓库URL
    created_at: datetime     # 创建时间
    last_indexed_at: datetime # 最后索引时间
```

## 演示脚本

运行项目管理演示：
```bash
python project_management_demo.py
```

这个脚本会演示：
- 项目创建和管理
- 项目切换和数据隔离
- 项目统计和搜索
- 完整的项目生命周期

## 与现有功能的集成

### 1. 代码索引器
```python
from coderepoindex.core import create_code_indexer

indexer = create_code_indexer()
with indexer:
    # 索引时会自动设置repository_id
    stats = indexer.index_repository(repo_config)
```

### 2. 代码搜索器
```python
from coderepoindex.core import create_code_searcher

searcher = create_code_searcher()  
with searcher:
    # 搜索支持项目过滤
    results = searcher.search(
        query="查询内容",
        repository_id="project_id"
    )
```

## 注意事项

1. **项目ID唯一性**: 确保每个项目都有唯一的ID
2. **数据一致性**: 删除项目时建议同时删除相关数据
3. **性能考虑**: 大量项目时建议定期清理不用的项目
4. **备份重要性**: 重要项目的索引数据建议定期备份

通过这个多项目管理系统，你现在可以：
- ✅ 在同一个系统中管理多个代码项目
- ✅ 确保不同项目的数据完全隔离  
- ✅ 方便地在项目间切换和搜索
- ✅ 获得项目级别的统计和管理功能 