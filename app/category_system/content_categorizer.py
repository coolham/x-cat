"""
内容分类系统
"""
from typing import Dict, Any, Optional
from loguru import logger

from .ai_categorizer import AICategorizer
from .custom_categorizer import CustomCategorizer


class ContentCategorizer:
    """内容分类系统"""
    
    def __init__(self):
        """初始化内容分类系统"""
        self.ai_categorizer = None
        self.custom_categorizer = None
        logger.info("初始化内容分类系统")
    
    def initialize(self, config: Dict[str, Any]):
        """初始化分类器
        
        Args:
            config: 配置信息
        """
        if not config:
            raise ValueError("配置信息不能为空")
        
        # 初始化AI分类器
        if 'ai' in config:
            self.ai_categorizer = AICategorizer(config['ai'])
            logger.info("AI分类器初始化成功")
        
        # 初始化自定义分类器
        if 'custom' in config:
            self.custom_categorizer = CustomCategorizer(config['custom'])
            logger.info("自定义分类器初始化成功")
        
        if not self.ai_categorizer and not self.custom_categorizer:
            raise ValueError("至少需要配置一个分类器")
    
    async def categorize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """分类数据
        
        Args:
            data: 输入数据
            
        Returns:
            Dict[str, Any]: 分类结果
        """
        try:
            # 检查内容
            if not data.get('content'):
                return {
                    'success': False,
                    'error': '内容为空'
                }
            
            # 尝试AI分类
            if self.ai_categorizer:
                result = await self.ai_categorizer.categorize(data)
                if result['success']:
                    return result
            
            # AI分类失败或未配置，尝试自定义分类
            if self.custom_categorizer:
                result = self.custom_categorizer.categorize_sync(data)
                if result['success']:
                    return result
            
            # 所有分类器都失败
            return {
                'success': False,
                'error': '所有分类器都失败'
            }
            
        except Exception as e:
            logger.error(f"内容分类失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def categorize_sync(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """同步分类数据
        
        Args:
            data: 输入数据
            
        Returns:
            Dict[str, Any]: 分类结果
        """
        import asyncio
        return asyncio.run(self.categorize(data)) 