# -*- coding: utf-8 -*-
"""
内容获取器测试
"""
import pytest
import pytest_asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from app.preprocessor.content_fetcher import ContentFetcher
from playwright.async_api import async_playwright

@pytest.fixture
def fetcher():
    """创建内容获取器实例"""
    return ContentFetcher(max_content_length=1000, timeout=5)

@pytest.fixture
async def playwright():
    """创建 Playwright 实例"""
    async with async_playwright() as p:
        yield p

@pytest.mark.asyncio
async def test_fetch_with_playwright(fetcher, playwright):
    """测试使用 Playwright 获取动态内容"""
    # 模拟 Twitter/X 链接
    url = "https://twitter.com/example/status/123456789"
    
    # 模拟 Playwright 浏览器
    browser = await playwright.chromium.launch(headless=True)
    context = await browser.new_context()
    page = await context.new_page()
    
    # 模拟页面内容
    await page.set_content("""
        <html>
            <head>
                <title>Twitter Post</title>
            </head>
            <body>
                <article>
                    <div class="tweet-content">
                        <p>This is a test tweet content</p>
                    </div>
                </article>
            </body>
        </html>
    """)
    
    # 模拟 Playwright 方法
    with patch('playwright.async_api.async_playwright') as mock_playwright:
        mock_playwright.return_value.__aenter__.return_value = playwright
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()
        
        playwright.chromium.launch.return_value = mock_browser
        mock_browser.new_context.return_value = mock_context
        mock_context.new_page.return_value = mock_page
        
        # 执行测试
        results = await fetcher.fetch_all([url])
        
        # 验证结果
        assert len(results) == 1
        assert results[0]['success'] is True
        assert 'This is a test tweet content' in results[0]['content']
        assert results[0]['type'] == 'twitter'
        
        # 验证 Playwright 方法被调用
        mock_playwright.assert_called_once()
        playwright.chromium.launch.assert_called_once()
        mock_browser.new_context.assert_called_once()
        mock_context.new_page.assert_called_once()
        mock_page.goto.assert_called_once_with(url)
        mock_page.content.assert_called_once()
        mock_page.close.assert_called_once()
        mock_context.close.assert_called_once()
        mock_browser.close.assert_called_once()

@pytest.mark.asyncio
async def test_fetch_with_proxy(fetcher, playwright):
    """测试使用代理获取内容"""
    url = "https://twitter.com/example/status/123456789"
    proxy_url = "http://127.0.0.1:7890"
    
    # 模拟 Playwright 浏览器
    with patch('playwright.async_api.async_playwright') as mock_playwright:
        mock_playwright.return_value.__aenter__.return_value = playwright
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()
        
        playwright.chromium.launch.return_value = mock_browser
        mock_browser.new_context.return_value = mock_context
        mock_context.new_page.return_value = mock_page
        
        # 设置代理
        fetcher.proxy_url = proxy_url
        
        # 执行测试
        results = await fetcher.fetch_all([url])
        
        # 验证代理设置
        mock_browser.new_context.assert_called_once_with(
            proxy={
                "server": proxy_url,
                "username": None,
                "password": None
            }
        )

@pytest.mark.asyncio
async def test_fetch_with_timeout(fetcher, playwright):
    """测试超时处理"""
    url = "https://twitter.com/example/status/123456789"
    
    # 模拟 Playwright 浏览器
    with patch('playwright.async_api.async_playwright') as mock_playwright:
        mock_playwright.return_value.__aenter__.return_value = playwright
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()
        
        playwright.chromium.launch.return_value = mock_browser
        mock_browser.new_context.return_value = mock_context
        mock_context.new_page.return_value = mock_page
        
        # 模拟超时
        mock_page.goto.side_effect = TimeoutError("Navigation timeout")
        
        # 执行测试
        results = await fetcher.fetch_all([url])
        
        # 验证结果
        assert len(results) == 1
        assert results[0]['success'] is False
        assert "Navigation timeout" in results[0]['error']

@pytest.mark.asyncio
async def test_fetch_with_js_error(fetcher, playwright):
    """测试 JavaScript 错误处理"""
    url = "https://twitter.com/example/status/123456789"
    
    # 模拟 Playwright 浏览器
    with patch('playwright.async_api.async_playwright') as mock_playwright:
        mock_playwright.return_value.__aenter__.return_value = playwright
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()
        
        playwright.chromium.launch.return_value = mock_browser
        mock_browser.new_context.return_value = mock_context
        mock_context.new_page.return_value = mock_page
        
        # 模拟 JavaScript 错误
        mock_page.content.return_value = "JavaScript is required to view this content"
        
        # 执行测试
        results = await fetcher.fetch_all([url])
        
        # 验证结果
        assert len(results) == 1
        assert results[0]['success'] is False
        assert "JavaScript is required" in results[0]['error']

@pytest.mark.asyncio
async def test_fetch_with_network_error(fetcher, playwright):
    """测试网络错误处理"""
    url = "https://twitter.com/example/status/123456789"
    
    # 模拟 Playwright 浏览器
    with patch('playwright.async_api.async_playwright') as mock_playwright:
        mock_playwright.return_value.__aenter__.return_value = playwright
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()
        
        playwright.chromium.launch.return_value = mock_browser
        mock_browser.new_context.return_value = mock_context
        mock_context.new_page.return_value = mock_page
        
        # 模拟网络错误
        mock_page.goto.side_effect = Exception("Network error")
        
        # 执行测试
        results = await fetcher.fetch_all([url])
        
        # 验证结果
        assert len(results) == 1
        assert results[0]['success'] is False
        assert "Network error" in results[0]['error']

@pytest.mark.asyncio
async def test_fetch_with_cleanup(fetcher, playwright):
    """测试资源清理"""
    url = "https://twitter.com/example/status/123456789"
    
    # 模拟 Playwright 浏览器
    with patch('playwright.async_api.async_playwright') as mock_playwright:
        mock_playwright.return_value.__aenter__.return_value = playwright
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()
        
        playwright.chromium.launch.return_value = mock_browser
        mock_browser.new_context.return_value = mock_context
        mock_context.new_page.return_value = mock_page
        
        # 执行测试
        results = await fetcher.fetch_all([url])
        
        # 验证资源清理
        mock_page.close.assert_called_once()
        mock_context.close.assert_called_once()
        mock_browser.close.assert_called_once()
        mock_playwright.return_value.__aexit__.assert_called_once()

@pytest.mark.asyncio
async def test_fetch_with_viewport(fetcher, playwright):
    """测试视口设置"""
    url = "https://twitter.com/example/status/123456789"
    
    # 模拟 Playwright 浏览器
    with patch('playwright.async_api.async_playwright') as mock_playwright:
        mock_playwright.return_value.__aenter__.return_value = playwright
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()
        
        playwright.chromium.launch.return_value = mock_browser
        mock_browser.new_context.return_value = mock_context
        mock_context.new_page.return_value = mock_page
        
        # 执行测试
        results = await fetcher.fetch_all([url])
        
        # 验证视口设置
        mock_context.new_page.assert_called_once_with(
            viewport={'width': 1920, 'height': 1080}
        )

@pytest.mark.asyncio
async def test_fetch_empty_urls(fetcher):
    """测试空URL列表"""
    results = await fetcher.fetch_all([])
    assert results == []

@pytest.mark.asyncio
async def test_fetch_single_url(fetcher):
    """测试单个URL获取"""
    with patch('aiohttp.ClientSession.get') as mock_get:
        # 模拟响应
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.text.return_value = '<html><body>测试内容</body></html>'
        mock_get.return_value.__aenter__.return_value = mock_response
        
        results = await fetcher.fetch_all(['https://example.com'])
        
        assert len(results) == 1
        assert results[0]['success'] is True
        assert results[0]['url'] == 'https://example.com'
        assert '测试内容' in results[0]['content']

@pytest.mark.asyncio
async def test_fetch_multiple_urls(fetcher):
    """测试多个URL获取"""
    with patch('aiohttp.ClientSession.get') as mock_get:
        # 模拟响应
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.text.return_value = '<html><body>测试内容</body></html>'
        mock_get.return_value.__aenter__.return_value = mock_response
        
        results = await fetcher.fetch_all([
            'https://example1.com',
            'https://example2.com'
        ])
        
        assert len(results) == 2
        assert all(r['success'] for r in results)

@pytest.mark.asyncio
async def test_fetch_error_status(fetcher):
    """测试错误状态码"""
    with patch('aiohttp.ClientSession.get') as mock_get:
        # 模拟404响应
        mock_response = MagicMock()
        mock_response.status = 404
        mock_get.return_value.__aenter__.return_value = mock_response
        
        results = await fetcher.fetch_all(['https://example.com'])
        
        assert len(results) == 1
        assert results[0]['success'] is False
        assert 'HTTP 404' in results[0]['error']

@pytest.mark.asyncio
async def test_fetch_timeout(fetcher):
    """测试超时"""
    with patch('aiohttp.ClientSession.get') as mock_get:
        # 模拟超时
        mock_get.side_effect = TimeoutError()
        
        results = await fetcher.fetch_all(['https://example.com'])
        
        assert len(results) == 1
        assert results[0]['success'] is False
        assert '请求超时' in results[0]['error']

@pytest.mark.asyncio
async def test_fetch_long_content(fetcher):
    """测试长内容截断"""
    with patch('aiohttp.ClientSession.get') as mock_get:
        # 模拟长内容
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.text.return_value = '<html><body>' + '测试内容' * 1000 + '</body></html>'
        mock_get.return_value.__aenter__.return_value = mock_response
        
        results = await fetcher.fetch_all(['https://example.com'])
        
        assert len(results) == 1
        assert results[0]['success'] is True
        assert len(results[0]['content']) <= 1000  # 检查是否被截断

@pytest.mark.asyncio
async def test_close(fetcher):
    """测试关闭资源"""
    await fetcher.close()
    assert fetcher.session is None 

"""
内容获取器工厂类测试
"""
import pytest
import pytest_asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from app.preprocessor.content_fetcher import ContentFetcher
from app.preprocessor.aiohttp_fetcher import AiohttpFetcher
from app.preprocessor.playwright_fetcher import PlaywrightFetcher

@pytest.fixture
def fetcher():
    """创建内容获取器工厂实例"""
    return ContentFetcher(max_content_length=1000, timeout=5)

@pytest.mark.asyncio
async def test_fetch_with_aiohttp(fetcher):
    """测试使用 aiohttp 获取普通网页内容"""
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
async def test_fetch_with_playwright(fetcher):
    """测试使用 Playwright 获取动态内容"""
    url = "https://twitter.com/example/status/123456789"
    
    # 模拟 Playwright 浏览器
    with patch('playwright.async_api.async_playwright') as mock_playwright:
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()
        
        mock_playwright.return_value.__aenter__.return_value.chromium.launch.return_value = mock_browser
        mock_browser.new_context.return_value = mock_context
        mock_context.new_page.return_value = mock_page
        
        # 模拟页面内容
        mock_page.content.return_value = """
            <html>
                <head>
                    <title>Twitter Post</title>
                </head>
                <body>
                    <article>
                        <div class="tweet-content">
                            <p>This is a test tweet content</p>
                        </div>
                    </article>
                </body>
            </html>
        """
        
        # 执行测试
        results = await fetcher.fetch([url])
        
        # 验证结果
        assert len(results) == 1
        assert results[0]['success'] is True
        assert 'This is a test tweet content' in results[0]['content']
        assert results[0]['type'] == 'html'
        
        # 验证 Playwright 方法被调用
        mock_playwright.assert_called_once()
        mock_browser.new_context.assert_called_once()
        mock_context.new_page.assert_called_once()
        mock_page.goto.assert_called_once_with(url)
        mock_page.content.assert_called_once()

@pytest.mark.asyncio
async def test_fetch_with_mixed_urls(fetcher):
    """测试混合获取普通网页和动态内容"""
    urls = [
        "https://example.com",  # 普通网页
        "https://twitter.com/example/status/123456789"  # 动态内容
    ]
    
    # 模拟 aiohttp 会话
    with patch('aiohttp.ClientSession.get') as mock_get, \
         patch('playwright.async_api.async_playwright') as mock_playwright:
        # 模拟 aiohttp 响应
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.headers = {"Content-Type": "text/html"}
        mock_response.text.return_value = "<html><body>Test content</body></html>"
        mock_get.return_value.__aenter__.return_value = mock_response
        
        # 模拟 Playwright 响应
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()
        mock_playwright.return_value.__aenter__.return_value.chromium.launch.return_value = mock_browser
        mock_browser.new_context.return_value = mock_context
        mock_context.new_page.return_value = mock_page
        mock_page.content.return_value = "<html><body>Tweet content</body></html>"
        
        # 执行测试
        results = await fetcher.fetch(urls)
        
        # 验证结果
        assert len(results) == 2
        assert all(r['success'] for r in results)
        assert 'Test content' in results[0]['content']
        assert 'Tweet content' in results[1]['content']
        
        # 验证两种方法都被调用
        mock_get.assert_called_once()
        mock_playwright.assert_called_once()

@pytest.mark.asyncio
async def test_fetch_with_proxy(fetcher):
    """测试使用代理获取内容"""
    urls = [
        "https://example.com",
        "https://twitter.com/example/status/123456789"
    ]
    proxy_url = "http://127.0.0.1:7890"
    
    # 模拟 aiohttp 会话
    with patch('aiohttp.ClientSession.get') as mock_get, \
         patch('playwright.async_api.async_playwright') as mock_playwright:
        # 模拟响应
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.headers = {"Content-Type": "text/html"}
        mock_response.text.return_value = "<html><body>Test content</body></html>"
        mock_get.return_value.__aenter__.return_value = mock_response
        
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_playwright.return_value.__aenter__.return_value.chromium.launch.return_value = mock_browser
        mock_browser.new_context.return_value = mock_context
        
        # 设置代理
        fetcher.proxy_url = proxy_url
        
        # 执行测试
        results = await fetcher.fetch(urls)
        
        # 验证代理设置
        mock_get.assert_called_with(
            urls[0],
            proxy=proxy_url,
            timeout=pytest.approx(5),
            headers={"User-Agent": fetcher.user_agent}
        )
        mock_browser.new_context.assert_called_with(
            proxy={
                "server": proxy_url,
                "username": None,
                "password": None
            },
            viewport={'width': 1920, 'height': 1080}
        )

@pytest.mark.asyncio
async def test_fetch_with_errors(fetcher):
    """测试错误处理"""
    urls = [
        "https://example.com",  # aiohttp 错误
        "https://twitter.com/example/status/123456789"  # Playwright 错误
    ]
    
    # 模拟错误
    with patch('aiohttp.ClientSession.get') as mock_get, \
         patch('playwright.async_api.async_playwright') as mock_playwright:
        # 模拟 aiohttp 错误
        mock_get.side_effect = Exception("aiohttp error")
        
        # 模拟 Playwright 错误
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()
        mock_playwright.return_value.__aenter__.return_value.chromium.launch.return_value = mock_browser
        mock_browser.new_context.return_value = mock_context
        mock_context.new_page.return_value = mock_page
        mock_page.goto.side_effect = Exception("Playwright error")
        
        # 执行测试
        results = await fetcher.fetch(urls)
        
        # 验证错误处理
        assert len(results) == 2
        assert not any(r['success'] for r in results)
        assert "aiohttp error" in results[0]['error']
        assert "Playwright error" in results[1]['error']

@pytest.mark.asyncio
async def test_fetch_empty_urls(fetcher):
    """测试空URL列表"""
    results = await fetcher.fetch([])
    assert results == []

@pytest.mark.asyncio
async def test_close(fetcher):
    """测试关闭资源"""
    await fetcher.close()
    assert fetcher._aiohttp_fetcher._session is None
    assert fetcher._playwright_fetcher._playwright is None 