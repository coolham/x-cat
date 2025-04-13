"""
提取器模块测试用例
"""
import pytest
from datetime import datetime
from typing import Dict, Any
from unittest.mock import MagicMock, patch

from app.extractors.base import BaseExtractor
from app.extractors.telegram import TelegramExtractor


@pytest.fixture
def test_config() -> Dict[str, Any]:
    """测试配置"""
    return {
        'api_key': 'test_api_key',
        'channel_id': 'test_channel_id',
        'timezone': 'Asia/Shanghai'
    }


@pytest.fixture
def test_message_data() -> Dict[str, Any]:
    """测试消息数据"""
    return {
        'message_id': 123456,
        'chat_id': 789012,
        'text': '测试消息',
        'date': datetime.now().isoformat(),
        'from_user': {
            'id': 345678,
            'username': 'test_user',
            'first_name': 'Test',
            'last_name': 'User'
        }
    }


class TestBaseExtractor:
    """测试基础提取器"""
    
    def test_init(self, test_config):
        """测试初始化"""
        extractor = BaseExtractor(test_config)
        assert extractor.config == test_config
        assert extractor.cache_manager is not None
    
    def test_extract_not_implemented(self, test_config):
        """测试未实现的extract方法"""
        extractor = BaseExtractor(test_config)
        with pytest.raises(NotImplementedError):
            extractor.extract({})
    
    def test_get_cache_key_not_implemented(self, test_config):
        """测试未实现的_get_cache_key方法"""
        extractor = BaseExtractor(test_config)
        with pytest.raises(NotImplementedError):
            extractor._get_cache_key({})


class TestTelegramExtractor:
    """测试Telegram提取器"""
    
    @pytest.fixture
    def mock_bot(self):
        """模拟Telegram机器人"""
        with patch('app.extractors.telegram.TelegramExtractor.bot') as mock:
            yield mock
    
    @pytest.fixture
    def mock_message(self):
        """模拟Telegram消息"""
        message = MagicMock()
        message.text = '测试消息'
        message.caption = None
        message.type = 'text'
        message.date = datetime.now()
        message.from_user = MagicMock()
        message.from_user.id = 345678
        message.from_user.username = 'test_user'
        message.from_user.first_name = 'Test'
        message.from_user.last_name = 'User'
        return message
    
    def test_init(self, test_config):
        """测试初始化"""
        extractor = TelegramExtractor(test_config)
        assert extractor.source_type == 'telegram'
        assert extractor.config == test_config
        assert extractor.cache_manager is not None
    
    def test_get_cache_key(self, test_config, test_message_data):
        """测试获取缓存键"""
        extractor = TelegramExtractor(test_config)
        cache_key = extractor._get_cache_key(test_message_data)
        assert cache_key == f"telegram:message:{test_message_data['message_id']}"
    
    def test_get_cache_key_no_message_id(self, test_config):
        """测试获取缓存键（无消息ID）"""
        extractor = TelegramExtractor(test_config)
        cache_key = extractor._get_cache_key({})
        assert cache_key is None
    
    def test_extract(self, test_config, test_message_data, mock_bot, mock_message):
        """测试提取数据"""
        # 设置模拟
        mock_bot.get_message.return_value = mock_message
        
        # 创建提取器
        extractor = TelegramExtractor(test_config)
        
        # 提取数据
        result = extractor.extract(test_message_data)
        
        # 验证结果
        assert result['content'] == mock_message.text
        assert result['message_type'] == mock_message.type
        assert result['date'] == mock_message.date.isoformat()
        assert result['sender']['id'] == mock_message.from_user.id
        assert result['sender']['username'] == mock_message.from_user.username
        assert result['sender']['first_name'] == mock_message.from_user.first_name
        assert result['sender']['last_name'] == mock_message.from_user.last_name
    
    def test_extract_no_message(self, test_config, test_message_data, mock_bot):
        """测试提取数据（无消息）"""
        # 设置模拟
        mock_bot.get_message.return_value = None
        
        # 创建提取器
        extractor = TelegramExtractor(test_config)
        
        # 提取数据
        result = extractor.extract(test_message_data)
        
        # 验证结果
        assert result == test_message_data
    
    def test_process_message_with_cache(self, test_config, test_message_data, mock_bot, mock_message):
        """测试处理消息（使用缓存）"""
        # 设置模拟
        mock_bot.get_message.return_value = mock_message
        
        # 创建提取器
        extractor = TelegramExtractor(test_config)
        
        # 第一次处理（无缓存）
        result1 = extractor.process_message(test_message_data)
        
        # 第二次处理（有缓存）
        result2 = extractor.process_message(test_message_data)
        
        # 验证结果
        assert result1 == result2
        assert result1['content'] == mock_message.text
        assert result1['message_type'] == mock_message.type
        assert result1['date'] == mock_message.date.isoformat()
        assert result1['sender']['id'] == mock_message.from_user.id
        assert result1['sender']['username'] == mock_message.from_user.username
        assert result1['sender']['first_name'] == mock_message.from_user.first_name
        assert result1['sender']['last_name'] == mock_message.from_user.last_name 