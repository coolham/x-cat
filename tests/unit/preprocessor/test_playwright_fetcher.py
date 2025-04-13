"""
Playwright 内容获取器测试
"""
import os
import sys
import pytest
import pytest_asyncio
import argparse
import asyncio
# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))
from app.preprocessor.playwright_fetcher import PlaywrightFetcher

@pytest.fixture
async def fetcher():
    """创建 Playwright 内容获取器实例"""
    fetcher = PlaywrightFetcher(max_content_length=1000, timeout=30)
    try:
        yield fetcher
    finally:
        fetcher.close()
    

@pytest.mark.asyncio
async def test_fetch_bing(fetcher):
    """测试获取 Bing 内容（不使用代理）"""
    url = "https://www.bing.com"

    # 执行测试
    results = await fetcher.fetch([url])

    # 验证结果
    assert len(results) == 1, "结果数量不正确"
    assert results[0]['success'] is True, f"Error: {results[0]['error']}"
    # assert '必应' in results[0]['content'], "内容中未找到 'Bing'"
    assert results[0]['type'] == 'html', "返回类型不正确"
    
    # 测试完成后不关闭浏览器
    await asyncio.sleep(2)  # 等待一段时间，让用户查看浏览器状态

@pytest.mark.asyncio
async def test_fetch_with_proxy(fetcher):
    """测试使用代理获取内容（访问需要代理的网站）"""
    url = "https://github.com/facebook/react/blob/main/README.md"
    proxy_url = "http://127.0.0.1:10808"  # 使用本地代理
    
    # 设置代理
    fetcher.proxy_url = proxy_url
    
    # 执行测试
    results = await fetcher.fetch([url])
    
    # 验证结果
    assert len(results) == 1
    if results[0]['success'] is False:
        # 如果代理连接失败，检查错误信息
        assert "net::ERR_PROXY_CONNECTION_FAILED" in results[0]['error'] or "获取失败" in results[0]['error']
    else:
        assert 'React' in results[0]['content']

@pytest.mark.asyncio
async def test_fetch_with_timeout(fetcher):
    """测试超时处理"""
    url = "https://www.bing.com"
    fetcher.timeout = 1  # 设置很短的超时时间
    
    # 执行测试
    results = await fetcher.fetch([url])
    
    # 验证结果
    assert len(results) == 1
    assert results[0]['success'] is False
    assert "请求超时" in results[0]['error'], f"Error: {results[0]['error']}"

@pytest.mark.asyncio
async def test_fetch_empty_urls(fetcher):
    """测试空URL列表"""
    results = await fetcher.fetch([])
    assert results == []

@pytest.mark.asyncio
async def test_fetch_multiple_urls(fetcher):
    """测试获取多个URL（混合使用代理和非代理）"""
    # 不使用代理的URL
    direct_urls = [
        "https://www.bing.com",
        "https://www.baidu.com"
    ]
    
    # 使用代理的URL
    proxy_urls = [
        "https://github.com/facebook/react/blob/main/README.md",
        "https://twitter.com/testuser/status/1346889436626259968",
    ]
    
    # 设置代理
    fetcher.proxy_url = "http://127.0.0.1:10808"
    
    # 执行测试
    results = await fetcher.fetch(direct_urls + proxy_urls)
    
    # 验证结果
    assert len(results) == 4
    # 检查直接访问的URL
    assert any(r['success'] and ('Bing' in r['content'] or '百度' in r['content']) for r in results[:2]), f"Results: {results[:2]}"
    # 检查代理访问的URL
    assert any(r['success'] and ('React' in r['content'] or 'Vue' in r['content']) for r in results[2:]), f"Results: {results[2:]}"

@pytest.mark.asyncio
async def test_fetch_with_long_content(fetcher):
    """测试长内容截断"""
    url = "https://www.bing.com"
    fetcher.max_content_length = 100  # 设置较小的内容长度限制

    # 执行测试
    results = await fetcher.fetch([url])

    # 验证结果
    assert len(results) == 1
    assert results[0]['success'] is True, f"Error: {results[0]['error']}"
    assert len(results[0]['content']) <= 100  # 检查是否被截断

@pytest.mark.asyncio
async def test_close(fetcher):
    """测试关闭资源"""
    await fetcher.close()
    assert fetcher._playwright is None
    assert fetcher._browser is None

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='运行 Playwright 内容获取器测试')
    parser.add_argument('-t', '--test', help='指定要运行的测试用例名称')
    parser.add_argument('-v', '--verbose', action='store_true', help='显示详细输出')
    return parser.parse_args()

if __name__ == "__main__":
    # 指定要运行的测试用例名称
    test_name = "test_fetch_with_proxy"  # 这里可以修改为其他测试用例名称
    
    # 构建 pytest 命令行参数
    pytest_args = [
        "-v",  # 显示详细输出
        "-k", test_name,  # 指定测试用例名称
        __file__  # 当前文件路径
    ]
    
    # 执行测试
    pytest.main(pytest_args)
    # pytest.main()
