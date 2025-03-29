# -*- coding: utf-8 -*-
"""
分发器模块集成测试
测试分发器与其他模块的交互
"""
import asyncio
import json
import pytest
from datetime import datetime
from pathlib import Path
from typing import Dict

from app.distributors.base import Distributor
from app.distributors.local import LocalDistributor
from app.distributors.notion import NotionDistributor
from app.category_system.models.category_manager import CategoryManager
from app.category_system.storage.category_storage import CategoryStorage

class TestDistributorIntegration:
    """分发器集成测试"""
    
    @pytest.fixture
    async def category_manager(self):
        """创建分类管理器"""
        manager = CategoryManager()
        return manager
    
    @pytest.fixture
    async def category_storage(self):
        """创建分类存储"""
        storage = CategoryStorage()
        return storage
    
    @pytest.fixture
    async def local_distributor(self):
        """创建本地分发器"""
        distributor = LocalDistributor()
        return distributor
    
    @pytest.fixture
    async def notion_distributor(self):
        """创建Notion分发器"""
        distributor = NotionDistributor()
        return distributor
    
    @pytest.fixture
    def test_content(self):
        """创建测试内容"""
        return {
            'id': 'test_001',
            'text': '测试内容',
            'source': 'test',
            'metadata': {
                'date': datetime.now().isoformat()
            },
            'classification': {
                'primary_category': '测试分类',
                'secondary_category': '测试子分类',
                'confidence': 0.9,
                'reasoning': '测试分类理由'
            }
        }
    
    @pytest.mark.asyncio
    async def test_local_distribution(self, local_distributor, test_content):
        """测试本地分发"""
        # 分发内容
        success = await local_distributor.distribute_with_retry(test_content)
        assert success
        
        # 检查统计信息
        stats = local_distributor.get_stats()
        assert stats['success_count'] == 1
        assert stats['total_count'] == 1
        
        # 检查健康状态
        health = local_distributor.check_health()
        assert health['status'] == 'healthy'
        
        # 检查告警信息
        alerts = local_distributor.get_alerts()
        assert len(alerts) == 0
    
    @pytest.mark.asyncio
    async def test_notion_distribution(self, notion_distributor, test_content):
        """测试Notion分发"""
        # 分发内容
        success = await notion_distributor.distribute_with_retry(test_content)
        assert success
        
        # 检查统计信息
        stats = notion_distributor.get_stats()
        assert stats['success_count'] == 1
        assert stats['total_count'] == 1
        
        # 检查健康状态
        health = notion_distributor.check_health()
        assert health['status'] == 'healthy'
        
        # 检查告警信息
        alerts = notion_distributor.get_alerts()
        assert len(alerts) == 0
    
    @pytest.mark.asyncio
    async def test_distribution_with_category(self, local_distributor, category_manager, test_content):
        """测试带分类的分发"""
        # 获取分类信息
        primary_categories = category_manager.get_primary_categories()
        assert len(primary_categories) > 0
        
        # 分发内容
        success = await local_distributor.distribute_with_retry(test_content)
        assert success
        
        # 检查分类信息
        formatted_content = local_distributor._format_content(test_content)
        assert formatted_content['classification']['primary'] == test_content['classification']['primary_category']
        assert formatted_content['classification']['secondary'] == test_content['classification']['secondary_category']
    
    @pytest.mark.asyncio
    async def test_distribution_with_storage(self, local_distributor, category_storage, test_content):
        """测试带存储的分发"""
        # 分发内容
        success = await local_distributor.distribute_with_retry(test_content)
        assert success
        
        # 检查存储结果
        stored_result = category_storage.get_classification(test_content['id'])
        assert stored_result is not None
        assert stored_result['primary_category'] == test_content['classification']['primary_category']
        assert stored_result['secondary_category'] == test_content['classification']['secondary_category']
    
    @pytest.mark.asyncio
    async def test_distribution_error_handling(self, local_distributor, test_content):
        """测试分发错误处理"""
        # 模拟网络错误
        local_distributor.config.set_retry_config('localdistributor', {
            'max_attempts': 3,
            'delay': 0.1,
            'backoff_factor': 1.0
        })
        
        # 设置失败率
        local_distributor.success_rate = 0
        
        # 分发内容
        success = await local_distributor.distribute_with_retry(test_content)
        assert not success
        
        # 检查统计信息
        stats = local_distributor.get_stats()
        assert stats['failure_count'] == 1
        assert stats['total_count'] == 1
        
        # 检查健康状态
        health = local_distributor.check_health()
        assert health['status'] == 'warning'
        
        # 检查告警信息
        alerts = local_distributor.get_alerts()
        assert len(alerts) > 0
    
    @pytest.mark.asyncio
    async def test_cleanup_integration(self, local_distributor, test_data_dir):
        """测试数据清理集成"""
        # 创建测试数据
        stats_file = test_data_dir / 'stats' / 'local_stats.json'
        health_file = test_data_dir / 'health' / 'distributor_health.json'
        alert_file = test_data_dir / 'alerts' / 'local_alerts.json'
        
        # 创建过期数据
        old_date = (datetime.now() - timedelta(days=31)).isoformat()
        
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump({'last_updated': old_date}, f)
        
        with open(health_file, 'w', encoding='utf-8') as f:
            json.dump({
                'localdistributor': {
                    'status': 'healthy',
                    'timestamp': old_date
                }
            }, f)
        
        with open(alert_file, 'w', encoding='utf-8') as f:
            json.dump([
                {'timestamp': old_date, 'message': '旧告警'},
                {'timestamp': datetime.now().isoformat(), 'message': '新告警'}
            ], f)
        
        # 执行清理
        success = local_distributor.cleanup.cleanup_all()
        assert success
        
        # 验证清理结果
        assert not stats_file.exists()
        
        with open(health_file, 'r', encoding='utf-8') as f:
            health_data = json.load(f)
        assert 'localdistributor' not in health_data
        
        with open(alert_file, 'r', encoding='utf-8') as f:
            alerts = json.load(f)
        assert len(alerts) == 1
        assert alerts[0]['message'] == '新告警' 