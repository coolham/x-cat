"""
提取器工厂
用于创建和管理不同类型的提取器
"""
from typing import Dict, Type
from loguru import logger

from .base import BaseExtractor
from .telegram import TelegramExtractor

class ExtractorFactory:
    """提取器工厂"""
    
    _extractors: Dict[str, Type[BaseExtractor]] = {
        'telegram': TelegramExtractor,
        # 在这里添加其他提取器
    }
    
    @classmethod
    def register_extractor(cls, source_type: str, extractor_class: Type[BaseExtractor]) -> None:
        """注册新的提取器
        
        Args:
            source_type: 数据源类型
            extractor_class: 提取器类
        """
        cls._extractors[source_type] = extractor_class
        logger.info(f"Registered extractor for source type: {source_type}")
    
    @classmethod
    def create_extractor(cls, source_type: str) -> BaseExtractor:
        """创建提取器实例
        
        Args:
            source_type: 数据源类型
            
        Returns:
            BaseExtractor: 提取器实例
            
        Raises:
            ValueError: 如果数据源类型未注册
        """
        if source_type not in cls._extractors:
            raise ValueError(f"No extractor registered for source type: {source_type}")
            
        extractor_class = cls._extractors[source_type]
        return extractor_class()
    
    @classmethod
    def get_available_extractors(cls) -> Dict[str, Type[BaseExtractor]]:
        """获取所有可用的提取器
        
        Returns:
            Dict[str, Type[BaseExtractor]]: 提取器映射
        """
        return cls._extractors.copy() 