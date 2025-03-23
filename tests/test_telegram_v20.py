#!/usr/bin/env python
"""
Telegram适配器v20.0测试脚本
使用python-telegram-bot v20.0 API测试频道消息接收
"""
import os
import sys
import json
import asyncio
import logging
from typing import Dict, Any, Optional

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from loguru import logger
import pytz
from telegram import Bot, Update
from telegram.ext import (
    Application, ApplicationBuilder, 
    CommandHandler, MessageHandler, 
    filters, ContextTypes, Defaults
)

# 配置日志
logger.remove()
logger.add(sys.stdout, level="DEBUG")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理所有类型的消息"""
    logger.info(f"收到更新: {update.update_id}")
    
    # 判断消息类型
    if update.message:
        logger.info(f"普通消息: {update.message.message_id}")
        logger.debug(f"消息内容: {update.message.text}")
    elif update.channel_post:
        logger.info(f"频道消息: {update.channel_post.message_id}")
        logger.debug(f"消息内容: {update.channel_post.text}")
        # 打印更多详情
        logger.debug(f"频道信息: {update.channel_post.chat.title} ({update.channel_post.chat.id})")
    elif update.edited_channel_post:
        logger.info(f"编辑的频道消息: {update.edited_channel_post.message_id}")
    else:
        logger.info(f"其他类型更新: {update}")

async def main():
    """运行测试脚本"""
    # 从config.json加载配置
    config_path = "config.json"
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            telegram_config = config.get("telegram_adapter", {})
    except Exception as e:
        logger.error(f"加载配置失败: {e}")
        return
        
    # 检查必要配置
    api_key = telegram_config.get("api_key")
    channel_id = telegram_config.get("channel_id")
    proxy_url = telegram_config.get("proxy_url")
    
    if not api_key or not channel_id:
        logger.error("缺少API密钥或频道ID")
        return
        
    logger.info(f"使用配置: API密钥={api_key[:5]}***, 频道={channel_id}, 代理={proxy_url}")
    
    # 设置默认值
    defaults = Defaults(tzinfo=pytz.UTC)
    
    # 构建应用
    application = (
        ApplicationBuilder()
        .token(api_key)
        .defaults(defaults)
    )
    
    # 如果有代理，则设置代理
    if proxy_url:
        application = application.proxy_url(proxy_url)
    
    # 完成构建
    app = application.build()
    
    # 添加消息处理器 - 注意处理所有可能的消息类型
    app.add_handler(MessageHandler(filters.ALL, handle_message))
    
    # 设置允许的更新类型，确保包含channel_post
    allowed_updates = ["message", "channel_post", "edited_channel_post"]
    
    logger.info("启动应用...")
    
    # 启动应用
    await app.initialize()
    await app.start()
    await app.updater.start_polling(allowed_updates=allowed_updates)
    
    logger.info("应用已启动，等待消息...")
    
    # 发送测试消息
    try:
        bot = app.bot
        result = await bot.send_message(
            chat_id=channel_id,
            text=f"测试消息: 使用v20.0 API测试频道接收功能"
        )
        logger.info(f"测试消息已发送: {result.message_id}")
    except Exception as e:
        logger.error(f"发送测试消息失败: {e}")
    
    # 等待一段时间或直到用户中断
    try:
        logger.info("按Ctrl+C停止测试...")
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("测试被用户中断")
    finally:
        # 停止应用
        logger.info("停止应用...")
        await app.updater.stop()
        await app.stop()
        await app.shutdown()
        logger.info("应用已停止")

if __name__ == "__main__":
    asyncio.run(main()) 