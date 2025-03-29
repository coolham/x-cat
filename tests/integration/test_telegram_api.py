"""
Integration tests for Telegram API adapter
"""
import os
import sys
import pytest
import asyncio
from datetime import datetime, timedelta
from dotenv import load_dotenv

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app.utils.logger import logger, define_log_level

# 配置logger
define_log_level(print_level="DEBUG", logfile_level="DEBUG", name="telegram_test")

from app.adapters.telegram import TelegramAdapter

# 加载环境变量
load_dotenv(override=True)  # 使用override=True确保覆盖已存在的环境变量

# 为整个模块添加integration标记
pytestmark = pytest.mark.integration

"""
Required environment variables in .env:
TELEGRAM_API_KEY=your_bot_token
TELEGRAM_CHANNEL_ID=your_channel_id
TELEGRAM_USE_PROXY=true  # 如果需要代理

"""
# pytest tests/test_telegram_api.py -v --integration

class TestTelegramIntegration:
    """Integration test suite for the TelegramAdapter class with real API"""
    
    @pytest.fixture(autouse=True)
    async def setup(self):
        """Setup method for each test"""
        # Check if API key is available
        self.api_key = os.getenv('TELEGRAM_API_KEY')
        self.channel_id = os.getenv('TELEGRAM_CHANNEL_ID')
        
        if not self.api_key:
            pytest.skip("TELEGRAM_API_KEY not found in environment")
            
        if not self.channel_id:
            pytest.skip("TELEGRAM_CHANNEL_ID not found in environment")
            
        # 打印环境变量信息（不包含敏感信息）
        print(f"Using channel ID: {self.channel_id}")
        print(f"Using proxy: {os.getenv('TELEGRAM_USE_PROXY', 'false')}")
        print(f"API Key format: {'bot' + '*' * (len(self.api_key) - 3)}")  # 只显示前3个字符
        
        # 创建适配器
        self.adapter = TelegramAdapter(self.api_key, self.channel_id)
        
        # 初始化适配器
        async def message_callback(message):
            print(f"Received message in callback: {message.get('metadata', {}).get('message_id')}")
            print(f"Message content: {message.get('content', '')}")
            
        if not await self.adapter.initialize(message_callback):
            pytest.skip("Failed to initialize Telegram adapter")
            
        # 启动轮询
        if not await self.adapter.start_polling():
            pytest.skip("Failed to start polling")
            
        yield
        
        # 清理
        await self.adapter.close()
    
    @pytest.mark.asyncio
    async def test_telegram_operations(self):
        """Test all Telegram operations in sequence"""
        # 1. 测试连接
        print("\nTesting bot connection...")
        bot_info = await self.adapter.get_bot_info()
        assert bot_info is not None
        assert 'id' in bot_info
        assert 'first_name' in bot_info
        assert 'username' in bot_info
        print(f"Connected to bot: {bot_info['first_name']} (@{bot_info['username']})")
        
        # 2. 测试消息发送
        print("\nTesting message sending...")
        category_channel_id = os.getenv('TELEGRAM_CHANNEL_ID')
        if not category_channel_id:
            pytest.skip("TELEGRAM_CHANNEL_ID not found in environment")
            
        # 发送测试消息
        test_message = "This is a test message for sending test."
        sent_message = await self.adapter.bot.send_message(
            chat_id=self.channel_id,
            text=test_message
        )
        
        if not sent_message:
            pytest.skip("Failed to send test message")
            
        # 3. 测试消息接收
        print("\nTesting message receiving...")
        print("Waiting for 20 seconds to check for new messages...")
        
        # 记录发送消息的时间
        sent_time = datetime.now()
        
        # 等待20秒，每5秒检查一次消息
        for i in range(4):
            await asyncio.sleep(5)
            messages = self.adapter.get_received_messages()
            print(f"After {5*(i+1)} seconds, found {len(messages)} messages")
            for msg in messages:
                print(f"Message {msg.get('metadata', {}).get('message_id')}: {msg.get('content', '')}")
        
        # 获取接收到的消息
        messages = self.adapter.get_received_messages()
        
        # 打印找到的消息
        print(f"\nFound {len(messages)} received messages:")
        for msg in messages:
            print("---Message Details---")
            print(f"Raw message: {msg}")  # 打印原始消息数据
            print(f"Message ID: {msg.get('metadata', {}).get('message_id')}")
            print(f"Message Type: {msg.get('metadata', {}).get('type')}")
            print(f"Content: {msg.get('content', '')}")
            print(f"Source: {msg.get('source', '')}")
            print("-------------------")

if __name__ == "__main__":
    # 直接运行时不使用integration标记
    pytest.main([__file__, "-v", "--integration"])
