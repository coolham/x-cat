"""
缓存管理器测试
"""
import os
import json
import pytest
from datetime import datetime
from app.cache.cache_manager import CacheManager

@pytest.fixture
def cache_manager(tmp_path):
    """创建临时缓存管理器"""
    cache_dir = str(tmp_path / "test_cache")
    return CacheManager(cache_dir)

@pytest.fixture
def sample_data():
    """创建测试数据"""
    return {
        "url": "https://example.com",
        "content": "测试内容",
        "title": "测试标题",
        "type": "html"
    }

def test_init(cache_manager):
    """测试初始化"""
    assert os.path.exists(cache_manager.cache_dir)
    assert os.path.isdir(cache_manager.cache_dir)

def test_save_and_load(cache_manager, sample_data):
    """测试保存和加载数据"""
    # 保存数据
    assert cache_manager.save(sample_data["url"], sample_data)
    
    # 加载数据
    loaded_data = cache_manager.load(sample_data["url"])
    assert loaded_data is not None
    assert loaded_data["url"] == sample_data["url"]
    assert loaded_data["content"] == sample_data["content"]
    assert loaded_data["title"] == sample_data["title"]
    assert loaded_data["type"] == sample_data["type"]
    assert "cached_at" in loaded_data

def test_save_with_special_characters(cache_manager):
    """测试保存包含特殊字符的URL"""
    url = "https://example.com/path?param=测试&id=123"
    data = {"url": url, "content": "测试内容"}
    
    assert cache_manager.save(url, data)
    loaded_data = cache_manager.load(url)
    assert loaded_data is not None
    assert loaded_data["url"] == url

def test_load_nonexistent(cache_manager):
    """测试加载不存在的缓存"""
    result = cache_manager.load("https://nonexistent.com")
    assert result is None

def test_exists(cache_manager, sample_data):
    """测试检查缓存是否存在"""
    # 初始状态
    assert not cache_manager.exists(sample_data["url"])
    
    # 保存后
    cache_manager.save(sample_data["url"], sample_data)
    assert cache_manager.exists(sample_data["url"])

def test_clear_single(cache_manager, sample_data):
    """测试清除单个缓存"""
    # 保存数据
    cache_manager.save(sample_data["url"], sample_data)
    assert cache_manager.exists(sample_data["url"])
    
    # 清除缓存
    assert cache_manager.clear(sample_data["url"])
    assert not cache_manager.exists(sample_data["url"])

def test_clear_all(cache_manager, sample_data):
    """测试清除所有缓存"""
    # 保存多个数据
    urls = [
        "https://example1.com",
        "https://example2.com",
        "https://example3.com"
    ]
    for url in urls:
        data = sample_data.copy()
        data["url"] = url
        cache_manager.save(url, data)
        assert cache_manager.exists(url)
    
    # 清除所有缓存
    assert cache_manager.clear()
    
    # 验证所有缓存都已清除
    for url in urls:
        assert not cache_manager.exists(url)

def test_save_error_handling(cache_manager):
    """测试保存时的错误处理"""
    # 使用无效的URL（空字符串）
    result = cache_manager.save("", {"content": "test"})
    assert not result

def test_load_error_handling(cache_manager):
    """测试加载时的错误处理"""
    # 创建损坏的缓存文件
    cache_path = cache_manager._get_cache_path("https://example.com")
    with open(cache_path, 'w', encoding='utf-8') as f:
        f.write("invalid json")
    
    # 尝试加载损坏的缓存
    result = cache_manager.load("https://example.com")
    assert result is None

def test_clear_error_handling(cache_manager):
    """测试清除时的错误处理"""
    # 使用不存在的URL
    assert cache_manager.clear("https://nonexistent.com")

def test_cache_file_format(cache_manager, sample_data):
    """测试缓存文件格式"""
    # 保存数据
    cache_manager.save(sample_data["url"], sample_data)
    
    # 读取文件内容
    cache_path = cache_manager._get_cache_path(sample_data["url"])
    with open(cache_path, 'r', encoding='utf-8') as f:
        file_content = f.read()
    
    # 验证JSON格式
    data = json.loads(file_content)
    assert data["url"] == sample_data["url"]
    assert data["content"] == sample_data["content"]
    assert "cached_at" in data
    assert isinstance(datetime.fromisoformat(data["cached_at"]), datetime) 