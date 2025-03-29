# -*- coding: utf-8 -*-
"""
分类服务
提供AI分类接口，供其他模块调用
"""
from typing import Dict, Optional, List
from loguru import logger

from ..models.category_manager import CategoryManager
from ..ai.classifier import AIClassifier
from ..storage.category_storage import CategoryStorage

class CategoryService:
    """分类服务，提供AI分类接口"""
    
    def __init__(self):
        """初始化分类服务"""
        self.category_manager = CategoryManager()
        self.classifier = AIClassifier(self.category_manager)
        self.storage = CategoryStorage()
    
    def classify_content(self, content: str, content_id: str, language: str = 'zh') -> Dict:
        """对内容进行分类
        
        Args:
            content: 要分类的内容
            content_id: 内容ID
            language: 语言代码，默认'zh'
            
        Returns:
            Dict: 分类结果，包含以下字段：
                - primary_category: 一级分类名称
                - secondary_category: 二级分类名称（可选）
                - confidence: 分类置信度
                - reasoning: 分类理由
        """
        try:
            # 检查是否已有分类结果
            existing_result = self.storage.get_classification(content_id)
            if existing_result:
                return existing_result['classification']
            
            # 使用AI分类器进行分类
            result = self.classifier.classify(content, language)
            
            # 存储分类结果
            self.storage.store_classification(content_id, result)
            
            return result
            
        except Exception as e:
            logger.error(f"内容分类失败: {str(e)}")
            return {
                'primary_category': '其它',
                'secondary_category': '待分类内容',
                'confidence': 0.0,
                'reasoning': f'分类失败: {str(e)}'
            }
    
    def get_category_info(self, category_id: str, language: str = 'zh') -> Optional[Dict]:
        """获取分类信息
        
        Args:
            category_id: 分类ID
            language: 语言代码，默认'zh'
            
        Returns:
            Optional[Dict]: 分类信息，如果不存在则返回None
        """
        return self.category_manager.get_category_by_id(category_id, language)
    
    def get_category_path(self, category_id: str, language: str = 'zh') -> List[Dict]:
        """获取分类路径
        
        Args:
            category_id: 分类ID
            language: 语言代码，默认'zh'
            
        Returns:
            List[Dict]: 分类路径列表，从根到目标分类
        """
        return self.category_manager.get_category_path(category_id, language)
    
    def get_statistics(self) -> Dict:
        """获取分类统计信息
        
        Returns:
            Dict: 统计信息
        """
        return self.storage.get_statistics()
    
    def get_category_usage(self) -> Dict[str, int]:
        """获取分类使用次数
        
        Returns:
            Dict[str, int]: 分类使用次数
        """
        return self.storage.get_category_usage()
    
    def get_daily_stats(self, date: str = None) -> Dict:
        """获取每日统计信息
        
        Args:
            date: 日期，格式为YYYY-MM-DD，如果为None则返回最新日期
            
        Returns:
            Dict: 每日统计信息
        """
        return self.storage.get_daily_stats(date) 