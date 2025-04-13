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
import logging
import signal
from typing import Dict, Any, Optional
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path

from loguru import logger

from app.core.prefect_pipeline import PrefectPipeline
from app.core.adapter_manager import AdapterManager
from app.core.config_loader import load_config

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# 首先加载环境变量
load_dotenv()

# 检查环境变量是否加载成功
http_proxy = os.environ.get('HTTP_PROXY', '')
https_proxy = os.environ.get('HTTPS_PROXY', '')
logger.info(f"加载环境变量后的代理设置: HTTP_PROXY={http_proxy}, HTTPS_PROXY={https_proxy}")

# Replace user directory with project directory for Prefect-related files
project_dir = Path(__file__).parent
prefect_dir = project_dir / "prefect_files"

# Ensure the directory exists
prefect_dir.mkdir(parents=True, exist_ok=True)

# Set Prefect environment variables to use the project directory
os.environ["PREFECT_PROFILES_PATH"] = str(prefect_dir / "profiles.toml")
os.environ["PREFECT_LOCAL_STORAGE_PATH"] = str(prefect_dir / "storage")

# 确保配置文件路径存在
profiles_path = os.environ["PREFECT_PROFILES_PATH"]
profiles_dir = os.path.dirname(profiles_path)
os.makedirs(profiles_dir, exist_ok=True)

# 如果配置文件不存在，则创建一个空文件
if not os.path.exists(profiles_path):
    with open(profiles_path, "w") as f:
        f.write("")

# 确保存储路径存在
storage_path = os.environ["PREFECT_LOCAL_STORAGE_PATH"]
os.makedirs(storage_path, exist_ok=True)

# 全局变量，用于存储管道和提取器管理器实例
pipeline = None
extractor_manager = None

# 配置日志
logging.basicConfig(level=logging.INFO)
logger.add("logs/app.log", rotation="10 MB")

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


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="X-Cat 内容自动分类与存储系统")
    parser.add_argument("-c", "--config", default="config", help="配置文件目录路径")
    parser.add_argument("-e", "--env", default=".env", help="环境变量文件路径")
    parser.add_argument("-l", "--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], help="日志级别")
    parser.add_argument("-f", "--log-file", help="日志文件路径")
    parser.add_argument("-d", "--data-dir", help="数据目录路径")
    return parser.parse_args()

def initialize_pipeline(config: Dict[str, Any]) -> PrefectPipeline:
    """
    初始化数据处理管道
    
    Args:
        config: 应用配置
        
    Returns:
        初始化后的管道
    """
    return PrefectPipeline(config)

async def shutdown(signal=None):
    """清理并关闭应用"""
    if signal:
        logger.info(f"收到退出信号 {signal.name}...")
    else:
        logger.info("正在关闭应用...")
    
    if pipeline:
        logger.info("正在停止管道...")
        await pipeline.stop()
        
    if extractor_manager:
        logger.info("正在停止提取器管理器...")
        await extractor_manager.stop()
    
    logger.info("关闭完成.")

def handle_exception(loop, context):
    """处理未捕获的异常"""
    msg = context.get("exception", context["message"])
    logger.error(f"未捕获的异常: {msg}")
    logger.info("正在关闭...")
    asyncio.create_task(shutdown())

async def main_async():
    """主异步函数"""
    global pipeline, extractor_manager

    try:
        logger.info("启动流程开始...")

        # 加载配置
        logger.info("加载配置文件...")
        config_path = os.path.join(os.path.dirname(__file__), "config", "config.yaml")
        config = load_config(config_path)
        logger.info("配置文件加载完成")

        # 初始化 Prefect 管道
        logger.info("初始化 Prefect 管道...")
        pipeline = PrefectPipeline(config)
        pipeline.initialize()
        logger.info("Prefect 管道初始化完成")

        if 1:
            # 初始化适配器管理器
            logger.info("初始化适配器管理器...")
            extractor_manager = AdapterManager(config)
            await extractor_manager.initialize(pipeline.process)
            logger.info("适配器管理器初始化完成")

            # 启动适配器管理器
            logger.info("启动适配器管理器...")
            await extractor_manager.start()
            logger.info("适配器管理器启动完成")
        else:
            # 在 main_async 函数中，启动适配器管理器后
            logger.info("手动触发测试...")
            test_data = {
                "id": "test_123",
                "content": "这是一条测试消息",
                "source": "test",
                "timestamp": datetime.now().isoformat()
            }
            result = await pipeline.process(test_data)
            logger.info(f"测试结果: {result}")

        # 保持程序运行
        logger.info("系统启动完成，等待消息...")
        while True:
            await asyncio.sleep(1)

    except Exception as e:
        logger.error(f"程序运行出错: {str(e)}")
        logger.debug(f"异常详情: {traceback.format_exc()}")
    finally:
        logger.info("流程结束")

def main():
    """主入口点"""
    try:
        # 创建新的事件循环
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # 设置异常处理器
        loop.set_exception_handler(handle_exception)

        # 设置信号处理 - Windows 兼容方式
        if os.name == 'nt':  # Windows
            def windows_signal_handler(sig, frame):
                logger.info(f"收到信号 {sig}")
                loop.call_soon_threadsafe(lambda: asyncio.create_task(shutdown()))

            signal.signal(signal.SIGINT, windows_signal_handler)
            signal.signal(signal.SIGTERM, windows_signal_handler)
        else:  # Unix/Linux/Mac
            for sig in (signal.SIGINT, signal.SIGTERM):
                loop.add_signal_handler(
                    sig,
                    lambda s=sig: asyncio.create_task(shutdown(s))
                )

        # 运行主异步函数
        loop.run_until_complete(main_async())

    except KeyboardInterrupt:
        logger.info("应用被用户停止")
        if 'loop' in locals() and not loop.is_closed():
            loop.run_until_complete(shutdown())
    except Exception as e:
        logger.error(f"应用错误: {str(e)}")
        raise
    finally:
        if 'loop' in locals() and not loop.is_closed():
            loop.close()

if __name__ == "__main__":
    main()