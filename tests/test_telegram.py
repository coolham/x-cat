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
import time

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

# 全局变量存储测试状态
received_messages = []
# 发送的测试消息ID，用于验证是否收到了自己发送的消息
sent_message_id = None
# 事件标记，用于异步通知测试进程消息已接收
message_received = asyncio.Event()

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理所有类型的消息"""
    global sent_message_id, message_received
    
    logger.info(f"收到更新: {update.update_id}")
    
    message = None
    # 判断消息类型
    if update.message:
        message = update.message
        logger.info(f"普通消息: {message.message_id}")
        logger.debug(f"消息内容: {message.text if hasattr(message, 'text') else '非文本消息'}")
        
    elif update.channel_post:
        message = update.channel_post
        logger.info(f"频道消息: {message.message_id}")
        logger.debug(f"消息内容: {message.text if hasattr(message, 'text') else '非文本消息'}")
        logger.debug(f"频道信息: {message.chat.title} ({message.chat.id})")
        
    elif update.edited_channel_post:
        message = update.edited_channel_post
        logger.info(f"编辑的频道消息: {message.message_id}")
        
    else:
        logger.info(f"其他类型更新: {update}")
        return
    
    # 如果收到消息，存储并检查
    if message:
        received_messages.append(message)
        logger.info(f"已存储消息 ID: {message.message_id}")
        
        # 检查是否是我们发送的测试消息
        if sent_message_id and message.message_id == sent_message_id:
            logger.info(f"✓ 已接收到发送的测试消息 ID: {sent_message_id}")
            message_received.set()  # 设置事件，通知测试进程

async def main(timeout=30):
    """运行测试脚本
    
    Args:
        timeout: 等待消息的最大秒数，默认30秒
    """
    global sent_message_id, message_received, received_messages
    
    # 重置全局状态
    received_messages = []
    sent_message_id = None
    message_received = asyncio.Event()
    
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
        test_message = f"测试消息: 使用v20.0 API测试频道接收功能 (时间戳: {int(time.time())})"
        result = await bot.send_message(
            chat_id=channel_id,
            text=test_message
        )
        sent_message_id = result.message_id
        logger.info(f"测试消息已发送: {sent_message_id}")
    except Exception as e:
        logger.error(f"发送测试消息失败: {e}")
    
    # 等待直到收到测试消息或超时
    try:
        logger.info(f"等待消息接收(最多{timeout}秒)...")
        
        # 使用asyncio.wait_for和事件来等待消息接收
        try:
            await asyncio.wait_for(message_received.wait(), timeout=timeout)
            logger.info("✓ 成功等待到消息接收事件")
        except asyncio.TimeoutError:
            logger.warning(f"测试超时({timeout}秒)，未接收到发送的消息")
            
            # 即使超时了，也再等待5秒看看是否会收到延迟消息
            logger.info("额外等待5秒以检查延迟消息...")
            await asyncio.sleep(5)
            
    except KeyboardInterrupt:
        logger.info("测试被用户中断")
    finally:
        # 停止应用
        logger.info("停止应用...")
        await app.updater.stop()
        await app.stop()
        await app.shutdown()
        logger.info("应用已停止")
        
        # 报告测试结果
        logger.info(f"测试结束，共接收到 {len(received_messages)} 条消息")
        if len(received_messages) > 0:
            for i, msg in enumerate(received_messages):
                logger.info(f"消息 {i+1}: ID={msg.message_id}, 内容={msg.text if hasattr(msg, 'text') else '非文本'}")
        
        return received_messages

if __name__ == "__main__":
    # 允许通过命令行参数设置超时
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        timeout = int(sys.argv[1])
    else:
        timeout = 30  # 默认超时30秒
    
    asyncio.run(main(timeout)) 