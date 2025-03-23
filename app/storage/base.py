"""
存储后端基类
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List


class StorageBackend(ABC):
    """存储后端基类"""
    
    @abstractmethod
    def save(self, analyzed_content: Dict[str, Any]) -> bool:
        """
        保存分析后的内容
        
        Args:
            analyzed_content: 分析后的内容
            
        Returns:
            是否成功保存
        """
        pass
    
    @abstractmethod
    def get_by_id(self, content_id: str) -> Dict[str, Any]:
        """
        通过ID获取内容
        
        Args:
            content_id: 内容ID
            
        Returns:
            获取的内容
        """
        pass
    
    @abstractmethod
    def get_by_category(self, category: str) -> List[Dict[str, Any]]:
        """
        获取特定类别的所有内容
        
        Args:
            category: 内容类别
            
        Returns:
            内容列表
        """
        pass 