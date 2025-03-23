"""
Telegram Adapter
Telegram数据源适配器，用于从Telegram频道获取内容
"""
import os
import time
import asyncio
import datetime
from typing import Dict, Any, List, Optional, Union, Callable
import json

from loguru import logger
import httpx
import pytz  # 仍然需要pytz库
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ApplicationBuilder, ContextTypes, Defaults


class TelegramAdapter:
    """
    Telegram数据源适配器
    使用Telegram Bot API获取频道内容
    """
    
    def __init__(self, api_key: str, channel_id: str, proxy_url: Optional[str] = None):
        """
        初始化Telegram适配器
        
        Args:
            api_key: Telegram Bot API密钥
            channel_id: 目标频道ID
            proxy_url: 代理服务器URL (可选)
        """
        self.api_key = api_key
        self.channel_id = channel_id
        self.proxy_url = proxy_url
        self.base_url = f"https://api.telegram.org/bot{api_key}"
        
        # 创建异步HTTP客户端
        # httpx 0.28+ 不再支持proxies作为参数，而是使用transport参数
        # 但v20.0版本使用的是旧版httpx，所以可以直接使用proxies
        if proxy_url:
            proxies = {"http://": proxy_url, "https://": proxy_url}
            self.client = httpx.AsyncClient(proxies=proxies, timeout=30.0)
        else:
            self.client = httpx.AsyncClient(timeout=30.0)
        
        logger.debug(f"Telegram adapter initialized: channel={channel_id}, proxy={proxy_url is not None}")
        
        # 创建Telegram应用
        self.application = None
        self.bot = None
        self.message_callback = None
        self.initialized = False
        
        # 设置允许的更新类型
        self.allowed_updates = ["message", "channel_post", "edited_channel_post"]
    
    async def initialize(self, message_callback: Callable[[Dict[str, Any]], None]) -> bool:
        """
        初始化Telegram应用
        
        Args:
            message_callback: 收到新消息时的回调函数
            
        Returns:
            初始化是否成功
        """
        try:
            # 保存消息回调
            self.message_callback = message_callback
            
            # 设置默认值，使用pytz时区
            defaults = Defaults(tzinfo=pytz.UTC)
            
            # 构建应用 - 使用方法链而不是属性赋值
            builder = (
                ApplicationBuilder()
                .token(self.api_key)
                .defaults(defaults)
            )
            
            # 如果有代理，则设置代理
            if self.proxy_url:
                builder = builder.proxy_url(self.proxy_url)
            
            # 建立应用
            self.application = builder.build()
            self.bot = self.application.bot
            
            # 注册处理器 - 同时处理普通消息和频道消息
            self.application.add_handler(MessageHandler(filters.ALL, self._message_handler))
            
            # 标记为已初始化
            self.initialized = True
            logger.info(f"Telegram application initialized with channel ID: {self.channel_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Telegram application: {str(e)}")
            return False
    
    async def _message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Telegram消息处理函数
        
        Args:
            update: 更新对象
            context: 上下文对象
        """
        try:
            # 首先确定消息类型
            effective_message = None
            message_type = "unknown"
            
            if update.message:
                effective_message = update.message
                message_type = "message"
            elif update.channel_post:
                effective_message = update.channel_post
                message_type = "channel_post"
            elif update.edited_channel_post:
                effective_message = update.edited_channel_post
                message_type = "edited_channel_post"
                
            if not effective_message or not update.effective_chat:
                logger.debug(f"接收到无效更新: {update.update_id}")
                return
                
            # 获取聊天ID和用户名
            chat_id = str(update.effective_chat.id)
            username = update.effective_chat.username
            
            logger.debug(f"收到{message_type}: chat_id={chat_id}, username={username}")
            
            # 检查是否是目标频道
            if self.channel_id.startswith('@'):
                # 如果配置的是用户名格式
                channel_username = self.channel_id[1:]  # 去掉@前缀
                if username != channel_username:
                    logger.debug(f"忽略非目标频道消息: @{username} (期望: @{channel_username})")
                    return
            else:
                # 如果配置的是ID格式
                if chat_id != self.channel_id:
                    logger.debug(f"忽略非目标频道消息: {chat_id} (期望: {self.channel_id})")
                    return
            
            logger.info(f"收到目标频道消息: {chat_id}")
            
            # 解析消息
            message_dict = effective_message.to_dict()
            message_data = self._parse_message(message_dict, update.update_id, message_type)
            
            # 调用回调处理消息
            if message_data and self.message_callback:
                await self.message_callback(message_data)
                logger.debug(f"已处理消息: ID={message_data.get('message_id')}")
                
        except Exception as e:
            logger.error(f"Error handling Telegram message: {str(e)}")
            import traceback
            logger.debug(traceback.format_exc())
    
    async def start_polling(self) -> bool:
        """
        启动轮询
        
        Returns:
            启动是否成功
        """
        if not self.initialized or not self.application:
            logger.error("Cannot start polling: Telegram application not initialized")
            return False
            
        try:
            # 启动应用
            await self.application.initialize()
            await self.application.start()
            
            # 明确指定允许的更新类型
            await self.application.updater.start_polling(allowed_updates=self.allowed_updates)
            
            logger.info(f"Telegram polling started with allowed_updates={self.allowed_updates}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start Telegram polling: {str(e)}")
            import traceback
            logger.debug(traceback.format_exc())
            return False
    
    async def stop_polling(self) -> None:
        """停止轮询"""
        if self.application and self.application.updater and self.application.updater.running:
            try:
                await self.application.updater.stop()
                await self.application.stop()
                await self.application.shutdown()
                logger.info("Telegram polling stopped")
            except Exception as e:
                logger.error(f"Error stopping Telegram polling: {str(e)}")
    
    async def close(self) -> None:
        """关闭HTTP客户端和Telegram应用"""
        await self.stop_polling()
        await self.client.aclose()
    
    async def get_messages(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        获取频道消息（兼容旧API，仅用于轮询模式）
        
        Args:
            limit: 获取消息的最大数量
            
        Returns:
            消息列表，每条消息为一个字典
        """
        try:
            # 构建请求
            url = f"{self.base_url}/getUpdates"
            params = {
                "offset": -limit,
                "timeout": 10,
                "allowed_updates": json.dumps(self.allowed_updates)
            }
            
            # 发送请求
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # 验证响应
            if not data.get("ok"):
                error_msg = data.get("description", "Unknown error")
                logger.error(f"Telegram API error: {error_msg}")
                return []
            
            # 解析消息
            messages = []
            for update in data.get("result", []):
                message_type = "unknown"
                msg = None
                
                # 检查更新类型
                if "message" in update:
                    msg = update["message"]
                    message_type = "message"
                elif "channel_post" in update:
                    msg = update["channel_post"]
                    message_type = "channel_post"
                elif "edited_channel_post" in update:
                    msg = update["edited_channel_post"]
                    message_type = "edited_channel_post"
                    
                if not msg:
                    continue
                    
                # 检查是否来自目标频道
                chat_id = str(msg.get("chat", {}).get("id", ""))
                username = msg.get("chat", {}).get("username", "")
                
                # 检查是否是目标频道
                is_target = False
                if self.channel_id.startswith('@'):
                    # 如果配置的是用户名格式
                    channel_username = self.channel_id[1:]  # 去掉@前缀
                    is_target = (username == channel_username)
                else:
                    # 如果配置的是ID格式
                    is_target = (chat_id == self.channel_id)
                
                if is_target:
                    message_data = self._parse_message(msg, update["update_id"], message_type)
                    if message_data:
                        messages.append(message_data)
            
            logger.debug(f"Retrieved {len(messages)} messages from Telegram")
            return messages
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error when retrieving messages: {e.response.status_code} - {e.response.text}")
            return []
        except httpx.RequestError as e:
            logger.error(f"Request error when retrieving messages: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Error retrieving messages: {str(e)}")
            import traceback
            logger.debug(traceback.format_exc())
            return []
    
    async def send_message(self, text: str, chat_id: Optional[str] = None) -> Dict[str, Any]:
        """
        发送消息到指定聊天
        
        Args:
            text: 消息文本
            chat_id: 目标聊天ID，默认为初始化时设置的channel_id
            
        Returns:
            API响应字典
        """
        try:
            # 使用指定的chat_id或默认channel_id
            target_id = chat_id or self.channel_id
            
            if self.bot:
                # 使用Bot API发送消息
                result = await self.bot.send_message(
                    chat_id=target_id,
                    text=text,
                    parse_mode="HTML"
                )
                logger.info(f"Message sent to {target_id}")
                return {"ok": True, "result": result.to_dict()}
            else:
                # 通过HTTP API发送
                url = f"{self.base_url}/sendMessage"
                data = {
                    "chat_id": target_id,
                    "text": text,
                    "parse_mode": "HTML"
                }
                
                # 发送请求
                response = await self.client.post(url, json=data)
                response.raise_for_status()
                result = response.json()
                
                # 验证响应
                if not result.get("ok"):
                    error_msg = result.get("description", "Unknown error")
                    logger.error(f"Failed to send message: {error_msg}")
                    return {"ok": False, "error": error_msg}
                
                logger.info(f"Message sent to {target_id}")
                return result
            
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            return {"ok": False, "error": str(e)}
    
    def _parse_message(self, message: Dict[str, Any], update_id: int, message_type: str = "message") -> Optional[Dict[str, Any]]:
        """
        解析消息数据
        
        Args:
            message: Telegram API返回的消息字典
            update_id: 更新ID
            message_type: 消息类型 (message, channel_post, edited_channel_post)
            
        Returns:
            解析后的消息字典，如果不是有效消息则返回None
        """
        # 检查必要的字段
        if "message_id" not in message:
            return None
        
        # 提取消息内容
        message_id = message["message_id"]
        from_user = message.get("from", {})
        chat = message.get("chat", {})
        
        # 获取消息文本
        text = message.get("text", "")
        if not text and message.get("caption"):
            text = message.get("caption")
        
        # 处理消息中的媒体
        media_type = None
        media_url = None
        
        # 检查不同类型的媒体
        if "photo" in message and message["photo"]:
            media_type = "photo"
            # 获取最大尺寸的照片
            photo = max(message["photo"], key=lambda x: x.get("file_size", 0))
            media_url = photo.get("file_id")
        elif "video" in message:
            media_type = "video"
            media_url = message["video"].get("file_id")
        elif "document" in message:
            media_type = "document"
            media_url = message["document"].get("file_id")
        
        # 构建结构化消息
        structured_message = {
            "message_id": message_id,
            "update_id": update_id,
            "message_type": message_type,
            "from_user_id": from_user.get("id"),
            "from_user_name": from_user.get("username"),
            "chat_id": chat.get("id"),
            "chat_type": chat.get("type"),
            "chat_title": chat.get("title"),
            "text": text,
            "date": message.get("date", int(time.time())),
            "media_type": media_type,
            "media_url": media_url,
            "original_message": message
        }
        
        return structured_message 