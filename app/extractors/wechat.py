# app/extractors/wechat.py
# -*- coding: utf-8 -*-
"""
微信数据提取器
用于从微信消息中提取数据
"""
from typing import Dict, Any
from loguru import logger
from app.extractors.base import BaseExtractor
from app.models.extracted_data import DataSourceType


class WeChatExtractor(BaseExtractor):
    """微信数据提取器"""
    
    def __init__(self):
        """初始化微信提取器"""
        super().__init__(DataSourceType.WECHAT)
        logger.info("初始化微信提取器")
    
    def extract(self, raw_data: Dict[str, Any]) -> 'ExtractedData':
        """从微信消息中提取数据
        
        Args:
            raw_data: 微信消息数据
            
        Returns:
            ExtractedData: 提取的数据
        """
        try:
            # 使用ExtractedData的from_raw_data方法处理数据
            extracted_data = self._create_extracted_data(raw_data)
            logger.info(f"成功提取微信消息数据: {extracted_data.id}")
            return extracted_data
        except Exception as e:
            logger.error(f"提取微信消息数据失败: {str(e)}")
            raise
