#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Unit tests for category analyzer
"""

import pytest
import pytest_asyncio
from unittest.mock import MagicMock, AsyncMock
from app.category_system.models.category import Category, CategoryLevel
from app.category_system.category_analyzer import CategoryAnalyzer

class TestCategoryAnalyzer:
    """Test category analyzer"""
    
    @pytest.fixture
    def category_manager(self):
        """Create mock category manager"""
        mock = MagicMock()
        mock.storage = AsyncMock()
        mock.storage.get_category_list = AsyncMock()
        mock.storage.save_analysis_results = AsyncMock()
        return mock
    
    @pytest.fixture
    def analyzer(self, category_manager):
        """Create a test analyzer instance"""
        analyzer = CategoryAnalyzer(category_manager)
        analyzer.storage = category_manager.storage
        return analyzer
    
    @pytest.fixture
    def test_categories(self):
        """Create test categories"""
        parent = Category.create_primary(
            name="Parent Category",
            description="Parent Description",
            examples=["Parent Example"]
        )
        
        child1 = Category.create_secondary(
            name="Child 1",
            description="Child 1 Description",
            parent_id=parent.id,
            examples=["Child Example 1"]
        )
        
        child2 = Category.create_secondary(
            name="Child 2",
            description="Child 2 Description",
            parent_id=parent.id,
            examples=["Child Example 2"]
        )
        
        return [parent, child1, child2]
    
    @pytest.mark.asyncio
    async def test_start_and_stop(self, analyzer):
        """Test starting and stopping analyzer"""
        # Initialize analyzer
        await analyzer.initialize({"analysis_interval": 3600})
        
        # Test start
        result = await analyzer.start()
        assert result is True
        assert analyzer.is_running is True
        
        # Test stop
        result = await analyzer.stop()
        assert result is True
        assert analyzer.is_running is False
    
    @pytest.mark.asyncio
    async def test_add_category_suggestion(self, analyzer):
        """Test adding category suggestion"""
        # Initialize analyzer
        await analyzer.initialize({"analysis_interval": 3600})
        
        parent_id = "p_12345"
        name = "Test Category"
        
        # Add suggestion
        await analyzer.add_category_suggestion(parent_id, name)
        
        # Verify suggestion added
        assert parent_id in analyzer.category_suggestions
        assert name in analyzer.category_suggestions[parent_id]
        assert analyzer.category_suggestions[parent_id][name] == 1
        
        # Add same suggestion again
        await analyzer.add_category_suggestion(parent_id, name)
        
        # Verify count increased
        assert analyzer.category_suggestions[parent_id][name] == 2
    
    @pytest.mark.asyncio
    async def test_analyze_usage_patterns(self, analyzer, test_categories):
        """Test analyzing usage patterns"""
        # Initialize analyzer
        await analyzer.initialize({"analysis_interval": 3600})
        
        # Convert categories to dictionary format
        categories = [
            {
                "id": cat.id,
                "name": cat.name,
                "level": cat.level.value,
                "description": cat.description,
                "parent_id": cat.parent_id,
                "examples": cat.examples,
                "created_at": cat.created_at,
                "updated_at": cat.updated_at,
                "count": 10 if cat.level == CategoryLevel.PRIMARY else 5
            }
            for cat in test_categories
        ]
        
        # Analyze patterns
        patterns = analyzer._analyze_usage_patterns(categories)
        
        assert "usage_trend" in patterns
        assert "popular_categories" in patterns
        assert "low_usage_categories" in patterns
        assert len(patterns["popular_categories"]) > 0
    
    @pytest.mark.asyncio
    async def test_calculate_performance_metrics(self, analyzer, test_categories):
        """Test calculating performance metrics"""
        # Initialize analyzer
        await analyzer.initialize({"analysis_interval": 3600})
        
        # Convert categories to dictionary format
        categories = [
            {
                "id": cat.id,
                "name": cat.name,
                "level": cat.level.value,
                "description": cat.description,
                "parent_id": cat.parent_id,
                "examples": cat.examples,
                "created_at": cat.created_at,
                "updated_at": cat.updated_at,
                "count": 10 if cat.level == CategoryLevel.PRIMARY else 5,
                "feedback_count": 10,
                "positive_feedback": 8,
                "metadata": {"response_time": 0.5},
                "status": "active"
            }
            for cat in test_categories
        ]
        
        # Calculate metrics
        metrics = analyzer._calculate_performance_metrics(categories)
        
        assert "classification_accuracy" in metrics
        assert "response_time" in metrics
        assert "category_coverage" in metrics
        assert metrics["classification_accuracy"] == 0.8
        assert metrics["response_time"] == 0.5
        assert metrics["category_coverage"] == 1.0

if __name__ == "__main__":
    pytest.main(['-v', __file__])

