#!/usr/bin/env python
"""
Telegram适配器测试脚本
用于测试Telegram消息接收功能
"""
import os
import sys
import json
import asyncio
import logging
import time
from typing import Dict, Any, List

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from loguru import logger
from app.adapters.telegram import TelegramAdapter

# 配置日志
logger.remove()
logger.add(sys.stdout, level="DEBUG")

# 全局变量存储接收到的消息
received_messages = []


async def test_message_callback(message: Dict[str, Any]) -> None:
    """
    测试用的消息回调函数
    
    Args:
        message: 收到的消息数据
    """
    global received_messages
    
    # 存储消息
    received_messages.append(message)
    
    logger.info(f"收到新消息: ID={message.get('message_id')}, 文本={message.get('text', '')[:30]}...")
    logger.debug(f"消息详情: {json.dumps(message, ensure_ascii=False, indent=2)}")


async def check_messages_periodically(adapter: TelegramAdapter, interval: int = 10):
    """
    定期检查消息（手动方式）
    
    Args:
        adapter: Telegram适配器
        interval: 检查间隔(秒)
    """
    while True:
        try:
            logger.info("手动获取最近消息...")
            messages = await adapter.get_messages(10)
            if messages:
                for msg in messages:
                    logger.info(f"手动获取消息: ID={msg.get('message_id')}, 文本={msg.get('text', '')[:30]}...")
            else:
                logger.debug("没有获取到新消息")
            
            # 等待下一次检查
            await asyncio.sleep(interval)
            
        except asyncio.CancelledError:
            logger.debug("周期性检查已取消")
            break
        except Exception as e:
            logger.error(f"周期性检查出错: {e}")
            await asyncio.sleep(interval)


async def test_telegram_adapter():
    """
    测试Telegram适配器
    """
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
    
    # 创建适配器
    adapter = TelegramAdapter(
        api_key=api_key,
        channel_id=channel_id,
        proxy_url=proxy_url
    )
    
    try:
        # 初始化适配器
        logger.info("初始化Telegram适配器...")
        success = await adapter.initialize(test_message_callback)
        if not success:
            logger.error("初始化适配器失败")
            return
        
        # 重写已处理的消息集合（测试用）
        last_update_id = 0
        
        # 启动轮询
        logger.info("启动Telegram轮询...")
        success = await adapter.start_polling()
        if not success:
            logger.error("启动轮询失败")
            return
        
        # 启动周期性检查任务
        check_task = asyncio.create_task(check_messages_periodically(adapter, 20))
        
        # 测试发送消息
        logger.info("发送测试消息到频道...")
        test_message = f"这是一条测试消息，时间：{time.strftime('%Y-%m-%d %H:%M:%S')}"
        result = await adapter.send_message(test_message)
        logger.info(f"发送结果: {result.get('ok', False)}")
        
        # 等待消息
        test_duration = 300  # 5分钟
        logger.info(f"等待接收消息 ({test_duration}秒后自动退出)...")
        
        # 创建一个倒计时定时器，每10秒报告一次状态
        start_time = time.time()
        received_count = 0
        
        while time.time() - start_time < test_duration:
            current_count = len(received_messages)
            if current_count > received_count:
                logger.info(f"已通过回调接收 {current_count} 条消息")
                received_count = current_count
            
            # 每10秒报告一次
            await asyncio.sleep(10)
            logger.debug(f"测试运行中: 已经过 {int(time.time() - start_time)} 秒, 已接收 {len(received_messages)} 条消息")
        
        # 测试结束时的摘要
        logger.info(f"测试结束，总共接收到 {len(received_messages)} 条消息")
        
        # 取消周期性检查任务
        check_task.cancel()
        try:
            await check_task
        except asyncio.CancelledError:
            pass
        
    except KeyboardInterrupt:
        logger.info("测试被用户中断")
    except Exception as e:
        logger.error(f"测试过程中出错: {e}")
        import traceback
        logger.debug(traceback.format_exc())
    finally:
        # 关闭适配器
        logger.info("关闭Telegram适配器...")
        await adapter.close()


def run_test():
    """运行测试"""
    try:
        asyncio.run(test_telegram_adapter())
    except KeyboardInterrupt:
        logger.info("测试被用户中断")
    except Exception as e:
        logger.error(f"运行测试时出错: {e}")
        import traceback
        logger.debug(traceback.format_exc())


if __name__ == "__main__":
    run_test() 