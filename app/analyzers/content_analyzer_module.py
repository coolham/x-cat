"""
内容分析器模块类
集成内容分析器到系统框架中
"""
import os
import json
import asyncio
from typing import Dict, Any, Optional, List
import traceback

from loguru import logger

from app.core.module import Module, ModuleState
from app.analyzers.content_analyzer import ContentAnalyzer

class ContentAnalyzerModule(Module):
    """
    内容分析器模块类
    提供对消息内容的分析和分类功能
    继承自Module基类，可以集成到系统框架中
    """
    
    def __init__(self, runtime=None, module_id: str = "content_analyzer"):
        """
        初始化内容分析器模块
        
        Args:
            runtime: 运行时环境
            module_id: 模块ID
        """
        super().__init__(runtime, module_id)
        self.analyzer = None
        self.api_key = None
        self.provider = None
        self.model = None
        self.proxy_url = None
        self.max_tokens = None
        self.temperature = None
        self.max_content_length = None
        self.max_total_length = None
        
        # 订阅事件
        if runtime:
            # 订阅新消息事件
            runtime.event_bus.subscribe("new_message", self.handle_new_message)
    
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """
        初始化模块
        
        Args:
            config: 配置字典
            
        Returns:
            初始化是否成功
        """
        try:
            logger.debug(f"初始化内容分析器模块: {list(config.keys())}")
            
            # 获取配置
            analyzer_config = config.get("content_analyzer", {})
            if not analyzer_config:
                # 尝试从顶级配置获取
                analyzer_config = {
                    "api_key": config.get("api_key"),
                    "provider": config.get("provider", "openai"),
                    "model": config.get("model"),
                    "proxy_url": config.get("proxy_url"),
                    "max_tokens": config.get("max_tokens", 2000),
                    "temperature": config.get("temperature", 0.7),
                    "max_content_length": config.get("max_content_length", 8000),
                    "max_total_length": config.get("max_total_length", 15000)
                }
                logger.warning("从顶级配置构建内容分析器配置")
            
            # 保存配置
            self.api_key = analyzer_config.get("api_key")
            self.provider = analyzer_config.get("provider", "openai")
            self.model = analyzer_config.get("model")
            self.proxy_url = analyzer_config.get("proxy_url")
            self.max_tokens = analyzer_config.get("max_tokens", 2000)
            self.temperature = analyzer_config.get("temperature", 0.7)
            self.max_content_length = analyzer_config.get("max_content_length", 8000)
            self.max_total_length = analyzer_config.get("max_total_length", 15000)
            
            # 创建分析器
            self.analyzer = ContentAnalyzer(
                api_key=self.api_key,
                provider=self.provider,
                model=self.model,
                proxy_url=self.proxy_url,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                max_content_length=self.max_content_length,
                max_total_length=self.max_total_length
            )
            
            # 更新状态
            self.state = ModuleState.INITIALIZED
            logger.info(f"内容分析器模块初始化成功: provider={self.provider}, model={self.model}")
            return True
            
        except Exception as e:
            logger.error(f"内容分析器模块初始化失败: {str(e)}")
            logger.debug(traceback.format_exc())
            return False
    
    async def start(self) -> bool:
        """
        启动模块
        
        Returns:
            启动是否成功
        """
        if self.state != ModuleState.INITIALIZED:
            logger.error("内容分析器模块未初始化")
            return False
        
        try:
            # 模块已准备好运行
            self.state = ModuleState.RUNNING
            logger.info("内容分析器模块已启动")
            return True
            
        except Exception as e:
            logger.error(f"内容分析器模块启动失败: {str(e)}")
            self.state = ModuleState.ERROR
            return False
    
    async def stop(self) -> bool:
        """
        停止模块
        
        Returns:
            停止是否成功
        """
        if self.state != ModuleState.RUNNING:
            return True
        
        try:
            # 关闭分析器
            if self.analyzer:
                await self.analyzer.close()
            
            # 更新状态
            self.state = ModuleState.STOPPED
            logger.info("内容分析器模块已停止")
            return True
            
        except Exception as e:
            logger.error(f"内容分析器模块停止失败: {str(e)}")
            self.state = ModuleState.ERROR
            return False
    
    async def health_check(self) -> bool:
        """
        健康检查
        
        Returns:
            模块是否健康
        """
        return self.state == ModuleState.RUNNING and self.analyzer is not None
    
    async def handle_new_message(self, event_data: Dict[str, Any]) -> None:
        """
        处理新消息事件
        
        Args:
            event_data: 事件数据，包含消息内容
        """
        if self.state != ModuleState.RUNNING:
            logger.warning("内容分析器模块未运行，跳过消息处理")
            return
        
        try:
            message = event_data.get("message", {})
            if not message:
                logger.warning("收到空消息事件，跳过处理")
                return
            
            logger.info(f"接收到新消息: {message.get('message_id')}")
            
            # 分析消息内容
            result = await self.analyzer.analyze(message)
            
            # 处理分析结果
            if result.get("success", False):
                logger.info(f"消息分析成功: {message.get('message_id')}")
                
                # 发布分析结果事件
                if self.runtime:
                    await self.runtime.event_bus.publish(
                        "message_analyzed",
                        {
                            "message_id": message.get("message_id"),
                            "analysis_result": result
                        }
                    )
                
                # 保存分析结果到存储
                await self._store_analysis_result(message.get("message_id"), result)
                
            else:
                logger.warning(f"消息分析失败: {message.get('message_id')}, 错误: {result.get('error')}")
            
        except Exception as e:
            logger.error(f"处理消息事件失败: {str(e)}")
            logger.debug(traceback.format_exc())
    
    async def _store_analysis_result(self, message_id: str, result: Dict[str, Any]) -> None:
        """
        存储分析结果
        
        Args:
            message_id: 消息ID
            result: 分析结果
        """
        try:
            # 检查存储模块是否可用
            if not self.runtime or not self.runtime.has_module("storage"):
                logger.warning("存储模块不可用，无法保存分析结果")
                return
            
            # 获取存储模块
            storage = self.runtime.get_module("storage")
            
            # 构造分析数据
            analysis_data = {
                "message_id": message_id,
                "content_type": result.get("content_type", "未知"),
                "category": result.get("category", "未知"),
                "subcategory": result.get("subcategory", "未知"),
                "sentiment": result.get("sentiment", "未知"),
                "language": result.get("language", "未知"),
                "summary": result.get("summary", ""),
                "keywords": json.dumps(result.get("keywords", [])),
                "urls": json.dumps(result.get("urls", [])),
                "content_format": result.get("content_format", "未知"),
                "has_web_content": result.get("has_web_content", False),
                "raw_result": json.dumps(result)
            }
            
            # 保存到存储
            await storage.store_analysis(analysis_data)
            logger.debug(f"分析结果已保存: {message_id}")
            
        except Exception as e:
            logger.error(f"保存分析结果失败: {str(e)}")
            logger.debug(traceback.format_exc())
    
    async def analyze_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析单个消息
        
        Args:
            message: 消息字典
            
        Returns:
            分析结果
        """
        if self.state != ModuleState.RUNNING:
            return {"success": False, "error": "内容分析器模块未运行"}
        
        try:
            # 分析消息
            result = await self.analyzer.analyze(message)
            return result
            
        except Exception as e:
            error_msg = f"分析消息失败: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg} 