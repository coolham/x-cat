"""
日志配置工具
"""
import os
import logging
from logging.handlers import RotatingFileHandler
from typing import Dict, Any, Optional


def setup_logging(config: Optional[Dict[str, Any]] = None) -> None:
    """
    设置日志配置
    
    Args:
        config: 日志配置字典，如果为None则使用默认配置
    """
    if config is None:
        config = {
            "level": "INFO",
            "file": "logs/xcat.log"
        }
    
    # 获取配置
    log_level_str = config.get("level", "INFO")
    log_file = config.get("file", "logs/xcat.log")
    
    # 转换日志级别
    log_level = getattr(logging, log_level_str.upper(), logging.INFO)
    
    # 创建日志目录
    log_dir = os.path.dirname(os.path.abspath(log_file))
    os.makedirs(log_dir, exist_ok=True)
    
    # 设置根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # 清除已有的处理器
    for handler in root_logger.handlers:
        root_logger.removeHandler(handler)
    
    # 创建格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 添加控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # 添加文件处理器
    file_handler = RotatingFileHandler(
        log_file, maxBytes=10*1024*1024, backupCount=5, encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    logging.info(f"日志系统初始化完成，级别: {log_level_str}，文件: {log_file}") 