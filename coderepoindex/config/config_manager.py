"""
配置管理器

统一管理CodeRepoIndex项目的所有配置。
"""

import os
import json
import logging
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, field, asdict
from pathlib import Path
from threading import Lock

logger = logging.getLogger(__name__)


@dataclass
class EmbeddingConfig:
    """嵌入模型配置"""
    provider_type: str = "api"
    model_name: str = "text-embedding-v3"
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    max_tokens: Optional[int] = None
    timeout: Optional[float] = 30.0
    batch_size: int = 32
    extra_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ModelConfig:
    """模型配置"""
    llm_provider_type: str = "api"
    llm_model_name: str = "qwen-plus"
    embedding_provider_type: str = "api"
    embedding_model_name: str = "text-embedding-v3"
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    timeout: Optional[float] = 30.0
    extra_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StorageConfig:
    """存储配置"""
    storage_backend: str = "local"
    vector_backend: str = "memory"
    base_path: str = "./storage"
    cache_enabled: bool = True
    cache_size: int = 1000
    auto_backup: bool = True
    backup_interval: int = 3600  # 秒
    extra_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CodeRepoConfig:
    """CodeRepoIndex项目配置"""
    # 基础配置
    project_name: str = "CodeRepoIndex"
    version: str = "1.0.0"
    log_level: str = "INFO"
    
    # 模型配置
    model: ModelConfig = field(default_factory=ModelConfig)
    
    # 存储配置
    storage: StorageConfig = field(default_factory=StorageConfig)
    
    # 嵌入配置
    embedding: EmbeddingConfig = field(default_factory=EmbeddingConfig)
    
    # 其他配置
    extra_config: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """配置验证和后处理"""
        # 确保model和embedding配置同步
        if self.model.api_key and not self.embedding.api_key:
            self.embedding.api_key = self.model.api_key
        if self.model.base_url and not self.embedding.base_url:
            self.embedding.base_url = self.model.base_url
        
        # 设置日志级别
        if self.log_level:
            logging.getLogger('coderepoindex').setLevel(getattr(logging, self.log_level.upper()))


class ConfigManager:
    """配置管理器"""
    
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化配置管理器"""
        if not hasattr(self, '_initialized'):
            self._config: Optional[CodeRepoConfig] = None
            self._config_file: Optional[str] = None
            self._initialized = True
    
    def load_config(
        self,
        config_path: Optional[str] = None,
        config_dict: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> CodeRepoConfig:
        """
        加载配置
        
        Args:
            config_path: 配置文件路径
            config_dict: 配置字典
            **kwargs: 额外配置参数
            
        Returns:
            配置对象
        """
        config_data = {}
        
        # 1. 从文件加载配置
        if config_path:
            config_data.update(self._load_from_file(config_path))
            self._config_file = config_path
        
        # 2. 从字典加载配置
        if config_dict:
            config_data.update(config_dict)
        
        # 3. 从环境变量加载配置
        config_data.update(self._load_from_env())
        
        # 4. 应用额外参数
        if kwargs:
            config_data.update(kwargs)
        
        # 5. 创建配置对象
        self._config = self._create_config(config_data)
        
        logger.info(f"配置加载完成: {self._config.project_name} v{self._config.version}")
        return self._config
    
    def save_config(self, config_path: Optional[str] = None) -> None:
        """
        保存配置到文件
        
        Args:
            config_path: 配置文件路径
        """
        if not self._config:
            raise ValueError("没有配置可以保存")
        
        save_path = config_path or self._config_file
        if not save_path:
            raise ValueError("没有指定保存路径")
        
        self._save_to_file(self._config, save_path)
        logger.info(f"配置已保存到: {save_path}")
    
    def get_config(self) -> Optional[CodeRepoConfig]:
        """获取当前配置"""
        return self._config
    
    def update_config(self, **kwargs) -> None:
        """
        更新配置
        
        Args:
            **kwargs: 要更新的配置项
        """
        if not self._config:
            raise ValueError("没有配置可以更新")
        
        # 更新配置
        config_dict = asdict(self._config)
        config_dict.update(kwargs)
        
        self._config = self._create_config(config_dict)
        logger.info("配置已更新")
    
    def _load_from_file(self, config_path: str) -> Dict[str, Any]:
        """从文件加载配置"""
        config_path = Path(config_path)
        
        if not config_path.exists():
            logger.warning(f"配置文件不存在: {config_path}")
            return {}
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                if config_path.suffix.lower() == '.json':
                    return json.load(f)
                else:
                    # 支持YAML格式
                    try:
                        import yaml
                        return yaml.safe_load(f)
                    except ImportError:
                        logger.warning("需要安装PyYAML来支持YAML配置文件")
                        return {}
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            return {}
    
    def _save_to_file(self, config: CodeRepoConfig, config_path: str) -> None:
        """保存配置到文件"""
        config_path = Path(config_path)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        config_dict = asdict(config)
        
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                if config_path.suffix.lower() == '.json':
                    json.dump(config_dict, f, indent=2, ensure_ascii=False)
                else:
                    # 支持YAML格式
                    try:
                        import yaml
                        yaml.safe_dump(config_dict, f, default_flow_style=False, allow_unicode=True)
                    except ImportError:
                        logger.warning("需要安装PyYAML来支持YAML配置文件，使用JSON格式保存")
                        json.dump(config_dict, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")
            raise
    
    def _load_from_env(self) -> Dict[str, Any]:
        """从环境变量加载配置"""
        config = {}
        
        # API 配置
        if api_key := os.getenv('CODEREPO_API_KEY') or os.getenv('OPENAI_API_KEY'):
            config['api_key'] = api_key
        
        if base_url := os.getenv('CODEREPO_BASE_URL') or os.getenv('OPENAI_BASE_URL'):
            config['base_url'] = base_url
        
        # 模型配置
        if llm_model := os.getenv('CODEREPO_LLM_MODEL'):
            config['llm_model_name'] = llm_model
        
        if embedding_model := os.getenv('CODEREPO_EMBEDDING_MODEL'):
            config['embedding_model_name'] = embedding_model
        
        # 存储配置
        if storage_path := os.getenv('CODEREPO_STORAGE_PATH'):
            config['storage_base_path'] = storage_path
        
        if storage_backend := os.getenv('CODEREPO_STORAGE_BACKEND'):
            config['storage_backend'] = storage_backend
        
        if vector_backend := os.getenv('CODEREPO_VECTOR_BACKEND'):
            config['vector_backend'] = vector_backend
        
        # 日志配置
        if log_level := os.getenv('CODEREPO_LOG_LEVEL'):
            config['log_level'] = log_level
        
        return config
    
    def _create_config(self, config_data: Dict[str, Any]) -> CodeRepoConfig:
        """创建配置对象"""
        # 处理嵌套配置
        model_config = ModelConfig()
        storage_config = StorageConfig()
        embedding_config = EmbeddingConfig()
        
        # 更新模型配置
        if 'model' in config_data:
            model_data = config_data['model']
            if isinstance(model_data, dict):
                for key, value in model_data.items():
                    if hasattr(model_config, key):
                        setattr(model_config, key, value)
        
        # 更新存储配置
        if 'storage' in config_data:
            storage_data = config_data['storage']
            if isinstance(storage_data, dict):
                for key, value in storage_data.items():
                    if hasattr(storage_config, key):
                        setattr(storage_config, key, value)
        
        # 更新嵌入配置
        if 'embedding' in config_data:
            embedding_data = config_data['embedding']
            if isinstance(embedding_data, dict):
                for key, value in embedding_data.items():
                    if hasattr(embedding_config, key):
                        setattr(embedding_config, key, value)
        
        # 处理顶级配置
        main_config = CodeRepoConfig()
        
        # 特殊处理一些配置项
        config_mappings = {
            'api_key': ['model.api_key', 'embedding.api_key'],
            'base_url': ['model.base_url', 'embedding.base_url'],
            'llm_model_name': ['model.llm_model_name'],
            'embedding_model_name': ['model.embedding_model_name', 'embedding.model_name'],
            'storage_base_path': ['storage.base_path'],
            'storage_backend': ['storage.storage_backend'],
            'vector_backend': ['storage.vector_backend'],
        }
        
        for key, value in config_data.items():
            if key in config_mappings:
                # 映射到具体的配置项
                for target_path in config_mappings[key]:
                    parts = target_path.split('.')
                    if parts[0] == 'model':
                        setattr(model_config, parts[1], value)
                    elif parts[0] == 'storage':
                        setattr(storage_config, parts[1], value)
                    elif parts[0] == 'embedding':
                        setattr(embedding_config, parts[1], value)
            elif hasattr(main_config, key):
                setattr(main_config, key, value)
        
        # 设置嵌套配置
        main_config.model = model_config
        main_config.storage = storage_config
        main_config.embedding = embedding_config
        
        return main_config


# 全局配置管理器实例
_config_manager = None


def get_config_manager() -> ConfigManager:
    """获取全局配置管理器实例"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def load_config(
    config_path: Optional[str] = None,
    config_dict: Optional[Dict[str, Any]] = None,
    **kwargs
) -> CodeRepoConfig:
    """
    加载配置的便利函数
    
    Args:
        config_path: 配置文件路径
        config_dict: 配置字典
        **kwargs: 额外配置参数
        
    Returns:
        配置对象
    """
    return get_config_manager().load_config(config_path, config_dict, **kwargs)


def save_config(config_path: Optional[str] = None) -> None:
    """
    保存配置的便利函数
    
    Args:
        config_path: 配置文件路径
    """
    get_config_manager().save_config(config_path)


def get_current_config() -> Optional[CodeRepoConfig]:
    """获取当前配置"""
    return get_config_manager().get_config()


def update_config(**kwargs) -> None:
    """
    更新配置的便利函数
    
    Args:
        **kwargs: 要更新的配置项
    """
    get_config_manager().update_config(**kwargs) 