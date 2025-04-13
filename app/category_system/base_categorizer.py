"""
基础分类器
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from loguru import logger


class BaseCategorizer(ABC):
    """基础分类器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """初始化分类器
        
        Args:
            config: 配置信息
        """
        self.config = config or {}
        logger.info(f"初始化分类器: {self.__class__.__name__}")
    
    @abstractmethod
    async def categorize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """分类数据
        
        Args:
            data: 输入数据
            
        Returns:
            Dict[str, Any]: 分类结果
        """
        raise NotImplementedError
    
    def categorize_sync(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """同步分类数据
        
        Args:
            data: 输入数据
            
        Returns:
            Dict[str, Any]: 分类结果
        """
        raise NotImplementedError
    
    def _validate_config(self) -> bool:
        """验证配置
        
        Returns:
            bool: 配置是否有效
        """
        return True
    
    def _get_cache_key(self, data: Dict[str, Any]) -> Optional[str]:
        """获取缓存键
        
        Args:
            data: 输入数据
            
        Returns:
            Optional[str]: 缓存键，如果不支持缓存则返回None
        """
        return None 