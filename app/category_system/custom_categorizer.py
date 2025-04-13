"""
自定义分类器
"""
from typing import Dict, Any, List, Optional
from loguru import logger
import re

from .base_categorizer import BaseCategorizer


class CustomCategorizer(BaseCategorizer):
    """自定义分类器"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化自定义分类器
        
        Args:
            config: 配置信息
        """
        super().__init__(config)
        self.rules = []
        self._validate_config()
        self._init_rules()
    
    def _validate_config(self) -> bool:
        """验证配置
        
        Returns:
            bool: 配置是否有效
        """
        if 'rules' not in self.config:
            raise ValueError("自定义分类器配置缺少rules字段")
        
        for rule in self.config['rules']:
            required_fields = ['name', 'patterns', 'category', 'subcategory']
            for field in required_fields:
                if field not in rule:
                    raise ValueError(f"规则配置缺少必要字段: {field}")
            if not isinstance(rule['patterns'], list):
                raise ValueError("patterns字段必须是列表类型")
        
        return True
    
    def _init_rules(self):
        """初始化规则"""
        try:
            for rule in self.config['rules']:
                # 编译正则表达式
                patterns = [re.compile(pattern, re.I) for pattern in rule['patterns']]
                self.rules.append({
                    'name': rule['name'],
                    'patterns': patterns,
                    'category': rule['category'],
                    'subcategory': rule['subcategory']
                })
            logger.info(f"成功加载{len(self.rules)}条分类规则")
        except Exception as e:
            logger.error(f"规则初始化失败: {str(e)}")
            raise
    
    async def categorize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """分类数据
        
        Args:
            data: 输入数据
            
        Returns:
            Dict[str, Any]: 分类结果
        """
        return self.categorize_sync(data)
    
    def categorize_sync(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """同步分类数据
        
        Args:
            data: 输入数据
            
        Returns:
            Dict[str, Any]: 分类结果
        """
        try:
            # 检查内容
            content = data.get('content', '')
            if not content:
                return {
                    'success': False,
                    'error': '内容为空'
                }
            
            # 匹配规则
            for rule in self.rules:
                for pattern in rule['patterns']:
                    if pattern.search(content):
                        return {
                            'success': True,
                            'category': rule['category'],
                            'subcategory': rule['subcategory'],
                            'confidence': 1.0,
                            'source': 'custom',
                            'rule_name': rule['name']
                        }
            
            # 未找到匹配规则
            return {
                'success': False,
                'error': '未找到匹配的分类规则'
            }
            
        except Exception as e:
            logger.error(f"自定义分类失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
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
        return f"custom:content:{content_hash}" 