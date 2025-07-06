from __future__ import annotations
import os
import json
import logging
from typing import Dict, Any, Optional, Union, TYPE_CHECKING
from dataclasses import dataclass, field, asdict
from pathlib import Path
from threading import Lock

if TYPE_CHECKING:
    from .defaults import CodeRepoConfig

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
class LLMConfig:
    """LLM模型配置"""
    provider_type: str = "api"
    model_name: str = "qwen-plus"
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    timeout: Optional[float] = 30.0
    extra_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ModelConfig:
    """模型配置（兼容性保留）"""
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
    
    # LLM配置
    llm: LLMConfig = field(default_factory=LLMConfig)
    
    # 嵌入配置
    embedding: EmbeddingConfig = field(default_factory=EmbeddingConfig)
    
    # 存储配置
    storage: StorageConfig = field(default_factory=StorageConfig)
    
    # 模型配置（兼容性保留）
    model: ModelConfig = field(default_factory=ModelConfig)
    
    # 其他配置
    extra_config: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """配置验证和后处理"""
        # 兼容性处理：如果model配置有值，同步到llm和embedding配置
        if self.model.api_key:
            if not self.llm.api_key:
                self.llm.api_key = self.model.api_key
            if not self.embedding.api_key:
                self.embedding.api_key = self.model.api_key
                
        if self.model.base_url:
            if not self.llm.base_url:
                self.llm.base_url = self.model.base_url
            if not self.embedding.base_url:
                self.embedding.base_url = self.model.base_url
        
        # 同步模型名称
        if self.model.llm_model_name != "qwen-plus":
            self.llm.model_name = self.model.llm_model_name
        if self.model.embedding_model_name != "text-embedding-v3":
            self.embedding.model_name = self.model.embedding_model_name
            
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
    ) -> "CodeRepoConfig":
        """
        加载配置，优先级：kwargs > 环境变量 > config_dict > 配置文件 > 默认值
        """
        config_data = {}

        # 1. 尝试从默认配置文件加载
        effective_config_path = config_path
        if effective_config_path is None:
            if Path('coderepoindex.json').exists():
                effective_config_path = 'coderepoindex.json'
            elif Path('config.json').exists():
                effective_config_path = 'config.json'
        
        if effective_config_path:
            config_data.update(self._load_from_file(effective_config_path))
            self._config_file = effective_config_path

        # 2. 从字典更新配置
        if config_dict:
            config_data.update(config_dict)

        # 3. 从环境变量更新配置
        config_data.update(self._load_from_env())

        # 4. 从关键字参数更新配置 (最高优先级)
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
        
        # 基础配置
        if os.getenv('CODEREPO_PROJECT_NAME'):
            config['project_name'] = os.getenv('CODEREPO_PROJECT_NAME')
        if os.getenv('CODEREPO_LOG_LEVEL'):
            config['log_level'] = os.getenv('CODEREPO_LOG_LEVEL')
        
        # LLM配置
        llm_config = {}
        if os.getenv('CODEREPO_LLM_API_KEY'):
            llm_config['api_key'] = os.getenv('CODEREPO_LLM_API_KEY')
        if os.getenv('CODEREPO_LLM_BASE_URL'):
            llm_config['base_url'] = os.getenv('CODEREPO_LLM_BASE_URL')
        if os.getenv('CODEREPO_LLM_MODEL'):
            llm_config['model_name'] = os.getenv('CODEREPO_LLM_MODEL')
        if os.getenv('CODEREPO_LLM_PROVIDER'):
            llm_config['provider_type'] = os.getenv('CODEREPO_LLM_PROVIDER')
        if llm_config:
            config['llm'] = llm_config
        
        # 嵌入配置
        embedding_config = {}
        if os.getenv('CODEREPO_EMBEDDING_API_KEY'):
            embedding_config['api_key'] = os.getenv('CODEREPO_EMBEDDING_API_KEY')
        if os.getenv('CODEREPO_EMBEDDING_BASE_URL'):
            embedding_config['base_url'] = os.getenv('CODEREPO_EMBEDDING_BASE_URL')
        if os.getenv('CODEREPO_EMBEDDING_MODEL'):
            embedding_config['model_name'] = os.getenv('CODEREPO_EMBEDDING_MODEL')
        if os.getenv('CODEREPO_EMBEDDING_PROVIDER'):
            embedding_config['provider_type'] = os.getenv('CODEREPO_EMBEDDING_PROVIDER')
        if embedding_config:
            config['embedding'] = embedding_config
        
        # 兼容性：通用API配置（如果没有分别配置）
        if os.getenv('CODEREPO_API_KEY') and not llm_config.get('api_key') and not embedding_config.get('api_key'):
            api_key = os.getenv('CODEREPO_API_KEY')
            config.setdefault('llm', {})['api_key'] = api_key
            config.setdefault('embedding', {})['api_key'] = api_key
            
        if os.getenv('CODEREPO_BASE_URL') and not llm_config.get('base_url') and not embedding_config.get('base_url'):
            base_url = os.getenv('CODEREPO_BASE_URL')
            config.setdefault('llm', {})['base_url'] = base_url
            config.setdefault('embedding', {})['base_url'] = base_url
        
        # 存储配置
        storage_config = {}
        if os.getenv('CODEREPO_STORAGE_PATH'):
            storage_config['base_path'] = os.getenv('CODEREPO_STORAGE_PATH')
        if os.getenv('CODEREPO_STORAGE_BACKEND'):
            storage_config['storage_backend'] = os.getenv('CODEREPO_STORAGE_BACKEND')
        if os.getenv('CODEREPO_VECTOR_BACKEND'):
            storage_config['vector_backend'] = os.getenv('CODEREPO_VECTOR_BACKEND')
        if storage_config:
            config['storage'] = storage_config
        
        return config
    
    def _create_config(self, config_data: Dict[str, Any]) -> CodeRepoConfig:
        """从字典创建配置对象"""
        from .defaults import DEFAULT_CONFIG
        
        # 创建默认配置的副本
        config = CodeRepoConfig(
            project_name=config_data.get('project_name', DEFAULT_CONFIG.project_name),
            version=config_data.get('version', DEFAULT_CONFIG.version),
            log_level=config_data.get('log_level', DEFAULT_CONFIG.log_level),
            extra_config=config_data.get('extra_config', {})
        )
        
        # 处理LLM配置
        llm_data = config_data.get('llm', {})
        config.llm = LLMConfig(
            provider_type=llm_data.get('provider_type', DEFAULT_CONFIG.llm.provider_type),
            model_name=llm_data.get('model_name', DEFAULT_CONFIG.llm.model_name),
            api_key=llm_data.get('api_key', DEFAULT_CONFIG.llm.api_key),
            base_url=llm_data.get('base_url', DEFAULT_CONFIG.llm.base_url),
            timeout=llm_data.get('timeout', DEFAULT_CONFIG.llm.timeout),
            extra_params=llm_data.get('extra_params', {})
        )
        
        # 处理嵌入配置
        embedding_data = config_data.get('embedding', {})
        config.embedding = EmbeddingConfig(
            provider_type=embedding_data.get('provider_type', DEFAULT_CONFIG.embedding.provider_type),
            model_name=embedding_data.get('model_name', DEFAULT_CONFIG.embedding.model_name),
            api_key=embedding_data.get('api_key', DEFAULT_CONFIG.embedding.api_key),
            base_url=embedding_data.get('base_url', DEFAULT_CONFIG.embedding.base_url),
            max_tokens=embedding_data.get('max_tokens', DEFAULT_CONFIG.embedding.max_tokens),
            timeout=embedding_data.get('timeout', DEFAULT_CONFIG.embedding.timeout),
            batch_size=embedding_data.get('batch_size', DEFAULT_CONFIG.embedding.batch_size),
            extra_params=embedding_data.get('extra_params', {})
        )
        
        # 处理存储配置
        storage_data = config_data.get('storage', {})
        config.storage = StorageConfig(
            storage_backend=storage_data.get('storage_backend', DEFAULT_CONFIG.storage.storage_backend),
            vector_backend=storage_data.get('vector_backend', DEFAULT_CONFIG.storage.vector_backend),
            base_path=storage_data.get('base_path', DEFAULT_CONFIG.storage.base_path),
            cache_enabled=storage_data.get('cache_enabled', DEFAULT_CONFIG.storage.cache_enabled),
            cache_size=storage_data.get('cache_size', DEFAULT_CONFIG.storage.cache_size),
            auto_backup=storage_data.get('auto_backup', DEFAULT_CONFIG.storage.auto_backup),
            backup_interval=storage_data.get('backup_interval', DEFAULT_CONFIG.storage.backup_interval),
            extra_params=storage_data.get('extra_params', {})
        )
        
        # 处理兼容性配置（model）
        model_data = config_data.get('model', {})
        config.model = ModelConfig(
            llm_provider_type=model_data.get('llm_provider_type', DEFAULT_CONFIG.model.llm_provider_type),
            llm_model_name=model_data.get('llm_model_name', DEFAULT_CONFIG.model.llm_model_name),
            embedding_provider_type=model_data.get('embedding_provider_type', DEFAULT_CONFIG.model.embedding_provider_type),
            embedding_model_name=model_data.get('embedding_model_name', DEFAULT_CONFIG.model.embedding_model_name),
            api_key=model_data.get('api_key', DEFAULT_CONFIG.model.api_key),
            base_url=model_data.get('base_url', DEFAULT_CONFIG.model.base_url),
            timeout=model_data.get('timeout', DEFAULT_CONFIG.model.timeout),
            extra_params=model_data.get('extra_params', {})
        )
        
        # 处理扁平化配置（兼容性）
        if 'api_key' in config_data:
            if not config.llm.api_key:
                config.llm.api_key = config_data['api_key']
            if not config.embedding.api_key:
                config.embedding.api_key = config_data['api_key']
            config.model.api_key = config_data['api_key']
            
        if 'base_url' in config_data:
            if not config.llm.base_url:
                config.llm.base_url = config_data['base_url']
            if not config.embedding.base_url:
                config.embedding.base_url = config_data['base_url']
            config.model.base_url = config_data['base_url']
        
        return config


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