# -*- coding: utf-8 -*-
"""
X-Cat: 主运行框架
提供基于asyncio的异步处理架构
"""
import os
import sys
import json
import asyncio
import argparse
import traceback
from typing import Dict, Any, Optional
from datetime import datetime
from dotenv import load_dotenv

from loguru import logger

from app.core.runtime import Runtime
from app.core.pipeline import Pipeline
from app.core.processors import (
    ContentExtractor,
    ContentPreprocessor,
    ContentClassifier,
    ContentDistributor,
    ContentStorage
)
from app.core.processor import ContentProcessor
from app.preprocessor.content_preprocessor import ContentPreprocessor
from app.adapters.telegram import TelegramAdapter

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

class DateTimeEncoder(json.JSONEncoder):
    """自定义JSON编码器，用于处理datetime对象"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> None:
    """
    设置日志系统
    
    Args:
        log_level: 日志级别
        log_file: 日志文件路径
    """
    # 移除默认处理器
    logger.remove()
    
    # 添加控制台处理器
    logger.add(
        sys.stderr,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )
    
    # 如果指定了日志文件，添加文件处理器
    if log_file:
        os.makedirs(os.path.dirname(os.path.abspath(log_file)), exist_ok=True)
        logger.add(
            log_file,
            rotation="10 MB",
            retention="1 week",
            level=log_level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
        )

    logger.info(f"日志系统已初始化，级别: {log_level}{f', 文件: {log_file}' if log_file else ''}")


def load_config(config_file: str = "config.json") -> Dict[str, Any]:
    """
    加载配置文件
    
    Args:
        config_file: 配置文件路径
        
    Returns:
        配置字典
    """
    default_config = {
        "system": {
            "log_level": "INFO",
            "log_file": "logs/app.log",
            "data_dir": "data",
            "worker_threads": 4,
            "timezone": "Asia/Shanghai"  # 添加默认时区
        },
        "telegram_adapter": {
            "api_key": "",
            "channel_id": "",
            "proxy_url": None,
            "polling_interval": 60,
            "processed_messages_file": "data/processed_messages.json",
            "timezone": "Asia/Shanghai"  # 添加 Telegram 时区设置
        },
        "twitter_api": {
            "enabled": False,
            "api_key": "",
            "api_secret": "",
            "access_token": "",
            "access_token_secret": "",
            "bearer_token": "",
            "proxy_url": None,
            "timeout": 30,
            "max_retries": 3,
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        },
        "content_analyzer": {
            "api_key": "",
            "model": "gpt-4",
            "proxy_url": None,
            "max_tokens": 4096,
            "temperature": 0.7,
            "max_concurrency": 1
        },
        "storage": {
            "db_path": "data/storage.db",
            "backup_dir": "data/backups"
        }
    }
    
    try:
        # 加载 .env 文件
        load_dotenv()
        
        # 从环境变量更新配置
        env_config = {
            "telegram_adapter": {
                "api_key": os.getenv("TELEGRAM_API_KEY", ""),
                "channel_id": os.getenv("TELEGRAM_CHANNEL_ID", ""),
                "proxy_url": os.getenv("TELEGRAM_PROXY_URL"),
                "polling_interval": int(os.getenv("TELEGRAM_POLLING_INTERVAL", "60")),
                "timezone": os.getenv("TELEGRAM_TIMEZONE", "Asia/Shanghai"),  # 添加时区环境变量
            },
            "twitter_api": {
                "api_key": os.getenv("TWITTER_API_KEY", ""),
                "api_secret": os.getenv("TWITTER_API_SECRET", ""),
                "access_token": os.getenv("TWITTER_ACCESS_TOKEN", ""),
                "access_token_secret": os.getenv("TWITTER_ACCESS_TOKEN_SECRET", ""),
                "bearer_token": os.getenv("TWITTER_BEARER_TOKEN", ""),
                "proxy_url": os.getenv("TWITTER_PROXY_URL"),
            },
            "content_analyzer": {
                "api_key": os.getenv("OPENAI_API_KEY", ""),
                "proxy_url": os.getenv("OPENAI_PROXY_URL"),
            },
            "storage": {
                "db_path": os.getenv("DB_PATH", "data/storage.db"),
                "backup_dir": os.getenv("BACKUP_DIR", "data/backups"),
            }
        }
        
        # 检查 config.json 文件是否存在
        if not os.path.exists(config_file):
            logger.warning(f"配置文件 '{config_file}' 不存在，使用默认配置")
            # 尝试加载示例配置
            example_file = f"{config_file}.example"
            if os.path.exists(example_file):
                logger.info(f"加载示例配置文件: {example_file}")
                with open(example_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            else:
                logger.warning(f"示例配置文件 '{example_file}' 不存在，使用硬编码默认配置")
                config = default_config
        else:
            # 加载配置文件
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                logger.info(f"已加载配置文件: {config_file}")
        
        # 合并配置
        for section in default_config:
            if section not in config:
                config[section] = default_config[section]
            else:
                for key in default_config[section]:
                    if key not in config[section]:
                        config[section][key] = default_config[section][key]
        
        # 使用环境变量覆盖配置
        for section, values in env_config.items():
            if section not in config:
                config[section] = {}
            for key, value in values.items():
                if value:  # 只覆盖非空值
                    config[section][key] = value
        
        # 验证必要的配置
        if not config["telegram_adapter"]["api_key"] or not config["telegram_adapter"]["channel_id"]:
            logger.error("缺少必要的 Telegram 配置信息")
            return None
            
        return config
    
    except Exception as e:
        logger.error(f"加载配置文件出错: {str(e)}")
        logger.debug(traceback.format_exc())
        return default_config


def parse_args() -> argparse.Namespace:
    """
    解析命令行参数
    
    Returns:
        解析后的参数
    """
    parser = argparse.ArgumentParser(description="X-Cat: 内容自动分类与存储系统")
    parser.add_argument("--config", "-c", type=str, default="config.json", help="配置文件路径")
    parser.add_argument("--log-level", "-l", type=str, default=None, help="日志级别 (DEBUG, INFO, WARNING, ERROR)")
    parser.add_argument("--log-file", "-f", type=str, default=None, help="日志文件路径")
    parser.add_argument("--data-dir", "-d", type=str, default=None, help="数据目录路径")
    return parser.parse_args()


async def process_message(message: Dict[str, Any], pipeline: Pipeline) -> None:
    """
    处理消息
    
    Args:
        message: 消息数据
        pipeline: 处理流水线
    """
    try:
        # 构建标准格式的消息
        processed_message = {
            'text': message.get('text', ''),
            'content': message.get('text', ''),  # 同时提供 content 字段
            'source': 'telegram',
            'source_type': 'telegram',
            'metadata': {
                'message_id': message.get('message_id'),
                'chat_id': message.get('chat_id'),
                'chat_type': message.get('chat_type'),
                'date': message.get('date'),
                'from_user': message.get('from_user'),
                'chat': message.get('chat'),
                'message_type': message.get('message_type', 'text')
            }
        }
        
        # 添加URL字段用于缓存
        if processed_message['text']:
            processed_message['url'] = f"telegram:{processed_message['metadata']['message_id']}"
        
        # 处理消息
        result = await pipeline.process(processed_message)
        
        if result and result.get('success', False):
            logger.info(f"消息处理完成: {result.get('url', 'unknown')}")
        else:
            error_msg = result.get('error', '未知错误') if result else '处理失败'
            logger.warning(f"消息处理失败: {error_msg}")
            
    except Exception as e:
        logger.error(f"处理消息出错: {str(e)}")
        logger.debug(traceback.format_exc())

async def main_async(config: Dict[str, Any], args: argparse.Namespace) -> int:
    """异步主函数"""
    try:
        # 初始化运行时环境
        runtime = Runtime(config)
        if not await runtime.initialize():
            logger.error("初始化运行时环境失败")
            return 1
            
        # 初始化Telegram适配器
        telegram_config = config.get('telegram_adapter', {})
        telegram = TelegramAdapter(
            api_key=telegram_config.get('api_key'),
            channel_id=telegram_config.get('channel_id')
        )
        
        # 设置消息回调
        async def message_callback(message: Dict[str, Any]) -> None:
            await process_message(message, runtime.pipeline)
        
        # 初始化Telegram适配器
        if not await telegram.initialize(message_callback):
            logger.error("初始化Telegram适配器失败")
            return 1
            
        # 启动轮询
        if not await telegram.start_polling():
            logger.error("启动Telegram轮询失败")
            return 1
            
        logger.info("系统启动成功，开始处理消息...")
        
        try:
            while True:
                # 获取新消息
                messages = telegram.get_received_messages()
                if messages:
                    for message in messages:
                        await message_callback(message)
                    
                    # 清空已处理的消息
                    telegram._received_messages = []
                    logger.debug("已清空消息列表")
                
                # 等待一段时间再检查新消息
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("收到停止信号，正在关闭...")
        finally:
            # 关闭资源
            await telegram.stop_polling()
            await runtime.stop()
        
        return 0
        
    except Exception as e:
        logger.error(f"运行出错: {str(e)}")
        logger.debug(traceback.format_exc())
        return 1


def main() -> int:
    """主函数"""
    try:
        # 解析命令行参数
        args = parse_args()
        
        # 加载配置
        config = load_config(args.config)
        if not config:
            logger.error("配置加载失败，程序退出")
            return 1
            
        # 优先使用命令行参数
        if args.log_level:
            config['system']['log_level'] = args.log_level
        if args.log_file:
            config['system']['log_file'] = args.log_file
        if args.data_dir:
            config['system']['data_dir'] = args.data_dir
            
        # 设置日志
        setup_logging(
            log_level=config['system']['log_level'],
            log_file=config['system']['log_file']
        )
        
        # 确保数据目录存在
        os.makedirs(config['system']['data_dir'], exist_ok=True)
        
        # 确保日志目录存在
        if 'log_file' in config['system'] and config['system']['log_file']:
            os.makedirs(os.path.dirname(config['system']['log_file']), exist_ok=True)
            
        # 运行异步主函数
        return asyncio.run(main_async(config, args))
        
    except Exception as e:
        logger.error(f"运行出错: {str(e)}")
        logger.debug(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())