"""
Telegram Adapter Module
基于模块化架构实现的Telegram数据源适配器
"""
import os
import time
import json
import asyncio
from typing import Dict, Any, List, Set, Optional

from loguru import logger

from app.core import Module, ModuleState, Event
from app.adapters.telegram import TelegramAdapter


class TelegramAdapterModule(Module):
    """
    Telegram适配器模块
    获取Telegram频道消息并生成消息事件
    """
    
    def __init__(self, runtime, module_id="telegram_adapter"):
        """
        初始化Telegram适配器模块
        
        Args:
            runtime: 运行时引用
            module_id: 模块ID
        """
        super().__init__(runtime, module_id)
        self.adapter = None
        self.polling_task = None
        self.polling_interval = 60  # 轮询间隔，单位秒
        self.last_processed_id = 0
        self.processed_ids_file = None
        self.processed_ids: Set[int] = set()  # 已处理的消息ID集合
    
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """
        初始化模块
        
        Args:
            config: 配置字典
            
        Returns:
            初始化是否成功
        """
        try:
            # 获取Telegram适配器配置
            if "telegram_adapter" not in config:
                logger.error("缺少Telegram适配器配置")
                return False
                
            telegram_config = config["telegram_adapter"]
            
            # 检查必要参数
            required_params = ["api_key", "channel_id"]
            for param in required_params:
                if param not in telegram_config:
                    logger.error(f"缺少Telegram适配器参数: {param}")
                    return False
            
            # 保存轮询间隔
            self.polling_interval = telegram_config.get("polling_interval", 60)
            
            # 设置已处理消息ID文件路径
            self.processed_ids_file = telegram_config.get(
                "processed_messages_file", 
                os.path.join(config["system"]["data_dir"], "processed_messages.txt")
            )
            
            # 加载已处理消息ID
            self._load_processed_ids()
            
            # 创建Telegram适配器
            logger.info(f"正在创建Telegram适配器: API密钥={telegram_config['api_key'][:5]}***, 频道={telegram_config['channel_id']}")
            self.adapter = TelegramAdapter(
                api_key=telegram_config["api_key"],
                channel_id=telegram_config["channel_id"],
                proxy_url=telegram_config.get("proxy_url")
            )
            
            # 初始化适配器
            logger.info("正在初始化Telegram适配器...")
            result = await self.adapter.initialize(self._message_callback)
            if not result:
                logger.error("Failed to initialize Telegram application")
                return False
            
            # 更新状态
            self.state = ModuleState.INITIALIZED
            logger.info(f"Telegram adapter module initialized with channel: {telegram_config['channel_id']}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Telegram adapter module: {str(e)}")
            return False
    
    async def start(self) -> bool:
        """
        启动模块
        
        Returns:
            启动是否成功
        """
        if self.state != ModuleState.INITIALIZED:
            logger.error("Telegram adapter module not initialized")
            return False
        
        try:
            # 启动轮询
            logger.info("正在启动Telegram轮询...")
            result = await self.adapter.start_polling()
            if not result:
                logger.error("Failed to start Telegram polling")
                return False
                
            # 启动轮询任务
            logger.info("创建消息轮询任务...")
            self.polling_task = asyncio.create_task(self._polling_loop())
            
            # 更新状态
            self.state = ModuleState.RUNNING
            logger.info("Telegram message polling started")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start Telegram adapter module: {str(e)}")
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
            # 取消轮询任务
            if self.polling_task:
                logger.info("正在取消轮询任务...")
                self.polling_task.cancel()
                try:
                    await self.polling_task
                except asyncio.CancelledError:
                    pass
            
            # 停止轮询
            logger.info("正在停止Telegram轮询...")
            await self.adapter.stop_polling()
            
            # 保存已处理消息ID
            self._save_processed_ids()
            
            # 更新状态
            self.state = ModuleState.STOPPED
            logger.info("Telegram adapter module stopped")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop Telegram adapter module: {str(e)}")
            self.state = ModuleState.ERROR
            return False
    
    async def health_check(self) -> bool:
        """
        健康检查
        
        Returns:
            模块是否健康
        """
        adapter_healthy = self.adapter is not None
        polling_task_healthy = self.polling_task is not None and not self.polling_task.done()
        
        return self.state == ModuleState.RUNNING and adapter_healthy and polling_task_healthy
    
    async def _message_callback(self, message_data: Dict[str, Any]) -> None:
        """
        消息回调函数
        
        Args:
            message_data: 消息数据
        """
        try:
            # 获取消息ID
            message_id = message_data.get("message_id")
            update_id = message_data.get("update_id")
            message_type = message_data.get("message_type", "unknown")
            
            if not message_id:
                logger.warning(f"收到无效消息，缺少message_id: {json.dumps(message_data, ensure_ascii=False)[:100]}")
                return
            
            text = message_data.get("text", "")    
            logger.info(f"收到Telegram消息: ID={message_id}, 类型={message_type}, 文本={text[:30]}")
                
            # 检查是否已处理过
            if message_id in self.processed_ids:
                logger.debug(f"跳过已处理消息: {message_id}")
                return
                
            # 标记为已处理
            self.processed_ids.add(message_id)
            if len(self.processed_ids) > 1000:  # 限制集合大小
                # 只保留最近的500条
                self.processed_ids = set(sorted(list(self.processed_ids))[-500:])
            
            # 更新最后处理的消息ID
            if message_id > self.last_processed_id:
                self.last_processed_id = message_id
            
            # 发布新消息事件
            event = Event(
                event_type="new_message",
                source=self.module_id,
                data=message_data
            )
            
            logger.info(f"正在发布新消息事件: ID={message_id}, 文本={text[:30]}")
            await self.runtime.publish_event(event)
            logger.debug(f"消息事件已发布: {message_id}")
            
        except Exception as e:
            logger.error(f"处理消息回调时出错: {str(e)}")
            import traceback
            logger.debug(traceback.format_exc())
    
    async def _polling_loop(self) -> None:
        """轮询循环"""
        logger.debug("开始消息轮询循环")
        
        while True:
            try:
                # 手动获取消息，作为消息处理器的补充
                # 这是为了防止错过处理器未捕获的消息
                logger.debug(f"正在轮询获取消息...")
                messages = await self.adapter.get_messages(100)
                if messages:
                    logger.info(f"轮询获取到 {len(messages)} 条消息")
                    for message in messages:
                        await self._process_message(message)
                
                # 等待下一次轮询
                await asyncio.sleep(self.polling_interval)
                
            except asyncio.CancelledError:
                logger.debug("消息轮询循环被取消")
                break
            except Exception as e:
                logger.error(f"消息轮询循环出错: {str(e)}")
                import traceback
                logger.debug(traceback.format_exc())
                await asyncio.sleep(10)  # 错误后等待一段时间再重试
    
    async def _process_message(self, message: Dict[str, Any]) -> None:
        """
        处理消息
        
        Args:
            message: 消息数据
        """
        # 委托给回调函数处理
        await self._message_callback(message)
    
    def _load_processed_ids(self) -> None:
        """加载已处理消息ID"""
        self.processed_ids = set()
        self.last_processed_id = 0
        
        try:
            if os.path.exists(self.processed_ids_file):
                with open(self.processed_ids_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:
                        # 尝试读取最后处理的ID
                        self.last_processed_id = int(content)
                        # 将最后处理的ID也加入已处理集合
                        self.processed_ids.add(self.last_processed_id)
            
            logger.info(f"已加载最后处理的消息ID: {self.last_processed_id}")
            
        except Exception as e:
            logger.error(f"加载已处理消息ID时出错: {str(e)}")
    
    def _save_processed_ids(self) -> None:
        """保存已处理消息ID"""
        try:
            # 创建目录（如果不存在）
            os.makedirs(os.path.dirname(os.path.abspath(self.processed_ids_file)), exist_ok=True)
            
            # 保存最后处理的ID
            with open(self.processed_ids_file, 'w', encoding='utf-8') as f:
                f.write(str(self.last_processed_id))
                
            logger.debug(f"已保存最后处理的消息ID: {self.last_processed_id}")
            
        except Exception as e:
            logger.error(f"保存已处理消息ID时出错: {str(e)}") 