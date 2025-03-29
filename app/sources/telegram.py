# -*- coding: utf-8 -*-
"""
Telegram信息源处理模块
从Telegram获取内容
"""
import os
from typing import Dict, List
from loguru import logger

from app.adapters.telegram import TelegramAdapter
from .base import Source

class TelegramSource(Source):
    """Telegram信息源处理模块"""
    
    def __init__(self, content_processor=None):
        """初始化Telegram信息源
        
        Args:
            content_processor: 内容处理器实例
        """
        # 从环境变量获取配置
        self.api_key = os.getenv('TELEGRAM_API_KEY')
        self.channel_id = os.getenv('TELEGRAM_CHANNEL_ID')
        
        if not self.api_key or not self.channel_id:
            raise ValueError("未配置Telegram API信息")
        
        # 初始化Telegram适配器
        self.adapter = TelegramAdapter(self.api_key, self.channel_id)
        self.processed_ids = set()
        
        # 保存内容处理器引用
        self.content_processor = content_processor
    
    async def initialize(self) -> bool:
        """初始化信息源
        
        Returns:
            bool: 是否初始化成功
        """
        try:
            # 初始化适配器
            async def message_callback(message):
                # 处理接收到的消息
                content = self._extract_content(message)
                if content and self.content_processor:
                    await self.content_processor.process_content(content)
            
            if not await self.adapter.initialize(message_callback):
                return False
                
            # 启动轮询
            if not await self.adapter.start_polling():
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"初始化Telegram信息源失败: {str(e)}")
            return False
    
    async def get_contents(self) -> List[Dict]:
        """获取Telegram内容
        
        Returns:
            List[Dict]: 内容列表
        """
        try:
            # 获取已接收的消息
            messages = self.adapter.get_received_messages()
            contents = []
            
            # 处理消息
            for message in messages:
                # 跳过已处理的消息
                message_id = message.get('metadata', {}).get('message_id')
                if message_id in self.processed_ids:
                    continue
                
                # 提取消息内容
                content = self._extract_content(message)
                if content:
                    contents.append(content)
                    self.processed_ids.add(message_id)
            
            return contents
            
        except Exception as e:
            logger.error(f"获取Telegram内容失败: {str(e)}")
            return []
    
    def _extract_content(self, message: Dict) -> Dict:
        """提取消息内容
        
        Args:
            message: 消息数据
            
        Returns:
            Dict: 内容信息
        """
        try:
            # 提取文本内容
            text = message.get('content', '')
            if not text:
                return None
            
            # 构建内容信息
            content = {
                'id': f"tg_{message.get('metadata', {}).get('message_id')}",
                'text': text,
                'source': 'telegram',
                'metadata': message.get('metadata', {})
            }
            
            return content
            
        except Exception as e:
            logger.error(f"提取消息内容失败: {str(e)}")
            return None
    
    async def mark_as_processed(self, content_id: str) -> bool:
        """标记内容为已处理
        
        Args:
            content_id: 内容ID
            
        Returns:
            bool: 是否标记成功
        """
        try:
            # 从ID中提取消息ID
            if content_id.startswith('tg_'):
                message_id = int(content_id[3:])
                self.processed_ids.add(message_id)
                return True
            return False
            
        except Exception as e:
            logger.error(f"标记内容为已处理失败: {str(e)}")
            return False 