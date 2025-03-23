#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Configuration helper utility for X-Cat
"""
import os
import json
import getpass
import sys


def create_config():
    """Interactive function to create configuration file"""
    print("X-Cat配置助手")
    print("=============")
    print("这个脚本将帮助你创建X-Cat的配置文件。")
    print()
    
    # Default config
    config = {
        "data_source": {
            "type": "telegram",
            "api_key": "",
            "channel_id": "",
            "processed_messages_file": "data/processed_messages.txt",
            "polling_interval": 60,
            "mock_mode": False,
            "category_channels": {
                "AI": "",
                "Python": "",
                "电子设计": "",
                "数字货币": "",
                "其他": ""
            }
        },
        "analyzer": {
            "type": "gpt",
            "api_key": "",
            "model": "gpt-4",
            "categories": ["AI", "Python", "电子设计", "数字货币", "其他"],
            "max_tokens": 150,
            "temperature": 0.2
        },
        "storage": {
            "type": "local",
            "db_path": "data/xcat.db"
        },
        "logging": {
            "level": "INFO",
            "file": "logs/xcat.log"
        }
    }
    
    # Data source configuration
    print("数据源配置")
    print("----------")
    
    # Telegram settings
    print("Telegram设置:")
    
    # Get API key
    api_key = input("请输入Telegram Bot API密钥 (从BotFather获取): ")
    if api_key:
        config["data_source"]["api_key"] = api_key
    
    # Get channel ID
    channel_id = input("请输入要监听的频道ID (数字ID或用户名，例如@channel_name): ")
    if channel_id:
        config["data_source"]["channel_id"] = channel_id
    
    # Mock mode
    mock_mode = input("是否启用模拟模式进行测试? (y/n, 默认: n): ").lower()
    config["data_source"]["mock_mode"] = mock_mode == 'y'
    
    # Category channels (optional)
    setup_categories = input("是否设置分类频道? (y/n, 默认: n): ").lower()
    if setup_categories == 'y':
        print("请输入各分类对应的频道ID (留空则跳过):")
        for category in config["data_source"]["category_channels"]:
            channel = input(f"  {category}频道ID: ")
            if channel:
                config["data_source"]["category_channels"][category] = channel
    
    # Analyzer configuration
    print("\nAI分析器配置")
    print("------------")
    
    # Get GPT API key
    gpt_api_key = getpass.getpass("请输入OpenAI API密钥: ")
    if gpt_api_key:
        config["analyzer"]["api_key"] = gpt_api_key
    
    # GPT model
    gpt_model = input("使用的GPT模型 (默认: gpt-4): ")
    if gpt_model:
        config["analyzer"]["model"] = gpt_model
    
    # Categories
    edit_categories = input("是否修改默认分类类别? (y/n, 默认: n): ").lower()
    if edit_categories == 'y':
        categories_str = input("请输入分类列表，用逗号分隔: ")
        if categories_str:
            config["analyzer"]["categories"] = [c.strip() for c in categories_str.split(',')]
    
    # Storage configuration
    print("\n存储配置")
    print("--------")
    
    # Database path
    db_path = input("数据库文件路径 (默认: data/xcat.db): ")
    if db_path:
        config["storage"]["db_path"] = db_path
    
    # Logging configuration
    print("\n日志配置")
    print("--------")
    
    # Log level
    log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    print("可用的日志级别:", ", ".join(log_levels))
    log_level = input("日志级别 (默认: INFO): ").upper()
    if log_level in log_levels:
        config["logging"]["level"] = log_level
    
    # Log file
    log_file = input("日志文件路径 (默认: logs/xcat.log): ")
    if log_file:
        config["logging"]["file"] = log_file
    
    # Save configuration
    output_path = input("\n配置文件保存路径 (默认: config/config.json): ")
    if not output_path:
        output_path = "config/config.json"
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    
    # Write configuration to file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)
    
    print(f"\n配置已保存到 {output_path}")
    print("你可以使用以下命令运行X-Cat:")
    print(f"  python main.py -c {output_path}")


if __name__ == '__main__':
    try:
        create_config()
    except KeyboardInterrupt:
        print("\n\n配置已取消。")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n配置过程中发生错误: {str(e)}")
        sys.exit(1) 