# -*- coding: utf-8 -*-
"""
分类系统集成测试
测试分类系统的完整工作流程
"""
import pytest
import asyncio
from datetime import datetime
from typing import Dict

from app.category_system.models.category_manager import CategoryManager
from app.category_system.ai.classifier import AIClassifier
from app.category_system.storage.category_storage import CategoryStorage
from app.core.events import Message, MessageAnalyzed

@pytest.fixture
async def category_manager():
    """创建分类管理器"""
    manager = CategoryManager()
    return manager

@pytest.fixture
async def category_storage():
    """创建分类存储"""
    storage = CategoryStorage()
    return storage

@pytest.fixture
async def classifier(category_manager):
    """创建分类器"""
    classifier = AIClassifier(category_manager)
    return classifier

@pytest.fixture
def test_content():
    """创建测试内容"""
    return {
        'id': 'test_001',
        'text': '测试内容',
        'source': 'test',
        'metadata': {
            'date': datetime.now().isoformat()
        }
    }

@pytest.mark.asyncio
async def test_end_to_end_classification(classifier, category_storage, test_content):
    """测试端到端分类流程"""
    # 执行分类
    result = classifier.classify(test_content['text'], 'zh')
    
    # 验证分类结果
    assert result['primary_category'] in classifier.category_manager.get_primary_categories()
    assert result['secondary_category'] in classifier.category_manager.get_secondary_categories(result['primary_category'])
    assert 0 <= result['confidence'] <= 1
    assert len(result['reasoning']) <= 50
    
    # 存储分类结果
    category_storage.store_classification(
        test_content['id'],
        result['primary_category'],
        result['secondary_category'],
        result['confidence'],
        result['reasoning']
    )
    
    # 验证存储结果
    stored_result = category_storage.get_classification(test_content['id'])
    assert stored_result is not None
    assert stored_result['primary_category'] == result['primary_category']
    assert stored_result['secondary_category'] == result['secondary_category']
    assert stored_result['confidence'] == result['confidence']
    assert stored_result['reasoning'] == result['reasoning']

@pytest.mark.asyncio
async def test_category_manager_integration(classifier, category_manager):
    """测试分类管理器集成"""
    # 获取分类信息
    primary_categories = category_manager.get_primary_categories()
    assert len(primary_categories) > 0
    
    # 测试分类结果
    result = classifier.classify('测试内容', 'zh')
    assert result['primary_category'] in primary_categories
    
    # 获取分类路径
    category_path = category_manager.get_category_path(result['primary_category'])
    assert len(category_path) > 0
    assert category_path[0] == result['primary_category']

@pytest.mark.asyncio
async def test_category_storage_integration(classifier, category_storage):
    """测试分类存储集成"""
    # 准备测试数据
    content_id = 'test_002'
    content_text = '人工智能和大语言模型的发展'
    
    # 执行分类
    result = classifier.classify(content_text, 'zh')
    
    # 存储分类结果
    category_storage.store_classification(
        content_id,
        result['primary_category'],
        result['secondary_category'],
        result['confidence'],
        result['reasoning']
    )
    
    # 验证存储
    stored_result = category_storage.get_classification(content_id)
    assert stored_result is not None
    assert stored_result['primary_category'] == result['primary_category']
    assert stored_result['secondary_category'] == result['secondary_category']
    
    # 验证统计信息
    stats = category_storage.get_statistics()
    assert stats['total_classifications'] > 0
    assert stats['success_rate'] > 0

@pytest.mark.asyncio
async def test_multiple_language_support(classifier, category_manager):
    """测试多语言支持"""
    # 测试中文分类
    zh_result = classifier.classify('测试内容', 'zh')
    assert zh_result['primary_category'] in category_manager.get_primary_categories('zh')
    
    # 测试英文分类
    en_result = classifier.classify('test content', 'en')
    assert en_result['primary_category'] in category_manager.get_primary_categories('en')
    
    # 验证分类结果不同
    assert zh_result['primary_category'] != en_result['primary_category']

@pytest.mark.asyncio
async def test_error_handling(classifier, category_storage):
    """测试错误处理"""
    # 测试无效内容
    result = classifier.classify('', 'zh')
    assert result['primary_category'] == '其它'
    assert result['secondary_category'] == '待分类内容'
    
    # 测试无效语言
    result = classifier.classify('测试内容', 'invalid')
    assert result['primary_category'] == '其它'
    assert result['secondary_category'] == '待分类内容'
    
    # 测试存储错误
    try:
        category_storage.store_classification(
            'test_003',
            'invalid_category',
            'invalid_subcategory',
            0.0,
            '测试错误'
        )
    except Exception as e:
        assert str(e) == '无效的分类'

@pytest.mark.asyncio
async def test_performance(classifier, category_storage):
    """测试性能"""
    import time
    
    # 测试分类性能
    start_time = time.time()
    for _ in range(100):
        classifier.classify('测试内容', 'zh')
    classification_time = time.time() - start_time
    assert classification_time < 10  # 100次分类应在10秒内完成
    
    # 测试存储性能
    start_time = time.time()
    for i in range(100):
        category_storage.store_classification(
            f'test_{i}',
            '测试分类',
            '测试子分类',
            0.9,
            '测试理由'
        )
    storage_time = time.time() - start_time
    assert storage_time < 5  # 100次存储应在5秒内完成

@pytest.mark.asyncio
async def test_concurrent_operations(classifier, category_storage):
    """测试并发操作"""
    async def process_content(content_id: str, text: str):
        """处理单个内容"""
        # 执行分类
        result = classifier.classify(text, 'zh')
        
        # 存储结果
        category_storage.store_classification(
            content_id,
            result['primary_category'],
            result['secondary_category'],
            result['confidence'],
            result['reasoning']
        )
        
        return result
    
    # 创建多个任务
    tasks = []
    for i in range(10):
        content_id = f'test_{i}'
        text = f'测试内容 {i}'
        tasks.append(process_content(content_id, text))
    
    # 并发执行任务
    results = await asyncio.gather(*tasks)
    
    # 验证结果
    assert len(results) == 10
    for result in results:
        assert result['primary_category'] in classifier.category_manager.get_primary_categories()
        assert result['secondary_category'] in classifier.category_manager.get_secondary_categories(result['primary_category'])

@pytest.mark.asyncio
async def test_event_handling(classifier, category_manager, category_storage):
    """测试事件处理"""
    # 创建测试消息
    message = Message(
        message_id="test_event_msg",
        content="这是一篇关于CNN架构的深度文章，详细讨论了神经网络的最新进展。"
    )
    analysis = {
        "title": "CNN架构进展",
        "summary": "本文详细讨论了CNN架构的最新进展",
        "keywords": ["CNN", "深度学习", "神经网络"]
    }
    
    # 创建事件
    event = MessageAnalyzed(message=message, analysis_result=analysis)
    
    # 处理事件
    await category_manager._handle_message_analyzed(event)
    
    # 验证分类结果
    stored_result = category_storage.get_classification(message.message_id)
    assert stored_result is not None
    assert stored_result['primary_category'] in category_manager.get_primary_categories()
    assert stored_result['secondary_category'] in category_manager.get_secondary_categories(stored_result['primary_category']) 