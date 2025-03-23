#!/usr/bin/env python
"""
Example script for monitoring a Telegram channel for X posts
"""
import os
import sys
import time
from dotenv import load_dotenv
from loguru import logger

# Add the project root directory to Python path so we can import our package
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.adapters.telegram import TelegramAdapter


def setup_logging():
    """Set up logging configuration"""
    logger.remove()  # Remove default handler
    logger.add(
        sys.stderr,
        level=os.environ.get("LOG_LEVEL", "DEBUG"),  # Default to DEBUG for more information
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )
    
    # Add file logger if LOG_FILE is set
    log_file = os.environ.get("LOG_FILE")
    if log_file:
        logger.add(
            log_file,
            rotation="10 MB",
            retention="1 week",
            level=os.environ.get("LOG_LEVEL", "DEBUG"),  # Default to DEBUG for more information
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
        )


def main():
    """Main function to monitor Telegram channel"""
    # Load environment variables
    load_dotenv()
    
    # Setup logging
    setup_logging()
    
    # Get configuration
    api_key = os.environ.get("TELEGRAM_API_KEY")
    channel_id = os.environ.get("TELEGRAM_CHANNEL_ID")
    proxy_url = os.environ.get("TELEGRAM_PROXY")
    
    if not api_key or not channel_id:
        logger.error("Missing TELEGRAM_API_KEY or TELEGRAM_CHANNEL_ID in environment variables")
        sys.exit(1)
        
    logger.info(f"Starting Telegram monitor for channel: {channel_id}")
    if proxy_url:
        logger.info(f"Using proxy: {proxy_url}")
    
    # Create adapter with proxy support
    adapter = TelegramAdapter(api_key, channel_id, proxy_url=proxy_url)
    
    # Monitor loop
    try:
        # 创建一个空文件，重新开始处理消息
        if os.path.exists('data/processed_messages.txt'):
            logger.info("Clearing processed messages file to receive all messages")
            os.remove('data/processed_messages.txt')
            with open('data/processed_messages.txt', 'w') as f:
                pass
        
        # 确保数据目录存在
        os.makedirs('data', exist_ok=True)
        
        # 测试连接
        logger.info("Testing connection to Telegram API...")
        try:
            me = adapter.bot.get_me()
            logger.info(f"Connected as: {me.username} (ID: {me.id})")
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            logger.info("Continuing anyway, will retry in the main loop")
        
        # 显示目标频道信息
        logger.info(f"Target channel ID: {channel_id}")
        
        # 检查目标频道格式，提供一些提示
        if channel_id.startswith('@'):
            logger.info(f"Using channel username: {channel_id}")
            logger.info("Make sure this is the exact username of the channel (case-sensitive)")
        else:
            logger.info(f"Using channel ID: {channel_id}")
            logger.info("Make sure this is the numeric ID of the channel")
            
        while True:
            logger.info("Checking for new messages...")
            # 设置较大的limit，确保获取到消息
            messages = adapter.fetch_content(limit=100)
            
            if not messages:
                logger.info("No new messages found")
                # 尝试通过发送一条消息到频道来测试
                if channel_id:
                    try:
                        logger.info(f"Trying to send a test message to {channel_id}...")
                        if adapter.bot:
                            # 尝试获取更新以检查连接
                            updates = adapter.bot.get_updates(limit=5)
                            logger.info(f"Successfully got {len(updates)} recent updates from Telegram")
                            
                            # 如果这是一个公共频道，尝试获取频道信息
                            try:
                                if channel_id.startswith('@'):
                                    chat = adapter.bot.get_chat(channel_id)
                                    logger.info(f"Chat info: {chat.type} | title: {chat.title} | username: {chat.username}")
                            except Exception as e:
                                logger.warning(f"Could not get chat info: {e}")
                            
                            # 只有在私人频道或群组中才能发送测试消息
                            if not channel_id.startswith('@'):
                                adapter.bot.send_message(
                                    chat_id=channel_id, 
                                    text="测试消息: https://x.com/test/status/123456"
                                )
                                logger.info("Test message sent successfully")
                    except Exception as e:
                        logger.error(f"Failed to perform API tests: {e}")
            else:
                logger.info(f"Found {len(messages)} new messages")
                
                for msg in messages:
                    # 打印消息信息
                    logger.info(f"Message {msg['id']}: {msg['text'][:50]}...")
                    logger.debug(f"Full message data: {msg}")
                    
                    # 示例: 处理消息
                    if "x.com" in msg['text'] or "twitter.com" in msg['text']:
                        logger.info(f"Found X post in message {msg['id']}")
                    else:
                        logger.debug(f"Message {msg['id']} does not contain X posts")
                    
                    # 标记为已处理
                    adapter.mark_as_processed(msg['id'])
            
            # 等待下次检查
            wait_time = 15
            logger.info(f"Waiting {wait_time} seconds before next check...")
            time.sleep(wait_time)
    except KeyboardInterrupt:
        logger.info("Monitoring stopped by user")
    except Exception as e:
        logger.exception(f"Error occurred: {e}")
    
    logger.info("Telegram monitor stopped")


if __name__ == "__main__":
    main() 