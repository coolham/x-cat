# -*- coding: utf-8 -*-
"""
URL提取器测试
"""
import pytest
from app.preprocessor.url_extractor import URLExtractor

@pytest.fixture
def extractor():
    """创建URL提取器实例"""
    return URLExtractor()

def test_extract_empty_content(extractor):
    """测试空内容"""
    urls = extractor.extract('')
    assert urls == []

def test_extract_no_urls(extractor):
    """测试无URL内容"""
    urls = extractor.extract('这是一条普通消息')
    assert urls == []

def test_extract_single_url(extractor):
    """测试单个URL"""
    urls = extractor.extract('访问 https://example.com')
    assert urls == ['https://example.com']

def test_extract_multiple_urls(extractor):
    """测试多个URL"""
    urls = extractor.extract('链接1: https://example1.com 链接2: https://example2.com')
    assert urls == ['https://example1.com', 'https://example2.com']

def test_extract_invalid_urls(extractor):
    """测试无效URL"""
    urls = extractor.extract('无效链接: http:// 有效链接: https://example.com')
    assert urls == ['https://example.com']

def test_is_valid_url(extractor):
    """测试URL验证"""
    assert extractor.is_valid_url('https://example.com') is True
    assert extractor.is_valid_url('http://example.com') is True
    assert extractor.is_valid_url('ftp://example.com') is False
    assert extractor.is_valid_url('invalid-url') is False 