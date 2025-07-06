# CodeRepoIndex 配置中心

CodeRepoIndex 提供了强大的配置中心，支持多种配置方式，让您能够灵活地管理API密钥、存储设置、模型参数等。

## 快速开始

### 1. 环境变量配置 (推荐)

最简单的配置方式是使用环境变量：

```bash
# 必需的配置
export CODEREPO_API_KEY="your-api-key"
export CODEREPO_BASE_URL="https://dashscope-intl.aliyuncs.com/compatible-mode/v1"

# 可选的配置
export CODEREPO_STORAGE_PATH="./storage"
export CODEREPO_LOG_LEVEL="INFO"
export CODEREPO_VECTOR_BACKEND="memory"
```

然后在代码中：

```python
from coderepoindex import CodeIndexer, CodeSearcher, load_config

# 自动从环境变量加载配置
config = load_config()

# 使用配置创建索引器和搜索器
indexer = CodeIndexer(config=config)
searcher = CodeSearcher(config=config)
```

### 2. 直接传递参数

```python
from coderepoindex import CodeIndexer, CodeSearcher

# 直接传递配置参数
indexer = CodeIndexer(
    api_key="your-api-key",
    base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
    storage_backend="local",
    vector_backend="memory"
)

searcher = CodeSearcher(
    api_key="your-api-key", 
    base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
    storage_backend="local",
    vector_backend="memory"
)
```

### 3. 配置文件

创建 `config.json` 文件：

```json
{
  "project_name": "CodeRepoIndex",
  "log_level": "INFO",
  "model": {
    "api_key": "your-api-key",
    "base_url": "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
  },
  "storage": {
    "storage_backend": "local",
    "vector_backend": "memory",
    "base_path": "./storage"
  },
  "embedding": {
    "api_key": "your-api-key",
    "base_url": "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
    "model_name": "text-embedding-v3"
  }
}
```

在代码中加载：

```python
from coderepoindex import load_config, CodeIndexer, CodeSearcher

# 从配置文件加载
config = load_config("config.json")

indexer = CodeIndexer(config=config)
searcher = CodeSearcher(config=config)
```

## 配置模板

CodeRepoIndex 提供了预定义的配置模板：

### 开发环境

```python
from coderepoindex import get_config_template, CodeIndexer

# 使用开发模板
config = get_config_template("development")
config.embedding.api_key = "your-api-key"
config.embedding.base_url = "your-base-url"

indexer = CodeIndexer(config=config)
```

### 生产环境

```python
# 使用生产模板
config = get_config_template("production")
config.embedding.api_key = "your-api-key"
config.embedding.base_url = "your-base-url"

indexer = CodeIndexer(config=config)
```

### 最小配置

```python
# 使用最小模板
config = get_config_template("minimal")
config.embedding.api_key = "your-api-key"
config.embedding.base_url = "your-base-url"

indexer = CodeIndexer(config=config)
```

## 配置项说明

### 模型配置 (ModelConfig)

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `api_key` | API密钥 | None |
| `base_url` | API基础URL | None |
| `llm_model_name` | LLM模型名称 | "qwen-plus" |
| `embedding_model_name` | 嵌入模型名称 | "text-embedding-v3" |
| `timeout` | 请求超时时间(秒) | 30.0 |

### 存储配置 (StorageConfig)

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `storage_backend` | 存储后端类型 | "local" |
| `vector_backend` | 向量存储后端 | "memory" |
| `base_path` | 存储基础路径 | "./storage" |
| `cache_enabled` | 是否启用缓存 | true |
| `cache_size` | 缓存大小 | 1000 |

### 嵌入配置 (EmbeddingConfig)

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `provider_type` | 提供商类型 | "api" |
| `model_name` | 模型名称 | "text-embedding-v3" |
| `api_key` | API密钥 | None |
| `base_url` | API基础URL | None |
| `batch_size` | 批处理大小 | 32 |
| `timeout` | 请求超时时间(秒) | 30.0 |

## 动态配置更新

您可以在运行时更新配置：

```python
from coderepoindex import update_config, get_current_config

# 更新全局配置
update_config(
    api_key="new-api-key",
    base_url="new-base-url",
    storage_backend="local",
    vector_backend="chromadb"
)

# 获取当前配置
current_config = get_current_config()
print(f"当前API密钥: {current_config.embedding.api_key}")
```

## 环境变量参考

CodeRepoIndex 支持以下环境变量：

| 环境变量 | 说明 | 映射的配置项 |
|----------|------|-------------|
| `CODEREPO_API_KEY` 或 `OPENAI_API_KEY` | API密钥 | `model.api_key`, `embedding.api_key` |
| `CODEREPO_BASE_URL` 或 `OPENAI_BASE_URL` | API基础URL | `model.base_url`, `embedding.base_url` |
| `CODEREPO_LLM_MODEL` | LLM模型名称 | `model.llm_model_name` |
| `CODEREPO_EMBEDDING_MODEL` | 嵌入模型名称 | `model.embedding_model_name`, `embedding.model_name` |
| `CODEREPO_STORAGE_PATH` | 存储路径 | `storage.base_path` |
| `CODEREPO_STORAGE_BACKEND` | 存储后端 | `storage.storage_backend` |
| `CODEREPO_VECTOR_BACKEND` | 向量后端 | `storage.vector_backend` |
| `CODEREPO_LOG_LEVEL` | 日志级别 | `log_level` |

## 最佳实践

### 1. 安全性

- **不要在代码中硬编码API密钥**
- 使用环境变量或安全的配置文件
- 在版本控制中排除包含敏感信息的配置文件

```bash
# .gitignore
config.json
config.yaml
.env
```

### 2. 不同环境的配置

为不同的环境使用不同的配置：

```python
import os
from coderepoindex import get_config_template

# 根据环境选择配置模板
env = os.getenv("ENVIRONMENT", "development")
config = get_config_template(env)

# 设置API密钥
config.embedding.api_key = os.getenv("CODEREPO_API_KEY")
config.embedding.base_url = os.getenv("CODEREPO_BASE_URL")
```

### 3. 性能优化

根据您的使用场景选择合适的配置：

```python
# 小规模项目
config = get_config_template("minimal")

# 中等规模项目
config = get_config_template("development")

# 大规模生产环境
config = get_config_template("production")
config.storage.vector_backend = "chromadb"  # 更好的向量存储
config.embedding.batch_size = 64           # 更大的批处理
```

### 4. 配置验证

在启动应用前验证配置：

```python
from coderepoindex import load_config

try:
    config = load_config()
    
    # 验证必需的配置
    if not config.embedding.api_key:
        raise ValueError("API密钥未设置")
    
    if not config.embedding.base_url:
        raise ValueError("API基础URL未设置")
    
    print("✅ 配置验证通过")
    
except Exception as e:
    print(f"❌ 配置验证失败: {e}")
    exit(1)
```

## 故障排除

### 常见问题

1. **配置加载失败**
   - 检查环境变量是否正确设置
   - 验证配置文件格式是否正确
   - 确保配置文件路径正确

2. **API调用失败**
   - 验证API密钥是否有效
   - 检查API基础URL是否正确
   - 确认网络连接正常

3. **存储错误**
   - 检查存储路径权限
   - 确保磁盘空间充足
   - 验证存储后端配置

### 调试技巧

启用调试日志：

```python
from coderepoindex import load_config

# 加载配置并设置调试日志
config = load_config(log_level="DEBUG")
```

或者通过环境变量：

```bash
export CODEREPO_LOG_LEVEL="DEBUG"
```

这将输出详细的配置加载和使用信息，帮助您诊断问题。 