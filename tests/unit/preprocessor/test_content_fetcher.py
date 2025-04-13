# -*- coding: utf-8 -*-
"""
内容获取器测试
"""
import pytest
import pytest_asyncio
from unittest.mock import patch, MagicMock, AsyncMock
import os
import sys
import asyncio
import argparse
import json
from loguru import logger
from pathlib import Path
from dotenv import load_dotenv
# 加载环境变量
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

from pathlib import Path
# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))
from app.preprocessor.content_fetcher import ContentFetcher
from playwright.async_api import async_playwright
from app.core.config_loader import load_config

def load_test_config():
    """加载测试配置"""
    # 尝试从项目根目录加载配置
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 
                              "config", "config.yaml")
    
    if os.path.exists(config_path):
        config = load_config(config_path)
        config['twitter_api'] = {
            'twitter_api_key': os.environ.get("TWITTER_API_KEY", ""),
            'twitter_api_secret_key': os.environ.get("TWITTER_API_SECRET_KEY", ""),
            'twitter_access_token': os.environ.get("TWITTER_ACCESS_TOKEN", ""),
            'twitter_access_token_secret': os.environ.get("TWITTER_ACCESS_TOKEN_SECRET", ""),
            'twitter_bearer_token': os.environ.get("TWITTER_BEARER_TOKEN", "")
        }
        return config
    
    # 如果配置文件不存在，使用默认配置
    return {
        "preprocessor": {
            "content_fetcher": {
                "timeout": 10,
                "max_content_length": 1000,
                "proxy_url": os.environ.get("HTTP_PROXY", ""),
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
        }
    }

@pytest.fixture
async def fetcher():
    """创建内容获取器实例"""
    # 加载配置
    config = load_test_config()
    
    # 从配置中获取内容获取器的配置
    fetcher_config = config.get("preprocessor", {}).get("content_fetcher", {})
    
    # 创建内容获取器实例
    fetcher = ContentFetcher(
        proxy_url=fetcher_config.get("proxy_url", ""),
        timeout=fetcher_config.get("timeout", 10),
        max_content_length=fetcher_config.get("max_content_length", 1000),
        user_agent=fetcher_config.get("user_agent", ""),
        max_retries=2
    )
    
    yield fetcher
    # 确保在测试结束后关闭资源
    await fetcher.close()

@pytest.fixture
async def playwright():
    """创建 Playwright 实例"""
    async with async_playwright() as p:
        yield p

@pytest.mark.asyncio
async def test_is_media_url(fetcher):
    """测试媒体文件URL检测"""
    # 测试图片URL
    assert fetcher._is_media_url("https://www.baidu.com/img/logo.png") is True
    assert fetcher._is_media_url("https://www.qq.com/image.jpeg") is True
    assert fetcher._is_media_url("https://www.163.com/image.png") is True
    
    # 测试视频URL
    assert fetcher._is_media_url("https://www.bilibili.com/video/BV123456789.mp4") is True
    assert fetcher._is_media_url("https://www.youku.com/video.webm") is True
    
    # 测试音频URL
    assert fetcher._is_media_url("https://music.163.com/song.mp3") is True
    assert fetcher._is_media_url("https://www.ximalaya.com/audio.wav") is True
    
    # 测试文档URL
    assert fetcher._is_media_url("https://www.zhihu.com/document.pdf") is True
    assert fetcher._is_media_url("https://www.douban.com/document.docx") is True
    
    # 测试非媒体URL
    assert fetcher._is_media_url("https://www.baidu.com") is False
    assert fetcher._is_media_url("https://www.qq.com/api") is False
    assert fetcher._is_media_url("https://www.163.com/") is False

@pytest.mark.asyncio
async def test_is_twitter_url(fetcher):
    """测试Twitter URL检测"""
    # 测试Twitter URL
    assert fetcher._is_twitter_url("https://twitter.com/username/status/123456789") is True
    assert fetcher._is_twitter_url("https://www.twitter.com/username/status/123456789") is True
    
    # 测试X URL
    assert fetcher._is_twitter_url("https://x.com/username/status/123456789") is True
    assert fetcher._is_twitter_url("https://www.x.com/username/status/123456789") is True
    
    # 测试非Twitter URL
    assert fetcher._is_twitter_url("https://twitter.com/username") is False
    assert fetcher._is_twitter_url("https://www.baidu.com/status/123456789") is False
    assert fetcher._is_twitter_url("https://www.qq.com") is False

@pytest.mark.asyncio
async def test_extract_tweet_id(fetcher):
    """测试从URL中提取推文ID"""
    # 测试Twitter URL
    assert fetcher._extract_tweet_id_from_url("https://twitter.com/username/status/123456789") == "123456789"
    assert fetcher._extract_tweet_id_from_url("https://www.twitter.com/username/status/123456789") == "123456789"
    
    # 测试X URL
    assert fetcher._extract_tweet_id_from_url("https://x.com/username/status/123456789") == "123456789"
    assert fetcher._extract_tweet_id_from_url("https://www.x.com/username/status/123456789") == "123456789"
    
    # 测试非Twitter URL
    assert fetcher._extract_tweet_id_from_url("https://twitter.com/username") is None
    assert fetcher._extract_tweet_id_from_url("https://www.baidu.com/status/123456789") is None
    assert fetcher._extract_tweet_id_from_url("https://www.qq.com") is None

@pytest.mark.asyncio
async def test_fetch_media_url(fetcher):
    """测试获取媒体文件URL"""
    media_url = "https://www.baidu.com/img/logo.png"
    
    # 执行测试
    results = await fetcher.fetch([media_url])
    
    # 验证结果
    assert len(results) == 1
    assert results[0]['success'] is True
    assert results[0]['url'] == media_url
    assert results[0]['content'] == media_url
    assert results[0]['type'] == 'media'
    assert results[0]['metadata']['is_media'] is True

@pytest.mark.asyncio
async def test_fetch_regular_url(fetcher):
    """测试获取常规URL内容"""
    # 使用一个稳定的网站进行测试
    url = "https://www.baidu.com"
    
    # 执行测试
    results = await fetcher.fetch([url])
    
    # 验证结果
    assert len(results) == 1
    assert results[0]['success'] is True
    assert results[0]['url'] == url
    assert len(results[0]['content']) > 0
    assert "百度" in results[0]['content']

@pytest.mark.asyncio
async def test_fetch_multiple_urls(fetcher):
    """测试获取多个URL内容"""
    # 使用稳定的网站进行测试
    urls = [
        "https://www.baidu.com",
        "https://www.qq.com"
    ]
    
    # 执行测试
    results = await fetcher.fetch(urls)
    
    # 验证结果
    assert len(results) == 2
    assert all(r['success'] for r in results)
    assert all(len(r['content']) > 0 for r in results)

@pytest.mark.asyncio
async def test_fetch_with_proxy(fetcher):
    """测试使用代理获取内容"""
    # 注意：这个测试需要有效的代理服务器
    # 如果没有代理，可以跳过这个测试
    proxy_url = os.environ.get("HTTP_PROXY")
    if not proxy_url:
        pytest.skip("没有设置代理服务器，跳过测试")
    
    fetcher.proxy_url = proxy_url
    url = "https://www.baidu.com"
    
    # 执行测试
    results = await fetcher.fetch([url])
    
    # 验证结果
    assert len(results) == 1
    assert results[0]['success'] is True
    assert results[0]['url'] == url
    assert len(results[0]['content']) > 0

@pytest.mark.asyncio
async def test_fetch_with_timeout(fetcher):
    """测试超时处理"""
    # 使用一个设置非常短的超时时间
    fetcher.timeout = 1
    
    # 使用一个响应较慢的网站
    url = "https://httpstat.us/200?sleep=3000"
    
    # 执行测试
    results = await fetcher.fetch([url])
    
    # 验证结果
    assert len(results) == 1
    assert results[0]['success'] is False
    assert "timeout" in results[0]['error'].lower() or "超时" in results[0]['error']

@pytest.mark.asyncio
async def test_fetch_error_status(fetcher):
    """测试错误状态码"""
    # 使用一个返回404的URL
    url = "https://httpstat.us/404"
    
    # 执行测试
    results = await fetcher.fetch([url])
    
    # 验证结果
    assert len(results) == 1
    assert results[0]['success'] is False
    assert "404" in results[0]['error']

@pytest.mark.asyncio
async def test_fetch_long_content(fetcher):
    """测试长内容截断"""
    # 使用一个内容较长的网站
    url = "https://www.zhihu.com"
    
    # 设置较小的最大内容长度
    fetcher.max_content_length = 100
    
    # 执行测试
    results = await fetcher.fetch([url])
    
    # 验证结果
    assert len(results) == 1
    assert results[0]['success'] is True
    assert len(results[0]['content']) <= 100  # 检查是否被截断

@pytest.mark.asyncio
async def test_close(fetcher):
    """测试关闭资源"""
    await fetcher.close()
    assert fetcher._aiohttp_fetcher._session is None
    assert fetcher._playwright_fetcher._browser is None
    assert fetcher._playwright_fetcher._playwright is None


# 测试用例映射表
TEST_CASES = {
    "media_url": test_is_media_url,
    "twitter_url": test_is_twitter_url,
    "tweet_id": test_extract_tweet_id,
    "fetch_media": test_fetch_media_url,
    "fetch_regular": test_fetch_regular_url,
    "fetch_multiple": test_fetch_multiple_urls,
    "fetch_proxy": test_fetch_with_proxy,
    "fetch_timeout": test_fetch_with_timeout,
    "fetch_error": test_fetch_error_status,
    "fetch_long": test_fetch_long_content,
    "close": test_close,
    "all": None  # 特殊标记，表示运行所有测试
}

async def run_single_test(test_func):
    """运行单个测试函数"""
    print(f"\n运行测试: {test_func.__name__}")
    print("=" * 50)
    try:
        # 加载配置
        config = load_test_config()
        
        # 从配置中获取内容获取器的配置
        fetcher_config = config.get("preprocessor", {}).get("content_fetcher", {})
        
        # 创建测试实例
        fetcher = ContentFetcher(
            proxy_url=fetcher_config.get("proxy_url", ""),
            timeout=fetcher_config.get("timeout", 10),
            max_content_length=fetcher_config.get("max_content_length", 1000),
            user_agent=fetcher_config.get("user_agent", ""),
            max_retries=2
        )
        
        try:
            # 运行测试
            await test_func(fetcher)
            print(f"✅ 测试通过: {test_func.__name__}")
        except Exception as e:
            print(f"❌ 测试失败: {test_func.__name__}")
            print(f"错误信息: {str(e)}")
        finally:
            # 确保资源被关闭
            await fetcher.close()
    except Exception as e:
        print(f"❌ 测试设置失败: {test_func.__name__}")
        print(f"错误信息: {str(e)}")
    print("=" * 50)

async def run_tests(test_names):
    """运行指定的测试用例"""
    if "all" in test_names:
        # 运行所有测试
        for name, test_func in TEST_CASES.items():
            if name != "all" and test_func:
                await run_single_test(test_func)
    else:
        # 运行指定的测试
        for name in test_names:
            if name in TEST_CASES and TEST_CASES[name]:
                await run_single_test(TEST_CASES[name])
            else:
                print(f"❌ 未知的测试用例: {name}")

def main():
    """主函数，解析命令行参数并运行测试"""
    parser = argparse.ArgumentParser(description="内容获取器测试")
    parser.add_argument("tests", nargs="*", default=["all"], 
                        help="要运行的测试用例名称，不指定则运行所有测试")
    parser.add_argument("--list", action="store_true", 
                        help="列出所有可用的测试用例")
    
    args = parser.parse_args()
    
    if args.list:
        print("可用的测试用例:")
        for name in TEST_CASES.keys():
            print(f"  - {name}")
        return
    
    # 运行测试
    asyncio.run(run_tests(args.tests))

if __name__ == "__main__":
    main()

