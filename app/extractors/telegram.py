# -*- coding: utf-8 -*-
"""
Telegram数据提取器
用于从Telegram消息中提取数据
"""
from typing import Dict, Any
from loguru import logger
from app.extractors.base import BaseExtractor
from app.models.extracted_data import DataSourceType
from app.adapters.telegram.types import TelegramMessage


class TelegramExtractor(BaseExtractor):
    """Telegram数据提取器"""
    
    def __init__(self):
        """初始化Telegram提取器"""
        super().__init__(DataSourceType.TELEGRAM)
        logger.info("初始化Telegram提取器")
    
    def extract(self, raw_data: Any) -> 'ExtractedData':
        """从Telegram消息中提取数据
        
        Args:
            raw_data: Telegram消息数据，可以是TelegramMessage对象或字典
            
        Returns:
            ExtractedData: 提取的数据
        """
        logger.info(f"开始提取Telegram消息数据: {raw_data}")
        try:
            # 如果raw_data是TelegramMessage对象，转换为字典
            if isinstance(raw_data, TelegramMessage):
                logger.debug(f"将TelegramMessage对象转换为字典: message_id={raw_data.message_id}")
                # 创建一个包含所有必要字段的字典
                raw_data_dict = {
                    'message_id': raw_data.message_id,
                    'date': raw_data.date,
                    'chat': raw_data.chat.to_dict() if raw_data.chat else {},
                    'text': raw_data.text,
                    'caption': raw_data.caption,
                    'media': raw_data.media or [],
                    'entities': raw_data.entities or []
                }
                
                # 如果有from_user，添加到字典中
                if raw_data.from_user:
                    raw_data_dict['from'] = raw_data.from_user.to_dict()
            else:
                raw_data_dict = raw_data
                
            # 使用ExtractedData的from_raw_data方法处理数据
            extracted_data = self._create_extracted_data(raw_data_dict)
            logger.info(f"成功提取Telegram消息数据: {extracted_data.id}")
            return extracted_data
        except Exception as e:
            logger.error(f"提取Telegram消息数据失败: {str(e)}")
            logger.debug(f"错误详情: {e.__class__.__name__}: {str(e)}")
            raise 