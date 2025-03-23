"""
Integration tests for Telegram API adapter
"""
import os
import sys
import pytest

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app.adapters.telegram import TelegramAdapter


# Skip all tests in this module unless --integration flag is provided
pytestmark = pytest.mark.integration


class TestTelegramIntegration:
    """Integration test suite for the TelegramAdapter class with real API"""
    
    def setup_method(self):
        """Setup method for each test"""
        # Check if API key is available
        self.api_key = os.environ.get('TELEGRAM_API_KEY')
        self.channel_id = os.environ.get('TELEGRAM_CHANNEL_ID')
        
        if not self.api_key or self.api_key.startswith('mock_') or self.api_key == 'test_api_key':
            pytest.skip("Valid TELEGRAM_API_KEY not found in environment")
            
        if not self.channel_id or self.channel_id == 'test_channel_id':
            pytest.skip("Valid TELEGRAM_CHANNEL_ID not found in environment")
    
    def test_connect_to_telegram(self):
        """Test connection to Telegram API"""
        adapter = TelegramAdapter(self.api_key, self.channel_id)
        
        # Test bot connection
        bot_info = adapter.bot.get_me()
        assert bot_info is not None
        assert hasattr(bot_info, 'first_name')
        assert hasattr(bot_info, 'username')
        
        print(f"Connected to bot: {bot_info.first_name} (@{bot_info.username})")
    
    def test_fetch_messages(self):
        """Test fetching messages from Telegram channel"""
        adapter = TelegramAdapter(self.api_key, self.channel_id)
        
        # Try to fetch some messages
        messages = adapter.fetch_content(limit=5)
        
        # May be empty if there are no new messages, but should not throw an error
        assert isinstance(messages, list)
        
        for msg in messages:
            assert 'id' in msg
            assert 'text' in msg
            assert 'timestamp' in msg
            
            # Print some debug info
            print(f"Retrieved message: {msg['id']}")
            print(f"Content: {msg['text'][:50]}...")
            
    def test_forward_to_category(self):
        """Test forwarding a message to a category"""
        # This assumes you have access to forward messages
        # Otherwise it will be skipped
        if not os.environ.get('CATEGORY_CHANNEL_IDS'):
            pytest.skip("CATEGORY_CHANNEL_IDS not configured")
            
        adapter = TelegramAdapter(self.api_key, self.channel_id)
        
        # Try to get a message first
        messages = adapter.fetch_content(limit=1)
        if not messages:
            pytest.skip("No messages available for testing forwarding")
            
        # Try to forward the message
        message_id = messages[0]['message_id']
        result = adapter.forward_to_category(message_id, "AI")
        
        assert result is True 