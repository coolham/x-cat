"""
内容清理器
负责清理和格式化文本内容
"""
import re
from typing import Dict, Any, Optional
from loguru import logger


class ContentCleaner:
    """内容清理器"""
    
    def __init__(self):
        """初始化内容清理器"""
        # 定义需要清理的模式
        self.patterns = {
            'urls': r'https?://\S+',  # URL
            'emails': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',  # 邮箱
            'phone_numbers': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # 电话号码
            'extra_whitespace': r'\s+',  # 多余空白
            'special_chars': r'[^\w\s\u4e00-\u9fff.,!?，。！？]',  # 特殊字符
        }
        
        logger.info("内容清理器初始化成功")
    
    def clean(self, text: str) -> str:
        """清理文本内容
        
        Args:
            text: 输入文本
            
        Returns:
            str: 清理后的文本
        """
        try:
            if not text:
                return ""
                
            # 1. 移除URL
            text = re.sub(self.patterns['urls'], '', text)
            
            # 2. 移除邮箱
            text = re.sub(self.patterns['emails'], '', text)
            
            # 3. 移除电话号码
            text = re.sub(self.patterns['phone_numbers'], '', text)
            
            # 4. 移除特殊字符
            text = re.sub(self.patterns['special_chars'], '', text)
            
            # 5. 规范化空白字符
            text = re.sub(self.patterns['extra_whitespace'], ' ', text)
            
            # 6. 移除首尾空白
            text = text.strip()
            
            return text
            
        except Exception as e:
            logger.error(f"内容清理失败: {str(e)}")
            return text
    
    def clean_html(self, html: str) -> str:
        """清理HTML内容
        
        Args:
            html: HTML文本
            
        Returns:
            str: 清理后的文本
        """
        try:
            if not html:
                return ""
                
            # 1. 移除HTML标签
            text = re.sub(r'<[^>]+>', '', html)
            
            # 2. 移除HTML实体
            text = re.sub(r'&[^;]+;', '', text)
            
            # 3. 清理文本
            text = self.clean(text)
            
            return text
            
        except Exception as e:
            logger.error(f"HTML清理失败: {str(e)}")
            return html
    
    def clean_markdown(self, markdown: str) -> str:
        """清理Markdown内容
        
        Args:
            markdown: Markdown文本
            
        Returns:
            str: 清理后的文本
        """
        try:
            if not markdown:
                return ""
                
            # 1. 移除Markdown链接
            text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', markdown)
            
            # 2. 移除Markdown图片
            text = re.sub(r'!\[([^\]]*)\]\([^)]+\)', '', text)
            
            # 3. 移除Markdown格式
            text = re.sub(r'[*_`~]', '', text)
            
            # 4. 清理文本
            text = self.clean(text)
            
            return text
            
        except Exception as e:
            logger.error(f"Markdown清理失败: {str(e)}")
            return markdown 