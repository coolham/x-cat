"""
Base processor module
"""
from typing import Any, Dict, Optional
from loguru import logger
from prefect import task

class BaseProcessor:
    """Base class for all processors"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize processor
        
        Args:
            config: Processor configuration
        """
        self.config = config
        self.name = self.__class__.__name__
        self._initialized = False
        
    def initialize(self) -> None:
        """Initialize processor"""
        if self._initialized:
            return
            
        logger.info(f"Initializing processor {self.name}")
        self._initialized = True
        
    @task
    def process(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process content
        
        Args:
            content: Content to process
            
        Returns:
            Processed content
        """
        if not self._initialized:
            self.initialize()
            
        raise NotImplementedError("Subclasses must implement process()")
        
    def cleanup(self) -> None:
        """Cleanup processor resources"""
        logger.info(f"Cleaning up processor {self.name}")
        
    def get_stats(self) -> Dict[str, Any]:
        """
        Get processor statistics
        
        Returns:
            Dict[str, Any]: Statistics
        """
        return {
            'name': self.name,
            'config': self.config,
            'initialized': self._initialized
        } 