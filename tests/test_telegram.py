#!/usr/bin/env python
"""
Telegram适配器测试脚本
测试TelegramAdapter模块的消息接收和发送功能
"""
import os
import sys
import asyncio
import time
from typing import Dict, Any
# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from pathlib import Path
from dotenv import load_dotenv
from loguru import logger
from telegram import Update
from telegram.ext import ContextTypes
from app.adapters.telegram.adapter import TelegramAdapter
from prefect import task

# 加载环境变量
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# 配置日志
logger.remove()
logger.add(sys.stdout, level="DEBUG")

# 全局变量存储测试状态
received_messages = []
sent_message_id = None
message_received = asyncio.Event()


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理接收到的消息"""
    global sent_message_id, message_received

    logger.info(f"收到更新: {update.update_id}")

    message = update.message or update.channel_post or update.edited_channel_post
    if not message:
        logger.info(f"未处理的更新类型: {update}")
        return

    logger.info(f"收到消息: {message.message_id}, 内容: {message.text if message.text else '非文本消息'}")

    # 检查是否是我们发送的测试消息
    if sent_message_id and message.message_id == sent_message_id:
        logger.info(f"✓ 已接收到发送的测试消息 ID: {sent_message_id}")
        message_received.set()  # 设置事件，通知测试进程


async def test_telegram_adapter(timeout=30):
    """测试Telegram适配器

    Args:
        timeout: 等待消息的最大秒数，默认30秒
    """
    global sent_message_id, message_received, received_messages

    # 重置全局状态
    received_messages = []
    sent_message_id = None
    message_received.clear()

    # 加载配置
    api_key = os.getenv("TELEGRAM_API_KEY")
    channel_id = os.getenv("TELEGRAM_CHANNEL_ID")
    use_proxy = os.getenv("TELEGRAM_USE_PROXY", "false").lower() == "true"

    # 获取代理配置
    proxy_url = None
    if use_proxy:
        http_proxy = os.getenv("HTTP_PROXY")
        https_proxy = os.getenv("HTTPS_PROXY")
        if http_proxy:
            proxy_url = http_proxy
        elif https_proxy:
            proxy_url = https_proxy

    if not api_key or not channel_id:
        logger.error("缺少API令牌或聊天ID")
        return

    logger.info(f"使用配置: API令牌={api_key[:5]}***, 聊天ID={channel_id}, 使用代理={use_proxy}, 代理URL={proxy_url}")

    # 创建Telegram适配器
    adapter = TelegramAdapter({
        "api_key": api_key,
        "channel_id": channel_id,
        "use_proxy": use_proxy,
        "proxy_url": proxy_url
    })

    # 初始化适配器
    async def message_callback(message):
        """消息回调函数"""
        global sent_message_id, message_received

        logger.info(f"收到消息回调: {message}")

        # 检查是否是我们发送的测试消息
        if sent_message_id and str(sent_message_id) == str(message.get('message_id')):
            logger.info(f"✓ 已接收到发送的测试消息 ID: {sent_message_id}")
            message_received.set()  # 设置事件，通知测试进程

    logger.debug("开始初始化Telegram适配器...")
    initialized = await adapter.initialize(message_callback)
    if not initialized:
        logger.error("初始化Telegram适配器失败")
        return
    logger.debug("Telegram适配器初始化完成")

    # 启动适配器
    logger.debug("启动Telegram适配器轮询...")
    started = await adapter.start_polling()
    if not started:
        logger.error("启动Telegram适配器失败")
        await adapter.close()
        return
    logger.debug("Telegram适配器轮询已启动")

    logger.info("Telegram适配器已启动，等待消息...")

    # 发送测试消息
    try:
        test_message = f"测试消息: 使用Telegram适配器测试消息接收功能 (时间戳: {int(time.time())})"
        logger.debug(f"发送测试消息: {test_message}")
        result = await adapter.send_message({"text": test_message})
        if result:
            logger.info("测试消息已发送")
            if isinstance(result, dict) and 'message_id' in result:
                sent_message_id = result['message_id']
                logger.info(f"发送的消息ID: {sent_message_id}")
        else:
            logger.error("发送测试消息失败")
    except Exception as e:
        logger.error(f"发送测试消息失败: {str(e)}")

    # 等待消息接收
    try:
        logger.info(f"等待消息接收(最多{timeout}秒)...")
        await asyncio.wait_for(message_received.wait(), timeout=timeout)
        logger.info("✓ 成功等待到消息接收事件")
    except asyncio.TimeoutError:
        logger.warning(f"测试超时({timeout}秒)，未接收到发送的消息")
    finally:
        # 关闭适配器
        logger.info("关闭Telegram适配器...")
        await adapter.close()
        logger.info("Telegram适配器已关闭")

        # 报告测试结果
        logger.info(f"测试结束，共接收到 {len(received_messages)} 条消息")
        if len(received_messages) > 0:
            for i, msg in enumerate(received_messages):
                logger.info(f"消息 {i+1}: {msg}")
        return received_messages


async def main(timeout=30):
    """运行测试脚本

    Args:
        timeout: 等待消息的最大秒数，默认30秒
    """
    logger.info("=== 测试Telegram适配器 ===")
    adapter_results = await test_telegram_adapter(timeout)

    logger.info(f"适配器测试: 接收到 {len(adapter_results) if adapter_results else 0} 条消息")


if __name__ == "__main__":
    # 允许通过命令行参数设置超时
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        timeout = int(sys.argv[1])
    else:
        timeout = 30  # 默认超时30秒

    asyncio.run(main(timeout))