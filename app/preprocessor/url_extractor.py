# -*- coding: utf-8 -*-
"""
URL提取器
负责从文本中提取URL
"""
import re
from typing import List, Dict, Any
from loguru import logger


class URLExtractor:
    """URL提取器"""
    
    def __init__(self):
        """初始化URL提取器"""
        # URL匹配模式
        self.url_pattern = r'https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&\/=]*)'
        
        logger.info("URL提取器初始化成功")
    
    def extract_urls(self, text: str) -> List[str]:
        """从文本中提取URL
        
        Args:
            text: 输入文本
            
        Returns:
            List[str]: URL列表
        """
        try:
            if not text:
                return []
                
            # 提取URL
            urls = re.findall(self.url_pattern, text)
            
            # 去重
            urls = list(set(urls))
            
            logger.debug(f"从文本中提取到 {len(urls)} 个URL")
            return urls
            
        except Exception as e:
            logger.error(f"URL提取失败: {str(e)}")
            return []
    
    def extract_urls_with_context(self, text: str) -> List[Dict[str, Any]]:
        """从文本中提取URL及其上下文
        
        Args:
            text: 输入文本
            
        Returns:
            List[Dict[str, Any]]: URL及其上下文列表
        """
        try:
            if not text:
                return []
                
            # 提取URL及其位置
            matches = re.finditer(self.url_pattern, text)
            
            results = []
            for match in matches:
                url = match.group()
                start = match.start()
                end = match.end()
                
                # 获取上下文（前后各50个字符）
                context_start = max(0, start - 50)
                context_end = min(len(text), end + 50)
                context = text[context_start:context_end]
                
                results.append({
                    "url": url,
                    "start": start,
                    "end": end,
                    "context": context
                })
            
            logger.debug(f"从文本中提取到 {len(results)} 个URL及其上下文")
            return results
            
        except Exception as e:
            logger.error(f"URL及其上下文提取失败: {str(e)}")
            return []

    def is_valid_url(self, url: str) -> bool:
        """检查URL是否有效
        
        Args:
            url: 要检查的URL
            
        Returns:
            bool: 是否有效
        """
        try:
            parsed = urlparse(url)
            return bool(parsed.scheme and parsed.netloc)
        except Exception:
            return False 