# CodeRepoIndex 配置中心

CodeRepoIndex 提供了强大的配置中心，支持多种配置方式，让您能够灵活地管理API密钥、存储设置、模型参数等。

## 配置管理

CodeRepoIndex 提供了灵活的配置管理系统，支持分离配置 LLM 模型和 Embedding 模型的 API 密钥和基础 URL。

## 配置结构

### 新的分离式配置结构

从 v1.0 开始，CodeRepoIndex 支持分别配置 LLM 模型和 Embedding 模型：

```json
{
  "project_name": "CodeRepoIndex",
  "version": "1.0.0",
  "log_level": "INFO",
  
  "llm": {
    "provider_type": "api",
    "model_name": "qwen-plus",
    "api_key": "your-llm-api-key",
    "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "timeout": 30.0,
    "extra_params": {
      "temperature": 0.7,
      "max_tokens": 2000
    }
  },
  
  "embedding": {
    "provider_type": "api",
    "model_name": "text-embedding-v3", 
    "api_key": "your-embedding-api-key",
    "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "timeout": 30.0,
    "batch_size": 32,
    "extra_params": {}
  },
  
  "storage": {
    "storage_backend": "local",
    "vector_backend": "memory",
    "base_path": "./storage",
    "cache_enabled": true,
    "cache_size": 1000,
    "auto_backup": true,
    "backup_interval": 3600
  }
}
```

### 配置项说明

#### LLM 配置 (`llm`)
- `provider_type`: 提供商类型 (默认: "api")
- `model_name`: LLM 模型名称 (如: "qwen-plus", "gpt-4")
- `api_key`: LLM API 密钥
- `base_url`: LLM API 基础 URL
- `timeout`: 请求超时时间 (秒)
- `extra_params`: 额外参数 (如 temperature, max_tokens)

#### Embedding 配置 (`embedding`)
- `provider_type`: 提供商类型 (默认: "api")
- `model_name`: Embedding 模型名称 (如: "text-embedding-v3")
- `api_key`: Embedding API 密钥
- `base_url`: Embedding API 基础 URL
- `timeout`: 请求超时时间 (秒)
- `batch_size`: 批处理大小
- `max_tokens`: 最大 token 数量
- `extra_params`: 额外参数

#### 存储配置 (`storage`)
- `storage_backend`: 存储后端 ("local", "s3", "azure")
- `vector_backend`: 向量存储后端 ("memory", "chromadb", "faiss")
- `base_path`: 基础存储路径
- `cache_enabled`: 是否启用缓存
- `cache_size`: 缓存大小
- `auto_backup`: 是否自动备份
- `backup_interval`: 备份间隔 (秒)

## 配置方式

### 1. 环境变量配置（推荐）

#### 分离式环境变量
```bash
# LLM 配置
export CODEREPO_LLM_API_KEY="your-llm-api-key"
export CODEREPO_LLM_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"
export CODEREPO_LLM_MODEL="qwen-plus"
export CODEREPO_LLM_PROVIDER="api"

# Embedding 配置
export CODEREPO_EMBEDDING_API_KEY="your-embedding-api-key"
export CODEREPO_EMBEDDING_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"
export CODEREPO_EMBEDDING_MODEL="text-embedding-v3"
export CODEREPO_EMBEDDING_PROVIDER="api"

# 存储配置
export CODEREPO_STORAGE_PATH="./storage"
export CODEREPO_STORAGE_BACKEND="local"
export CODEREPO_VECTOR_BACKEND="memory"

# 基础配置
export CODEREPO_PROJECT_NAME="MyProject"
export CODEREPO_LOG_LEVEL="INFO"
```

#### 兼容性环境变量（统一配置）
```bash
# 如果 LLM 和 Embedding 使用相同的 API
export CODEREPO_API_KEY="your-unified-api-key"
export CODEREPO_BASE_URL="https://api.example.com/v1"
```

### 2. 配置文件

#### 创建配置文件
```python
from coderepoindex.config import load_config, save_config

# 加载并修改配置
config = load_config()
config.llm.api_key = "your-llm-key"
config.embedding.api_key = "your-embedding-key"

# 保存到文件
save_config("coderepoindex.json")
```

#### 使用配置文件
```python
from coderepoindex.config import load_config

# 自动查找 coderepoindex.json 或 config.json
config = load_config()

# 或指定文件路径
config = load_config("my_config.json")
```

### 3. 字典配置

```python
from coderepoindex.config import load_config

config_dict = {
    "llm": {
        "api_key": "llm-key",
        "base_url": "https://llm-api.example.com",
        "model_name": "gpt-4"
    },
    "embedding": {
        "api_key": "embedding-key",
        "base_url": "https://embedding-api.example.com", 
        "model_name": "text-embedding-ada-002"
    },
    "storage": {
        "base_path": "./custom_storage"
    }
}

config = load_config(config_dict=config_dict)
```

### 4. 直接传参

```python
from coderepoindex.config import load_config

config = load_config(
    llm_api_key="llm-key",
    llm_base_url="https://llm-api.example.com",
    llm_model_name="qwen-plus",
    embedding_api_key="embedding-key",
    embedding_base_url="https://embedding-api.example.com",
    embedding_model_name="text-embedding-v3",
    storage_base_path="./storage"
)
```

### 5. 配置模板

```python
from coderepoindex.config import get_config_template, load_config

# 使用预定义模板
config = get_config_template("production")

# 修改配置
config.llm.api_key = "your-llm-key"
config.embedding.api_key = "your-embedding-key"

# 应用配置
from coderepoindex.config import ConfigManager
manager = ConfigManager()
manager.load_config(config_dict=config.__dict__)
```

可用模板：
- `default`: 默认配置
- `production`: 生产环境配置
- `development`: 开发环境配置
- `minimal`: 最小配置

## 配置优先级

配置加载的优先级从高到低：

1. **直接传参** (`load_config(llm_api_key="...")`)
2. **环境变量** (`CODEREPO_LLM_API_KEY`)
3. **字典配置** (`config_dict`)
4. **配置文件** (`coderepoindex.json`, `config.json`)
5. **默认值**

## 使用示例

### 基本使用

```python
from coderepoindex.config import load_config
from coderepoindex.core import CodeIndexer, CodeSearcher

# 加载配置
config = load_config()

# 创建索引器和搜索器
indexer = CodeIndexer()  # 自动使用当前配置
searcher = CodeSearcher()  # 自动使用当前配置
```

### 不同服务使用不同 API

```python
from coderepoindex.config import load_config

# 配置不同的 API 服务
config = load_config(
    llm_api_key="openai-key",
    llm_base_url="https://api.openai.com/v1",
    llm_model_name="gpt-4",
    
    embedding_api_key="cohere-key", 
    embedding_base_url="https://api.cohere.ai/v1",
    embedding_model_name="embed-english-v3.0"
)
```

### 动态配置更新

```python
from coderepoindex.config import ConfigManager

manager = ConfigManager()

# 运行时更新配置
manager.update_config(
    llm_model_name="qwen-turbo",
    embedding_batch_size=64,
    storage_cache_size=2000
)
```

## 兼容性

为了保持向后兼容性，系统仍然支持旧的统一配置方式：

```python
# 旧方式仍然有效
config = load_config(
    api_key="unified-key",
    base_url="https://api.example.com"
)

# 会自动应用到 LLM 和 Embedding 配置
print(config.llm.api_key)        # "unified-key"
print(config.embedding.api_key)  # "unified-key"
```

## 最佳实践

1. **生产环境**: 使用环境变量配置，避免在代码中硬编码密钥
2. **开发环境**: 使用配置文件，便于版本控制和团队协作
3. **测试环境**: 使用配置模板，快速切换不同配置
4. **安全考虑**: 
   - 不要将 API 密钥提交到版本控制
   - 使用 `.env` 文件管理环境变量
   - 在 `.gitignore` 中排除配置文件
5. **性能优化**:
   - 根据使用场景选择合适的向量存储后端
   - 调整批处理大小以优化内存使用
   - 启用缓存以提高搜索性能

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