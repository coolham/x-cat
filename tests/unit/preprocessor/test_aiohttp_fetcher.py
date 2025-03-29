"""
aiohttp 内容获取器测试
"""
import pytest
import pytest_asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from app.preprocessor.aiohttp_fetcher import AiohttpFetcher

@pytest.fixture
def fetcher():
    """创建 aiohttp 内容获取器实例"""
    return AiohttpFetcher(max_content_length=1000, timeout=5)

@pytest.mark.asyncio
async def test_fetch_with_aiohttp(fetcher):
    """测试使用 aiohttp 获取内容"""
    url = "https://example.com"
    
    # 模拟 aiohttp 会话
    with patch('aiohttp.ClientSession.get') as mock_get:
        # 模拟响应
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.headers = {"Content-Type": "text/html"}
        mock_response.text.return_value = """
            <html>
                <head>
                    <title>Test Page</title>
                </head>
                <body>
                    <article>
                        <p>This is a test content</p>
                    </article>
                </body>
            </html>
        """
        mock_get.return_value.__aenter__.return_value = mock_response
        
        # 执行测试
        results = await fetcher.fetch([url])
        
        # 验证结果
        assert len(results) == 1
        assert results[0]['success'] is True
        assert 'This is a test content' in results[0]['content']
        assert results[0]['type'] == 'html'
        
        # 验证请求参数
        mock_get.assert_called_once_with(
            url,
            proxy=None,
            timeout=pytest.approx(5),
            headers={"User-Agent": fetcher.user_agent}
        )

@pytest.mark.asyncio
async def test_fetch_with_proxy(fetcher):
    """测试使用代理获取内容"""
    url = "https://example.com"
    proxy_url = "http://127.0.0.1:7890"
    
    # 模拟 aiohttp 会话
    with patch('aiohttp.ClientSession.get') as mock_get:
        # 模拟响应
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.headers = {"Content-Type": "text/html"}
        mock_response.text.return_value = "<html><body>Test content</body></html>"
        mock_get.return_value.__aenter__.return_value = mock_response
        
        # 设置代理
        fetcher.proxy_url = proxy_url
        
        # 执行测试
        results = await fetcher.fetch([url])
        
        # 验证代理设置
        mock_get.assert_called_once_with(
            url,
            proxy=proxy_url,
            timeout=pytest.approx(5),
            headers={"User-Agent": fetcher.user_agent}
        )

@pytest.mark.asyncio
async def test_fetch_with_timeout(fetcher):
    """测试超时处理"""
    url = "https://example.com"
    
    # 模拟 aiohttp 会话
    with patch('aiohttp.ClientSession.get') as mock_get:
        # 模拟超时
        mock_get.side_effect = TimeoutError("Request timeout")
        
        # 执行测试
        results = await fetcher.fetch([url])
        
        # 验证结果
        assert len(results) == 1
        assert results[0]['success'] is False
        assert "Request timeout" in results[0]['error']

@pytest.mark.asyncio
async def test_fetch_with_http_error(fetcher):
    """测试 HTTP 错误处理"""
    url = "https://example.com"
    
    # 模拟 aiohttp 会话
    with patch('aiohttp.ClientSession.get') as mock_get:
        # 模拟 404 错误
        mock_response = MagicMock()
        mock_response.status = 404
        mock_get.return_value.__aenter__.return_value = mock_response
        
        # 执行测试
        results = await fetcher.fetch([url])
        
        # 验证结果
        assert len(results) == 1
        assert results[0]['success'] is False
        assert "HTTP 404" in results[0]['error']

@pytest.mark.asyncio
async def test_fetch_with_non_html_content(fetcher):
    """测试非 HTML 内容处理"""
    url = "https://example.com"
    
    # 模拟 aiohttp 会话
    with patch('aiohttp.ClientSession.get') as mock_get:
        # 模拟 PDF 内容
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.headers = {"Content-Type": "application/pdf"}
        mock_get.return_value.__aenter__.return_value = mock_response
        
        # 执行测试
        results = await fetcher.fetch([url])
        
        # 验证结果
        assert len(results) == 1
        assert results[0]['success'] is True
        assert results[0]['type'] == 'non_html'
        assert "[非HTML内容: application/pdf]" in results[0]['content']

@pytest.mark.asyncio
async def test_fetch_with_retry(fetcher):
    """测试重试机制"""
    url = "https://example.com"
    
    # 模拟 aiohttp 会话
    with patch('aiohttp.ClientSession.get') as mock_get:
        # 模拟第一次失败，第二次成功
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.headers = {"Content-Type": "text/html"}
        mock_response.text.return_value = "<html><body>Test content</body></html>"
        
        mock_get.side_effect = [
            Exception("First attempt failed"),
            mock_response
        ]
        
        # 执行测试
        results = await fetcher.fetch([url])
        
        # 验证结果
        assert len(results) == 1
        assert results[0]['success'] is True
        assert 'Test content' in results[0]['content']
        
        # 验证重试次数
        assert mock_get.call_count == 2

@pytest.mark.asyncio
async def test_fetch_with_max_retries(fetcher):
    """测试最大重试次数"""
    url = "https://example.com"
    
    # 模拟 aiohttp 会话
    with patch('aiohttp.ClientSession.get') as mock_get:
        # 模拟连续失败
        mock_get.side_effect = Exception("Request failed")
        
        # 执行测试
        results = await fetcher.fetch([url])
        
        # 验证结果
        assert len(results) == 1
        assert results[0]['success'] is False
        assert "Request failed" in results[0]['error']
        
        # 验证重试次数
        assert mock_get.call_count == 3  # 初始尝试 + 2次重试

@pytest.mark.asyncio
async def test_fetch_empty_urls(fetcher):
    """测试空URL列表"""
    results = await fetcher.fetch([])
    assert results == []

@pytest.mark.asyncio
async def test_fetch_with_long_content(fetcher):
    """测试长内容截断"""
    url = "https://example.com"
    long_content = "Test content " * 1000
    
    # 模拟 aiohttp 会话
    with patch('aiohttp.ClientSession.get') as mock_get:
        # 模拟响应
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.headers = {"Content-Type": "text/html"}
        mock_response.text.return_value = f"<html><body>{long_content}</body></html>"
        mock_get.return_value.__aenter__.return_value = mock_response
        
        # 执行测试
        results = await fetcher.fetch([url])
        
        # 验证结果
        assert len(results) == 1
        assert results[0]['success'] is True
        assert len(results[0]['content']) <= 1000  # 检查是否被截断

@pytest.mark.asyncio
async def test_close(fetcher):
    """测试关闭资源"""
    await fetcher.close()
    assert fetcher._session is None 