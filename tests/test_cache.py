"""
缓存模块测试用例
"""
import os
import json
import pytest
from datetime import datetime
from typing import Dict, Any

from app.cache.models import CacheEntry
from app.cache.db import DatabaseManager
from app.cache.cache_manager import CacheManager


@pytest.fixture
def test_data() -> Dict[str, Any]:
    """测试数据"""
    return {
        'title': '测试标题',
        'content': '测试内容',
        'tags': ['测试', '标签']
    }


@pytest.fixture
def test_url() -> str:
    """测试URL"""
    return 'https://example.com/test'


@pytest.fixture
def db_path(tmp_path) -> str:
    """测试数据库路径"""
    return str(tmp_path / 'test_cache.db')


@pytest.fixture
def db_manager(db_path) -> DatabaseManager:
    """数据库管理器"""
    return DatabaseManager(db_path)


@pytest.fixture
def cache_manager(db_path) -> CacheManager:
    """缓存管理器"""
    return CacheManager(os.path.dirname(db_path))


class TestCacheEntry:
    """测试缓存条目"""
    
    def test_init(self, test_url, test_data):
        """测试初始化"""
        entry = CacheEntry(test_url, test_data)
        assert entry.url == test_url
        assert entry.data == test_data
        assert isinstance(entry.created_at, datetime)
        assert isinstance(entry.updated_at, datetime)
    
    def test_to_dict(self, test_url, test_data):
        """测试转换为字典"""
        entry = CacheEntry(test_url, test_data)
        data = entry.to_dict()
        assert data['url'] == test_url
        assert data['data'] == test_data
        assert isinstance(data['created_at'], str)
        assert isinstance(data['updated_at'], str)
    
    def test_from_dict(self, test_url, test_data):
        """测试从字典创建"""
        data = {
            'url': test_url,
            'data': test_data,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        entry = CacheEntry.from_dict(data)
        assert entry.url == test_url
        assert entry.data == test_data
        assert isinstance(entry.created_at, datetime)
        assert isinstance(entry.updated_at, datetime)
    
    def test_to_sql(self, test_url, test_data):
        """测试转换为SQL格式"""
        entry = CacheEntry(test_url, test_data)
        data = entry.to_sql()
        assert data['url'] == test_url
        assert isinstance(data['data'], str)
        assert isinstance(data['created_at'], str)
        assert isinstance(data['updated_at'], str)
    
    def test_from_sql(self, test_url, test_data):
        """测试从SQL数据创建"""
        data = {
            'url': test_url,
            'data': json.dumps(test_data, ensure_ascii=False),
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        entry = CacheEntry.from_sql(data)
        assert entry.url == test_url
        assert entry.data == test_data
        assert isinstance(entry.created_at, datetime)
        assert isinstance(entry.updated_at, datetime)


class TestDatabaseManager:
    """测试数据库管理器"""
    
    def test_init(self, db_path):
        """测试初始化"""
        db = DatabaseManager(db_path)
        assert os.path.exists(db_path)
    
    def test_save_and_load(self, db_manager, test_url, test_data):
        """测试保存和加载"""
        # 创建缓存条目
        entry = CacheEntry(test_url, test_data)
        
        # 保存
        assert db_manager.save(entry)
        
        # 加载
        loaded = db_manager.load(test_url)
        assert loaded is not None
        assert loaded.url == test_url
        assert loaded.data == test_data
    
    def test_exists(self, db_manager, test_url, test_data):
        """测试检查存在"""
        # 初始不存在
        assert not db_manager.exists(test_url)
        
        # 保存后存在
        entry = CacheEntry(test_url, test_data)
        db_manager.save(entry)
        assert db_manager.exists(test_url)
    
    def test_clear(self, db_manager, test_url, test_data):
        """测试清除"""
        # 保存数据
        entry = CacheEntry(test_url, test_data)
        db_manager.save(entry)
        
        # 清除单个
        assert db_manager.clear(test_url)
        assert not db_manager.exists(test_url)
        
        # 保存多个
        entry1 = CacheEntry('url1', {'data': 1})
        entry2 = CacheEntry('url2', {'data': 2})
        db_manager.save(entry1)
        db_manager.save(entry2)
        
        # 清除所有
        assert db_manager.clear()
        assert not db_manager.exists('url1')
        assert not db_manager.exists('url2')
    
    def test_get_all(self, db_manager, test_data):
        """测试获取所有"""
        # 保存多个数据
        urls = ['url1', 'url2', 'url3']
        for url in urls:
            entry = CacheEntry(url, test_data)
            db_manager.save(entry)
        
        # 获取所有
        entries = db_manager.get_all()
        assert len(entries) == len(urls)
        assert all(entry.url in urls for entry in entries)


class TestCacheManager:
    """测试缓存管理器"""
    
    def test_save_and_load(self, cache_manager, test_url, test_data):
        """测试保存和加载"""
        # 保存
        assert cache_manager.save(test_url, test_data)
        
        # 加载
        loaded = cache_manager.load(test_url)
        assert loaded is not None
        assert loaded['title'] == test_data['title']
        assert loaded['content'] == test_data['content']
        assert loaded['tags'] == test_data['tags']
        assert 'cached_at' in loaded
    
    def test_exists(self, cache_manager, test_url, test_data):
        """测试检查存在"""
        # 初始不存在
        assert not cache_manager.exists(test_url)
        
        # 保存后存在
        cache_manager.save(test_url, test_data)
        assert cache_manager.exists(test_url)
    
    def test_clear(self, cache_manager, test_url, test_data):
        """测试清除"""
        # 保存数据
        cache_manager.save(test_url, test_data)
        
        # 清除单个
        assert cache_manager.clear(test_url)
        assert not cache_manager.exists(test_url)
        
        # 保存多个
        urls = ['url1', 'url2']
        for url in urls:
            cache_manager.save(url, test_data)
        
        # 清除所有
        assert cache_manager.clear()
        assert not cache_manager.exists('url1')
        assert not cache_manager.exists('url2')
    
    def test_get_all(self, cache_manager, test_data):
        """测试获取所有"""
        # 保存多个数据
        urls = ['url1', 'url2', 'url3']
        for url in urls:
            cache_manager.save(url, test_data)
        
        # 获取所有
        entries = cache_manager.get_all()
        assert len(entries) == len(urls)
        assert all(entry['title'] == test_data['title'] for entry in entries)
        assert all(entry['content'] == test_data['content'] for entry in entries)
        assert all(entry['tags'] == test_data['tags'] for entry in entries)
        assert all('cached_at' in entry for entry in entries) 