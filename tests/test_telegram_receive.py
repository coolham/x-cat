#!/usr/bin/env python
"""
Telegram接收测试脚本
专门测试Telegram适配器接收频道消息的功能
"""
import os
import sys
import json
import asyncio
import logging
from typing import Dict, Any, List, Optional

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# 导入Telegram适配器
from app.adapters.telegram import TelegramAdapter

# 存储接收到的消息
received_messages = []

async def message_handler(message_data: Dict[str, Any]) -> None:
    """消息处理函数"""
    message_id = message_data.get("message_id")
    text = message_data.get("text", "")
    message_type = message_data.get("message_type", "unknown")
    
    # 记录消息信息
    logger.info(f"收到新消息 [类型: {message_type}] ID: {message_id}, 文本: {text[:50]}...")
    received_messages.append(message_data)
    
    # 打印消息源数据
    logger.debug(f"消息原始数据: {json.dumps(message_data, ensure_ascii=False, indent=2)}")


async def main():
    """主函数"""
    try:
        # 加载配置
        config_path = "config.json"
        if not os.path.exists(config_path):
            logger.error(f"配置文件不存在: {config_path}")
            return 1
            
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        
        # 获取Telegram配置
        telegram_config = config.get("telegram_adapter", {})
        api_key = telegram_config.get("api_key")
        channel_id = telegram_config.get("channel_id")
        proxy_url = telegram_config.get("proxy_url")
        
        if not api_key or not channel_id:
            logger.error("缺少API密钥或频道ID")
            return 1
        
        # 创建Telegram适配器
        logger.info(f"创建Telegram适配器: 频道={channel_id}, 代理={proxy_url is not None}")
        adapter = TelegramAdapter(
            api_key=api_key,
            channel_id=channel_id,
            proxy_url=proxy_url
        )
        
        # 初始化适配器
        logger.info("初始化适配器...")
        result = await adapter.initialize(message_handler)
        if not result:
            logger.error("初始化Telegram适配器失败")
            return 1
        
        # 启动轮询
        logger.info("启动轮询...")
        result = await adapter.start_polling()
        if not result:
            logger.error("启动Telegram轮询失败")
            return 1
        
        # 发送测试消息
        logger.info("发送测试消息...")
        message = await adapter.send_message("这是一条测试消息 " + asyncio.current_task().get_name())
        if message:
            logger.info(f"测试消息已发送: {message.get('message_id')}")
        else:
            logger.warning("发送测试消息失败")
        
        # 运行一段时间然后退出
        logger.info(f"等待接收消息...")
        logger.info("按Ctrl+C停止测试")
        
        # 30秒倒计时
        for remaining in range(120, 0, -1):
            if remaining % 10 == 0:
                logger.info(f"剩余时间: {remaining}秒, 已接收 {len(received_messages)} 条消息")
                
                # 每10秒尝试主动获取消息一次
                if remaining % 30 == 0:
                    logger.info("尝试主动获取消息...")
                    messages = await adapter.get_messages(10)
                    logger.info(f"主动获取到 {len(messages)} 条消息")
                    for msg in messages:
                        logger.info(f"消息: {msg.get('message_id')} - {msg.get('text', '')[:30]}")
                        
            await asyncio.sleep(1)
        
        # 关闭适配器
        logger.info("关闭Telegram适配器...")
        await adapter.stop_polling()
        
        # 总结
        logger.info(f"测试完成，共收到 {len(received_messages)} 条消息")
        for i, msg in enumerate(received_messages):
            logger.info(f"消息 {i+1}: ID={msg.get('message_id')}, 类型={msg.get('message_type')}, 文本={msg.get('text', '')[:30]}")
        
        return 0
    
    except KeyboardInterrupt:
        logger.info("测试被用户中断")
        # 确保停止轮询
        if 'adapter' in locals():
            await adapter.stop_polling()
        return 130
    
    except Exception as e:
        logger.exception(f"测试过程中出错: {str(e)}")
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("程序被用户中断")
        sys.exit(130) 