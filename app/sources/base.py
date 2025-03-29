# -*- coding: utf-8 -*-
"""
信息源处理模块基类
定义信息源处理的基本接口
"""
from abc import ABC, abstractmethod
from typing import Dict, List

class Source(ABC):
    """信息源基类"""
    
    @abstractmethod
    async def get_contents(self) -> List[Dict]:
        """获取内容
        
        Returns:
            List[Dict]: 内容列表，每个内容包含以下字段：
                - id: 内容ID
                - text: 内容文本
                - source: 来源
                - metadata: 元数据
        """
        pass
    
    @abstractmethod
    async def mark_as_processed(self, content_id: str) -> bool:
        """标记内容为已处理
        
        Args:
            content_id: 内容ID
            
        Returns:
            bool: 是否标记成功
        """
        pass 