#!/usr/bin/env python
# -*- coding: utf-8 -*-
# tests/integration/test_category_system_integration.py

import pytest
import sys
import os
from unittest.mock import MagicMock, AsyncMock, patch
import sqlite3

# 确保可以导入app模块
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# 导入所需模块
from app.core.events import Message, MessageAnalyzed
from app.core.runtime import Runtime
from app.category_system.models.category import CategoryLevel

@pytest.fixture
def mock_storage_module():
    """模拟存储模块"""
    mock = MagicMock()
    
    # 创建内存数据库连接
    conn = sqlite3.connect(":memory:")
    mock.connection = conn
    
    return mock

@pytest.fixture
def mock_runtime(mock_storage_module):
    """模拟运行时环境"""
    mock = MagicMock()
    
    # 模拟事件总线
    mock.event_bus = MagicMock()
    mock.publish = AsyncMock()
    
    # 注册模拟存储模块
    mock.get_module = MagicMock(return_value=mock_storage_module)
    
    return mock

@pytest.fixture
def config():
    """测试配置"""
    return {
        "content_analyzer": {
            "api_key": "test_key",
            "provider": "openrouter",
            "model": "test_model"
        }
    }

# 模拟CategoryManager用于测试
class MockCategoryManager:
    """模拟分类管理器用于测试"""
    
    def __init__(self, runtime):
        self.runtime = runtime
        self.storage = MagicMock()
        self.classifier = MagicMock()
        self.analyzer = MagicMock()
        self.is_running = False
        self.initialized = False
    
    async def initialize(self, config):
        self.initialized = True
        return True
    
    async def start(self):
        self.is_running = True
        if self.analyzer:
            await self.analyzer.start()
        return True
    
    async def stop(self):
        self.is_running = False
        if self.analyzer:
            await self.analyzer.stop()
        return True
    
    async def _handle_message_analyzed(self, event):
        if not self.is_running:
            return
        
        message_id = event.message.message_id
        content = event.message.content
        analysis = event.analysis_result
        
        # 调用分类器
        classification = await self.classifier.classify_content(
            message_id=message_id,
            content=content,
            full_analysis=analysis
        )
        
        if classification and classification.get("suggest_new_category"):
            await self._handle_new_category_suggestion(
                primary_category_id=classification["primary_category_id"],
                suggested_name=classification["suggested_category"],
                message_id=message_id,
                content=content
            )
        
        # 存储分类结果
        await self.storage.store_content_category(
            message_id=message_id,
            primary_cat_id=classification.get("primary_category_id"),
            secondary_cat_id=classification.get("secondary_category_id"),
            confidence=classification.get("confidence", 0.5)
        )
    
    async def _handle_new_category_suggestion(self, primary_category_id, suggested_name, message_id, content):
        # 向分析器添加建议
        if self.analyzer:
            await self.analyzer.add_category_suggestion(primary_category_id, suggested_name)

class TestCategorySystemIntegration:
    """分类系统集成测试"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_classification(self, mock_runtime, config, mock_storage_module, tmp_path):
        """测试端到端分类流程"""
        # 设置临时目录
        config_dir = os.path.join(tmp_path, "test_category_config")
        os.makedirs(config_dir, exist_ok=True)
        
        # 创建分类管理器
        manager = MockCategoryManager(mock_runtime)
        
        # 模拟存储和分类器
        manager.storage.active_version = MagicMock()
        manager.storage.active_version.categories = {
            "p_12345": {
                "id": "p_12345",
                "name": "人工智能",
                "level": 1,
                "description": "AI相关内容"
            }
        }
        manager.storage.store_content_category = AsyncMock(return_value=True)
        
        # 模拟分类结果
        classification_result = {
            "primary_category": "人工智能",
            "primary_category_id": "p_12345",
            "secondary_category": "深度学习",
            "secondary_category_id": "s_67890",
            "confidence": 0.85,
            "suggest_new_category": False
        }
        
        manager.classifier.classify_content = AsyncMock(return_value=classification_result)
        
        # 初始化和启动
        await manager.initialize(config)
        await manager.start()
        
        # 创建测试消息
        message = Message(
            message_id="test_integration_msg",
            content="这是一篇关于CNN架构的深度文章，详细讨论了神经网络的最新进展。"
        )
        analysis = {
            "title": "CNN架构进展",
            "summary": "本文详细讨论了CNN架构的最新进展",
            "keywords": ["CNN", "深度学习", "神经网络"]
        }
        
        # 触发事件处理
        event = MessageAnalyzed(message=message, analysis_result=analysis)
        await manager._handle_message_analyzed(event)
        
        # 验证分类器调用
        manager.classifier.classify_content.assert_awaited_once_with(
            message_id="test_integration_msg",
            content="这是一篇关于CNN架构的深度文章，详细讨论了神经网络的最新进展。",
            full_analysis=analysis
        )
        
        # 验证存储调用
        manager.storage.store_content_category.assert_awaited_once_with(
            message_id="test_integration_msg",
            primary_cat_id="p_12345",
            secondary_cat_id="s_67890",
            confidence=0.85
        )
        
        # 停止管理器
        await manager.stop()
    
    @pytest.mark.asyncio
    async def test_suggestion_handling(self, mock_runtime, config, mock_storage_module, tmp_path):
        """测试分类建议处理"""
        # 设置临时目录
        config_dir = os.path.join(tmp_path, "test_category_system")
        os.makedirs(config_dir, exist_ok=True)
        
        # 创建分类管理器
        manager = MockCategoryManager(mock_runtime)
        
        # 模拟存储和分类器
        manager.storage.active_version = MagicMock()
        manager.storage.active_version.categories = {
            "p_12345": {
                "id": "p_12345",
                "name": "人工智能",
                "level": 1,
                "description": "AI相关内容"
            }
        }
        manager.storage.store_content_category = AsyncMock(return_value=True)
        
        # 模拟分类结果（包含建议）
        classification_result = {
            "message_id": "test_suggestion_msg",
            "primary_category": "人工智能",
            "primary_category_id": "p_12345",
            "secondary_category": None,
            "secondary_category_id": None,
            "confidence": 0.75,
            "suggest_new_category": True,
            "suggested_category": "生成式AI",
            "reasoning": "内容讨论了生成模型，应该创建一个新的二级分类"
        }
        
        manager.classifier.classify_content = AsyncMock(return_value=classification_result)
        
        # 模拟分析器
        manager.analyzer = MagicMock()
        manager.analyzer.start = AsyncMock(return_value=True)
        manager.analyzer.stop = AsyncMock(return_value=True)
        manager.analyzer.add_category_suggestion = AsyncMock()
        
        # 初始化和启动
        await manager.initialize(config)
        await manager.start()
        
        # 创建测试消息
        message = Message(
            message_id="test_suggestion_msg",
            content="这篇文章讨论了最新的生成式AI模型，包括文本到图像和文本生成技术。"
        )
        analysis = {}
        
        # 触发事件处理
        event = MessageAnalyzed(message=message, analysis_result=analysis)
        await manager._handle_message_analyzed(event)
        
        # 验证建议处理
        manager.analyzer.add_category_suggestion.assert_awaited_once_with(
            "p_12345", "生成式AI"
        )
        
        # 停止管理器
        await manager.stop()
    
    @pytest.mark.asyncio
    async def test_category_evolution(self, mock_runtime, config, mock_storage_module, tmp_path):
        """测试分类系统演化"""
        # 设置临时目录
        config_dir = os.path.join(tmp_path, "test_category_system")
        os.makedirs(config_dir, exist_ok=True)
        
        # 创建分类管理器
        manager = MockCategoryManager(mock_runtime)
        
        # 模拟分析器
        manager.analyzer = MagicMock()
        manager.analyzer.start = AsyncMock(return_value=True)
        manager.analyzer.stop = AsyncMock(return_value=True)
        manager.analyzer.add_category_suggestion = AsyncMock()
        
        # 初始化和启动
        await manager.initialize(config)
        await manager.start()
        
        # 模拟多次分类建议
        for i in range(15):
            await manager._handle_new_category_suggestion(
                primary_category_id="p_12345",
                suggested_name="生成式AI",
                message_id=f"test_msg_{i}",
                content="相关内容"
            )
        
        # 验证建议处理
        assert manager.analyzer.add_category_suggestion.await_count == 15
        
        # 停止管理器
        await manager.stop()

    @pytest.mark.asyncio
    async def test_category_evolution_workflow(self, mock_runtime, config):
        """测试分类演化工作流"""
        # 测试分类演化流程
        pass


    @pytest.mark.asyncio
    async def test_category_metadata_storage(self, mock_runtime, config):
        """测试分类元数据存储"""
        # 测试元数据的存储和检索
        pass
