"""
内容分析器模块类
集成内容分析器到系统框架中，并使用MCP服务架构
"""
import os
import json
import asyncio
from typing import Dict, Any, Optional, List
import traceback

from loguru import logger

from app.core.module import Module, ModuleState, Event
from app.services.mcp_service import ContentAnalysisMCPService

class ContentAnalyzerModule(Module):
    """
    内容分析器模块类
    提供对消息内容的分析和分类功能
    继承自Module基类，可以集成到系统框架中
    使用MCP服务架构进行内容分析
    """
    
    def __init__(self, runtime=None, module_id: str = "content_analyzer"):
        """
        初始化内容分析器模块
        
        Args:
            runtime: 运行时环境
            module_id: 模块ID
        """
        super().__init__(runtime, module_id)
        self.mcp_service = None
        self.api_key = None
        self.provider = None
        self.model = None
        self.proxy_url = None
        self.max_tokens = None
        self.temperature = None
        self.max_content_length = None
        self.max_total_length = None
        self.max_urls = None
        self.format_type = None
        self._subscribed = False
    
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
                    "provider": config.get("provider", "openrouter"),
                    "model": config.get("model"),
                    "proxy_url": config.get("proxy_url"),
                    "max_tokens": config.get("max_tokens", 2000),
                    "temperature": config.get("temperature", 0.7),
                    "max_content_length": config.get("max_content_length", 8000),
                    "max_total_length": config.get("max_total_length", 15000),
                    "max_urls": config.get("max_urls", 5),
                    "format_type": config.get("format_type", "markdown")
                }
                logger.warning("从顶级配置构建内容分析器配置")
            
            # 保存配置
            self.api_key = analyzer_config.get("api_key")
            self.provider = analyzer_config.get("provider", "openrouter")
            self.model = analyzer_config.get("model")
            self.proxy_url = analyzer_config.get("proxy_url")
            self.max_tokens = analyzer_config.get("max_tokens", 2000)
            self.temperature = analyzer_config.get("temperature", 0.7)
            self.max_content_length = analyzer_config.get("max_content_length", 8000)
            self.max_total_length = analyzer_config.get("max_total_length", 15000)
            self.max_urls = analyzer_config.get("max_urls", 5)
            self.format_type = analyzer_config.get("format_type", "markdown")
            
            # 创建MCP服务
            self.mcp_service = ContentAnalysisMCPService(
                api_key=self.api_key,
                provider=self.provider,
                model=self.model,
                proxy_url=self.proxy_url,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                max_content_length=self.max_content_length,
                max_total_length=self.max_total_length,
                max_urls=self.max_urls,
                format_type=self.format_type
            )
            
            # 订阅事件
            if self.runtime and not self._subscribed:
                # 订阅新消息事件
                self.runtime.subscribe_event("new_message", self.handle_new_message)
                self._subscribed = True
            
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
            # 关闭MCP服务
            if self.mcp_service:
                await self.mcp_service.close()
            
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
        return self.state == ModuleState.RUNNING and self.mcp_service is not None
    
    async def handle_new_message(self, event) -> None:
        """
        处理新消息事件
        
        Args:
            event: 事件对象
        """
        if self.state != ModuleState.RUNNING:
            logger.warning("内容分析器模块未运行，忽略消息")
            return
        
        try:
            # 从事件中提取消息
            message = event.data
            
            # 提取消息ID
            message_id = message.get("message_id")
            if not message_id:
                logger.error("消息缺少ID，无法处理")
                return
            
            # 检查是否已处理过该消息
            if await self._is_message_analyzed(message_id):
                logger.debug(f"消息已分析过，跳过: {message_id}")
                return
            
            logger.info(f"处理新消息: {message_id}")
            
            # 分析消息
            try:
                result = await self.mcp_service.process(message)
            except AttributeError:
                # 处理异步模拟对象的情况
                if hasattr(self.mcp_service, 'process') and callable(self.mcp_service.process):
                    if asyncio.iscoroutinefunction(self.mcp_service.process):
                        result = await self.mcp_service.process(message)
                    else:
                        result = self.mcp_service.process(message)
                else:
                    raise AttributeError("MCP服务没有process方法")
            
            # 如果分析成功，发布分析结果事件
            if result.get("success", False):
                # 存储分析结果
                await self._store_analysis_result(message_id, result)
                
                # 发布事件
                if self.runtime:
                    event_data = {
                        "message_id": message_id,
                        "analysis_result": result
                    }
                    message_analyzed_event = Event("message_analyzed", self.module_id, event_data)
                    await self.runtime.publish_event(message_analyzed_event)
                    logger.info(f"消息分析完成并发布事件: {message_id}")
            else:
                logger.error(f"消息分析失败: {message_id} - {result.get('error', '未知错误')}")
                
        except Exception as e:
            logger.error(f"处理消息失败: {str(e)}")
            logger.debug(traceback.format_exc())
    
    async def _is_message_analyzed(self, message_id: str) -> bool:
        """
        检查消息是否已分析
        
        Args:
            message_id: 消息ID
            
        Returns:
            是否已分析
        """
        # 检查存储模块是否可用
        if not self.runtime or not self.runtime.has_module("storage"):
            return False
        
        # 获取存储模块
        storage = self.runtime.get_module("storage")
        
        # 查询是否存在分析结果
        return await storage.has_analysis(message_id)
    
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
            
            # 确保result中包含message_id
            analysis_data = result.copy()
            analysis_data["message_id"] = message_id
            
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
            # 直接使用MCP服务进行分析
            result = await self.mcp_service.process(message)
            return result
            
        except Exception as e:
            error_msg = f"分析消息失败: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg} 