"""
统一的数据提取模型定义
用于从不同数据源提取数据后，统一存储到不同目标
"""
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import uuid
from loguru import logger


# 数据源类型常量
class DataSourceType:
    """数据源类型"""
    TELEGRAM = "telegram"
    WECHAT = "wechat"
    EMAIL = "email"
    WEB = "web"
    OTHER = "other"


# 数据类型常量
class DataType:
    """数据类型"""
    TEXT = "text"  # 纯文本
    IMAGE = "image"  # 图片
    VIDEO = "video"  # 视频
    AUDIO = "audio"  # 音频
    DOCUMENT = "document"  # 文档
    OTHER = "other"  # 其他


@dataclass
class ExtractedData:
    """提取的数据"""
    # 基本信息
    id: str  # 数据ID（唯一标识）
    timestamp: datetime  # 时间戳
    source_type: str  # 数据源类型
    data_type: str  # 数据类型
    content: str  # 内容（文本内容或媒体URL）
    
    # 存储信息
    storage_status: Dict[str, bool] = None  # 存储状态，如 {"local": True, "feishu": False}
    storage_ids: Dict[str, str] = None  # 存储ID，如 {"local": "123", "feishu": "456"}
    
    def __post_init__(self):
        """初始化后的处理"""
        if self.storage_status is None:
            self.storage_status = {}
        if self.storage_ids is None:
            self.storage_ids = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "source_type": self.source_type,
            "data_type": self.data_type,
            "content": self.content,
            "storage_status": self.storage_status,
            "storage_ids": self.storage_ids
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExtractedData':
        """从字典创建对象"""
        # 处理日期时间
        timestamp = datetime.fromisoformat(data["timestamp"]) if isinstance(data["timestamp"], str) else data["timestamp"]
        
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            timestamp=timestamp,
            source_type=data["source_type"],
            data_type=data["data_type"],
            content=data["content"],
            storage_status=data.get("storage_status", {}),
            storage_ids=data.get("storage_ids", {})
        )
    
    @classmethod
    def from_raw_data(cls, raw_data: Dict[str, Any], source_type: str) -> 'ExtractedData':
        """从原始数据创建对象
        
        Args:
            raw_data: 原始数据
            source_type: 数据源类型
            
        Returns:
            ExtractedData: 提取的数据
        """
        # 根据数据源类型处理原始数据
        if source_type == DataSourceType.TELEGRAM:
            return cls._from_telegram_data(raw_data)
        elif source_type == DataSourceType.WECHAT:
            return cls._from_wechat_data(raw_data)
        else:
            # 默认处理
            return cls._from_default_data(raw_data, source_type)
    
    @classmethod
    def _from_telegram_data(cls, raw_data: Dict[str, Any]) -> 'ExtractedData':
        """从Telegram数据创建对象
        
        Args:
            raw_data: Telegram原始数据
            
        Returns:
            ExtractedData: 提取的数据
        """
        # 获取消息时间
        try:
            if isinstance(raw_data.get('date'), datetime):
                timestamp = raw_data['date']
            elif isinstance(raw_data.get('date'), str):
                # 处理ISO格式的日期字符串
                timestamp = datetime.fromisoformat(raw_data['date'])
            else:
                # 处理时间戳
                timestamp = datetime.fromtimestamp(raw_data.get('date', datetime.now().timestamp()))
        except (ValueError, TypeError) as e:
            logger.warning(f"无法解析日期 {raw_data.get('date')}，使用当前时间: {str(e)}")
            timestamp = datetime.now()
        
        # 确定数据类型和内容
        if raw_data.get('text'):
            data_type = DataType.TEXT
            content = raw_data['text']
        elif raw_data.get('photo'):
            data_type = DataType.IMAGE
            # 获取最大尺寸的图片
            photo = max(raw_data['photo'], key=lambda x: x.get('file_size', 0))
            content = photo.get('file_id', '')
        elif raw_data.get('video'):
            data_type = DataType.VIDEO
            content = raw_data['video'].get('file_id', '')
        elif raw_data.get('audio'):
            data_type = DataType.AUDIO
            content = raw_data['audio'].get('file_id', '')
        elif raw_data.get('document'):
            data_type = DataType.DOCUMENT
            content = raw_data['document'].get('file_id', '')
        elif raw_data.get('caption'):
            data_type = DataType.TEXT
            content = raw_data['caption']
        else:
            data_type = DataType.OTHER
            content = str(raw_data)
        
        # 创建提取的数据对象
        return cls(
            id=str(uuid.uuid4()),
            timestamp=timestamp,
            source_type=DataSourceType.TELEGRAM,
            data_type=data_type,
            content=content
        )
    
    @classmethod
    def _from_wechat_data(cls, raw_data: Dict[str, Any]) -> 'ExtractedData':
        """从微信数据创建对象
        
        Args:
            raw_data: 微信原始数据
            
        Returns:
            ExtractedData: 提取的数据
        """
        # 实现微信数据处理逻辑
        # 这里只是一个示例，实际实现需要根据微信API的数据结构
        timestamp = datetime.fromtimestamp(raw_data.get('CreateTime', datetime.now().timestamp()))
        
        if 'Content' in raw_data:
            data_type = DataType.TEXT
            content = raw_data['Content']
        elif 'PicUrl' in raw_data:
            data_type = DataType.IMAGE
            content = raw_data['PicUrl']
        elif 'MediaId' in raw_data:
            data_type = DataType.OTHER
            content = raw_data['MediaId']
        else:
            data_type = DataType.OTHER
            content = str(raw_data)
        
        return cls(
            id=str(uuid.uuid4()),
            timestamp=timestamp,
            source_type=DataSourceType.WECHAT,
            data_type=data_type,
            content=content
        )
    
    @classmethod
    def _from_default_data(cls, raw_data: Dict[str, Any], source_type: str) -> 'ExtractedData':
        """从默认数据创建对象
        
        Args:
            raw_data: 原始数据
            source_type: 数据源类型
            
        Returns:
            ExtractedData: 提取的数据
        """
        # 默认处理逻辑
        timestamp = datetime.now()
        
        if isinstance(raw_data, str):
            data_type = DataType.TEXT
            content = raw_data
        elif isinstance(raw_data, dict):
            if 'text' in raw_data:
                data_type = DataType.TEXT
                content = raw_data['text']
            elif 'content' in raw_data:
                data_type = DataType.TEXT
                content = raw_data['content']
            else:
                data_type = DataType.OTHER
                content = str(raw_data)
        else:
            data_type = DataType.OTHER
            content = str(raw_data)
        
        return cls(
            id=str(uuid.uuid4()),
            timestamp=timestamp,
            source_type=source_type,
            data_type=data_type,
            content=content
        ) 