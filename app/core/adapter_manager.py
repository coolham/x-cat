from typing import Dict, Any, List, Callable, Awaitable, Optional
import asyncio
import os
from loguru import logger

from app.adapters.telegram import TelegramAdapter
from app.adapters.wechat import WeChatAdapter
from app.adapters.base import BaseAdapter
from app.extractors.telegram import TelegramExtractor

class AdapterManager:
    """适配器管理器，用于管理和协调不同的消息适配器"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化适配器管理器
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.adapters: Dict[str, Dict[str, Any]] = {}
        self.message_callback: Optional[Callable[[Dict[str, Any]], Awaitable[None]]] = None
        self.running = False
        self.tasks: List[asyncio.Task] = []
        
        # 首先从环境变量中获取代理设置
        self.http_proxy = os.environ.get("HTTP_PROXY", "")
        self.https_proxy = os.environ.get("HTTPS_PROXY", "")
        
        # 如果环境变量中有代理设置，直接使用
        if self.http_proxy or self.https_proxy:
            logger.info(f"使用环境变量中的代理设置: HTTP_PROXY={self.http_proxy}, HTTPS_PROXY={self.https_proxy}")
        else:
            # 如果环境变量中没有代理设置，尝试从配置文件中获取
            proxy_config = config.get("proxy", {})
            self.http_proxy = proxy_config.get("http_proxy", "")
            self.https_proxy = proxy_config.get("https_proxy", "")
            
            # 如果配置中有代理设置，更新环境变量
            if self.http_proxy:
                os.environ["HTTP_PROXY"] = self.http_proxy
            if self.https_proxy:
                os.environ["HTTPS_PROXY"] = self.https_proxy
                
            logger.info(f"使用配置文件中的代理设置: HTTP_PROXY={self.http_proxy}, HTTPS_PROXY={self.https_proxy}")
        
        # 记录最终的代理设置
        logger.info(f"全局代理设置: HTTP_PROXY={self.http_proxy}, HTTPS_PROXY={self.https_proxy}")
        
        # 如果启用了代理但没有配置，记录警告
        if config.get("proxy", {}).get("enabled", False) and not (self.http_proxy or self.https_proxy):
            logger.warning("代理已启用但未配置全局代理")
        
    def _get_adapter_config_with_proxy(self, adapter_config: Dict[str, Any]) -> Dict[str, Any]:
        """为适配器配置添加代理设置
        
        Args:
            adapter_config: 原始适配器配置
            
        Returns:
            添加代理设置后的配置
        """
        config = adapter_config.copy()
        
        # 检查适配器是否需要使用代理
        if config.get("use_proxy", False):
            # 优先使用HTTPS代理，如果没有则使用HTTP代理
            if self.https_proxy:
                config["proxy_url"] = self.https_proxy
                logger.info(f"已为适配器添加HTTPS代理: {self.https_proxy}")
            elif self.http_proxy:
                config["proxy_url"] = self.http_proxy
                logger.info(f"已为适配器添加HTTP代理: {self.http_proxy}")
            else:
                config["proxy_url"] = ""
                logger.warning("适配器启用了代理但未配置全局代理")
        else:
            config["proxy_url"] = ""
            
        return config
        
    async def initialize(self, message_callback: Callable[[Dict[str, Any]], Awaitable[None]]):
        """初始化适配器管理器
        
        Args:
            message_callback: 消息处理回调函数
        """
        self.message_callback = message_callback
        
        # 初始化各个适配器
        await self._initialize_telegram()
        await self._initialize_wechat()
        # 未来可以添加其他适配器
        # await self._initialize_email()
        # await self._initialize_rss()
        
        logger.info("适配器管理器初始化完成")
        
    async def _initialize_telegram(self):
        """初始化Telegram适配器"""
        telegram_config = self.config.get("telegram_adapter", {})
        if not telegram_config.get("enabled", True):
            logger.info("Telegram适配器未启用")
            return
            
        try:
            # 添加代理配置
            telegram_config = self._get_adapter_config_with_proxy(telegram_config)
            logger.info(f"Telegram适配器配置: {telegram_config}")
            
            # 创建 Telegram 适配器
            telegram_adapter = TelegramAdapter(telegram_config)
            
            # 创建 Telegram 提取器
            telegram_extractor = TelegramExtractor()
            
            # 初始化 Telegram 适配器
            if await telegram_adapter.initialize(self._handle_telegram_message):
                self.adapters["telegram"] = {
                    "adapter": telegram_adapter,
                    "extractor": telegram_extractor
                }
                logger.info("Telegram适配器初始化成功")
            else:
                logger.error("Telegram适配器初始化失败")
        except Exception as e:
            logger.error(f"初始化Telegram适配器出错: {str(e)}")
            
    async def _initialize_wechat(self):
        """初始化微信适配器"""
        wechat_config = self.config.get("wechat_adapter", {})
        if not wechat_config.get("enabled", False):  # 默认不启用
            logger.info("微信适配器未启用")
            return
            
        try:
            # 添加代理配置
            wechat_config = self._get_adapter_config_with_proxy(wechat_config)
            logger.info(f"微信适配器配置: {wechat_config}")
            
            # 创建微信适配器
            wechat_adapter = WeChatAdapter(wechat_config)
            
            # 初始化微信适配器
            if await wechat_adapter.initialize(self._handle_wechat_message):
                self.adapters["wechat"] = {
                    "adapter": wechat_adapter,
                }
                logger.info("微信适配器初始化成功")
            else:
                logger.error("微信适配器初始化失败")
        except Exception as e:
            logger.error(f"初始化微信适配器出错: {str(e)}")
            
    async def _handle_telegram_message(self, message: Dict[str, Any]):
        """处理Telegram消息
        
        Args:
            message: Telegram消息
        """
        if self.message_callback:
            try:
                # 使用 Telegram 提取器处理消息
                telegram_extractor = self.adapters["telegram"]["extractor"]
                logger.debug(f"开始处理Telegram消息: {message.message_id if hasattr(message, 'message_id') else 'unknown'}")
                extracted_data = telegram_extractor.extract(message)
                
                # 调用消息回调
                await self.message_callback(extracted_data)
            except Exception as e:
                logger.error(f"处理Telegram消息出错: {str(e)}")
                logger.debug(f"消息对象类型: {type(message)}")
                if hasattr(message, 'to_dict'):
                    logger.debug(f"消息内容: {message.to_dict()}")
            
    async def _handle_wechat_message(self, message: Dict[str, Any]):
        """处理微信消息
        
        Args:
            message: 微信消息
        """
        if self.message_callback:
            try:
                # 直接使用消息
                extracted_data = message
                
                # 添加消息来源标记
                extracted_data["source"] = "wechat"
                
                # 调用消息回调
                await self.message_callback(extracted_data)
            except Exception as e:
                logger.error(f"处理微信消息出错: {str(e)}")
            
    async def start(self):
        """启动所有适配器"""
        if self.running:
            return
            
        self.running = True
        
        # 启动各个适配器
        for name, adapter_info in self.adapters.items():
            adapter = adapter_info.get("adapter")
            if adapter and hasattr(adapter, "start_polling"):
                task = asyncio.create_task(self._start_adapter(name, adapter))
                self.tasks.append(task)
                
        logger.info("所有适配器已启动")
        
    async def _start_adapter(self, name: str, adapter: BaseAdapter):
        """启动单个适配器
        
        Args:
            name: 适配器名称
            adapter: 适配器实例
        """
        try:
            if await adapter.start_polling():
                logger.info(f"{name}适配器启动成功")
            else:
                logger.error(f"{name}适配器启动失败")
        except Exception as e:
            logger.error(f"启动{name}适配器出错: {str(e)}")
            
    async def stop(self):
        """停止所有适配器"""
        if not self.running:
            return
            
        self.running = False
        
        # 取消所有任务
        for task in self.tasks:
            if not task.done():
                task.cancel()
                
        # 等待所有任务完成
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)
            
        # 停止各个适配器
        for name, adapter in self.adapters.items():
            if hasattr(adapter, "stop"):
                try:
                    await adapter.stop()
                    logger.info(f"{name}适配器已停止")
                except Exception as e:
                    logger.error(f"停止{name}适配器出错: {str(e)}")
                    
        logger.info("所有适配器已停止")
        
    async def wait(self):
        """等待所有适配器完成"""
        if not self.running:
            return
            
        try:
            logger.info("开始等待消息...")
            # 创建一个永不完成的future，用于保持程序运行
            forever = asyncio.Future()
            # 添加一个回调，用于在future被取消时记录日志
            forever.add_done_callback(lambda f: logger.info("等待被取消"))
            await forever
        except asyncio.CancelledError:
            logger.info("等待被取消")
            raise
        finally:
            # 确保在退出时清理资源
            logger.info("正在清理资源...")
            await self.stop() 