# -*- coding: utf-8 -*-
"""
Telegram消息提取器
用于从Telegram消息中提取内容
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from loguru import logger
import traceback
from .base import BaseExtractor
from .url_extractor import URLExtractor
from telegram import Bot, Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters


class TelegramExtractor(BaseExtractor):
    """Telegram内容提取器
    
    使用说明：
    1. 消息获取机制：
       - 使用轮询机制获取消息，不要使用 get_chat_history
       - 通过 Application 和 MessageHandler 处理消息
       - 支持实时接收和处理新消息
    
    2. 代理配置：
       - 默认启用代理（TELEGRAM_USE_PROXY=true）
       - 默认代理地址：http://127.0.0.1:10808
       - 可通过环境变量配置：
         * TELEGRAM_USE_PROXY：是否使用代理
         * TELEGRAM_PROXY_URL：代理服务器地址
    
    3. 时区设置：
       - 默认时区：Asia/Shanghai
       - 可通过配置修改时区
       - 支持 pytz 库支持的所有时区
    
    4. 消息处理：
       - 支持文本消息
       - 支持媒体内容（图片、视频、文档）
       - 自动提取消息元数据
       - 支持消息验证和过滤
    
    5. 配置要求：
       - api_key：Bot Token（必需）
       - channel_id：频道ID（必需）
       - proxy_url：代理服务器URL（可选）
       - polling_interval：轮询间隔（默认60秒）
       - timezone：时区设置（默认Asia/Shanghai）
    """
    
    def __init__(self, config: Dict[str, Any]):
        """初始化Telegram提取器
        
        Args:
            config: 配置字典
        """
        super().__init__()
        self.config = config
        
        # 获取配置
        telegram_config = config
        self.api_key = telegram_config.get('api_key', '')
        self.channel_id = telegram_config.get('channel_id', '')
        self.proxy_url = telegram_config.get('proxy_url')
        self.polling_interval = telegram_config.get('polling_interval', 60)
        
        # 初始化客户端
        self.bot = None
        self.application = None
        
        logger.info("Telegram提取器初始化成功")
        
    async def initialize(self) -> bool:
        """初始化提取器
        
        Returns:
            bool: 是否初始化成功
        """
        try:
            # 验证配置
            if not self.api_key:
                raise ValueError("缺少Telegram API密钥")
                
            if not self.channel_id:
                raise ValueError("缺少Telegram频道ID")
                
            # 获取时区设置
            timezone = self.config.get('timezone', 'Asia/Shanghai')
            try:
                import pytz
                tz = pytz.timezone(timezone)
            except Exception as e:
                logger.error(f"时区设置无效: {timezone}, 使用默认时区 Asia/Shanghai")
                import pytz
                tz = pytz.timezone('Asia/Shanghai')
                
            # 创建机器人实例
            self.bot = Bot(token=self.api_key)
            
            # 创建应用实例
            self.application = ApplicationBuilder().token(self.api_key).build()
            
            # 添加消息处理器
            self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_message))
            
            # 启动应用
            await self.application.initialize()
            await self.application.start()
            
            logger.info("Telegram提取器初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"Telegram提取器初始化失败: {str(e)}")
            logger.debug(traceback.format_exc())
            return False
            
    async def extract(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """从消息中提取内容
        
        Args:
            data: 消息数据
            
        Returns:
            Dict[str, Any]: 提取的内容
        """
        try:
            # 检查消息ID
            if 'metadata' not in data or 'message_id' not in data['metadata']:
                logger.warning("消息数据中缺少message_id")
                return data
                
            # 提取消息内容
            text = data.get('text', '')
            caption = data.get('caption', '')
            
            # 更新数据
            data.update({
                'text': text or caption,
                'content': text or caption,
                'message_type': self._get_message_type(data),
                'metadata': {
                    'message_id': data['metadata']['message_id'],
                    'chat_id': data.get('chat', {}).get('id'),
                    'chat_type': data.get('chat', {}).get('type'),
                    'date': data.get('date'),
                    'from_user': data.get('from_user'),
                    'chat': data.get('chat')
                }
            })
            
            logger.debug(f"成功提取消息内容: {data['metadata']['message_id']}")
            return data
            
        except Exception as e:
            logger.error(f"消息提取失败: {str(e)}")
            return data
    
    def _get_message_type(self, data: Dict[str, Any]) -> str:
        """获取消息类型
        
        Args:
            data: 消息数据
            
        Returns:
            str: 消息类型
        """
        # 从 metadata 中获取消息类型
        if 'metadata' in data:
            metadata = data['metadata']
            if metadata.get('media_type'):
                return metadata['media_type']
                
        # 如果 metadata 中没有，则从原始数据中判断
        if data.get('text'):
            return 'text'
        elif data.get('photo'):
            return 'photo'
        elif data.get('video'):
            return 'video'
        elif data.get('document'):
            return 'document'
        elif data.get('sticker'):
            return 'sticker'
        elif data.get('voice'):
            return 'voice'
        elif data.get('video_note'):
            return 'video_note'
        else:
            return 'unknown'
            
    async def _extract_photo(self, photo) -> Optional[Dict[str, Any]]:
        """提取照片信息
        
        Args:
            photo: 照片对象
            
        Returns:
            Optional[Dict[str, Any]]: 照片信息
        """
        try:
            return {
                'type': 'photo',
                'file_id': photo[-1].file_id,  # 使用最大尺寸的照片
                'width': photo[-1].width,
                'height': photo[-1].height,
                'file_size': photo[-1].file_size
            }
        except Exception as e:
            logger.error(f"提取照片信息失败: {str(e)}")
            return None
            
    async def _extract_document(self, document) -> Optional[Dict[str, Any]]:
        """提取文档信息
        
        Args:
            document: 文档对象
            
        Returns:
            Optional[Dict[str, Any]]: 文档信息
        """
        try:
            return {
                'type': 'document',
                'file_id': document.file_id,
                'file_name': document.file_name,
                'mime_type': document.mime_type,
                'file_size': document.file_size
            }
        except Exception as e:
            logger.error(f"提取文档信息失败: {str(e)}")
            return None
            
    async def _handle_message(self, update: Update, context: Any):
        """处理消息
        
        Args:
            update: 更新对象
            context: 上下文对象
        """
        try:
            message = update.message
            if not message:
                return
                
            # 提取消息内容
            content = message.text if message.text else ''
            
            # 提取媒体内容
            media = None
            if message.photo:
                media = await self._extract_photo(message.photo)
            elif message.document:
                media = await self._extract_document(message.document)
                
            # 生成元数据
            metadata = {
                'message_id': message.message_id,
                'date': message.date.isoformat() if message.date else datetime.now().isoformat(),
                'from_user': {
                    'id': message.from_user.id if message.from_user else None,
                    'username': message.from_user.username if message.from_user else None,
                    'first_name': message.from_user.first_name if message.from_user else None,
                    'last_name': message.from_user.last_name if message.from_user else None
                },
                'chat': {
                    'id': message.chat.id,
                    'type': message.chat.type,
                    'title': message.chat.title,
                    'username': message.chat.username
                },
                'source_type': 'telegram'
            }
            
            # 发送到流水线
            await self.process_content({
                'content': content,
                'media': media,
                'metadata': metadata
            })
            
        except Exception as e:
            logger.error(f"处理消息失败: {str(e)}")
            logger.debug(traceback.format_exc())
            
    async def stop(self):
        """停止提取器"""
        try:
            if self.application:
                await self.application.stop()
                await self.application.shutdown()
                self.application = None
                
            if self.bot:
                await self.bot.close()
                self.bot = None
                
            logger.info("Telegram提取器已停止")
            
        except Exception as e:
            logger.error(f"停止Telegram提取器失败: {str(e)}")
            logger.debug(traceback.format_exc())

    def get_source_type(self) -> str:
        """获取数据源类型"""
        return 'telegram'
    
    async def validate(self, raw_data: Dict[str, Any]) -> bool:
        """验证Telegram消息格式
        
        Args:
            raw_data: 原始消息数据
            
        Returns:
            bool: 是否有效
        """
        try:
            # 验证必要字段
            required_fields = ['message_id', 'text', 'chat']
            if not all(field in raw_data for field in required_fields):
                return False
                
            # 验证聊天类型
            chat = raw_data.get('chat', {})
            chat_type = chat.get('type')
            allowed_types = self.config.source_config.get('telegram', {}).get('allowed_chat_types', ['private', 'group'])
            
            if chat_type not in allowed_types:
                return False
                
            # 验证消息长度
            text = raw_data.get('text', '')
            min_length = self.config.source_config.get('telegram', {}).get('min_message_length', 1)
            if len(text) < min_length:
                return False
                
            return True
        except Exception as e:
            logger.error(f"Failed to validate Telegram message: {str(e)}")
            return False
    
    async def extract_content(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """从Telegram消息中提取内容
        
        Args:
            raw_data: 原始消息数据
            
        Returns:
            Dict: 提取结果
        """
        try:
            # 测试模式下模拟异常
            if self._test_mode and self._raise_error:
                raise Exception("Test error")
            
            # 验证消息格式
            if not await self.validate(raw_data):
                return self._create_error_data("Invalid message format")
            
            # 提取基本信息
            message_id = raw_data.get('message_id')
            chat = raw_data.get('chat', {})
            from_user = raw_data.get('from', {})
            date = raw_data.get('date')
            text = raw_data.get('text', '')
            
            # 提取URL并限制数量
            urls = self.url_extractor.extract_urls(text)
            max_url_count = self.config.max_url_count
            if len(urls) > max_url_count:
                urls = urls[:max_url_count]
            
            # 限制内容长度
            max_content_length = self.config.max_content_length
            if len(text) > max_content_length:
                text = text[:max_content_length]
            
            # 创建元数据
            metadata = {
                'message_id': message_id,
                'chat_id': chat.get('id'),
                'chat_type': chat.get('type'),
                'chat_title': chat.get('title'),
                'chat_username': chat.get('username'),
                'from_user': {
                    'id': from_user.get('id'),
                    'first_name': from_user.get('first_name'),
                    'last_name': from_user.get('last_name'),
                    'username': from_user.get('username'),
                    'language_code': from_user.get('language_code'),
                    'is_bot': from_user.get('is_bot', False)
                },
                'date': datetime.fromtimestamp(date) if date else datetime.now(),
                'entities': raw_data.get('entities', []),
                'media_type': raw_data.get('media_type', 'text'),
                'raw_data': raw_data
            }
            
            # 创建成功数据
            return self._create_success_data(
                content=text,
                metadata=metadata,
                urls=urls
            )
            
        except Exception as e:
            logger.error(f"Failed to extract content from Telegram message: {str(e)}")
            if self._test_mode:
                raise
            return self._create_error_data(f"Extraction failed: {str(e)}")
            
    def update_config(self, config: Dict[str, Any]):
        """更新提取器配置
        
        Args:
            config: 新的配置
        """
        super().update_config(config)
        # 更新URL提取器配置
        if 'url_pattern' in config:
            self.url_extractor.set_url_pattern(config['url_pattern'])
        if 'allowed_schemes' in config:
            self.url_extractor.set_allowed_schemes(set(config['allowed_schemes']))
            
    def set_test_mode(self, enabled: bool = True, raise_error: bool = False):
        """设置测试模式
        
        Args:
            enabled: 是否启用测试模式
            raise_error: 是否抛出异常
        """
        self._test_mode = enabled
        self._raise_error = raise_error 