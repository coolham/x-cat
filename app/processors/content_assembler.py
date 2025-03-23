"""
内容组装器模块
负责将原始消息和网页内容组合成适合AI分析的格式
"""
import re
import json
from typing import Dict, Any, List, Optional, Tuple, Union

from loguru import logger

class ContentAssembler:
    """
    内容组装器
    将原始消息和提取的网页内容组合成统一的Markdown格式
    
    属性:
        max_content_length: 每个网页内容的最大长度限制
        max_total_length: 组装后的最大总长度
    """
    
    def __init__(
        self,
        max_content_length: int = 8000,
        max_total_length: int = 15000
    ):
        """
        初始化内容组装器
        
        Args:
            max_content_length: 每个网页内容的最大长度限制
            max_total_length: 组装后的最大总长度
        """
        self.max_content_length = max_content_length
        self.max_total_length = max_total_length
        
        logger.debug(f"内容组装器初始化成功: max_content_length={max_content_length}, max_total_length={max_total_length}")
    
    def assemble(
        self, 
        message: Dict[str, Any], 
        web_contents: List[Dict[str, Any]]
    ) -> str:
        """
        组装内容为Markdown格式
        
        Args:
            message: 原始消息数据
            web_contents: 提取的网页内容列表
            
        Returns:
            组装后的Markdown格式内容
        """
        # 构建Markdown内容
        sections = []
        
        # 添加原始消息部分
        message_section = self._format_message(message)
        sections.append(message_section)
        
        # 添加网页内容部分
        if web_contents:
            sections.append("\n## 网页内容\n")
            
            for i, content in enumerate(web_contents):
                if "error" in content and content["error"]:
                    # 网页内容提取失败
                    sections.append(f"\n### {i+1}. URL: {content.get('url', '未知URL')}\n")
                    sections.append(f"*提取失败: {content['error']}*\n")
                else:
                    # 网页内容提取成功
                    title = content.get("title", "无标题")
                    url = content.get("url", "")
                    web_content = content.get("content", "")
                    
                    # 限制内容长度
                    if len(web_content) > self.max_content_length:
                        web_content = web_content[:self.max_content_length] + "...(内容已截断)"
                    
                    sections.append(f"\n### {i+1}. {title}\n")
                    sections.append(f"**URL**: {url}\n")
                    sections.append(f"\n{web_content}\n")
        
        # 组合所有部分
        full_content = "\n".join(sections)
        
        # 检查总长度并截断（如有必要）
        if len(full_content) > self.max_total_length:
            full_content = full_content[:self.max_total_length] + "\n\n...(内容已截断，超过最大长度限制)"
            logger.warning(f"组装内容已截断，原始长度超过最大限制: {len(full_content)} > {self.max_total_length}")
        
        return full_content
    
    def _format_message(self, message: Dict[str, Any]) -> str:
        """
        格式化原始消息为Markdown
        
        Args:
            message: 原始消息数据
            
        Returns:
            格式化后的Markdown内容
        """
        # 提取消息数据
        message_id = message.get("message_id", "未知ID")
        sender_name = message.get("sender_name", "未知发送者")
        chat_title = message.get("chat_title", "未知频道")
        text = message.get("text", "")
        
        # 构建Markdown
        md = [
            "# 待分析内容\n",
            f"**来源**: {chat_title}",
            f"**发送者**: {sender_name}\n",
            "## 原始消息\n",
            f"{text}\n"
        ]
        
        # 提取消息中的URL（作为参考）
        urls = message.get("urls", [])
        if urls:
            md.append("\n## 消息中的链接\n")
            for i, url in enumerate(urls):
                md.append(f"{i+1}. {url}")
        
        return "\n".join(md)
    
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