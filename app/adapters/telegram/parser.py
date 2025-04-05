"""
Telegram消息解析器
负责解析Telegram消息数据
"""
from typing import Dict, List, Any, Optional
from loguru import logger
from telegram import Update, Message
from .types import TelegramMessage, TelegramUser, TelegramChat

class TelegramMessageParser:
    """Telegram消息解析器"""
    
    @staticmethod
    def parse_update(update: Update) -> Optional[TelegramMessage]:
        """解析Telegram更新对象
        
        Args:
            update: Telegram更新对象
            
        Returns:
            Optional[TelegramMessage]: 解析后的消息对象
        """
        if not update.message:
            return None
            
        try:
            message = update.message
            return TelegramMessageParser.parse_message(message)
        except Exception as e:
            logger.error(f"解析Telegram更新对象失败: {str(e)}")
            return None
    
    @staticmethod
    def parse_message(message: Message) -> TelegramMessage:
        """解析Telegram消息对象
        
        Args:
            message: Telegram消息对象
            
        Returns:
            TelegramMessage: 解析后的消息对象
        """
        # 解析用户信息
        from_user = None
        if hasattr(message, 'from_user') and message.from_user:
            from_user = TelegramUser(
                id=message.from_user.id,
                first_name=message.from_user.first_name,
                username=message.from_user.username,
                last_name=message.from_user.last_name,
                is_bot=message.from_user.is_bot
            )
        
        # 解析聊天信息
        chat = TelegramChat(
            id=message.chat.id,
            type=message.chat.type,
            title=message.chat.title,
            username=message.chat.username
        )
        
        # 解析媒体内容
        media = []
        if message.photo:
            media.extend([{
                'type': 'photo',
                'file_id': photo.file_id,
                'file_unique_id': photo.file_unique_id
            } for photo in message.photo])
        elif message.video:
            media.append({
                'type': 'video',
                'file_id': message.video.file_id,
                'file_unique_id': message.video.file_unique_id
            })
        elif message.document:
            media.append({
                'type': 'document',
                'file_id': message.document.file_id,
                'file_unique_id': message.document.file_unique_id
            })
        elif message.sticker:
            media.append({
                'type': 'sticker',
                'file_id': message.sticker.file_id,
                'file_unique_id': message.sticker.file_unique_id
            })
        elif message.voice:
            media.append({
                'type': 'voice',
                'file_id': message.voice.file_id,
                'file_unique_id': message.voice.file_unique_id
            })
        elif message.video_note:
            media.append({
                'type': 'video_note',
                'file_id': message.video_note.file_id,
                'file_unique_id': message.video_note.file_unique_id
            })
        
        # 解析实体
        entities = []
        if message.entities:
            entities.extend([{
                'type': entity.type,
                'offset': entity.offset,
                'length': entity.length,
                'url': entity.url if hasattr(entity, 'url') else None
            } for entity in message.entities])
        
        # 创建消息对象
        return TelegramMessage(
            message_id=message.message_id,
            date=message.date,
            chat=chat,
            from_user=from_user,
            text=message.text,
            caption=message.caption,
            media=media if media else None,
            entities=entities if entities else None
        )
    
    @staticmethod
    def to_standard_format(message: TelegramMessage) -> Dict[str, Any]:
        """转换为标准消息格式
        
        Args:
            message: Telegram消息对象
            
        Returns:
            Dict[str, Any]: 标准格式的消息数据
        """
        return {
            'message_id': str(message.message_id),
            'text': message.get_content(),
            'from': message.from_user.to_dict(),
            'chat': message.chat.to_dict(),
            'date': message.date.isoformat(),
            'media': message.media,
            'entities': message.entities,
            'metadata': {
                'message_id': message.message_id,
                'chat_id': message.chat.id,
                'chat_type': message.chat.type,
                'date': message.date.isoformat(),
                'from_user': message.from_user.to_dict(),
                'chat': message.chat.to_dict()
            }
        } 