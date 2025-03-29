"""
Telegram API adapter
"""
import os
import pytz
import asyncio
from typing import Dict, List, Any, Optional, Callable
from app.utils.logger import logger
from telegram import Bot, Update, Message
from telegram.error import TelegramError, InvalidToken

from .telegram_parser import TelegramMessageParser

class TelegramAdapter:
    """Telegram API适配器"""
    
    def __init__(self, api_key: str, channel_id: str):
        """初始化Telegram适配器
        
        Args:
            api_key: Bot Token
            channel_id: 频道ID
        """
        self.api_key = api_key
        self.channel_id = channel_id  # 保持原始格式
        self.message_callback: Optional[Callable] = None
        self.bot: Optional[Bot] = None
        self._polling_task: Optional[asyncio.Task] = None
        self._stop_polling = False
        self._received_messages: List[Dict[str, Any]] = []
        
        # 检查是否需要使用代理
        self.use_proxy = os.getenv('TELEGRAM_USE_PROXY', 'true').lower() == 'true'
        self.proxy_url = os.getenv('TELEGRAM_PROXY_URL', 'http://127.0.0.1:10808')
        
        # 设置代理环境变量
        if self.use_proxy and self.proxy_url:
            os.environ['HTTP_PROXY'] = self.proxy_url
            os.environ['HTTPS_PROXY'] = self.proxy_url
            logger.info(f"使用代理服务器: {self.proxy_url}")
        else:
            logger.info("不使用代理服务器")
        
        logger.debug(f"Telegram adapter initialized: channel={channel_id}, proxy={self.use_proxy}")
        
    async def initialize(self, message_callback: Callable[[Dict[str, Any]], None]) -> bool:
        """初始化适配器
        
        Args:
            message_callback: 消息回调函数
            
        Returns:
            bool: 是否成功
        """
        try:
            self.message_callback = message_callback
            
            # 创建bot实例
            logger.debug("Creating bot instance...")
            self.bot = Bot(token=self.api_key)
            
            # 验证token
            logger.debug("Validating bot token...")
            await self.bot.get_me()
            
            # 验证频道访问权限
            logger.debug("Validating channel access...")
            channel = await self.bot.get_chat(self.channel_id)
            if channel.type != 'channel':
                logger.error(f"Chat {self.channel_id} is not a channel")
                return False
                
            logger.info("Telegram adapter initialized successfully")
            return True
            
        except InvalidToken as e:
            logger.error(f"Invalid bot token: {str(e)}")
            return False
        except TelegramError as e:
            logger.error(f"Telegram API error: {str(e)}")
            return False
        except Exception as e:
            print(e)
            logger.error(f"Failed to initialize Telegram adapter: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False
            
    async def start_polling(self) -> bool:
        """启动消息轮询
        
        Returns:
            bool: 是否成功
        """
        try:
            if not self.bot:
                logger.error("Bot not initialized")
                return False
                
            # 定义处理更新的回调函数
            async def handle_update(update: Update):
                try:
                    # 获取消息
                    message = update.message or update.channel_post
                    if not message:
                        return
                        
                    # 记录消息来源
                    chat_id = message.chat.id
                    chat_username = message.chat.username
                    logger.debug(f"Received message from chat_id: {chat_id}, username: {chat_username}")
                    logger.debug(f"Expected channel_id: {self.channel_id}")
                    logger.debug(f"Message type: {'channel_post' if update.channel_post else 'message'}")
                    logger.debug(f"Message content: {message.text}")
                        
                    # 检查消息是否来自指定频道
                    # 如果channel_id是数字格式，比较chat_id
                    # 如果channel_id是字符串格式，比较username
                    if self.channel_id.startswith('-') or self.channel_id.isdigit():
                        if str(chat_id) != self.channel_id:
                            logger.debug(f"Message not from target channel (ID mismatch), skipping...")
                            return
                    else:
                        # channel_id 是 @username 格式
                        if "@" + chat_username != self.channel_id:
                            logger.debug(f"Message not from target channel (username mismatch), skipping...")
                            return
                        
                    # 解析消息
                    message_data = TelegramMessageParser.parse_message(
                        message.to_dict(),
                        update.update_id,
                        "channel_post" if update.channel_post else "message"
                    )
                    
                    # 存储消息
                    if message_data:
                        # 确保消息数据包含必要字段
                        if 'metadata' not in message_data:
                            message_data['metadata'] = {}
                        message_data['metadata'].update({
                            'message_id': message.message_id,
                            'chat_id': message.chat.id,
                            'chat_type': message.chat.type,
                            'date': message.date,
                            'from_user': message.from_user.to_dict() if message.from_user else None,
                            'chat': message.chat.to_dict() if message.chat else None
                        })
                        
                        # 确保有content字段
                        if 'content' not in message_data:
                            message_data['content'] = message.text or message.caption or ""
                        if 'text' not in message_data:
                            message_data['text'] = message_data['content']
                            
                        self._received_messages.append(message_data)
                        logger.info(f"Received message from target channel: {message_data.get('metadata', {}).get('message_id')}")
                        logger.debug(f"Message content: {message_data.get('content', '')}")
                        logger.debug(f"Total received messages: {len(self._received_messages)}")
                    
                    # 调用回调
                    if message_data and self.message_callback:
                        await self.message_callback(message_data)
                        
                except Exception as e:
                    logger.error(f"Error handling message: {str(e)}")
                    import traceback
                    logger.error(f"Traceback: {traceback.format_exc()}")
            
            # 开始轮询
            logger.info("Starting polling...")
            self._stop_polling = False
            self._polling_task = asyncio.create_task(self._poll_updates(handle_update))
            return True
            
        except Exception as e:
            logger.error(f"Failed to start Telegram polling: {str(e)}")
            return False
            
    async def _poll_updates(self, callback):
        """轮询更新
        
        Args:
            callback: 回调函数
        """
        try:
            offset = 0
            while not self._stop_polling:
                try:
                    updates = await self.bot.get_updates(offset=offset, timeout=30)
                    for update in updates:
                        await callback(update)
                        offset = update.update_id + 1
                except Exception as e:
                    logger.error(f"Error polling updates: {str(e)}")
                    await asyncio.sleep(1)  # 出错时等待一秒后重试
                    
        except Exception as e:
            logger.error(f"Polling task error: {str(e)}")
            
    async def stop_polling(self) -> None:
        """停止消息轮询"""
        try:
            self._stop_polling = True
            if self._polling_task:
                self._polling_task.cancel()
                try:
                    await self._polling_task
                except asyncio.CancelledError:
                    pass
                self._polling_task = None
            logger.info("Telegram polling stopped")
        except Exception as e:
            logger.error(f"Error stopping Telegram polling: {str(e)}")
            
    async def get_bot_info(self) -> Dict[str, Any]:
        """获取Bot信息
        
        Returns:
            Dict[str, Any]: Bot信息
        """
        try:
            if not self.bot:
                logger.error("Bot not initialized")
                return {}
                
            bot_info = await self.bot.get_me()
            return {
                'id': bot_info.id,
                'first_name': bot_info.first_name,
                'username': bot_info.username,
                'can_join_groups': bot_info.can_join_groups,
                'can_read_all_group_messages': bot_info.can_read_all_group_messages,
                'supports_inline_queries': bot_info.supports_inline_queries
            }
        except TelegramError as e:
            logger.error(f"获取Bot信息失败: {str(e)}")
            raise
            
    async def forward_to_category(self, message_id: int, category: str) -> bool:
        """转发消息到分类频道
        
        Args:
            message_id: 消息ID
            category: 分类名称
            
        Returns:
            bool: 是否成功
        """
        try:
            if not self.bot:
                logger.error("Bot not initialized")
                return False
                
            # 获取分类频道ID
            category_channel_id = os.getenv(f'CATEGORY_CHANNEL_{category.upper()}')
            if not category_channel_id:
                logger.error(f"未找到分类 {category} 的频道ID")
                return False
                
            # 转发消息
            await self.bot.forward_message(
                chat_id=category_channel_id,
                from_chat_id=self.channel_id,
                message_id=message_id
            )
            return True
            
        except TelegramError as e:
            logger.error(f"转发消息失败: {str(e)}")
            return False
            
    def get_received_messages(self) -> List[Dict[str, Any]]:
        """获取已接收的消息列表
        
        Returns:
            List[Dict[str, Any]]: 消息列表
        """
        return self._received_messages
            
    async def close(self):
        """关闭适配器"""
        try:
            await self.stop_polling()
            logger.debug("Telegram adapter closed")
        except Exception as e:
            logger.error(f"关闭Telegram适配器失败: {str(e)}")
            raise 