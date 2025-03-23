"""
内容分析器基类
"""
from abc import ABC, abstractmethod
from typing import Dict, Any


class ContentAnalyzer(ABC):
    """内容分析器基类"""
    
    @abstractmethod
    def analyze(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析内容
        
        Args:
            content: 要分析的内容
            
        Returns:
            分析结果，包括分类和总结
        """
        pass 