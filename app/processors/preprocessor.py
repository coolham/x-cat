"""
AI预处理模块
负责初步分析消息内容，提取和验证URL链接，识别消息类型和格式
"""
import re
from typing import Dict, Any, List, Tuple, Optional
import traceback
from urllib.parse import urlparse

from loguru import logger


class PreProcessor:
    """
    预处理模块
    负责对原始消息进行初步分析，提取URL，识别消息类型等
    
    职责:
    1. 初步分析消息内容
    2. 提取和验证URL链接
    3. 识别消息类型和格式
    4. 评估消息分析价值
    """
    
    def __init__(self, max_urls: int = 5):
        """
        初始化预处理模块
        
        Args:
            max_urls: 最大处理URL数量
        """
        self.max_urls = max_urls
        
        # URL正则表达式
        self.url_pattern = re.compile(
            r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[^\s]*'
        )
    
    async def process(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理消息
        
        Args:
            message: 消息字典，应包含text字段
                {
                    "message_id": "消息ID",
                    "text": "消息文本",
                    "sender_name": "发送者名称",
                    "chat_title": "聊天标题"
                }
                
        Returns:
            预处理结果字典
            {
                "original_message": 原始消息,
                "content_format": "消息格式(text_only/text_with_url/url_only)",
                "urls": ["URL1", "URL2", ...],
                "valid_urls": ["有效URL1", "有效URL2", ...],
                "text_content": "消息文本内容",
                "analysis_value": "分析价值评分(0-10)",
                "metadata": {
                    "lang_hint": "语言提示",
                    "has_hashtags": 是否包含标签,
                    "has_mentions": 是否包含@提及
                }
            }
        """
        try:
            # 提取消息文本
            text = message.get("text", "")
            if not text.strip():
                return {
                    "success": False,
                    "error": "消息内容为空",
                    "original_message": message
                }
            
            # 提取URL
            urls = self._extract_urls(text)
            
            # 验证URL
            valid_urls = self._validate_urls(urls)
            
            # 识别内容格式
            content_format = self._identify_content_format(text, valid_urls)
            
            # 评估分析价值
            analysis_value = self._evaluate_analysis_value(text, valid_urls)
            
            # 提取元数据
            metadata = self._extract_metadata(text)
            
            # 构建结果
            result = {
                "success": True,
                "original_message": message,
                "content_format": content_format,
                "urls": urls,
                "valid_urls": valid_urls[:self.max_urls],  # 限制URL数量
                "text_content": text,
                "analysis_value": analysis_value,
                "metadata": metadata
            }
            
            return result
            
        except Exception as e:
            error_msg = f"预处理失败: {str(e)}"
            logger.error(error_msg)
            logger.debug(traceback.format_exc())
            return {
                "success": False,
                "error": error_msg,
                "original_message": message
            }
    
    def _extract_urls(self, text: str) -> List[str]:
        """
        从文本中提取URL
        
        Args:
            text: 消息文本
            
        Returns:
            URL列表
        """
        urls = self.url_pattern.findall(text)
        return urls
    
    def _validate_urls(self, urls: List[str]) -> List[str]:
        """
        验证URL有效性
        
        Args:
            urls: URL列表
            
        Returns:
            有效URL列表
        """
        valid_urls = []
        
        for url in urls:
            try:
                # 简单验证URL结构
                parsed_url = urlparse(url)
                if parsed_url.scheme and parsed_url.netloc:
                    valid_urls.append(url)
            except Exception:
                # 忽略无效URL
                pass
        
        return valid_urls
    
    def _identify_content_format(self, text: str, urls: List[str]) -> str:
        """
        识别内容格式
        
        Args:
            text: 消息文本
            urls: URL列表
            
        Returns:
            内容格式(text_only/text_with_url/url_only)
        """
        # 1. 只有链接（如 https://x.com/user/status/123456）
        if text.strip().startswith("http") and len(urls) == 1:
            return "url_only"
        
        # 2. 文本和链接
        elif urls:
            return "text_with_url"
        
        # 3. 只有文本
        else:
            return "text_only"
    
    def _evaluate_analysis_value(self, text: str, urls: List[str]) -> int:
        """
        评估内容分析价值
        
        Args:
            text: 消息文本
            urls: URL列表
            
        Returns:
            分析价值评分(0-10)
        """
        # 简单评估逻辑，可扩展为更复杂的算法
        score = 5  # 默认中等价值
        
        # 长文本可能价值更高
        if len(text) > 500:
            score += 1
        
        # 包含URL可能价值更高
        if urls:
            score += 1
        
        # 包含多个URL可能价值更高
        if len(urls) > 1:
            score += 1
        
        # 限制范围
        return max(0, min(10, score))
    
    def _extract_metadata(self, text: str) -> Dict[str, Any]:
        """
        提取消息元数据
        
        Args:
            text: 消息文本
            
        Returns:
            元数据字典
        """
        # 简单元数据提取
        has_hashtags = "#" in text
        has_mentions = "@" in text
        
        # 简单语言检测（可扩展为更复杂的语言检测）
        lang_hint = "unknown"
        # 简单规则：中文字符比例
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        if chinese_chars / max(1, len(text)) > 0.3:
            lang_hint = "zh"
        
        return {
            "lang_hint": lang_hint,
            "has_hashtags": has_hashtags,
            "has_mentions": has_mentions
        } 