from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .config_manager import CodeRepoConfig

"""
默认配置定义

定义CodeRepoIndex项目的默认配置值。
"""

from .config_manager import CodeRepoConfig, ModelConfig, StorageConfig, EmbeddingConfig, LLMConfig


# 默认LLM配置
DEFAULT_LLM_CONFIG = LLMConfig(
    provider_type="api",
    model_name="qwen-plus",
    api_key=None,
    base_url=None,
    timeout=30.0,
    extra_params={}
)

# 默认嵌入配置
DEFAULT_EMBEDDING_CONFIG = EmbeddingConfig(
    provider_type="api",
    model_name="text-embedding-v3",
    api_key=None,
    base_url=None,
    max_tokens=None,
    timeout=30.0,
    batch_size=32,
    extra_params={}
)

# 默认模型配置（兼容性保留）
DEFAULT_MODEL_CONFIG = ModelConfig(
    llm_provider_type="api",
    llm_model_name="qwen-plus",
    embedding_provider_type="api", 
    embedding_model_name="text-embedding-v3",
    api_key=None,
    base_url=None,
    timeout=30.0,
    extra_params={}
)

# 默认存储配置
DEFAULT_STORAGE_CONFIG = StorageConfig(
    storage_backend="local",
    vector_backend="memory",
    base_path="./storage",
    cache_enabled=True,
    cache_size=1000,
    auto_backup=True,
    backup_interval=3600,
    extra_params={}
)

# 默认项目配置
DEFAULT_CONFIG = CodeRepoConfig(
    project_name="CodeRepoIndex",
    version="1.0.0",
    log_level="INFO",
    llm=DEFAULT_LLM_CONFIG,
    embedding=DEFAULT_EMBEDDING_CONFIG,
    storage=DEFAULT_STORAGE_CONFIG,
    model=DEFAULT_MODEL_CONFIG,
    extra_config={}
)


# 配置模板
CONFIG_TEMPLATES = {
    "default": DEFAULT_CONFIG,
    "production": CodeRepoConfig(
        project_name="CodeRepoIndex",
        version="1.0.0",
        log_level="WARNING",
        llm=LLMConfig(
            provider_type="api",
            model_name="qwen-plus",
            timeout=60.0
        ),
        embedding=EmbeddingConfig(
            provider_type="api",
            model_name="text-embedding-v3",
            timeout=60.0,
            batch_size=64
        ),
        storage=StorageConfig(
            storage_backend="local",
            vector_backend="chromadb",
            base_path="./storage",
            cache_enabled=True,
            cache_size=5000,
            auto_backup=True,
            backup_interval=1800
        ),
        model=ModelConfig(
            llm_provider_type="api",
            llm_model_name="qwen-plus",
            embedding_provider_type="api",
            embedding_model_name="text-embedding-v3",
            timeout=60.0
        )
    ),
    "development": CodeRepoConfig(
        project_name="CodeRepoIndex",
        version="1.0.0",
        log_level="DEBUG",
        llm=LLMConfig(
            provider_type="api",
            model_name="qwen-plus",
            timeout=30.0
        ),
        embedding=EmbeddingConfig(
            provider_type="api",
            model_name="text-embedding-v3",
            timeout=30.0,
            batch_size=16
        ),
        storage=StorageConfig(
            storage_backend="local",
            vector_backend="memory",
            base_path="./storage_dev",
            cache_enabled=True,
            cache_size=500,
            auto_backup=False,
            backup_interval=3600
        ),
        model=ModelConfig(
            llm_provider_type="api",
            llm_model_name="qwen-plus",
            embedding_provider_type="api",
            embedding_model_name="text-embedding-v3",
            timeout=30.0
        )
    ),
    "minimal": CodeRepoConfig(
        project_name="CodeRepoIndex",
        version="1.0.0",
        log_level="ERROR",
        llm=LLMConfig(
            provider_type="api",
            model_name="qwen-plus",
            timeout=30.0
        ),
        embedding=EmbeddingConfig(
            provider_type="api",
            model_name="text-embedding-v3",
            timeout=30.0,
            batch_size=8
        ),
        storage=StorageConfig(
            storage_backend="local",
            vector_backend="memory",
            base_path="./storage_minimal",
            cache_enabled=False,
            cache_size=100,
            auto_backup=False,
            backup_interval=7200
        ),
        model=ModelConfig(
            llm_provider_type="api",
            llm_model_name="qwen-plus",
            embedding_provider_type="api",
            embedding_model_name="text-embedding-v3",
            timeout=30.0
        )
    )
}


def get_config_template(template_name: str = "default") -> CodeRepoConfig:
    """
    获取配置模板
    
    Args:
        template_name: 模板名称 ("default", "production", "development", "minimal")
        
    Returns:
        配置对象
        
    Raises:
        ValueError: 未知的模板名称
    """
    if template_name not in CONFIG_TEMPLATES:
        raise ValueError(f"未知的配置模板: {template_name}，可选: {list(CONFIG_TEMPLATES.keys())}")
    
    return CONFIG_TEMPLATES[template_name] 