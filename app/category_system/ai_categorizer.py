"""
AI分类器
"""
from typing import Dict, Any, Optional, Tuple
from loguru import logger

from .base_categorizer import BaseCategorizer
from app.analyzers.ai_client import AIClient


class AICategorizer(BaseCategorizer):
    """AI分类器"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化AI分类器
        
        Args:
            config: 配置信息
        """
        super().__init__(config)
        self.ai_client = None
        self._validate_config()
        self._init_ai_client()
    
    def _validate_config(self) -> bool:
        """验证配置
        
        Returns:
            bool: 配置是否有效
        """
        required_fields = ['api_key', 'provider', 'model', 'system_prompt']
        for field in required_fields:
            if field not in self.config:
                raise ValueError(f"AI分类器配置缺少必要字段: {field}")
        return True
    
    def _init_ai_client(self):
        """初始化AI客户端"""
        try:
            self.ai_client = AIClient(
                api_key=self.config['api_key'],
                provider=self.config['provider'],
                model=self.config['model'],
                max_tokens=self.config.get('max_tokens', 500),
                temperature=self.config.get('temperature', 0.5)
            )
            logger.info("AI客户端初始化成功")
        except Exception as e:
            logger.error(f"AI客户端初始化失败: {str(e)}")
            raise
    
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
            
            # 调用AI分析
            success, result = await self.ai_client.analyze(
                data,
                system_prompt=self.config['system_prompt']
            )
            if not success:
                return {
                    'success': False,
                    'error': result.get('error', 'AI分析失败')
                }
            
            # 转换结果
            return {
                'success': True,
                'category': result.get('category', '未分类'),
                'subcategory': result.get('subcategory', '未分类'),
                'confidence': result.get('confidence', 0.95),  # 默认置信度为0.95
                'keywords': result.get('keywords', []),
                'summary': result.get('summary', ''),
                'source': 'ai'
            }
            
        except Exception as e:
            logger.error(f"AI分类失败: {str(e)}")
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
    
    def _get_cache_key(self, data: Dict[str, Any]) -> Optional[str]:
        """获取缓存键
        
        Args:
            data: 输入数据
            
        Returns:
            Optional[str]: 缓存键
        """
        # 使用内容的哈希值作为缓存键
        content = data.get('content', '')
        if not content:
            return None
            
        import hashlib
        content_hash = hashlib.md5(content.encode()).hexdigest()
        return f"ai:content:{content_hash}" 