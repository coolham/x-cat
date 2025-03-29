# -*- coding: utf-8 -*-
"""
内容提取器测试
"""
import pytest
import pytest_asyncio
from datetime import datetime
from app.extractors.telegram import TelegramExtractor

# Telegram提取器测试
@pytest.mark.asyncio
async def test_telegram_extractor():
    """测试Telegram提取器"""
    extractor = TelegramExtractor()
    
    # 测试有效消息
    valid_message = {
        'message_id': 123,
        'text': '查看 https://example.com',
        'chat': {
            'id': 456,
            'type': 'private'
        },
        'from': {
            'id': 789,
            'first_name': 'Test',
            'username': 'test_user'
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
    
    result = await extractor.extract(valid_message)
    assert result['success']
    assert result['content'] == '查看 https://example.com'
    assert result['source'] == 'telegram'
    assert len(result['urls']) == 1
    assert 'https://example.com' in result['urls']
    assert 'message_id' in result['metadata']
    assert 'chat_id' in result['metadata']
    assert 'from_user' in result['metadata']
    
    # 测试无效消息
    invalid_message = {
        'text': '测试消息'
    }
    
    result = await extractor.extract(invalid_message)
    assert not result['success']
    assert result['errors'] == ['Invalid Telegram message format']
    
    # 测试异常处理
    malformed_message = {
        'message_id': 123,
        'text': '测试消息',
        'chat': None  # 故意设置无效的chat字段
    }
    
    result = await extractor.extract(malformed_message)
    assert not result['success']
    assert len(result['errors']) > 0
    
    # 测试URL提取
    message_with_urls = {
        'message_id': 123,
        'text': '''
        查看以下链接：
        https://example.com
        http://test.com
        ''',
        'chat': {
            'id': 456,
            'type': 'private'
        },
        'date': int(datetime.now().timestamp())
    }
    
    result = await extractor.extract(message_with_urls)
    assert result['success']
    assert len(result['urls']) == 2
    assert 'https://example.com' in result['urls']
    assert 'http://test.com' in result['urls']
    
    # 测试元数据提取
    message_with_metadata = {
        'message_id': 123,
        'text': '测试消息',
        'chat': {
            'id': 456,
            'type': 'group',
            'title': '测试群组'
        },
        'from': {
            'id': 789,
            'first_name': 'Test',
            'username': 'test_user'
        },
        'reply_to_message': {
            'message_id': 100,
            'text': '回复的消息'
        },
        'date': int(datetime.now().timestamp())
    }
    
    result = await extractor.extract(message_with_metadata)
    assert result['success']
    assert result['metadata']['chat_type'] == 'group'
    assert result['metadata']['from_user']['username'] == 'test_user'
    assert 'reply_to_message' in result['metadata'] 