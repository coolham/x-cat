#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Unit tests for category manager
"""
import pytest
import pytest_asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from app.category_system.category_manager import CategoryManager
from app.category_system.models.category import Category, CategoryLevel
from app.core.runtime import Runtime
from app.core.events import MessageAnalyzed

class TestCategoryManager:
    """Test category manager"""
    
    @pytest.fixture
    def mock_runtime(self):
        """Create mock runtime"""
        runtime = MagicMock(spec=Runtime)
        runtime.get_module = MagicMock()
        runtime.event_bus = MagicMock()
        return runtime
    
    @pytest.fixture
    def mock_storage_module(self):
        """Create mock storage module"""
        storage = MagicMock()
        storage.connection = MagicMock()
        storage.connection.cursor = MagicMock()
        return storage
    
    @pytest.fixture
    def category_manager(self, mock_runtime, mock_storage_module):
        """Create category manager instance"""
        mock_runtime.get_module.return_value = mock_storage_module
        manager = CategoryManager(mock_runtime)
        return manager
    
    @pytest.mark.asyncio
    async def test_initialize(self, category_manager, mock_runtime, mock_storage_module):
        """Test category manager initialization"""
        config = {
            "content_analyzer": {
                "api_key": "test_key",
                "provider": "test_provider",
                "model": "test_model"
            }
        }
        
        # Mock storage initialization
        with patch('app.category_system.storage.category_storage.CategoryStorage') as mock_storage:
            storage_instance = AsyncMock()
            storage_instance.initialize = AsyncMock(return_value=True)
            mock_storage.return_value = storage_instance
            
            # Mock classifier initialization
            with patch('app.category_system.ai.classifier.AIClassifier') as mock_classifier:
                classifier_instance = AsyncMock()
                classifier_instance.initialize = AsyncMock(return_value=True)
                mock_classifier.return_value = classifier_instance
                
                # Initialize manager
                result = await category_manager.initialize(config)
                
                # Verify initialization
                assert result is True
                assert category_manager.initialized is True
                assert category_manager.storage is not None
                assert category_manager.classifier is not None
                assert category_manager.config == config
    
    @pytest.mark.asyncio
    async def test_start_and_stop(self, category_manager):
        """Test starting and stopping category manager"""
        # Initialize manager
        await category_manager.initialize({})
        
        # Test start
        result = await category_manager.start()
        assert result is True
        assert category_manager.is_running is True
        
        # Test stop
        result = await category_manager.stop()
        assert result is True
        assert category_manager.is_running is False
    
    @pytest.mark.asyncio
    async def test_handle_message_analyzed(self, category_manager):
        """Test handling message analyzed event"""
        # Initialize manager
        await category_manager.initialize({})
        await category_manager.start()
        
        # Create test event
        event = MessageAnalyzed(
            message=MagicMock(message_id="test_msg"),
            analysis_result={
                "title": "Test Title",
                "summary": "Test Summary",
                "keywords": ["test"]
            }
        )
        
        # Mock classifier response
        category_manager.classifier.classify_content = AsyncMock(return_value={
            "primary_category_id": "p_123",
            "secondary_category_id": "s_456",
            "confidence": 0.85
        })
        
        # Mock storage
        category_manager.storage.store_content_category = AsyncMock(return_value=True)
        
        # Handle event
        await category_manager._handle_message_analyzed(event)
        
        # Verify calls
        category_manager.classifier.classify_content.assert_called_once()
        category_manager.storage.store_content_category.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_active_categories(self, category_manager):
        """Test getting active categories"""
        # Initialize manager
        await category_manager.initialize({})
        
        # Mock storage response
        test_categories = [
            {
                "id": "p_123",
                "name": "Test Category",
                "level": CategoryLevel.PRIMARY.value,
                "description": "Test Description",
                "examples": ["test"]
            }
        ]
        category_manager.storage.get_category_list = AsyncMock(return_value=test_categories)
        
        # Get categories
        categories = await category_manager.get_active_categories()
        
        # Verify result
        assert categories == test_categories
        category_manager.storage.get_category_list.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_classify_message(self, category_manager):
        """Test direct message classification"""
        # Initialize manager
        await category_manager.initialize({})
        await category_manager.start()
        
        # Mock classifier response
        classification = {
            "primary_category_id": "p_123",
            "secondary_category_id": "s_456",
            "confidence": 0.85
        }
        category_manager.classifier.classify_content = AsyncMock(return_value=classification)
        
        # Mock storage
        category_manager.storage.store_content_category = AsyncMock(return_value=True)
        
        # Classify message
        result = await category_manager.classify_message(
            message_id="test_msg",
            content="Test content"
        )
        
        # Verify result
        assert result == classification
        category_manager.classifier.classify_content.assert_called_once()
        category_manager.storage.store_content_category.assert_called_once()

if __name__ == "__main__":
    pytest.main(['-v', __file__])
