# -*- coding: utf-8 -*-
"""
内容提取器基类
定义所有提取器必须实现的接口
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
from loguru import logger

from .config import ExtractorConfig
from .url_extractor import URLExtractor

class BaseExtractor(ABC):
    """基础内容提取器接口"""
    
    def __init__(self, config: Optional[ExtractorConfig] = None):
        """初始化提取器
        
        Args:
            config: 提取器配置
        """
        self.source_type = self.get_source_type()
        self.config = config or ExtractorConfig()
        self.url_extractor = URLExtractor()
    
    @abstractmethod
    def get_source_type(self) -> str:
        """获取数据源类型"""
        pass
    
    @abstractmethod
    async def extract(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """提取内容
        
        Args:
            raw_data: 原始数据
            
        Returns:
            Dict: 提取结果
        """
        pass
    
    @abstractmethod
    async def validate(self, raw_data: Dict[str, Any]) -> bool:
        """验证原始数据
        
        Args:
            raw_data: 原始数据
            
        Returns:
            bool: 是否有效
        """
        pass
    
    def _extract_urls(self, content: str) -> List[str]:
        """提取URL
        
        Args:
            content: 文本内容
            
        Returns:
            List[str]: URL列表
        """
        # 使用配置的URL模式
        self.url_extractor.URL_PATTERN = self.config.url_pattern
        
        # 提取URL
        urls = self.url_extractor.extract_urls(content)
        
        # 限制URL数量
        if len(urls) > self.config.max_url_count:
            urls = urls[:self.config.max_url_count]
            
        return urls
    
    def _create_metadata(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建元数据
        
        Args:
            raw_data: 原始数据
            
        Returns:
            Dict: 元数据
        """
        return {
            'source_type': self.source_type,
            'extracted_at': datetime.now(),
            'raw_data': raw_data,
            'config': self.config.to_dict()
        }
    
    def _create_error_data(self, error: str) -> Dict[str, Any]:
        """创建错误数据
        
        Args:
            error: 错误信息
            
        Returns:
            Dict: 错误数据
        """
        return {
            'success': False,
            'content': '',
            'metadata': self._create_metadata({}),
            'source': self.source_type,
            'timestamp': datetime.now(),
            'urls': [],
            'errors': [error]
        }
    
    def _create_success_data(self, 
                           content: str,
                           metadata: Dict[str, Any],
                           urls: List[str] = None,
                           errors: List[str] = None) -> Dict[str, Any]:
        """创建成功数据
        
        Args:
            content: 提取的内容
            metadata: 元数据
            urls: URL列表
            errors: 错误信息列表
            
        Returns:
            Dict: 成功数据
        """
        # 限制内容长度
        if len(content) > self.config.max_content_length:
            content = content[:self.config.max_content_length]
            
        return {
            'success': True,
            'content': content,
            'metadata': metadata,
            'source': self.source_type,
            'timestamp': datetime.now(),
            'urls': urls or [],
            'errors': errors or []
        }
    
    def update_config(self, config_dict: Dict[str, Any]) -> None:
        """更新配置
        
        Args:
            config_dict: 新的配置字典
        """
        self.config.update(config_dict)
        logger.info(f"Updated config for extractor {self.source_type}") 