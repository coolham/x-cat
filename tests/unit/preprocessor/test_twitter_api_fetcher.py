"""
Twitter API 获取器测试
"""
import os
import sys
import pytest
import asyncio
import aiohttp
from unittest.mock import patch, MagicMock, AsyncMock
# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from app.preprocessor.twitter_api_fetcher import TwitterAPIFetcher
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 从环境变量获取Twitter API配置
TEST_CONFIG = {
    'api_key': os.getenv('TWITTER_API_KEY'),
    'api_secret': os.getenv('TWITTER_API_SECRET'),
    'access_token': os.getenv('TWITTER_ACCESS_TOKEN'),
    'access_token_secret': os.getenv('TWITTER_ACCESS_TOKEN_SECRET'),
    'bearer_token': os.getenv('TWITTER_BEARER_TOKEN')
}

def check_twitter_config():
    """检查Twitter API配置是否完整"""
    missing_keys = [key for key, value in TEST_CONFIG.items() if not value]
    if missing_keys:
        pytest.skip(f"缺少必要的Twitter API配置: {', '.join(missing_keys)}")

@pytest.fixture
async def twitter_fetcher():
    """创建TwitterAPIFetcher实例"""
    check_twitter_config()
    fetcher = TwitterAPIFetcher(**TEST_CONFIG)
    
    # 获取当前事件循环
    loop = asyncio.get_running_loop()
    
    try:
        yield fetcher
    finally:
        # 确保在测试结束时关闭所有资源
        await fetcher.close()
        
        # 清理所有未完成的任务
        tasks = [t for t in asyncio.all_tasks(loop) if t is not asyncio.current_task()]
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        # 关闭所有未关闭的客户端会话
        for task in tasks:
            for obj in task._coro.cr_frame.f_locals.values():
                if isinstance(obj, aiohttp.ClientSession):
                    if not obj.closed:
                        await obj.close()

@pytest.fixture
def twitter_api_config():
    """Twitter API 配置"""
    return {
        'api_key': 'test_api_key',
        'api_secret': 'test_api_secret',
        'access_token': 'test_access_token',
        'access_token_secret': 'test_access_token_secret',
        'bearer_token': 'test_bearer_token'
    }

@pytest.fixture
def mock_response():
    """模拟 API 响应"""
    return {
        'data': {
            'author_id': '2244994945',
            'created_at': 'Wed Jan 06 18:40:40 +0000 2021',
            'id': '1346889436626259968',
            'text': 'Test tweet content',
            'username': 'XDevelopers'
        },
        'includes': {
            'users': [
                {
                    'id': '2244994945',
                    'name': 'X Dev',
                    'username': 'TwitterDev',
                    'created_at': '2013-12-14T04:35:55Z',
                    'protected': False
                }
            ],
            'media': [
                {
                    'media_key': 'media_key_1',
                    'type': 'photo',
                    'url': 'https://example.com/image.jpg',
                    'height': 800,
                    'width': 600
                }
            ]
        }
    }

@pytest.mark.asyncio
async def test_fetch_single_tweet(twitter_fetcher, mock_response):
    """测试获取单条推文"""
    # 使用一个真实的推文URL进行测试
    test_url = 'https://twitter.com/testuser/status/1346889436626259968'
    
    try:
        # 执行测试
        results = await twitter_fetcher.fetch([test_url])
        
        # 验证结果
        assert len(results) == 1
        result = results[0]
        
        # 打印结果以便查看
        print("\n获取到的推文内容:")
        print(f"成功状态: {result['success']}")
        print(f"URL: {result['url']}")
        if result['success']:
            print(f"作者: {result['content']['author']}")
            print(f"时间: {result['content']['created_at']}")
            print(f"内容: {result['content']['text']}")
            if 'media' in result['content']:
                print(f"媒体数量: {len(result['content']['media'])}")
        else:
            print(f"错误信息: {result['error']}")
        
        # 验证基本字段
        assert result['url'] == test_url
        if result['success']:
            assert 'text' in result['content']
            assert 'author' in result['content']
            assert 'created_at' in result['content']
    except Exception as e:
        print(f"测试执行出错: {e}")
        raise

@pytest.mark.asyncio
async def test_fetch_multiple_tweets(twitter_api_config, mock_response):
    """测试获取多条推文"""
    # 准备测试数据
    test_urls = [
        'https://twitter.com/testuser/status/1346889436626259968',
        'https://twitter.com/testuser/status/1346889436626259969'
    ]
    
    # 模拟 aiohttp 会话
    mock_session = MagicMock()
    mock_session.get.return_value.__aenter__.return_value.status = 200
    mock_session.get.return_value.__aenter__.return_value.json.return_value = mock_response
    
    # 创建获取器实例
    fetcher = TwitterAPIFetcher(
        **twitter_api_config,
        max_content_length=100,
        proxy_url='http://127.0.0.1:10808'
    )
    
    # 替换会话创建方法
    with patch.object(fetcher, '_get_session', return_value=mock_session):
        # 获取内容
        results = await fetcher.fetch(test_urls)
        
        # 验证结果
        assert len(results) == 2
        assert all(r['success'] for r in results)
        assert all(r['source'] == 'twitter_api' for r in results)

@pytest.mark.asyncio
async def test_fetch_invalid_url(twitter_api_config):
    """测试无效URL"""
    # 准备测试数据
    test_url = 'https://twitter.com/testuser/invalid'
    
    # 创建获取器实例
    fetcher = TwitterAPIFetcher(
        **twitter_api_config,
        max_content_length=100,
        proxy_url='http://127.0.0.1:10808'
    )
    
    # 获取内容
    results = await fetcher.fetch([test_url])
    
    # 验证结果
    assert len(results) == 1
    assert results[0]['success'] is False
    assert results[0]['url'] == test_url
    assert results[0]['error'] == '无效的推文URL'

@pytest.mark.asyncio
async def test_fetch_api_error(twitter_api_config):
    """测试API错误"""
    # 准备测试数据
    test_url = 'https://twitter.com/testuser/status/1346889436626259968'
    
    # 模拟 aiohttp 会话
    mock_session = MagicMock()
    mock_session.get.return_value.__aenter__.return_value.status = 401
    mock_session.get.return_value.__aenter__.return_value.text.return_value = 'Unauthorized'
    
    # 创建获取器实例
    fetcher = TwitterAPIFetcher(
        **twitter_api_config,
        max_content_length=100,
        proxy_url='http://127.0.0.1:10808'
    )
    
    # 替换会话创建方法
    with patch.object(fetcher, '_get_session', return_value=mock_session):
        # 获取内容
        results = await fetcher.fetch([test_url])
        
        # 验证结果
        assert len(results) == 1
        assert results[0]['success'] is False
        assert results[0]['url'] == test_url
        assert results[0]['error'] == 'API请求失败: 401'

@pytest.mark.asyncio
async def test_fetch_empty_urls(twitter_api_config):
    """测试空URL列表"""
    # 创建获取器实例
    fetcher = TwitterAPIFetcher(
        **twitter_api_config,
        max_content_length=100,
        proxy_url='http://127.0.0.1:10808'
    )
    
    # 获取内容
    results = await fetcher.fetch([])
    
    # 验证结果
    assert len(results) == 0

@pytest.mark.asyncio
async def test_fetch_with_proxy(twitter_api_config, mock_response):
    """测试使用代理"""
    # 准备测试数据
    test_url = 'https://twitter.com/testuser/status/1346889436626259968'
    # proxy_url = 'http://user:pass@127.0.0.1:10808'
    proxy_url = 'http://127.0.0.1:10808'
    
    # 模拟 aiohttp 会话
    mock_session = MagicMock()
    mock_session.get.return_value.__aenter__.return_value.status = 200
    mock_session.get.return_value.__aenter__.return_value.json.return_value = mock_response
    
    # 创建获取器实例
    fetcher = TwitterAPIFetcher(
        **twitter_api_config,
        max_content_length=100,
        proxy_url=proxy_url
    )
    
    # 替换会话创建方法
    with patch.object(fetcher, '_get_session', return_value=mock_session):
        # 获取内容
        results = await fetcher.fetch([test_url])
        
        # 验证结果
        assert len(results) == 1
        assert results[0]['success'] is True
        assert results[0]['url'] == test_url
        assert results[0]['content'] == 'Test tweet content'

if __name__ == '__main__':
    pytest.main()
