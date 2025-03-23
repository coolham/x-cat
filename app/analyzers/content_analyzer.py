"""
内容分析器模块
负责处理不同格式的消息内容，提取关键信息并使用AI进行分析
"""
import re
import json
import asyncio
from typing import Dict, Any, List, Optional, Tuple, Union
import traceback

from loguru import logger

from app.analyzers.ai_client import AIClient
from app.processors.content_extractor import ContentExtractor
from app.processors.content_assembler import ContentAssembler

class ContentAnalyzer:
    """
    内容分析器
    处理不同格式的消息内容，提取链接并使用AI进行分析
    
    支持的内容格式：
    1. 纯文本
    2. 文本+链接
    3. 纯链接
    
    属性:
        ai_client: AI客户端实例
        extractor: 内容提取器实例
        assembler: 内容组装器实例
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        provider: str = "openai",
        model: Optional[str] = None,
        proxy_url: Optional[str] = None,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        max_content_length: int = 8000,
        max_total_length: int = 15000
    ):
        """
        初始化内容分析器
        
        Args:
            api_key: AI服务API密钥 (可选，如不提供则从环境变量获取)
            provider: AI服务提供商，支持"openai"、"openrouter"、"deepseek"
            model: 使用的模型名称 (可选，默认由provider决定)
            proxy_url: 代理服务器URL (可选)
            max_tokens: 最大生成token数
            temperature: 温度参数
            max_content_length: 每个网页内容的最大长度限制
            max_total_length: 组装后的最大总长度
        """
        # 初始化AI客户端
        self.ai_client = AIClient(
            api_key=api_key,
            provider=provider,
            model=model,
            proxy_url=proxy_url,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        # 初始化内容提取器
        self.extractor = ContentExtractor(
            proxy_url=proxy_url,
            max_content_length=max_content_length
        )
        
        # 初始化内容组装器
        self.assembler = ContentAssembler(
            max_content_length=max_content_length,
            max_total_length=max_total_length
        )
        
        # 分析参数
        self.max_tokens = max_tokens
        self.temperature = temperature
        
        # 系统提示词
        self.system_prompt = """
        你是一个专业的内容分析助手，负责分析互联网内容并进行分类。请分析提供的内容，返回以下JSON格式的结果：
        {
            "content_type": "文章/问答/广告/新闻/列表/引用/其他",
            "category": "主题分类（如技术、健康、商业、教育等）",
            "subcategory": "更具体的子分类",
            "sentiment": "情感倾向（积极/消极/中性）",
            "keywords": ["关键词1", "关键词2", "关键词3", "关键词4", "关键词5"],
            "summary": "100字以内的内容摘要，捕捉核心信息",
            "language": "内容的主要语言",
            "urls": ["内容中包含的URL1", "URL2", ...]
        }
        
        注意事项：
        1. 确保分类准确，特别是区分内容的基本类型
        2. 摘要应简明扼要，突出重点
        3. 关键词应提取最具代表性的词语或短语
        4. 请严格按照上述JSON格式返回，不要包含其他文本
        """
        
        logger.info(f"内容分析器初始化成功: provider={provider}, model={self.ai_client.model}")
    
    async def analyze(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析消息内容
        
        Args:
            content: 消息内容字典，应包含text字段
                {
                    "message_id": "消息ID",
                    "text": "消息文本",
                    "sender_name": "发送者名称",
                    "chat_title": "聊天标题",
                    "urls": ["URL1", "URL2", ...] (可选)
                }
            
        Returns:
            分析结果字典
        """
        try:
            # 提取消息文本
            text = content.get("text", "")
            if not text.strip():
                return {
                    "success": False,
                    "error": "消息内容为空",
                    "raw_content": content
                }
            
            # 识别内容格式和提取URL
            content_type, urls = self._identify_content_format(text)
            
            # 如果消息没有提供urls字段，使用提取的URLs
            if "urls" not in content or not content["urls"]:
                content["urls"] = urls
            
            # 提取URL内容
            web_contents = []
            if content["urls"]:
                web_contents = await self._extract_url_contents(content["urls"])
            
            # 组装内容
            assembled_content = self.assembler.assemble(content, web_contents)
            
            # 调用AI分析
            success, result = await self.ai_client.analyze(
                assembled_content, 
                self.system_prompt,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            if not success:
                return {
                    "success": False,
                    "error": result.get("error", "AI分析失败"),
                    "raw_content": assembled_content[:500] + "..." if len(assembled_content) > 500 else assembled_content
                }
            
            # 确保结果包含必要的字段
            self._ensure_result_fields(result)
            
            # 添加成功标志和元数据
            result["success"] = True
            result["content_format"] = content_type
            result["has_web_content"] = len(web_contents) > 0
            result["source"] = {
                "message_id": content.get("message_id", ""),
                "sender_name": content.get("sender_name", ""),
                "chat_title": content.get("chat_title", "")
            }
            
            return result
            
        except Exception as e:
            error_msg = f"内容分析失败: {str(e)}"
            logger.error(error_msg)
            logger.debug(traceback.format_exc())
            return {
                "success": False,
                "error": error_msg,
                "raw_content": content.get("text", "")[:500] + "..." if len(content.get("text", "")) > 500 else content.get("text", "")
            }
    
    def _identify_content_format(self, text: str) -> Tuple[str, List[str]]:
        """
        识别内容格式并提取URL
        
        Args:
            text: 消息文本
            
        Returns:
            (内容格式, URL列表)
        """
        # 提取URL
        urls = self.extractor.extract_urls_from_text(text)
        
        # 识别内容格式
        # 1. 只有链接（如 @https://x.com/user/status/123456）
        if text.strip().startswith("@http") and len(urls) == 1:
            return "url_only", urls
        
        # 2. 文本和链接
        elif urls:
            return "text_with_url", urls
        
        # 3. 只有文本
        else:
            return "text_only", []
    
    async def _extract_url_contents(self, urls: List[str]) -> List[Dict[str, Any]]:
        """
        提取URL内容
        
        Args:
            urls: URL列表
            
        Returns:
            提取的内容列表
        """
        web_contents = []
        
        # 限制URL数量，避免处理太多
        urls = urls[:5]  # 最多处理5个URL
        
        # 并行提取内容
        tasks = [self.extractor.extract_from_url(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # 处理异常
                web_contents.append({
                    "url": urls[i],
                    "error": f"提取失败: {str(result)}"
                })
                continue
                
            success, content = result
            if success:
                web_contents.append(content)
            else:
                web_contents.append(content)  # 内容中已包含错误信息
        
        return web_contents
    
    def _ensure_result_fields(self, result: Dict[str, Any]) -> None:
        """
        确保结果包含所有必要字段
        
        Args:
            result: 分析结果字典
        """
        # 基本字段
        required_fields = [
            "content_type", "category", "subcategory", "sentiment", 
            "keywords", "summary", "language", "urls"
        ]
        
        # 确保所有字段都存在
        for field in required_fields:
            if field not in result:
                if field == "keywords" or field == "urls":
                    result[field] = []
                else:
                    result[field] = "未知"
        
        # 确保keywords是列表
        if not isinstance(result["keywords"], list):
            result["keywords"] = [result["keywords"]] if result["keywords"] else []
        
        # 确保urls是列表
        if not isinstance(result["urls"], list):
            result["urls"] = [result["urls"]] if result["urls"] else []
    
    async def close(self):
        """关闭资源"""
        await self.ai_client.close()
        await self.extractor.close() 