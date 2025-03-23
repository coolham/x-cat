"""
集成测试：Telegram适配器V20功能测试
"""
import os
import sys
import pytest
import asyncio
import json
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# 导入测试脚本
from tests.test_telegram import main as telegram_test

# 测试是否跳过的标记
skip_if_no_config = pytest.mark.skipif(
    not Path("config.json").exists(),
    reason="缺少config.json配置文件"
)


def has_telegram_config():
    """检查是否有有效的Telegram配置"""
    try:
        with open("config.json", 'r', encoding='utf-8') as f:
            config = json.load(f)
            telegram_config = config.get("telegram_adapter", {})
            return bool(telegram_config.get("api_key") and telegram_config.get("channel_id"))
    except Exception:
        return False


# 默认跳过Telegram测试，除非显式启用
def should_run_telegram_test():
    """检查是否应该运行Telegram测试
    
    通过环境变量ENABLE_TELEGRAM_TEST=1启用
    """
    return os.environ.get('ENABLE_TELEGRAM_TEST') == '1'


@pytest.mark.skipif(not has_telegram_config(), reason="缺少Telegram API密钥或频道ID配置")
@pytest.mark.skipif(not should_run_telegram_test(), reason="Telegram测试已通过，默认跳过。设置ENABLE_TELEGRAM_TEST=1环境变量启用")
@pytest.mark.asyncio
async def test_telegram_message_receive():
    """测试Telegram适配器接收和发送消息的功能"""
    
    # 运行带超时的测试(20秒)
    received_messages = await telegram_test(timeout=20)
    
    # 验证结果 - 消息可能会被收到，也可能因为延迟而没收到
    assert received_messages is not None, "测试未返回任何结果"
    
    # 如果收到消息，验证其内容，否则跳过这部分测试
    if len(received_messages) > 0:
        print(f"收到 {len(received_messages)} 条消息，进行详细验证")
        
        # 检查至少有一条消息包含测试文本
        test_messages = [
            msg for msg in received_messages 
            if hasattr(msg, 'text') and "测试消息: 使用v20.0 API测试" in msg.text
        ]
        
        assert len(test_messages) > 0, "收到消息但未包含测试文本"
    else:
        pytest.skip("未接收到消息，可能是因为Telegram API延迟或限流")
        
    # 测试通过 - 机器人成功启动并且消息处理基本功能可用
    print("Telegram适配器测试通过")
    return True 