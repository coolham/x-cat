"""
Telegram适配器
负责与Telegram API交互，处理消息的收发
"""
import os
import asyncio
import time
from typing import Dict, Any, Optional, List, Callable, Awaitable
from loguru import logger
from telegram import Update, Bot
from telegram.ext import (
    Application, 
    MessageHandler, 
    filters,
    ContextTypes,
    CommandHandler
)
from telegram.error import TelegramError, InvalidToken

from ..base import BaseAdapter
from .types import TelegramMessage
from .parser import TelegramMessageParser

class TelegramAdapter(BaseAdapter):
    """Telegram适配器"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化Telegram适配器
        
        Args:
            config: 配置字典
        """
        super().__init__(config)
        self.api_token = config.get("api_token")
        self.channel_id = config.get("channel_id")
        self.use_proxy = config.get("use_proxy", False)
        self.proxy_url = config.get("proxy_url")
        self.application: Optional[Application] = None
        self.bot: Optional[Bot] = None
        self._polling_task: Optional[asyncio.Task] = None
        self._stop_polling: bool = False

        if self.use_proxy and self.proxy_url:
            os.environ['HTTP_PROXY'] = self.proxy_url
            os.environ['HTTPS_PROXY'] = self.proxy_url
            logger.info(f"使用代理服务器: {self.proxy_url}")
        else:
            logger.info("不使用代理服务器")
    
    def get_source_type(self) -> str:
        """获取消息来源类型
        
        Returns:
            消息来源类型
        """
        return "telegram"
    
    async def _handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理接收到的消息"""
        try:
            logger.debug(f"收到更新: {update}")

            # 获取消息
            message = update.message or update.channel_post
            if not message:
                logger.debug("未处理的更新类型")
                return

            # 检查消息是否来自目标频道
            chat_id = message.chat.id
            chat_username = message.chat.username
            if self.channel_id.startswith('-') or self.channel_id.isdigit():
                if str(chat_id) != self.channel_id:
                    logger.debug(f"消息不来自目标频道 (ID 不匹配)，跳过...")
                    return
            else:
                if f"@{chat_username}" != self.channel_id:
                    logger.debug(f"消息不来自目标频道 (用户名不匹配)，跳过...")
                    return

            # 解析消息
            telegram_message = TelegramMessageParser.parse_message(message.to_dict())
            if not telegram_message:
                logger.warning("消息解析失败")
                return

            # 调用消息回调
            if self.message_callback:
                await self.message_callback(telegram_message)
        except Exception as e:
            logger.error(f"处理消息时出错: {str(e)}")
    
    async def _handle_update(self, update: Update):
        """处理从 Telegram 获取的更新"""
        try:
            # 获取消息
            message = update.message or update.channel_post
            if not message:
                logger.debug("未处理的更新类型")
                return

            # 检查消息是否来自目标频道
            chat_id = message.chat.id
            chat_username = message.chat.username
            if self.channel_id.startswith('-') or self.channel_id.isdigit():
                if str(chat_id) != self.channel_id:
                    logger.debug(f"消息不来自目标频道 (ID 不匹配)，跳过...")
                    return
            else:
                if f"@{chat_username}" != self.channel_id:
                    logger.debug(f"消息不来自目标频道 (用户名不匹配)，跳过...")
                    return

            # 解析消息
            telegram_message = TelegramMessageParser.parse_message(message)
            if not telegram_message:
                logger.warning("消息解析失败")
                return

            # 调用消息回调
            if self.message_callback:
                await self.message_callback(telegram_message)
        except Exception as e:
            logger.error(f"处理消息时出错: {str(e)}")
            logger.debug(f"更新对象: {update}")
            if hasattr(update, 'message') and update.message:
                logger.debug(f"消息对象: {update.message}")
            if hasattr(update, 'channel_post') and update.channel_post:
                logger.debug(f"频道消息对象: {update.channel_post}")
    

    async def initialize(self, message_callback: Callable[[Dict[str, Any]], Awaitable[None]]) -> bool:
        """初始化适配器"""
        try:
            self.message_callback = message_callback

            # 创建 Bot 实例
            self.bot = Bot(token=self.api_token)

            # 验证 Bot Token
            bot_info = await self.bot.get_me()
            logger.info(f"Bot 已验证: {bot_info.username}")

            # 验证频道访问权限
            channel = await self.bot.get_chat(self.channel_id)
            if channel.type != 'channel':
                logger.error(f"Chat {self.channel_id} 不是频道")
                return False

            logger.info("Telegram 适配器初始化成功")
            return True
        except Exception as e:
            logger.error(f"初始化 Telegram 适配器失败: {str(e)}")
            return False
    
    async def start_polling(self) -> bool:
        """启动消息轮询"""
        try:
            if not self.bot:
                logger.error("Bot 未初始化")
                return False

            logger.info("开始轮询消息...")
            self._stop_polling = False
            self._polling_task = asyncio.create_task(self._poll_updates())
            return True
        except Exception as e:
            logger.error(f"启动轮询失败: {str(e)}")
            return False

    async def _poll_updates(self):
        """轮询更新"""
        try:
            offset = 0
            while not self._stop_polling:
                try:
                    updates = await self.bot.get_updates(offset=offset, timeout=30)
                    for update in updates:
                        await self._handle_update(update)
                        offset = update.update_id + 1
                except Exception as e:
                    logger.error(f"轮询更新时出错: {str(e)}")
                    await asyncio.sleep(1)  # 出错时等待一秒后重试
        except Exception as e:
            logger.error(f"轮询任务出错: {str(e)}")

    async def stop(self):
        """停止轮询"""
        self._stop_polling = True
        if self._polling_task and not self._polling_task.done():
            self._polling_task.cancel()
            try:
                await self._polling_task
            except asyncio.CancelledError:
                pass
            self._polling_task = None
            
        if self.application:
            try:
                if self.application.updater:
                    self.application.updater.stop()
                await self.application.stop()
                logger.info("Telegram适配器停止轮询")
            except Exception as e:
                logger.error(f"停止应用时出错: {str(e)}")
    
    async def close(self) -> None:
        """关闭适配器"""
        await self.stop()
        logger.info("Telegram适配器已关闭")
    
    async def get_messages(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取消息
        
        Args:
            limit: 获取消息的最大数量
            
        Returns:
            List[Dict]: 消息列表
        """
        if not self.bot:
            logger.error("Bot 未初始化")
            return []
            
        try:
            # 获取频道消息
            messages = await self.bot.get_chat_history(self.channel_id, limit=limit)
            result = []
            
            for message in messages:
                if message.text:
                    result.append({
                        'message_id': message.message_id,
                        'text': message.text,
                        'date': message.date,
                        'chat_id': message.chat.id
                    })
            
            return result
        except Exception as e:
            logger.error(f"获取消息时出错: {str(e)}")
            return []
    
    async def send_message(self, message: Dict[str, Any]) -> bool:
        """发送消息
        
        Args:
            message: 消息内容
            
        Returns:
            bool: 是否发送成功
        """
        if not self.bot:
            logger.error("Bot 未初始化")
            return False
            
        try:
            text = message.get('text', '')
            if not text:
                logger.warning("消息内容为空")
                return False
                
            result = await self.bot.send_message(
                chat_id=self.channel_id,
                text=text
            )
            
            logger.info(f"消息发送成功: {result.message_id}")
            return result
        except Exception as e:
            logger.error(f"发送消息时出错: {str(e)}")
            return False