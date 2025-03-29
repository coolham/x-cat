"""
通用URL提取器
用于从文本中提取URL
"""
import re
from typing import List
from urllib.parse import urlparse

class URLExtractor:
    """URL提取器"""
    
    # URL正则表达式模式
    URL_PATTERN = r'https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&\/=]*)'
    
    # 允许的URL方案
    ALLOWED_SCHEMES = {'http', 'https'}
    
    def __init__(self):
        """初始化URL提取器"""
        self.url_pattern = self.URL_PATTERN
        self.allowed_schemes = self.ALLOWED_SCHEMES.copy()
    
    def extract_urls(self, text: str) -> List[str]:
        """从文本中提取URL
        
        Args:
            text: 输入文本
            
        Returns:
            List[str]: URL列表
        """
        if not text:
            return []
            
        # 使用正则表达式提取URL
        urls = re.findall(self.url_pattern, text)
        
        # 验证URL格式
        valid_urls = []
        for url in urls:
            if self.is_valid_url(url):
                valid_urls.append(url)
                
        return valid_urls
    
    def is_valid_url(self, url: str) -> bool:
        """验证URL是否有效
        
        Args:
            url: URL字符串
            
        Returns:
            bool: 是否有效
        """
        try:
            parsed = urlparse(url)
            return bool(
                parsed.scheme and 
                parsed.netloc and 
                parsed.scheme in self.allowed_schemes
            )
        except Exception:
            return False
            
    def set_url_pattern(self, pattern: str):
        """设置URL模式
        
        Args:
            pattern: 新的URL模式
        """
        self.url_pattern = pattern
        
    def set_allowed_schemes(self, schemes: set):
        """设置允许的URL方案
        
        Args:
            schemes: 允许的URL方案集合
        """
        self.allowed_schemes = schemes 