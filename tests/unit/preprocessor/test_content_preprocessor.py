# -*- coding: utf-8 -*-
"""
内容预处理器测试
"""
import pytest
import pytest_asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from app.preprocessor.content_preprocessor import ContentPreprocessor
from playwright.async_api import async_playwright

@pytest.fixture
def preprocessor():
    """创建预处理器实例"""
    return ContentPreprocessor(max_url_count=2, max_content_length=1000)

@pytest.fixture
async def playwright():
    """创建 Playwright 实例"""
    async with async_playwright() as p:
        yield p

@pytest.mark.asyncio
async def test_preprocess_text_only(preprocessor):
    """测试纯文本处理"""
    raw_content = {
        'text': '这是一条测试消息',
        'source': 'telegram',
        'metadata': {'chat_id': '123456'}
    }
    
    result = await preprocessor.preprocess(raw_content)
    
    assert result['success'] is True
    assert isinstance(result['content'], dict)
    assert result['content']['text'] == '这是一条测试消息'
    assert result['content']['type'] == 'message'
    assert result['content']['format'] == 'text'
    assert result['content']['source'] == 'telegram'
    assert 'timestamp' in result['content']
    assert 'summary' in result['content']
    assert 'keywords' in result['content']
    assert 'entities' in result['content']
    assert 'sentiment' in result['content']
    assert 'language' in result['content']
    assert result['content']['metadata'] == {'chat_id': '123456'}
    assert result['errors'] == []
    assert 'text_length' in result['debug_info']

@pytest.mark.asyncio
async def test_preprocess_url(preprocessor):
    """测试URL处理"""
    raw_content = {
        'text': 'https://example.com',
        'source': 'telegram',
        'metadata': {'chat_id': '123456'}
    }
    
    result = await preprocessor.preprocess(raw_content)
    
    assert result['success'] is True
    assert isinstance(result['content'], dict)
    assert result['content']['type'] == 'article'
    assert result['content']['format'] == 'text'
    assert result['content']['source'] == 'https://example.com'
    assert 'timestamp' in result['content']
    assert 'summary' in result['content']
    assert 'keywords' in result['content']
    assert 'entities' in result['content']
    assert 'sentiment' in result['content']
    assert 'language' in result['content']
    assert 'url' in result['content']['metadata']
    assert 'original_text' in result['content']['metadata']
    assert result['errors'] == []
    assert 'url' in result['debug_info']
    assert 'content_length' in result['debug_info']

@pytest.mark.asyncio
async def test_preprocess_command_test(preprocessor):
    """测试 /test 命令"""
    raw_content = {
        'text': '/test',
        'source': 'telegram',
        'metadata': {'chat_id': '123456'}
    }
    
    result = await preprocessor.preprocess(raw_content)
    
    assert result['success'] is True
    assert isinstance(result['content'], dict)
    assert result['content']['text'] == '测试命令执行成功'
    assert result['content']['type'] == 'command'
    assert result['content']['format'] == 'text'
    assert result['content']['source'] == 'telegram'
    assert 'timestamp' in result['content']
    assert result['content']['summary'] == '测试命令执行成功'
    assert 'command' in result['content']['keywords']
    assert result['content']['sentiment'] == 'neutral'
    assert 'command' in result['content']['metadata']
    assert 'original_text' in result['content']['metadata']
    assert result['errors'] == []
    assert 'command' in result['debug_info']

@pytest.mark.asyncio
async def test_preprocess_command_abc(preprocessor):
    """测试 /abc 命令"""
    raw_content = {
        'text': '/abc',
        'source': 'telegram',
        'metadata': {'chat_id': '123456'}
    }
    
    result = await preprocessor.preprocess(raw_content)
    
    assert result['success'] is True
    assert isinstance(result['content'], dict)
    assert result['content']['text'] == 'ABC命令执行成功'
    assert result['content']['type'] == 'command'
    assert result['content']['format'] == 'text'
    assert result['content']['source'] == 'telegram'
    assert 'timestamp' in result['content']
    assert result['content']['summary'] == 'ABC命令执行成功'
    assert 'command' in result['content']['keywords']
    assert result['content']['sentiment'] == 'neutral'
    assert 'command' in result['content']['metadata']
    assert 'original_text' in result['content']['metadata']
    assert result['errors'] == []
    assert 'command' in result['debug_info']

@pytest.mark.asyncio
async def test_preprocess_command_help(preprocessor):
    """测试 /help 命令"""
    raw_content = {
        'text': '/help',
        'source': 'telegram',
        'metadata': {'chat_id': '123456'}
    }
    
    result = await preprocessor.preprocess(raw_content)
    
    assert result['success'] is True
    assert isinstance(result['content'], dict)
    assert '可用命令列表' in result['content']['text']
    assert result['content']['type'] == 'command'
    assert result['content']['format'] == 'text'
    assert result['content']['source'] == 'telegram'
    assert 'timestamp' in result['content']
    assert result['content']['summary'] == result['content']['text']
    assert 'command' in result['content']['keywords']
    assert result['content']['sentiment'] == 'neutral'
    assert 'command' in result['content']['metadata']
    assert 'original_text' in result['content']['metadata']
    assert result['errors'] == []
    assert 'command' in result['debug_info']

@pytest.mark.asyncio
async def test_preprocess_unknown_command(preprocessor):
    """测试未知命令"""
    raw_content = {
        'text': '/unknown',
        'source': 'telegram',
        'metadata': {'chat_id': '123456'}
    }
    
    result = await preprocessor.preprocess(raw_content)
    
    assert result['success'] is False
    assert '未知命令' in result['errors'][0]
    assert 'content' not in result

@pytest.mark.asyncio
async def test_preprocess_command_with_args(preprocessor):
    """测试带参数的命令"""
    raw_content = {
        'text': '/test arg1 arg2',
        'source': 'telegram',
        'metadata': {'chat_id': '123456'}
    }
    
    result = await preprocessor.preprocess(raw_content)
    
    assert result['success'] is True
    assert isinstance(result['content'], dict)
    assert result['content']['text'] == '测试命令执行成功'
    assert result['content']['type'] == 'command'
    assert result['content']['format'] == 'text'
    assert result['content']['source'] == 'telegram'
    assert 'timestamp' in result['content']
    assert result['content']['summary'] == '测试命令执行成功'
    assert 'command' in result['content']['keywords']
    assert result['content']['sentiment'] == 'neutral'
    assert 'command' in result['content']['metadata']
    assert 'original_text' in result['content']['metadata']
    assert result['errors'] == []
    assert 'command' in result['debug_info']

@pytest.mark.asyncio
async def test_preprocess_invalid_input(preprocessor):
    """测试无效输入处理"""
    raw_content = {
        'source': 'telegram',  # 缺少text字段
        'metadata': {'chat_id': '123456'}
    }
    
    result = await preprocessor.preprocess(raw_content)
    
    assert result['success'] is False
    assert '输入内容格式无效' in result['errors']
    assert 'content' not in result

@pytest.mark.asyncio
async def test_preprocess_media(preprocessor):
    """测试媒体内容处理"""
    raw_content = {
        'text': '这是一条带图片的消息',
        'source': 'telegram',
        'metadata': {
            'chat_id': '123456',
            'photo': ['https://example.com/photo.jpg'],
            'video': ['https://example.com/video.mp4']
        }
    }
    
    result = await preprocessor.preprocess(raw_content)
    
    assert result['success'] is True
    assert isinstance(result['content'], dict)
    assert result['content']['text'] == '这是一条带图片的消息'
    assert result['content']['type'] == 'media'
    assert result['content']['format'] == 'image'  # 优先使用图片格式
    assert result['content']['source'] == 'telegram'
    assert 'timestamp' in result['content']
    assert 'summary' in result['content']
    assert 'keywords' in result['content']
    assert 'entities' in result['content']
    assert 'sentiment' in result['content']
    assert 'language' in result['content']
    assert 'photo' in result['content']['metadata']
    assert 'video' in result['content']['metadata']
    assert result['errors'] == []
    assert 'media_types' in result['debug_info']
    assert 'image' in result['debug_info']['media_types']
    assert 'video' in result['debug_info']['media_types']

@pytest.mark.asyncio
async def test_preprocess_twitter_url(preprocessor, playwright):
    """测试处理 Twitter/X URL"""
    raw_content = {
        'text': 'https://twitter.com/example/status/123456789',
        'source': 'telegram',
        'metadata': {'chat_id': '123456'}
    }
    
    # 模拟 Playwright 浏览器
    with patch('playwright.async_api.async_playwright') as mock_playwright:
        mock_playwright.return_value.__aenter__.return_value = playwright
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()
        
        playwright.chromium.launch.return_value = mock_browser
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
        
        result = await preprocessor.preprocess(raw_content)
        
        assert result['success'] is True
        assert isinstance(result['content'], dict)
        assert result['content']['type'] == 'article'
        assert result['content']['format'] == 'text'
        assert result['content']['source'] == 'https://twitter.com/example/status/123456789'
        assert 'This is a test tweet content' in result['content']['content']
        assert result['errors'] == []
        assert 'url' in result['debug_info']
        assert 'content_length' in result['debug_info']

@pytest.mark.asyncio
async def test_preprocess_twitter_url_with_proxy(preprocessor, playwright):
    """测试使用代理处理 Twitter/X URL"""
    raw_content = {
        'text': 'https://twitter.com/example/status/123456789',
        'source': 'telegram',
        'metadata': {'chat_id': '123456'}
    }
    
    # 设置代理
    preprocessor.content_fetcher.proxy_url = "http://127.0.0.1:7890"
    
    # 模拟 Playwright 浏览器
    with patch('playwright.async_api.async_playwright') as mock_playwright:
        mock_playwright.return_value.__aenter__.return_value = playwright
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()
        
        playwright.chromium.launch.return_value = mock_browser
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
        
        result = await preprocessor.preprocess(raw_content)
        
        # 验证代理设置
        mock_browser.new_context.assert_called_once_with(
            proxy={
                "server": "http://127.0.0.1:7890",
                "username": None,
                "password": None
            }
        )
        
        assert result['success'] is True
        assert 'This is a test tweet content' in result['content']['content']

@pytest.mark.asyncio
async def test_preprocess_twitter_url_with_timeout(preprocessor, playwright):
    """测试处理 Twitter/X URL 超时情况"""
    raw_content = {
        'text': 'https://twitter.com/example/status/123456789',
        'source': 'telegram',
        'metadata': {'chat_id': '123456'}
    }
    
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
        
        result = await preprocessor.preprocess(raw_content)
        
        assert result['success'] is False
        assert "Navigation timeout" in result['errors'][0]

@pytest.mark.asyncio
async def test_preprocess_twitter_url_with_js_error(preprocessor, playwright):
    """测试处理 Twitter/X URL JavaScript 错误情况"""
    raw_content = {
        'text': 'https://twitter.com/example/status/123456789',
        'source': 'telegram',
        'metadata': {'chat_id': '123456'}
    }
    
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
        
        result = await preprocessor.preprocess(raw_content)
        
        assert result['success'] is False
        assert "JavaScript is required" in result['errors'][0]

@pytest.mark.asyncio
async def test_preprocess_twitter_url_with_network_error(preprocessor, playwright):
    """测试处理 Twitter/X URL 网络错误情况"""
    raw_content = {
        'text': 'https://twitter.com/example/status/123456789',
        'source': 'telegram',
        'metadata': {'chat_id': '123456'}
    }
    
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
        
        result = await preprocessor.preprocess(raw_content)
        
        assert result['success'] is False
        assert "Network error" in result['errors'][0]

@pytest.mark.asyncio
async def test_preprocess_twitter_url_with_cleanup(preprocessor, playwright):
    """测试处理 Twitter/X URL 资源清理"""
    raw_content = {
        'text': 'https://twitter.com/example/status/123456789',
        'source': 'telegram',
        'metadata': {'chat_id': '123456'}
    }
    
    # 模拟 Playwright 浏览器
    with patch('playwright.async_api.async_playwright') as mock_playwright:
        mock_playwright.return_value.__aenter__.return_value = playwright
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()
        
        playwright.chromium.launch.return_value = mock_browser
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
        
        result = await preprocessor.preprocess(raw_content)
        
        # 验证资源清理
        mock_page.close.assert_called_once()
        mock_context.close.assert_called_once()
        mock_browser.close.assert_called_once()
        mock_playwright.return_value.__aexit__.assert_called_once()
        
        assert result['success'] is True
        assert 'This is a test tweet content' in result['content']['content']

@pytest.mark.asyncio
async def test_preprocess_twitter_url_with_viewport(preprocessor, playwright):
    """测试处理 Twitter/X URL 视口设置"""
    raw_content = {
        'text': 'https://twitter.com/example/status/123456789',
        'source': 'telegram',
        'metadata': {'chat_id': '123456'}
    }
    
    # 模拟 Playwright 浏览器
    with patch('playwright.async_api.async_playwright') as mock_playwright:
        mock_playwright.return_value.__aenter__.return_value = playwright
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()
        
        playwright.chromium.launch.return_value = mock_browser
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
        
        result = await preprocessor.preprocess(raw_content)
        
        # 验证视口设置
        mock_context.new_page.assert_called_once_with(
            viewport={'width': 1920, 'height': 1080}
        )
        
        assert result['success'] is True
        assert 'This is a test tweet content' in result['content']['content'] 