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
from app.cache.cache_manager import CacheManager
from app.models.extracted_data import ExtractedData, DataSourceType

class BaseExtractor(ABC):
    """数据提取器基类"""
    
    def __init__(self, source_type: DataSourceType):
        """初始化提取器
        
        Args:
            source_type: 数据源类型
        """
        self.source_type = source_type
    
    @abstractmethod
    def extract(self, raw_data: Any) -> ExtractedData:
        """从原始数据中提取数据
        
        Args:
            raw_data: 原始数据
            
        Returns:
            ExtractedData: 提取的数据
        """
        pass
    
    def extract_batch(self, raw_data_list: List[Any]) -> List[ExtractedData]:
        """批量提取数据
        
        Args:
            raw_data_list: 原始数据列表
            
        Returns:
            List[ExtractedData]: 提取的数据列表
        """
        return [self.extract(raw_data) for raw_data in raw_data_list]
    
    def _create_extracted_data(self, raw_data: Dict[str, Any]) -> ExtractedData:
        """创建提取的数据对象
        
        Args:
            raw_data: 原始数据
            
        Returns:
            ExtractedData: 提取的数据
        """
        return ExtractedData.from_raw_data(raw_data, self.source_type)
    
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
    
    def _get_cache_key(self, data: Dict[str, Any]) -> Optional[str]:
        """获取缓存键
        
        Args:
            data: 输入数据
            
        Returns:
            Optional[str]: 缓存键，如果不支持缓存则返回None
        """
        raise NotImplementedError
    
    def _process_with_cache(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """使用缓存处理数据
        
        Args:
            data: 输入数据
            
        Returns:
            Dict[str, Any]: 处理后的数据
        """
        # 获取缓存键
        cache_key = self._get_cache_key(data)
        if not cache_key:
            return self.extract(data)
        
        # 检查缓存
        if self.cache_manager.exists(cache_key):
            logger.info(f"从缓存加载数据: {cache_key}")
            cached_data = self.cache_manager.load(cache_key)
            if cached_data:
                return cached_data
        
        # 提取数据
        extracted_data = self.extract(data)
        
        # 保存到缓存
        if extracted_data:
            self.cache_manager.save(cache_key, extracted_data)
            logger.info(f"数据已缓存: {cache_key}")
        
        return extracted_data 