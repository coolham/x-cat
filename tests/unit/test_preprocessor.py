# -*- coding: utf-8 -*-
"""
预处理模块单元测试
使用真实的网络请求进行测试
"""
import pytest
import pytest_asyncio
import asyncio
from app.preprocessor.url_extractor import URLExtractor
from app.preprocessor.content_fetcher import ContentFetcher
from app.preprocessor.content_preprocessor import ContentPreprocessor

# URL提取器测试
def test_url_extractor():
    """测试URL提取器"""
    extractor = URLExtractor()
    
    # 测试基本URL提取
    content = "访问 https://example.com 和 http://test.com"
    urls = extractor.extract(content)
    assert len(urls) == 2
    assert "https://example.com" in urls
    assert "http://test.com" in urls
    
    # 测试无效URL
    content = "无效URL: http://"
    urls = extractor.extract(content)
    assert len(urls) == 0
    
    # 测试复杂URL
    content = "https://example.com/path?param=value#fragment"
    urls = extractor.extract(content)
    assert len(urls) == 1
    assert urls[0] == "https://example.com/path?param=value#fragment"
    
    # 测试URL验证
    assert extractor.is_valid_url("https://example.com")
    assert not extractor.is_valid_url("http://")
    assert not extractor.is_valid_url("invalid")

# 内容获取器测试
@pytest.mark.asyncio
async def test_content_fetcher():
    """测试内容获取器"""
    fetcher = ContentFetcher(max_content_length=1000)
    
    # 测试成功获取
    result = await fetcher._fetch_single("https://example.com")
    assert result['success']
    assert 'content' in result
    assert len(result['content']) <= 1000
    assert 'Example Domain' in result['content']  # example.com 的标准内容
    
    # 测试不存在的URL
    result = await fetcher._fetch_single("https://this-is-a-non-existent-domain.com")
    assert not result['success']
    assert 'error' in result
    
    # 测试并发获取
    urls = [
        "https://example.com",
        "https://httpbin.org/get",
        "https://httpbin.org/status/200"
    ]
    results = await fetcher.fetch_all(urls)
    assert len(results) == 3
    success_count = sum(1 for r in results if r['success'])
    assert success_count >= 2  # 至少两个URL应该能成功获取
    
    await fetcher.close()

# 内容预处理器测试
@pytest.mark.asyncio
async def test_content_preprocessor():
    """测试内容预处理器"""
    preprocessor = ContentPreprocessor(max_url_count=2)
    
    # 测试基本处理
    content = {
        'text': '查看 https://example.com',
        'source': 'telegram',
        'metadata': {'user_id': '123'}
    }
    
    result = await preprocessor.preprocess(content)
    assert result['success']
    assert 'content' in result
    assert 'urls' in result
    assert len(result['urls']) == 1
    assert 'Example Domain' in result['content']
    
    # 测试URL数量限制
    content = {
        'text': '''
        查看以下链接：
        https://example.com
        https://httpbin.org/get
        https://httpbin.org/status/200
        ''',
        'source': 'telegram'
    }
    
    result = await preprocessor.preprocess(content)
    assert result['success']
    assert len(result['urls']) <= 2  # 检查URL数量限制
    
    # 测试错误处理
    invalid_content = {'text': 'test'}  # 缺少source字段
    result = await preprocessor.preprocess(invalid_content)
    assert not result['success']
    assert 'errors' in result
    
    # 测试混合URL处理
    content = {
        'text': '''
        https://example.com
        https://this-is-a-non-existent-domain.com
        ''',
        'source': 'telegram'
    }
    
    result = await preprocessor.preprocess(content)
    assert result['success']
    assert len(result['errors']) == 1  # 应该有一个URL获取失败
    assert 'Example Domain' in result['content']  # 成功获取的内容应该存在
    
    await preprocessor.close()

# 集成测试
@pytest.mark.asyncio
async def test_preprocessing_pipeline():
    """测试预处理流水线"""
    preprocessor = ContentPreprocessor()
    
    # 测试完整流程
    content = {
        'text': '''
        查看以下链接：
        https://example.com
        https://httpbin.org/get
        ''',
        'source': 'telegram',
        'metadata': {'user_id': '123'}
    }
    
    result = await preprocessor.preprocess(content)
    
    # 验证结果
    assert result['success']
    assert len(result['urls']) <= 5  # 检查URL数量限制
    assert 'content' in result
    assert 'errors' in result
    
    # 验证内容格式
    content_parts = result['content'].split('\n\n')
    assert len(content_parts) >= 1  # 至少包含原始内容
    
    # 验证错误处理
    if result['errors']:
        assert all(isinstance(error, str) for error in result['errors'])
    
    await preprocessor.close()

# 性能测试
@pytest.mark.asyncio
async def test_preprocessor_performance():
    """测试预处理器性能"""
    preprocessor = ContentPreprocessor(max_url_count=3)
    
    # 测试多个URL的处理时间
    content = {
        'text': '''
        https://example.com
        https://httpbin.org/get
        https://httpbin.org/status/200
        ''',
        'source': 'telegram'
    }
    
    start_time = asyncio.get_event_loop().time()
    result = await preprocessor.preprocess(content)
    end_time = asyncio.get_event_loop().time()
    
    # 验证处理时间
    processing_time = end_time - start_time
    assert processing_time < 5.0  # 处理时间应该小于5秒
    
    # 验证结果
    assert result['success']
    assert len(result['urls']) <= 3
    
    await preprocessor.close() 