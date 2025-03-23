"""
模型-上下文-协议 (MCP) 服务模块
负责整合内容分析的各个组件，形成完整的内容分析服务
"""
import asyncio
from typing import Dict, Any, List, Optional, Tuple, Union
import traceback
import time

from loguru import logger

from app.processors.preprocessor import PreProcessor
from app.processors.content_fetcher import ContentFetcher  
from app.processors.content_assembler import ContentAssembler
from app.analyzers.content_analyzer import ContentAnalyzer


class ContentAnalysisMCPService:
    """
    内容分析MCP服务
    整合预处理、内容获取、组装和分析模块，形成完整的内容分析服务
    
    遵循模型-上下文-协议(Model-Context-Protocol)架构:
    - 模型(Model): 内容分析模型，负责实际的分析和推理
    - 上下文(Context): 原始消息、提取的网页内容和组装的分析数据
    - 协议(Protocol): 定义数据流转格式和处理规则
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        provider: str = "openrouter",
        model: Optional[str] = None,
        proxy_url: Optional[str] = None,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        max_content_length: int = 8000,
        max_total_length: int = 15000,
        max_urls: int = 5,
        format_type: str = "markdown"
    ):
        """
        初始化内容分析MCP服务
        
        Args:
            api_key: AI服务API密钥
            provider: AI服务提供商
            model: 使用的模型
            proxy_url: 代理服务器URL
            max_tokens: 最大生成token数
            temperature: 温度参数
            max_content_length: 每个内容块的最大长度
            max_total_length: 组装后的最大总长度
            max_urls: 最大处理URL数量
            format_type: 输出格式类型
        """
        # 创建各个模块实例
        self.preprocessor = PreProcessor(max_urls=max_urls)
        
        self.content_fetcher = ContentFetcher(
            proxy_url=proxy_url,
            max_content_length=max_content_length
        )
        
        self.content_assembler = ContentAssembler(
            max_content_length=max_content_length,
            max_total_length=max_total_length,
            format_type=format_type
        )
        
        self.content_analyzer = ContentAnalyzer(
            api_key=api_key,
            provider=provider,
            model=model,
            proxy_url=proxy_url,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        # 服务配置
        self.config = {
            "api_key": api_key,
            "provider": provider,
            "model": model,
            "proxy_url": proxy_url,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "max_content_length": max_content_length,
            "max_total_length": max_total_length,
            "max_urls": max_urls,
            "format_type": format_type
        }
        
        logger.info(f"内容分析MCP服务初始化成功: provider={provider}, model={model}")
    
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
            分析结果字典
        """
        start_time = time.time()
        
        try:
            # 1. 预处理阶段
            logger.debug(f"预处理消息: {message.get('message_id', '')}")
            preprocessed_data = await self.preprocessor.process(message)
            
            if not preprocessed_data.get("success", False):
                logger.error(f"预处理失败: {preprocessed_data.get('error', '未知错误')}")
                return preprocessed_data
            
            # 2. 获取网页内容
            web_contents = []
            if preprocessed_data.get("valid_urls"):
                logger.debug(f"获取URL内容: {preprocessed_data['valid_urls']}")
                web_contents = await self.content_fetcher.fetch(preprocessed_data["valid_urls"])
            
            # 3. 组装内容
            logger.debug("组装内容")
            assembled_data = self.content_assembler.assemble(preprocessed_data, web_contents)
            
            # 4. AI分析
            logger.debug("AI分析内容")
            analysis_result = await self.content_analyzer.analyze(assembled_data)
            
            # 记录处理时间
            duration = time.time() - start_time
            logger.info(f"内容分析完成: {message.get('message_id', '')}, 耗时: {duration:.2f}秒")
            
            # 添加处理元数据
            analysis_result["processing"] = {
                "duration": duration,
                "preprocessor": "success" if preprocessed_data.get("success") else "failed",
                "web_content": "success" if web_contents else "skipped",
                "urls_processed": len(web_contents),
                "content_length": len(assembled_data.get("content", "")),
                "provider": self.config["provider"],
                "model": self.config["model"]
            }
            
            return analysis_result
            
        except Exception as e:
            error_msg = f"内容分析服务处理失败: {str(e)}"
            logger.error(error_msg)
            logger.debug(traceback.format_exc())
            
            # 记录处理时间
            duration = time.time() - start_time
            
            return {
                "success": False,
                "error": error_msg,
                "processing": {
                    "duration": duration,
                    "error_stage": "unknown"
                },
                "raw_message": message
            }
    
    async def close(self):
        """关闭资源"""
        tasks = [
            self.content_fetcher.close(),
            self.content_analyzer.close()
        ]
        await asyncio.gather(*tasks, return_exceptions=True)
        logger.info("内容分析MCP服务已关闭") 