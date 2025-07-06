"""
配置管理模块

提供统一的配置管理功能，支持多种配置方式。
"""

from .config_manager import (
    ConfigManager,
    CodeRepoConfig,
    LLMConfig,
    EmbeddingConfig,
    ModelConfig,
    StorageConfig,
    load_config,
    save_config,
    get_current_config,
    update_config,
    get_config_manager
)

from .defaults import (
    DEFAULT_CONFIG,
    DEFAULT_LLM_CONFIG,
    DEFAULT_EMBEDDING_CONFIG,
    DEFAULT_MODEL_CONFIG,
    DEFAULT_STORAGE_CONFIG,
    CONFIG_TEMPLATES,
    get_config_template
)

__all__ = [
    # 配置管理器
    'ConfigManager',
    'get_config_manager',
    
    # 配置类
    'CodeRepoConfig',
    'LLMConfig',
    'EmbeddingConfig', 
    'ModelConfig',
    'StorageConfig',
    
    # 配置函数
    'load_config',
    'save_config',
    'get_current_config',
    'update_config',
    
    # 默认配置
    'DEFAULT_CONFIG',
    'DEFAULT_LLM_CONFIG',
    'DEFAULT_EMBEDDING_CONFIG',
    'DEFAULT_MODEL_CONFIG',
    'DEFAULT_STORAGE_CONFIG',
    'CONFIG_TEMPLATES',
    'get_config_template'
] 