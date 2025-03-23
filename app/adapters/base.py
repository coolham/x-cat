"""
Base interface for data source adapters
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Set, Callable, Awaitable


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