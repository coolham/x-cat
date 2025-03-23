"""
AI内容分析模块
负责对内容进行深度分析，分类，情感分析，关键词提取和摘要生成
"""
import json
import asyncio
from typing import Dict, Any, List, Optional, Tuple, Union
import traceback

from loguru import logger

from app.analyzers.ai_client import AIClient


class ContentAnalyzer:
    """
    AI内容分析模块
    负责对内容进行深度分析
    
    职责:
    1. 内容深度分析
    2. 分类和子分类
    3. 情感分析
    4. 关键词提取
    5. 摘要生成
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        provider: str = "openrouter",
        model: Optional[str] = None,
        proxy_url: Optional[str] = None,
        max_tokens: int = 2000,
        temperature: float = 0.7
    ):
        """
        初始化AI内容分析模块
        
        Args:
            api_key: AI服务API密钥
            provider: AI服务提供商 ("openrouter", "deepseek")
            model: 使用的模型
            proxy_url: 代理服务器URL
            max_tokens: 最大生成token数
            temperature: 温度参数
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
        
        logger.info(f"AI内容分析模块初始化成功: provider={provider}, model={self.ai_client.model}")
    
    async def analyze(self, assembled_content: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析内容
        
        Args:
            assembled_content: 组装后的内容字典
                {
                    "content": 组装的内容文本,
                    "metadata": 元数据字典,
                    "urls": URL列表,
                    "content_format": 内容格式,
                    "has_web_content": 是否包含网页内容
                }
                
        Returns:
            分析结果字典
        """
        try:
            # 获取内容
            content = assembled_content.get("content", "")
            if not content.strip():
                return {
                    "success": False,
                    "error": "内容为空",
                    "raw_content": assembled_content
                }
            
            # 获取元数据
            metadata = assembled_content.get("metadata", {})
            urls = assembled_content.get("urls", [])
            content_format = assembled_content.get("content_format", "text_only")
            
            # 调用AI分析
            success, result = await self.ai_client.analyze(
                content, 
                self.system_prompt,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            if not success:
                return {
                    "success": False,
                    "error": result.get("error", "AI分析失败"),
                    "raw_content": content[:500] + "..." if len(content) > 500 else content
                }
            
            # 确保结果包含必要的字段
            self._ensure_result_fields(result)
            
            # 添加成功标志和元数据
            result["success"] = True
            result["content_format"] = content_format
            result["has_web_content"] = assembled_content.get("has_web_content", False)
            
            # 添加源信息
            result["source"] = {
                "message_id": metadata.get("message_id", ""),
                "sender_name": metadata.get("sender_name", ""),
                "chat_title": metadata.get("chat_title", "")
            }
            
            # 确保URL列表包含原始URL
            if urls and "urls" in result:
                result_urls = set(result["urls"])
                for url in urls:
                    result_urls.add(url)
                result["urls"] = list(result_urls)
            
            return result
            
        except Exception as e:
            error_msg = f"内容分析失败: {str(e)}"
            logger.error(error_msg)
            logger.debug(traceback.format_exc())
            return {
                "success": False,
                "error": error_msg,
                "raw_content": content[:500] + "..." if len(content) > 500 else content
            }
    
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