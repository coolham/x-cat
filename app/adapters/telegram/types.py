"""
Telegram消息类型定义
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class TelegramUser:
    """Telegram用户信息"""
    id: int
    first_name: str
    username: Optional[str] = None
    last_name: Optional[str] = None
    is_bot: bool = False
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TelegramUser':
        return cls(
            id=data['id'],
            first_name=data['first_name'],
            username=data.get('username'),
            last_name=data.get('last_name'),
            is_bot=data.get('is_bot', False)
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'first_name': self.first_name,
            'username': self.username,
            'last_name': self.last_name,
            'is_bot': self.is_bot
        }

@dataclass
class TelegramChat:
    """Telegram聊天信息"""
    id: int
    type: str
    title: Optional[str] = None
    username: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TelegramChat':
        return cls(
            id=data['id'],
            type=data['type'],
            title=data.get('title'),
            username=data.get('username')
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'type': self.type,
            'title': self.title,
            'username': self.username
        }

@dataclass
class TelegramMessage:
    """Telegram消息"""
    message_id: int
    date: datetime
    chat: TelegramChat
    from_user: Optional[TelegramUser] = None
    text: Optional[str] = None
    caption: Optional[str] = None
    media: List[Dict[str, Any]] = None
    entities: List[Dict[str, Any]] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TelegramMessage':
        from_user = None
        if 'from' in data and data['from']:
            from_user = TelegramUser.from_dict(data['from'])
            
        return cls(
            message_id=data['message_id'],
            date=datetime.fromisoformat(data['date']) if isinstance(data['date'], str) else data['date'],
            chat=TelegramChat.from_dict(data['chat']),
            from_user=from_user,
            text=data.get('text'),
            caption=data.get('caption'),
            media=data.get('media', []),
            entities=data.get('entities', [])
        )
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            'message_id': self.message_id,
            'date': self.date.isoformat(),
            'chat': self.chat.to_dict(),
            'text': self.text,
            'caption': self.caption,
            'media': self.media,
            'entities': self.entities
        }
        
        if self.from_user:
            result['from'] = self.from_user.to_dict()
            
        return result
    
    def get_content(self) -> str:
        """获取消息内容"""
        return self.text or self.caption or ''
    
    def has_media(self) -> bool:
        """是否有媒体内容"""
        return bool(self.media)
    
    def get_media_types(self) -> List[str]:
        """获取媒体类型列表"""
        return [m['type'] for m in (self.media or [])]
    
    def get_urls(self) -> List[str]:
        """获取消息中的URL列表"""
        if not self.entities:
            return []
            
        urls = []
        text = self.get_content()
        for entity in self.entities:
            if entity['type'] == 'url':
                start = entity['offset']
                length = entity['length']
                url = text[start:start + length]
                if url:
                    urls.append(url)
        return urls 