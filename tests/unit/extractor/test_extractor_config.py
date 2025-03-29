"""
提取器配置测试
"""
import pytest
from app.extractors.config import ExtractorConfig

def test_extractor_config_initialization():
    """测试配置初始化"""
    # 测试默认配置
    config = ExtractorConfig()
    assert config.max_content_length == 8000
    assert config.max_url_count == 5
    assert config.timeout == 30
    assert config.validate_urls is True
    assert isinstance(config.source_config, dict)
    
    # 测试自定义配置
    custom_config = ExtractorConfig(
        max_content_length=10000,
        max_url_count=10,
        timeout=60,
        validate_urls=False
    )
    assert custom_config.max_content_length == 10000
    assert custom_config.max_url_count == 10
    assert custom_config.timeout == 60
    assert custom_config.validate_urls is False

def test_extractor_config_serialization():
    """测试配置序列化"""
    config = ExtractorConfig(
        max_content_length=10000,
        source_config={'telegram': {'allowed_chat_types': ['private']}}
    )
    
    # 测试转换为字典
    config_dict = config.to_dict()
    assert config_dict['max_content_length'] == 10000
    assert config_dict['source_config']['telegram']['allowed_chat_types'] == ['private']
    
    # 测试从字典创建
    new_config = ExtractorConfig.from_dict(config_dict)
    assert new_config.max_content_length == 10000
    assert new_config.source_config['telegram']['allowed_chat_types'] == ['private']

def test_extractor_config_update():
    """测试配置更新"""
    config = ExtractorConfig()
    
    # 测试更新通用配置
    config.update({
        'max_content_length': 15000,
        'timeout': 45
    })
    assert config.max_content_length == 15000
    assert config.timeout == 45
    
    # 测试更新数据源配置
    config.update({
        'source_config': {
            'telegram': {
                'allowed_chat_types': ['private', 'group']
            }
        }
    })
    assert config.source_config['telegram']['allowed_chat_types'] == ['private', 'group']
    
    # 测试未知配置键
    config.update({'unknown_key': 'value'})
    assert not hasattr(config, 'unknown_key')

def test_extractor_config_source_config():
    """测试数据源配置"""
    config = ExtractorConfig()
    
    # 测试设置数据源配置
    config.set_source_config('telegram', {'allowed_chat_types': ['private']})
    assert config.get_source_config('telegram')['allowed_chat_types'] == ['private']
    
    # 测试获取不存在的配置
    assert config.get_source_config('unknown') is None
    assert config.get_source_config('unknown', default='default') == 'default' 