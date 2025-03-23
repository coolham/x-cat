#!/usr/bin/env python
"""
X-Cat: 主运行框架
提供模块化架构来协调和管理各种功能模块
"""
import os
import sys
import json
import asyncio
import argparse
import traceback
import signal
from typing import Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor

from loguru import logger

from app.core.runtime import Runtime
from app.adapters.telegram_module import TelegramAdapterModule
from app.analyzers.content_analyzer_module import ContentAnalyzerModule
from app.storage.storage_module import StorageModule


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
            "worker_threads": 4
        },
        "telegram_adapter": {
            "api_key": "",
            "channel_id": "",
            "proxy_url": None,
            "polling_interval": 60,
            "processed_messages_file": "data/processed_messages.json"
        },
        "content_analyzer": {
            "api_key": "",
            "model": "gpt-4o",
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
        # 检查文件是否存在
        if not os.path.exists(config_file):
            logger.warning(f"配置文件 '{config_file}' 不存在，使用默认配置")
            # 尝试加载示例配置
            example_file = f"{config_file}.example"
            if os.path.exists(example_file):
                logger.info(f"加载示例配置文件: {example_file}")
                with open(example_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                logger.warning(f"示例配置文件 '{example_file}' 不存在，使用硬编码默认配置")
                return default_config
        
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


async def main_async(config, args) -> int:
    """
    异步主函数
    
    Args:
        config: 配置字典
        args: 命令行参数
    """
    # 创建运行时
    runtime = Runtime()
    
    # 注册并手动初始化所有模块
    logger.info("注册并初始化所有模块...")
    
    # 1. 初始化Telegram模块
    telegram_module = TelegramAdapterModule(runtime, "telegram_adapter")
    runtime.modules["telegram_adapter"] = telegram_module
    logger.info("初始化Telegram模块...")
    if not await telegram_module.initialize(config):
        logger.error("Telegram模块初始化失败")
        return 1
    logger.info("Telegram模块初始化成功")
    
    # 2. 初始化内容分析器模块
    content_analyzer_module = ContentAnalyzerModule(runtime, "content_analyzer")
    runtime.modules["content_analyzer"] = content_analyzer_module
    logger.info("初始化内容分析器模块...")
    if not await content_analyzer_module.initialize(config):
        logger.error("内容分析器模块初始化失败")
        return 1
    logger.info("内容分析器模块初始化成功")
    
    # 3. 初始化存储模块
    storage_module = StorageModule(runtime, "storage")
    runtime.modules["storage"] = storage_module
    logger.info("初始化存储模块...")
    if not await storage_module.initialize(config):
        logger.error("存储模块初始化失败")
        return 1
    logger.info("存储模块初始化成功")
    
    # 启动所有模块
    logger.info("启动所有模块...")
    
    # 1. 启动Telegram模块
    logger.info("启动Telegram模块...")
    if not await telegram_module.start():
        logger.error("Telegram模块启动失败")
        return 1
    logger.info("Telegram模块启动成功")
    
    # 2. 启动内容分析器模块
    logger.info("启动内容分析器模块...")
    if not await content_analyzer_module.start():
        logger.error("内容分析器模块启动失败")
        return 1
    logger.info("内容分析器模块启动成功")
    
    # 3. 启动存储模块
    logger.info("启动存储模块...")
    if not await storage_module.start():
        logger.error("存储模块启动失败")
        return 1
    logger.info("存储模块启动成功")
    
    # 添加事件订阅
    logger.info("设置事件订阅...")
    # 将新消息事件连接到内容分析器
    for module in runtime.modules.values():
        if hasattr(module, "on_new_message") and callable(module.on_new_message):
            runtime.subscribe_event("new_message", module.on_new_message)
            logger.info(f"模块 {module.module_id} 订阅了新消息事件")
    
    # 系统健康检查循环
    logger.info("系统运行中...")
    try:
        while True:
            # 检查所有模块状态
            all_healthy = True
            for module_id, module in runtime.modules.items():
                try:
                    if module.state.name == "RUNNING":
                        healthy = await module.health_check()
                        if not healthy:
                            logger.warning(f"模块 '{module_id}' 健康检查失败")
                            all_healthy = False
                except Exception as e:
                    logger.error(f"模块 '{module_id}' 健康检查错误: {str(e)}")
                    all_healthy = False
            
            if not all_healthy:
                logger.warning("一些模块状态异常")
            
            # 等待30秒再次检查
            await asyncio.sleep(30)
    except asyncio.CancelledError:
        logger.info("收到取消信号")
    except KeyboardInterrupt:
        logger.info("收到中断信号")
    finally:
        # 关闭所有模块
        logger.info("关闭所有模块...")
        for module_id, module in reversed(list(runtime.modules.items())):
            try:
                logger.info(f"正在停止模块: {module_id}")
                await module.stop()
                logger.info(f"模块已停止: {module_id}")
            except Exception as e:
                logger.error(f"停止模块 '{module_id}' 时出错: {str(e)}")
    
    logger.info("系统已停止")
    return 0


def main() -> int:
    """
    主函数
    
    Returns:
        退出代码
    """
    try:
        # 解析命令行参数
        args = parse_args()
        
        # 加载配置
        config = load_config(args.config)
        
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
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(main_async(config, args))
    except Exception as e:
        logger.error(f"运行出错: {str(e)}")
        logger.debug(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())