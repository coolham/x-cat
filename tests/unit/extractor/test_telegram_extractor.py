"""
Telegram提取器测试
"""
import pytest
from datetime import datetime
from app.extractors.telegram import TelegramExtractor
from app.extractors.config import ExtractorConfig

@pytest.fixture
def telegram_config():
    """创建Telegram配置"""
    return ExtractorConfig(
        max_content_length=10000,
        max_url_count=10,
        source_config={
            'telegram': {
                'allowed_chat_types': ['private', 'group'],
                'min_message_length': 1
            }
        }
    )

@pytest.fixture
def telegram_extractor(telegram_config):
    """创建Telegram提取器"""
    return TelegramExtractor(config=telegram_config)

@pytest.mark.asyncio
async def test_telegram_extractor_initialization(telegram_extractor):
    """测试Telegram提取器初始化"""
    assert telegram_extractor.source_type == 'telegram'
    assert telegram_extractor.config.max_content_length == 10000
    assert telegram_extractor.config.max_url_count == 10

@pytest.mark.asyncio
async def test_telegram_message_validation(telegram_extractor):
    """测试Telegram消息验证"""
    # 测试有效消息
    valid_message = {
        'message_id': 123,
        'text': '测试消息',
        'chat': {'id': 456, 'type': 'private'},
        'from': {'id': 789, 'username': 'test_user'},
        'date': int(datetime.now().timestamp())
    }
    assert await telegram_extractor.validate(valid_message)
    
    # 测试无效消息（缺少必要字段）
    invalid_message = {
        'text': '测试消息'
    }
    assert not await telegram_extractor.validate(invalid_message)
    
    # 测试无效消息（无效的聊天类型）
    invalid_chat_message = {
        'message_id': 123,
        'text': '测试消息',
        'chat': {'id': 456, 'type': 'invalid_type'},
        'from': {'id': 789},
        'date': int(datetime.now().timestamp())
    }
    assert not await telegram_extractor.validate(invalid_chat_message)

@pytest.mark.asyncio
async def test_telegram_content_extraction(telegram_extractor):
    """测试Telegram内容提取"""
    # 测试基本消息提取
    message = {
        'message_id': 123,
        'text': '查看 https://example.com',
        'chat': {
            'id': 456,
            'type': 'private',
            'title': '测试群组',
            'username': 'test_group'
        },
        'from': {
            'id': 789,
            'first_name': 'Test',
            'last_name': 'User',
            'username': 'test_user',
            'language_code': 'zh',
            'is_bot': False
        },
        'date': int(datetime.now().timestamp()),
        'entities': [
            {
                'type': 'url',
                'offset': 3,
                'length': 19
            }
        ]
    }
    
    result = await telegram_extractor.extract(message)
    assert result['success']
    assert result['content'] == '查看 https://example.com'
    assert len(result['urls']) == 1
    assert 'https://example.com' in result['urls']
    
    # 验证元数据
    metadata = result['metadata']
    assert metadata['message_id'] == 123
    assert metadata['chat_id'] == 456
    assert metadata['chat_type'] == 'private'
    assert metadata['chat_title'] == '测试群组'
    assert metadata['chat_username'] == 'test_group'
    assert metadata['from_user']['username'] == 'test_user'
    assert metadata['from_user']['language_code'] == 'zh'
    assert metadata['from_user']['is_bot'] is False

@pytest.mark.asyncio
async def test_telegram_content_limits(telegram_extractor):
    """测试内容限制"""
    # 测试内容长度限制
    long_text = "测试消息" * 1000
    message = {
        'message_id': 123,
        'text': long_text,
        'chat': {'id': 456, 'type': 'private'},
        'from': {'id': 789},
        'date': int(datetime.now().timestamp())
    }
    
    result = await telegram_extractor.extract(message)
    assert result['success']
    assert len(result['content']) <= telegram_extractor.config.max_content_length
    
    # 测试URL数量限制
    urls = [f"https://example{i}.com" for i in range(20)]
    message['text'] = " ".join(urls)
    
    result = await telegram_extractor.extract(message)
    assert result['success']
    assert len(result['urls']) <= telegram_extractor.config.max_url_count

@pytest.mark.asyncio
async def test_telegram_error_handling(telegram_extractor):
    """测试错误处理"""
    # 测试无效消息格式
    invalid_message = {
        'text': '测试消息'
    }
    
    result = await telegram_extractor.extract(invalid_message)
    assert not result['success']
    assert "Invalid message format" in result['errors'][0]
    
    # 测试提取异常
    message = {
        'message_id': 123,
        'text': '测试消息',
        'chat': {'id': 456, 'type': 'private'},
        'from': {'id': 789},
        'date': int(datetime.now().timestamp())
    }
    
    # 启用测试模式并设置抛出异常
    telegram_extractor.set_test_mode(enabled=True, raise_error=True)
    
    # 模拟提取异常
    with pytest.raises(Exception):
        await telegram_extractor.extract(message)

@pytest.mark.asyncio
async def test_telegram_config_update(telegram_extractor):
    """测试配置更新"""
    # 更新配置
    new_config = {
        'max_content_length': 5000,
        'source_config': {
            'telegram': {
                'allowed_chat_types': ['channel'],
                'min_message_length': 1
            }
        }
    }
    telegram_extractor.update_config(new_config)
    
    # 验证配置更新
    assert telegram_extractor.config.max_content_length == 5000
    assert telegram_extractor.config.get_source_config('telegram')['allowed_chat_types'] == ['channel']
    
    # 测试新配置生效
    message = {
        'message_id': 123,
        'text': '测试消息',
        'chat': {'id': 456, 'type': 'channel'},
        'from': {'id': 789},
        'date': int(datetime.now().timestamp())
    }
    
    result = await telegram_extractor.extract(message)
    assert result['success']
    assert len(result['content']) <= 5000 