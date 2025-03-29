"""
Base interface for data source adapters
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Set, Callable, Awaitable
from datetime import datetime


class BaseAdapter(ABC):
    """基础适配器接口"""
    
    def __init__(self):
        """初始化适配器"""
        self.source_type = self.get_source_type()
        self.initialized = False
        self.message_callback = None
    
    @abstractmethod
    def get_source_type(self) -> str:
        """获取数据源类型"""
        pass
    
    @abstractmethod
    async def initialize(self, message_callback: Callable[[Dict[str, Any]], None]) -> bool:
        """初始化适配器
        
        Args:
            message_callback: 收到新消息时的回调函数
            
        Returns:
            bool: 初始化是否成功
        """
        pass
    
    @abstractmethod
    async def start(self) -> bool:
        """启动适配器
        
        Returns:
            bool: 启动是否成功
        """
        pass
    
    @abstractmethod
    async def stop(self) -> None:
        """停止适配器"""
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """关闭适配器"""
        pass
    
    @abstractmethod
    async def get_messages(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取消息
        
        Args:
            limit: 获取消息的最大数量
            
        Returns:
            List[Dict]: 消息列表
        """
        pass
    
    def _create_message_data(self, 
                           content: str,
                           metadata: Dict[str, Any],
                           urls: List[str] = None,
                           errors: List[str] = None) -> Dict[str, Any]:
        """创建标准消息数据格式
        
        Args:
            content: 消息内容
            metadata: 元数据
            urls: URL列表
            errors: 错误信息列表
            
        Returns:
            Dict: 标准消息数据
        """
        return {
            'success': True,
            'content': content,
            'metadata': metadata,
            'source': self.source_type,
            'timestamp': datetime.now(),
            'urls': urls or [],
            'errors': errors or []
        }
    
    def _create_error_data(self, error: str) -> Dict[str, Any]:
        """创建错误数据格式
        
        Args:
            error: 错误信息
            
        Returns:
            Dict: 错误数据
        """
        return {
            'success': False,
            'content': '',
            'metadata': {},
            'source': self.source_type,
            'timestamp': datetime.now(),
            'urls': [],
            'errors': [error]
        }

class DataSourceAdapter(ABC):
    """Base class for all data source adapters"""
    
    def __init__(self):
        """Initialize adapter"""
        self.event_handlers: Dict[str, Set[Callable[[Dict[str, Any]], Awaitable[None]]]] = {
            'new_content': set(),
            'content_processed': set(),
            'error': set()
        }
    
    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """
        Initialize the adapter with configuration
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Whether initialization was successful
        """
        return True
    
    @abstractmethod
    async def start(self) -> bool:
        """
        Start the adapter
        
        Returns:
            Whether startup was successful
        """
        return True
    
    @abstractmethod
    async def stop(self) -> bool:
        """
        Stop the adapter
        
        Returns:
            Whether shutdown was successful
        """
        return True
    
    @abstractmethod
    async def fetch_content(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Fetch content from the data source
        
        Args:
            limit: Maximum number of items to fetch
            
        Returns:
            List of dictionaries containing the content
        """
        return []
    
    @abstractmethod
    async def mark_as_processed(self, content_id: str) -> bool:
        """
        Mark content as processed
        
        Args:
            content_id: Content ID to mark as processed
            
        Returns:
            Whether marking was successful
        """
        return False
    
    @abstractmethod
    async def forward_to_category(self, content_id: str, category: str) -> bool:
        """
        Forward content to specific category
        
        Args:
            content_id: Content ID to forward
            category: Category name
            
        Returns:
            Whether forwarding was successful
        """
        return False
    
    def add_event_handler(self, event_type: str, handler: Callable[[Dict[str, Any]], Awaitable[None]]) -> bool:
        """
        Add event handler
        
        Args:
            event_type: Event type ('new_content', 'content_processed', 'error')
            handler: Event handler function
            
        Returns:
            Whether handler was added successfully
        """
        if event_type not in self.event_handlers:
            return False
        
        self.event_handlers[event_type].add(handler)
        return True
    
    def remove_event_handler(self, event_type: str, handler: Callable[[Dict[str, Any]], Awaitable[None]]) -> bool:
        """
        Remove event handler
        
        Args:
            event_type: Event type
            handler: Event handler function
            
        Returns:
            Whether handler was removed successfully
        """
        if event_type not in self.event_handlers:
            return False
        
        try:
            self.event_handlers[event_type].remove(handler)
            return True
        except KeyError:
            return False
    
    async def _notify_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """
        Notify event handlers
        
        Args:
            event_type: Event type
            data: Event data
        """
        if event_type not in self.event_handlers:
            return
        
        for handler in self.event_handlers[event_type]:
            try:
                await handler(data)
            except Exception as e:
                # Log error and continue
                print(f"Error in event handler: {str(e)}") 