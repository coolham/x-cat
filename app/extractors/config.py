"""
提取器配置
用于管理提取器的配置参数
"""
from typing import Dict, Any, Optional
from dataclasses import dataclass
from loguru import logger

@dataclass
class ExtractorConfig:
    """提取器配置"""
    
    # 通用配置
    max_content_length: int = 8000  # 最大内容长度
    max_url_count: int = 5          # 最大URL数量
    timeout: int = 30               # 超时时间（秒）
    
    # URL提取配置
    url_pattern: str = r'https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&\/=]*)'
    validate_urls: bool = True      # 是否验证URL
    
    # 数据源特定配置
    source_config: Dict[str, Any] = None
    
    def __post_init__(self):
        """初始化后的处理"""
        if self.source_config is None:
            self.source_config = {}
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'ExtractorConfig':
        """从字典创建配置
        
        Args:
            config_dict: 配置字典
            
        Returns:
            ExtractorConfig: 配置对象
        """
        return cls(**config_dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            Dict[str, Any]: 配置字典
        """
        return {
            'max_content_length': self.max_content_length,
            'max_url_count': self.max_url_count,
            'timeout': self.timeout,
            'url_pattern': self.url_pattern,
            'validate_urls': self.validate_urls,
            'source_config': self.source_config
        }
    
    def update(self, config_dict: Dict[str, Any]) -> None:
        """更新配置
        
        Args:
            config_dict: 新的配置字典
        """
        for key, value in config_dict.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                logger.warning(f"Unknown config key: {key}")
    
    def get_source_config(self, key: str, default: Any = None) -> Any:
        """获取数据源特定配置
        
        Args:
            key: 配置键
            default: 默认值
            
        Returns:
            Any: 配置值
        """
        return self.source_config.get(key, default)
    
    def set_source_config(self, key: str, value: Any) -> None:
        """设置数据源特定配置
        
        Args:
            key: 配置键
            value: 配置值
        """
        self.source_config[key] = value 