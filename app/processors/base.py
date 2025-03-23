"""
内容处理器基类
"""
from abc import ABC, abstractmethod
from typing import Dict, Any


class ContentProcessor(ABC):
    """内容处理基类"""
    
    @abstractmethod
    def process(self, raw_content: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理原始内容
        
        Args:
            raw_content: 原始内容数据
            
        Returns:
            处理后的结构化数据
        """
        pass 