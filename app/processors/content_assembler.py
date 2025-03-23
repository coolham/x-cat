"""
内容组装模块
负责将原始消息和网页内容组合成统一格式，控制内容长度和结构
"""
from typing import Dict, Any, List, Optional, Union
import traceback

from loguru import logger


class ContentAssembler:
    """
    内容组装模块
    负责将原始消息和网页内容组合成统一格式
    
    职责:
    1. 将原始消息和网页内容组合为统一格式
    2. 控制内容长度和结构
    3. 优化内容以便AI分析
    4. 处理多语言和特殊字符
    """
    
    def __init__(
        self,
        max_content_length: int = 8000,
        max_total_length: int = 15000,
        format_type: str = "markdown"
    ):
        """
        初始化内容组装模块
        
        Args:
            max_content_length: 每个内容块的最大长度
            max_total_length: 组装后的最大总长度
            format_type: 输出格式类型 ("markdown", "text")
        """
        self.max_content_length = max_content_length
        self.max_total_length = max_total_length
        self.format_type = format_type
    
    def assemble(
        self,
        preprocessed_data: Dict[str, Any],
        web_contents: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        组装内容
        
        Args:
            preprocessed_data: 预处理后的数据
            web_contents: 网页内容列表
                每个元素是一个字典: {
                    "url": URL,
                    "success": 是否成功,
                    "content": 内容,
                    "title": 标题,
                    "type": 内容类型
                }
                
        Returns:
            组装后的内容字典
        """
        try:
            # 确保web_contents不为None
            web_contents = web_contents or []
            
            # 获取原始消息
            original_message = preprocessed_data.get("original_message", {})
            text_content = preprocessed_data.get("text_content", "")
            content_format = preprocessed_data.get("content_format", "text_only")
            
            # 组装元数据
            metadata = {
                "message_id": original_message.get("message_id", ""),
                "sender_name": original_message.get("sender_name", ""),
                "chat_title": original_message.get("chat_title", ""),
                "content_format": content_format,
                "content_metadata": preprocessed_data.get("metadata", {})
            }
            
            # 根据内容格式组装
            if content_format == "url_only":
                # 纯URL内容，主要展示网页内容
                assembled_content = self._assemble_url_only(text_content, web_contents)
            elif content_format == "text_with_url":
                # 文本+URL，展示原文和网页内容
                assembled_content = self._assemble_text_with_url(text_content, web_contents)
            else:
                # 纯文本，只展示原文
                assembled_content = self._assemble_text_only(text_content)
            
            # 控制总长度
            if len(assembled_content) > self.max_total_length:
                assembled_content = assembled_content[:self.max_total_length] + "...(内容已截断)"
            
            return {
                "content": assembled_content,
                "metadata": metadata,
                "urls": preprocessed_data.get("valid_urls", []),
                "content_format": content_format,
                "has_web_content": bool(web_contents)
            }
            
        except Exception as e:
            error_msg = f"内容组装失败: {str(e)}"
            logger.error(error_msg)
            logger.debug(traceback.format_exc())
            return {
                "content": text_content[:self.max_total_length],
                "metadata": {"error": error_msg},
                "urls": preprocessed_data.get("valid_urls", []),
                "content_format": content_format,
                "has_web_content": False
            }
    
    def _assemble_text_only(self, text: str) -> str:
        """
        组装纯文本内容
        
        Args:
            text: 原始文本
            
        Returns:
            组装后的内容
        """
        if self.format_type == "markdown":
            return f"## 原始消息\n\n{text}"
        else:
            return f"原始消息:\n\n{text}"
    
    def _assemble_text_with_url(self, text: str, web_contents: List[Dict[str, Any]]) -> str:
        """
        组装文本+URL内容
        
        Args:
            text: 原始文本
            web_contents: 网页内容列表
            
        Returns:
            组装后的内容
        """
        # 组装原始文本
        if self.format_type == "markdown":
            result = f"## 原始消息\n\n{text}\n\n"
        else:
            result = f"原始消息:\n\n{text}\n\n"
        
        # 组装网页内容
        result += self._format_web_contents(web_contents)
        
        return result
    
    def _assemble_url_only(self, text: str, web_contents: List[Dict[str, Any]]) -> str:
        """
        组装纯URL内容
        
        Args:
            text: 原始文本
            web_contents: 网页内容列表
            
        Returns:
            组装后的内容
        """
        # 对于纯URL，优先展示网页内容，原始文本作为参考
        if self.format_type == "markdown":
            result = f"## 链接内容\n\n"
        else:
            result = f"链接内容:\n\n"
        
        # 组装网页内容
        result += self._format_web_contents(web_contents)
        
        # 添加原始文本作为参考
        if self.format_type == "markdown":
            result += f"\n\n## 原始链接\n\n{text}"
        else:
            result += f"\n\n原始链接:\n\n{text}"
        
        return result
    
    def _format_web_contents(self, web_contents: List[Dict[str, Any]]) -> str:
        """
        格式化网页内容
        
        Args:
            web_contents: 网页内容列表
            
        Returns:
            格式化后的内容
        """
        if not web_contents:
            return "没有找到网页内容"
        
        result = ""
        
        for i, content in enumerate(web_contents):
            url = content.get("url", "")
            title = content.get("title", url)
            text = content.get("content", "")
            success = content.get("success", False)
            error = content.get("error", "")
            
            # 如果内容获取失败
            if not success:
                if self.format_type == "markdown":
                    result += f"### 网页 {i+1}: {title}\n\n"
                    result += f"URL: {url}\n\n"
                    result += f"获取失败: {error}\n\n"
                else:
                    result += f"网页 {i+1}: {title}\n"
                    result += f"URL: {url}\n"
                    result += f"获取失败: {error}\n\n"
                continue
            
            # 控制内容长度
            if len(text) > self.max_content_length:
                text = text[:self.max_content_length] + "...(内容已截断)"
            
            # 添加格式化内容
            if self.format_type == "markdown":
                result += f"### 网页 {i+1}: {title}\n\n"
                result += f"URL: {url}\n\n"
                result += f"{text}\n\n"
            else:
                result += f"网页 {i+1}: {title}\n"
                result += f"URL: {url}\n"
                result += f"{text}\n\n"
        
        return result
    
    def extract_metadata(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        从消息中提取元数据
        
        Args:
            message: 原始消息数据
            
        Returns:
            元数据字典
        """
        # 提取基本元数据
        metadata = {
            "message_id": message.get("message_id", ""),
            "sender_id": message.get("sender_id", ""),
            "sender_name": message.get("sender_name", ""),
            "chat_id": message.get("chat_id", ""),
            "chat_title": message.get("chat_title", ""),
            "message_type": message.get("message_type", "unknown"),
            "has_urls": len(message.get("urls", [])) > 0,
            "url_count": len(message.get("urls", [])),
            "text_length": len(message.get("text", "")),
            "has_media": bool(message.get("media_url"))
        }
        
        return metadata 