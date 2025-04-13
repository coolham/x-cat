"""
预处理配置管理
"""
from typing import Dict, Any, Optional
from dataclasses import dataclass
from loguru import logger

@dataclass
class PreprocessorConfig:
    """预处理器配置类"""
    # 基础配置
    proxy_url: Optional[str] = None
    timeout: int = 30
    max_content_length: int = 8000
    max_url_count: int = 5
    user_agent: Optional[str] = None
    max_retries: int = 2
    
    # URL提取配置
    url_patterns: list = None
    url_blacklist: list = None
    
    # 内容清理配置
    remove_html: bool = True
    remove_extra_spaces: bool = True
    max_line_length: int = 1000
    
    # 媒体处理配置
    max_media_size: int = 10 * 1024 * 1024  # 10MB
    allowed_media_types: list = None
    media_storage_path: str = "media"
    
    # 命令处理配置
    command_prefix: str = "/"
    allowed_commands: list = None
    
    def __post_init__(self):
        """初始化默认值"""
        if self.url_patterns is None:
            self.url_patterns = [
                r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
                r'www\.(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
            ]
        
        if self.url_blacklist is None:
            self.url_blacklist = []
            
        if self.allowed_media_types is None:
            self.allowed_media_types = [
                'image/jpeg',
                'image/png',
                'image/gif',
                'video/mp4',
                'application/pdf'
            ]
            
        if self.allowed_commands is None:
            self.allowed_commands = [
                'help',
                'status',
                'config'
            ]

    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> 'PreprocessorConfig':
        """从字典创建预处理器配置
        
        Args:
            config: 配置字典
            
        Returns:
            PreprocessorConfig: 预处理器配置对象
        """
        # 确保配置字典中的键与 PreprocessorConfig 的属性匹配
        valid_config = {}
        for key, value in config.items():
            if hasattr(cls, key):
                valid_config[key] = value
        
        return cls(**valid_config)
    
    def validate(self) -> bool:
        """验证配置
        
        Returns:
            bool: 是否有效
        """
        try:
            # 验证超时时间
            if self.timeout <= 0:
                logger.error("超时时间必须大于0")
                return False
            
            # 验证内容长度限制
            if self.max_content_length <= 0:
                logger.error("内容长度限制必须大于0")
                return False
            
            # 验证URL数量限制
            if self.max_url_count <= 0:
                logger.error("URL数量限制必须大于0")
                return False
            
            # 验证重试次数
            if self.max_retries < 0:
                logger.error("重试次数不能为负数")
                return False
            
            logger.info("预处理器配置验证通过")
            return True
            
        except Exception as e:
            logger.error(f"预处理器配置验证失败: {str(e)}")
            return False 