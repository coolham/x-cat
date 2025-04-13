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
        self.api_key = config.get("api_key")
        self.channel_id = config.get("channel_id")
        self.use_proxy = config.get("use_proxy", False)
        self.proxy_url = config.get("proxy_url")
        self.application: Optional[Application] = None
        self.bot: Optional[Bot] = None
        self._polling_task: Optional[asyncio.Task] = None
        self._stop_polling: bool = False
        self.message_callback: Optional[Callable[[Dict[str, Any]], Awaitable[None]]] = None

        logger.info(f"Telegram适配器初始化，配置: channel_id={self.channel_id}, use_proxy={self.use_proxy}")
        if self.use_proxy and self.proxy_url:
            os.environ['HTTP_PROXY'] = self.proxy_url
            os.environ['HTTPS_PROXY'] = self.proxy_url
            logger.info(f"使用代理服务器: {self.proxy_url}")
        else:
            logger.info("不使用代理服务器")
    
    async def initialize(self, message_callback: Callable[[Dict[str, Any]], Awaitable[None]]) -> bool:
        """初始化适配器"""
        try:
            logger.info(f"开始初始化Telegram适配器，API密钥长度: {len(self.api_key) if self.api_key else 0}")
            if not self.api_key:
                logger.error("Telegram API密钥未设置")
                return False
                
            self.message_callback = message_callback

            # 创建 Bot 实例
            logger.info("创建Telegram Bot实例...")
            self.bot = Bot(token=self.api_key)

            # 验证 Bot Token
            logger.info("测试Telegram Bot连接...")
            bot_info = await self.bot.get_me()
            logger.info(f"Bot连接成功: @{bot_info.username} (ID: {bot_info.id})")

            # 验证频道访问权限
            logger.info(f"验证频道访问权限: {self.channel_id}")
            channel = await self.bot.get_chat(self.channel_id)
            if channel.type != 'channel':
                logger.error(f"Chat {self.channel_id} 不是频道")
                return False
            logger.info(f"频道验证成功: {channel.title}")

            logger.info("Telegram 适配器初始化成功")
            return True
        except Exception as e:
            logger.error(f"初始化 Telegram 适配器失败: {str(e)}")
            logger.debug(f"详细错误信息: {e.__class__.__name__}: {str(e)}")
            return False

    def get_source_type(self) -> str:
        """获取消息来源类型
        
        Returns:
            消息来源类型
        """
        return "telegram"
    
    async def _handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理接收到的消息"""
        try:
            logger.info(f"收到Telegram消息: update_id={update.update_id}")

            # 获取消息
            message = update.message or update.channel_post
            if not message:
                logger.debug("消息对象为空，跳过处理")
                return

            # 检查消息是否来自目标频道
            chat_id = message.chat.id
            chat_username = message.chat.username
            logger.debug(f"消息来源: chat_id={chat_id}, username=@{chat_username}")
            
            if self.channel_id.startswith('-') or self.channel_id.isdigit():
                if str(chat_id) != self.channel_id:
                    logger.debug(f"消息不来自目标频道 (ID 不匹配)，跳过...")
                    return
            else:
                if f"@{chat_username}" != self.channel_id:
                    logger.debug(f"消息不来自目标频道 (用户名不匹配)，跳过...")
                    return

            # 解析消息
            logger.debug("开始解析Telegram消息...")
            telegram_message = TelegramMessageParser.parse_message(message)
            if not telegram_message:
                logger.warning("消息解析失败")
                return
                
            logger.info(f"消息解析成功: message_id={telegram_message.message_id}, message={telegram_message}")

            # 调用消息回调
            if self.message_callback:
                logger.debug("调用消息回调函数...")
                await self.message_callback(telegram_message)
                logger.debug("消息回调函数执行完成")
        except Exception as e:
            logger.error(f"处理消息时出错: {str(e)}")
            logger.debug(f"更新对象: {update}")
            if hasattr(update, 'message') and update.message:
                logger.debug(f"消息对象: {update.message}")
            if hasattr(update, 'channel_post') and update.channel_post:
                logger.debug(f"频道消息对象: {update.channel_post}")
    
    async def _handle_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理命令消息"""
        try:
            logger.debug(f"收到命令: {update.message.text}")
            # 这里可以添加命令处理逻辑
        except Exception as e:
            logger.error(f"处理命令时出错: {str(e)}")
    
    async def start_polling(self) -> bool:
        """启动消息轮询"""
        try:
            if not self.bot:
                logger.error("Bot 未初始化")
                return False

            logger.info("开始轮询消息...")
            self._stop_polling = False
            self._polling_task = asyncio.create_task(self._poll_updates())
            logger.info("轮询任务已创建")

            # 发送启动成功消息
            try:
                start_message = f"🤖 X-Cat 服务已启动\n⏰ 时间: {time.strftime('%Y-%m-%d %H:%M:%S')}"
                await self.bot.send_message(
                    chat_id=self.channel_id,
                    text=start_message
                )
                logger.info("已发送启动成功消息")
            except Exception as e:
                logger.error(f"发送启动成功消息失败: {str(e)}")

            return True
        except Exception as e:
            logger.error(f"启动轮询失败: {str(e)}")
            return False

    async def _poll_updates(self):
        """轮询更新"""
        try:
            offset = 0
            logger.info("开始轮询Telegram消息...")
            while not self._stop_polling:
                try:
                    logger.debug(f"获取更新，offset={offset}")
                    updates = await self.bot.get_updates(offset=offset, timeout=30)
                    if updates:
                        logger.info(f"收到 {len(updates)} 条新消息")
                        for update in updates:
                            logger.debug(f"处理更新: update_id={update.update_id}")
                            await self._handle_message(update, None)
                            offset = update.update_id + 1
                    else:
                        logger.debug("没有新消息")
                except Exception as e:
                    logger.error(f"轮询更新时出错: {str(e)}")
                    logger.debug(f"详细错误信息: {e.__class__.__name__}: {str(e)}")
                    await asyncio.sleep(1)  # 出错时等待一秒后重试
        except Exception as e:
            logger.error(f"轮询任务出错: {str(e)}")
            logger.debug(f"详细错误信息: {e.__class__.__name__}: {str(e)}")
        finally:
            logger.info("Telegram轮询任务结束")

    async def stop(self):
        """停止轮询"""
        logger.info("正在停止Telegram轮询...")
        self._stop_polling = True
        if self._polling_task and not self._polling_task.done():
            logger.debug("取消轮询任务...")
            self._polling_task.cancel()
            try:
                await self._polling_task
            except asyncio.CancelledError:
                logger.debug("轮询任务已取消")
                pass
            self._polling_task = None
            
        if self.application:
            try:
                logger.debug("停止Telegram应用...")
                await self.application.stop()
                logger.info("Telegram适配器停止轮询")
            except Exception as e:
                logger.error(f"停止应用时出错: {str(e)}")
    
    async def close(self) -> None:
        """关闭适配器"""
        logger.info("正在关闭Telegram适配器...")
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
            logger.info(f"获取最近 {limit} 条消息...")
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
            
            logger.info(f"成功获取 {len(result)} 条消息")
            return result
        except Exception as e:
            logger.error(f"获取消息时出错: {str(e)}")
            logger.debug(f"详细错误信息: {e.__class__.__name__}: {str(e)}")
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
                
            logger.info(f"发送消息到频道 {self.channel_id}，内容长度: {len(text)}")
            result = await self.bot.send_message(
                chat_id=self.channel_id,
                text=text
            )
            
            logger.info(f"消息发送成功: {result.message_id}")
            return result
        except Exception as e:
            logger.error(f"发送消息时出错: {str(e)}")
            logger.debug(f"详细错误信息: {e.__class__.__name__}: {str(e)}")
            return False