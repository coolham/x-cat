from dataclasses import dataclass
from typing import Dict, Any, Optional

@dataclass
class Message:
    """表示一条消息"""
    message_id: str
    content: str
    metadata: Dict[str, Any] = None

@dataclass
class MessageAnalyzed:
    """表示消息已分析事件"""
    message: Message
    analysis_result: Dict[str, Any]
