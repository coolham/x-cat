# -*- coding: utf-8 -*-
"""
分发器模块单元测试
"""
import asyncio
import json
import os
import pytest
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict

from app.distributors.base import Distributor
from app.distributors.stats import DistributorStats
from app.distributors.health import DistributorHealth
from app.distributors.alert import DistributorAlert
from app.distributors.cleanup import DistributorCleanup

class MockDistributor(Distributor):
    """模拟分发器，用于测试"""
    
    def __init__(self, success_rate: float = 1.0):
        """初始化模拟分发器
        
        Args:
            success_rate: 分发成功率
        """
        super().__init__()
        self.success_rate = success_rate
        self.distribute_count = 0
    
    async def distribute(self, content: Dict) -> bool:
        """模拟分发内容
        
        Args:
            content: 内容信息
            
        Returns:
            bool: 是否分发成功
        """
        self.distribute_count += 1
        return self.distribute_count % (1 / self.success_rate) != 0

@pytest.fixture
def mock_distributor():
    """创建模拟分发器"""
    return MockDistributor()

@pytest.fixture
def test_content():
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

@pytest.fixture
def test_data_dir(tmp_path):
    """创建测试数据目录"""
    data_dir = tmp_path / 'data'
    (data_dir / 'stats').mkdir(parents=True)
    (data_dir / 'health').mkdir(parents=True)
    (data_dir / 'alerts').mkdir(parents=True)
    return data_dir

@pytest.mark.asyncio
async def test_distribute_success(mock_distributor, test_content):
    """测试成功分发"""
    success = await mock_distributor.distribute_with_retry(test_content)
    assert success
    assert mock_distributor.distribute_count == 1

@pytest.mark.asyncio
async def test_distribute_retry(mock_distributor, test_content):
    """测试分发重试"""
    # 设置50%的成功率
    mock_distributor.success_rate = 0.5
    
    success = await mock_distributor.distribute_with_retry(test_content)
    assert success
    assert mock_distributor.distribute_count > 1

@pytest.mark.asyncio
async def test_distribute_failure(mock_distributor, test_content):
    """测试分发失败"""
    # 设置0%的成功率
    mock_distributor.success_rate = 0
    
    success = await mock_distributor.distribute_with_retry(test_content)
    assert not success
    assert mock_distributor.distribute_count == 3  # 默认最大重试次数

def test_format_content(mock_distributor, test_content):
    """测试内容格式化"""
    formatted = mock_distributor._format_content(test_content)
    
    assert formatted['id'] == test_content['id']
    assert formatted['text'] == test_content['text']
    assert formatted['source'] == test_content['source']
    assert formatted['classification']['primary'] == test_content['classification']['primary_category']
    assert formatted['classification']['secondary'] == test_content['classification']['secondary_category']
    assert formatted['classification']['confidence'] == test_content['classification']['confidence']
    assert formatted['classification']['reasoning'] == test_content['classification']['reasoning']

def test_stats_recording(mock_distributor, test_content):
    """测试统计记录"""
    # 模拟成功分发
    mock_distributor.stats.record_distribution(
        mock_distributor.name,
        success=True,
        retry=False,
        response_time=100
    )
    
    stats = mock_distributor.get_stats()
    assert stats['success_count'] == 1
    assert stats['total_count'] == 1
    assert stats['success_rate'] == 1.0
    assert stats['avg_response_time'] == 100

def test_health_check(mock_distributor):
    """测试健康检查"""
    health_status = mock_distributor.check_health()
    
    assert 'status' in health_status
    assert 'success_rate' in health_status
    assert 'avg_response_time' in health_status
    assert 'last_check' in health_status

def test_cleanup_stats(test_data_dir):
    """测试统计数据清理"""
    cleanup = DistributorCleanup()
    cleanup.data_dir = test_data_dir
    
    # 创建测试统计文件
    stats_file = test_data_dir / 'stats' / 'test_stats.json'
    old_date = (datetime.now() - timedelta(days=31)).isoformat()
    
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump({'last_updated': old_date}, f)
    
    # 执行清理
    success = cleanup.cleanup_stats()
    assert success
    assert not stats_file.exists()

def test_cleanup_health(test_data_dir):
    """测试健康状态清理"""
    cleanup = DistributorCleanup()
    cleanup.data_dir = test_data_dir
    
    # 创建测试健康状态文件
    health_file = test_data_dir / 'health' / 'distributor_health.json'
    old_date = (datetime.now() - timedelta(days=8)).isoformat()
    
    health_data = {
        'test_distributor': {
            'status': 'healthy',
            'timestamp': old_date
        }
    }
    
    with open(health_file, 'w', encoding='utf-8') as f:
        json.dump(health_data, f)
    
    # 执行清理
    success = cleanup.cleanup_health()
    assert success
    
    # 验证清理结果
    with open(health_file, 'r', encoding='utf-8') as f:
        cleaned_data = json.load(f)
    assert 'test_distributor' not in cleaned_data

def test_cleanup_alerts(test_data_dir):
    """测试告警记录清理"""
    cleanup = DistributorCleanup()
    cleanup.data_dir = test_data_dir
    
    # 创建测试告警文件
    alert_file = test_data_dir / 'alerts' / 'test_alerts.json'
    old_date = (datetime.now() - timedelta(days=15)).isoformat()
    
    alerts = [
        {'timestamp': old_date, 'message': '旧告警'},
        {'timestamp': datetime.now().isoformat(), 'message': '新告警'}
    ]
    
    with open(alert_file, 'w', encoding='utf-8') as f:
        json.dump(alerts, f)
    
    # 执行清理
    success = cleanup.cleanup_alerts()
    assert success
    
    # 验证清理结果
    with open(alert_file, 'r', encoding='utf-8') as f:
        cleaned_alerts = json.load(f)
    assert len(cleaned_alerts) == 1
    assert cleaned_alerts[0]['message'] == '新告警'

def test_update_cleanup_config(mock_distributor):
    """测试更新清理配置"""
    new_config = {
        'stats_retention_days': 60,
        'health_retention_days': 14,
        'alert_retention_days': 30,
        'cleanup_interval': 43200
    }
    
    mock_distributor.update_cleanup_config(new_config)
    
    assert mock_distributor.cleanup.config['stats_retention_days'] == 60
    assert mock_distributor.cleanup.config['health_retention_days'] == 14
    assert mock_distributor.cleanup.config['alert_retention_days'] == 30
    assert mock_distributor.cleanup.config['cleanup_interval'] == 43200 