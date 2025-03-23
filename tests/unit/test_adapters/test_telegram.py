"""
Unit tests for the Telegram adapter
"""
import os
import sys
import pytest
import datetime
from unittest.mock import MagicMock, patch, PropertyMock

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from app.adapters.telegram import TelegramAdapter


class TestTelegramAdapter:
    """Test suite for the TelegramAdapter class"""
    
    @pytest.fixture
    def mock_bot(self):
        """Create a mock Telegram Bot"""
        with patch('app.adapters.telegram.Bot') as mock_bot_cls:
            mock_instance = mock_bot_cls.return_value
            # Configure mock behavior
            mock_instance.get_me.return_value = MagicMock(
                first_name="TestBot", 
                username="test_bot"
            )
            yield mock_instance
    
    @pytest.fixture
    def adapter(self):
        """Create a TelegramAdapter instance for testing"""
        # Use mock_ prefix to ensure mock mode is activated
        test_api_key = "mock_test_key"
        test_channel_id = "test_channel"
        
        # Use temporary file for processed messages
        temp_file = "temp_processed_messages.txt"
        if os.path.exists(temp_file):
            os.remove(temp_file)
            
        adapter = TelegramAdapter(test_api_key, test_channel_id, temp_file)
        yield adapter
        
        # Cleanup
        if os.path.exists(temp_file):
            os.remove(temp_file)
    
    def test_init(self, adapter):
        """Test adapter initialization"""
        assert adapter.api_key.startswith("mock_")
        assert adapter.channel_id == "test_channel"
        assert hasattr(adapter, 'processed_message_ids')
        assert isinstance(adapter.processed_message_ids, set)
    
    def test_fetch_content_mock_mode(self, adapter):
        """Test fetch_content in mock mode"""
        # Mock mode should automatically generate sample messages
        messages = adapter.fetch_content()
        
        # Verify messages structure
        assert isinstance(messages, list)
        if messages:  # Messages are randomly generated, might be empty
            sample_msg = messages[0]
            assert 'id' in sample_msg
            assert 'text' in sample_msg
            assert 'timestamp' in sample_msg
            assert 'twitter.com' in sample_msg['text'] or 'x.com' in sample_msg['text']
    
    def test_mark_as_processed(self, adapter):
        """Test marking messages as processed"""
        test_id = "test_message_123"
        
        # Message should not be marked as processed initially
        assert test_id not in adapter.processed_message_ids
        
        # Mark message as processed
        result = adapter.mark_as_processed(test_id)
        
        # Verify result and state
        assert result is True
        assert test_id in adapter.processed_message_ids
        
        # Check if ID was written to file
        with open(adapter.processed_messages_file, 'r') as f:
            content = f.read()
            assert test_id in content
    
    @patch('app.adapters.telegram.Bot')
    def test_fetch_content_real_api(self, mock_bot_cls):
        """Test fetch_content with real API (mocked)"""
        # Setup mock telegram.Bot
        mock_bot = mock_bot_cls.return_value
        
        # Create mock update and message objects
        mock_update = MagicMock()
        mock_message = MagicMock()
        
        # Configure channel post
        mock_update.update_id = 12345
        mock_update.channel_post = mock_message
        
        # Configure message
        mock_message.message_id = 67890
        mock_message.chat.id = "-1001234567890"
        mock_message.text = "Check out this tweet: https://twitter.com/user/status/123456"
        mock_message.date = datetime.datetime.now()
        mock_message.from_user = MagicMock(username="user123")
        
        # Set up the mock to return our prepared data
        mock_bot.get_updates.return_value = [mock_update]
        
        # Create adapter with real API mode
        adapter = TelegramAdapter("real_api_key", "-1001234567890")
        
        # Manual patch of the bot
        adapter.bot = mock_bot
        
        # Test fetch_content
        messages = adapter.fetch_content()
        
        # Verify results
        assert len(messages) == 1
        assert messages[0]['id'] == "12345"
        assert messages[0]['message_id'] == "67890"
        assert messages[0]['chat_id'] == "-1001234567890"
        assert "twitter.com/user/status/123456" in messages[0]['text']
    
    def test_forward_to_category_mock_mode(self, adapter):
        """Test forwarding a message to a category channel in mock mode"""
        # In mock mode, this should just log the action without errors
        result = adapter.forward_to_category("test_msg_123", "AI")
        assert result is True 