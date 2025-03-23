#!/usr/bin/env python
"""
测试脚本：发送消息到Telegram频道或聊天
此脚本用于测试Telegram API连接和代理设置
"""
import os
import sys
import time
import argparse
from dotenv import load_dotenv
from loguru import logger
from telegram import Bot
from telegram.utils.request import Request
from telegram.error import TelegramError

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def setup_logging():
    """设置日志"""
    logger.remove()  # 移除默认处理器
    logger.add(
        sys.stderr,
        level="DEBUG",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{function}</cyan> - <level>{message}</level>"
    )


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='发送测试消息到Telegram')
    parser.add_argument('--message', '-m', type=str, 
                        default="测试消息 X-Cat: https://x.com/test/status/123456",
                        help='要发送的消息')
    parser.add_argument('--chat', '-c', type=str,
                        help='目标聊天ID或用户名 (默认使用.env中的TELEGRAM_CHANNEL_ID)')
    parser.add_argument('--env', '-e', type=str,
                        default='.env.test',
                        help='环境变量文件路径 (默认: .env.test)')
    return parser.parse_args()


def main():
    """主函数"""
    # 解析命令行参数
    args = parse_arguments()
    
    # 设置日志
    setup_logging()
    
    # 加载环境变量
    load_dotenv(args.env)
    logger.info(f"已加载环境变量文件: {args.env}")
    
    # 获取配置
    api_key = os.environ.get("TELEGRAM_API_KEY")
    channel_id = args.chat or os.environ.get("TELEGRAM_CHANNEL_ID")
    proxy_url = os.environ.get("TELEGRAM_PROXY")
    
    if not api_key:
        logger.error("未设置TELEGRAM_API_KEY环境变量")
        sys.exit(1)
    
    if not channel_id:
        logger.error("未指定目标聊天ID，请使用--chat参数或设置TELEGRAM_CHANNEL_ID环境变量")
        sys.exit(1)
    
    logger.info(f"API Key: {api_key[:5]}...{api_key[-5:]}")
    logger.info(f"目标聊天: {channel_id}")
    
    # 配置Bot
    try:
        if proxy_url:
            logger.info(f"使用代理: {proxy_url}")
            request = Request(proxy_url=proxy_url, con_pool_size=8)
            bot = Bot(token=api_key, request=request)
        else:
            logger.info("不使用代理")
            bot = Bot(token=api_key)
        
        # 测试连接
        me = bot.get_me()
        logger.info(f"成功连接到Telegram API，机器人信息: {me.username} (ID: {me.id})")
        
        # 发送消息
        logger.info(f"正在发送消息: '{args.message}'")
        
        # 尝试获取有关聊天的信息
        try:
            chat_info = bot.get_chat(channel_id)
            logger.info(f"聊天信息: 类型={chat_info.type}, 标题={chat_info.title}, 用户名=@{chat_info.username}")
        except TelegramError as e:
            logger.warning(f"无法获取聊天信息: {e}")
        
        # 发送消息
        message = bot.send_message(
            chat_id=channel_id,
            text=args.message
        )
        
        logger.success(f"消息发送成功! 消息ID: {message.message_id}")
        
    except TelegramError as e:
        logger.error(f"Telegram API错误: {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"发生错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 