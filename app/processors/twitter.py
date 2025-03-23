"""
Twitter链接处理器
"""
import re
import logging
from typing import Dict, Any, Optional

from .base import ContentProcessor


class TwitterLinkProcessor(ContentProcessor):
    """Twitter链接处理器"""
    
    def __init__(self):
        """初始化Twitter链接处理器"""
        self.logger = logging.getLogger(__name__)
        # Twitter链接的正则表达式模式
        self.twitter_pattern = re.compile(
            r'https?://(?:www\.)?(?:twitter\.com|x\.com)/\w+/status/\d+'
        )
    
    def process(self, raw_content: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理可能包含Twitter链接的原始内容
        
        Args:
            raw_content: 原始内容数据
            
        Returns:
            处理后的结构化数据，包含提取的Twitter链接
        """
        try:
            text = raw_content.get('text', '')
            
            # 提取Twitter链接
            twitter_links = self.extract_twitter_links(text)
            
            # 构建处理后的数据
            processed_data = {
                'original_message_id': raw_content.get('id'),
                'original_text': text,
                'twitter_links': twitter_links,
                'source': raw_content.get('source', 'unknown'),
                'timestamp': raw_content.get('timestamp'),
                'processed': bool(twitter_links)
            }
            
            return processed_data
        except Exception as e:
            self.logger.error(f"处理Twitter链接失败: {str(e)}")
            return {
                'original_message_id': raw_content.get('id', 'unknown'),
                'processed': False,
                'error': str(e)
            }
    
    def extract_twitter_links(self, text: str) -> list:
        """
        从文本中提取Twitter链接
        
        Args:
            text: 要分析的文本
            
        Returns:
            提取的Twitter链接列表
        """
        if not text:
            return []
        
        matches = self.twitter_pattern.findall(text)
        return matches 