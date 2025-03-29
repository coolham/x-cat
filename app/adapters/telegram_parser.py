# -*- coding: utf-8 -*-
"""
Telegram消息解析器
负责解析Telegram消息数据
"""
from typing import Dict, List, Any, Optional
from loguru import logger


class TelegramMessageParser:
    """Telegram消息解析器"""
    
    @staticmethod
    def parse_message(message_data: Dict[str, Any], update_id: int, message_type: str) -> Optional[Dict[str, Any]]:
        """解析Telegram消息
        
        Args:
            message_data: 原始消息数据
            update_id: 更新ID
            message_type: 消息类型
            
        Returns:
            Optional[Dict[str, Any]]: 解析后的消息数据
        """
        try:
            # 确保消息数据包含必要字段
            if not message_data or 'message_id' not in message_data:
                logger.warning("消息数据中缺少message_id")
                return None
                
            # 构建标准格式的消息数据
            parsed_data = {
                'message_id': message_data['message_id'],
                'update_id': update_id,
                'message_type': message_type,
                'text': message_data.get('text', ''),
                'content': message_data.get('text', ''),
                'date': message_data.get('date'),
                'chat': message_data.get('chat', {}),
                'from_user': message_data.get('from_user', {}),
                'entities': message_data.get('entities', []),
                'metadata': {
                    'message_id': message_data['message_id'],
                    'chat_id': message_data.get('chat', {}).get('id'),
                    'chat_type': message_data.get('chat', {}).get('type'),
                    'date': message_data.get('date'),
                    'from_user': message_data.get('from_user'),
                    'chat': message_data.get('chat')
                }
            }
            
            # 处理不同类型的消息
            if 'photo' in message_data:
                parsed_data['message_type'] = 'photo'
                parsed_data['content'] = message_data.get('caption', '')
            elif 'video' in message_data:
                parsed_data['message_type'] = 'video'
                parsed_data['content'] = message_data.get('caption', '')
            elif 'document' in message_data:
                parsed_data['message_type'] = 'document'
                parsed_data['content'] = message_data.get('caption', '')
            elif 'sticker' in message_data:
                parsed_data['message_type'] = 'sticker'
                parsed_data['content'] = ''
            elif 'voice' in message_data:
                parsed_data['message_type'] = 'voice'
                parsed_data['content'] = ''
            elif 'video_note' in message_data:
                parsed_data['message_type'] = 'video_note'
                parsed_data['content'] = ''
            
            logger.debug(f"解析消息成功: {parsed_data['message_id']}")
            return parsed_data
            
        except Exception as e:
            logger.error(f"解析消息失败: {str(e)}")
            return None
    
    @staticmethod
    def validate_message(message: Dict[str, Any]) -> bool:
        """验证Telegram消息格式
        
        Args:
            message: 消息数据
            
        Returns:
            bool: 是否有效
        """
        required_fields = ['message_id', 'chat', 'date']
        return all(field in message for field in required_fields)
    
    @staticmethod
    def extract_urls(message: Dict[str, Any]) -> List[str]:
        """从消息中提取URL
        
        Args:
            message: 消息数据
            
        Returns:
            List[str]: URL列表
        """
        urls = []
        text = message.get('text', '')
        entities = message.get('entities', [])
        
        for entity in entities:
            if entity.get('type') == 'url':
                start = entity.get('offset', 0)
                length = entity.get('length', 0)
                url = text[start:start + length]
                if url:
                    urls.append(url)
        
        return urls 