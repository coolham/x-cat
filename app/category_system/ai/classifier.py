# -*- coding: utf-8 -*-
"""
AI分类器
负责使用AI模型对内容进行分类
"""
from typing import Dict, Optional, Any
from loguru import logger

from app.core.processors import BaseProcessor
from ..models.category_manager import CategoryManager

class AIClassifier(BaseProcessor):
    """AI分类器，负责使用AI模型对内容进行分类"""
    
    def __init__(self, config: Dict[str, Any], runtime: Any):
        """初始化AI分类器
        
        Args:
            config: 配置字典
            runtime: 运行时环境
        """
        super().__init__(config, runtime)
        self.category_manager = None
    
    async def initialize(self) -> bool:
        """初始化分类器
        
        Returns:
            bool: 是否成功
        """
        try:
            # 检查运行时环境
            if not hasattr(self.runtime, 'category_manager'):
                raise RuntimeError("运行时环境未正确初始化")
                
            self.category_manager = self.runtime.category_manager
            return True
            
        except Exception as e:
            logger.error(f"AI分类器初始化失败: {str(e)}")
            return False
    
    async def classify(self, content: str, language: str = 'zh') -> Dict:
        """对内容进行分类
        
        Args:
            content: 要分类的内容
            language: 语言代码，默认'zh'
            
        Returns:
            Dict: 分类结果，包含以下字段：
                - primary_category: 一级分类名称
                - secondary_category: 二级分类名称（可选）
                - confidence: 分类置信度
                - reasoning: 分类理由
        """
        try:
            if not content:
                return {
                    'primary_category': '其它',
                    'secondary_category': '待分类内容',
                    'confidence': 0.0,
                    'reasoning': '内容为空'
                }
            
            # 获取AI提示词
            prompt = self.category_manager.get_ai_prompt(language)
            if not prompt:
                raise ValueError("获取AI提示词失败")
            
            # 构建完整提示词
            full_prompt = f"{prompt}\n\n内容：\n{content}"
            
            # 使用关键词匹配进行分类
            result = self._classify_by_keywords(content, language)
            
            return result
            
        except Exception as e:
            logger.error(f"AI分类失败: {str(e)}")
            return {
                'primary_category': '其它',
                'secondary_category': '待分类内容',
                'confidence': 0.0,
                'reasoning': f'分类失败: {str(e)}'
            }
    
    def _classify_by_keywords(self, content: str, language: str) -> Dict:
        """使用关键词匹配进行分类
        
        Args:
            content: 要分类的内容
            language: 语言代码
            
        Returns:
            Dict: 分类结果
        """
        # 定义关键词映射
        keywords = {
            'ai': ['人工智能', 'AI', '机器学习', '深度学习', 'artificial intelligence', 'machine learning', 'deep learning'],
            'programming': ['编程', '开发', '代码', '软件', 'programming', 'development', 'code', 'software'],
            'electronics': ['电子', '硬件', '电路', '元器件', 'electronics', 'hardware', 'circuit', 'component'],
            'crypto': ['区块链', '比特币', '加密货币', 'NFT', 'blockchain', 'bitcoin', 'cryptocurrency'],
            'tech': ['科技', '技术', '创新', '产品', 'technology', 'innovation', 'product'],
            'personal': ['学习', '成长', '效率', '思维', 'learning', 'growth', 'efficiency', 'thinking'],
            'health': ['健康', '饮食', '运动', '医疗', 'health', 'diet', 'exercise', 'medical'],
            'finance': ['理财', '投资', '股票', '基金', 'finance', 'investment', 'stock', 'fund'],
            'travel': ['旅游', '旅行', '景点', '攻略', 'travel', 'tourism', 'attraction', 'guide'],
            'sports': ['运动', '体育', '健身', '训练', 'sports', 'fitness', 'training']
        }
        
        # 计算关键词匹配度
        max_matches = 0
        best_category = None
        
        for category, words in keywords.items():
            matches = sum(1 for word in words if word.lower() in content.lower())
            if matches > max_matches:
                max_matches = matches
                best_category = category
        
        if best_category:
            # 获取分类信息
            category_info = self.category_manager.get_category_by_id(best_category)
            if category_info:
                return {
                    'primary_category': category_info['name'],
                    'secondary_category': None,
                    'confidence': min(1.0, max_matches / 4),  # 简单的置信度计算
                    'reasoning': f'基于关键词匹配，匹配到{max_matches}个关键词'
                }
        
        return {
            'primary_category': '其它',
            'secondary_category': '待分类内容',
            'confidence': 0.0,
            'reasoning': '未匹配到任何关键词'
        }
