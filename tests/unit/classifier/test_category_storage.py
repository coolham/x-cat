# -*- coding: utf-8 -*-
"""
Unit tests for category storage
"""

import pytest
import os
import json
import time
import asyncio
from unittest.mock import MagicMock, patch
from app.category_system.models.category import Category, CategoryLevel
from app.category_system.storage.category_storage import CategoryStorage

class TestCategoryStorage:
    """Test category storage"""
    
    @pytest.fixture
    def storage_module(self):
        """Create mock storage module"""
        return MagicMock()
    
    @pytest.fixture
    def storage(self, storage_module, tmp_path):
        """Create a test storage instance"""
        db_path = str(tmp_path / "test_categories.json")
        storage = CategoryStorage(storage_module, db_path)
        return storage
    
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
    async def test_initialize(self, storage, tmp_path):
        """Test storage initialization"""
        # Test creating new storage
        assert await storage.initialize()
        assert os.path.exists(storage.db_path)
        
        # Test loading existing storage
        storage2 = CategoryStorage(MagicMock(), storage.db_path)
        assert await storage2.initialize()
        assert storage2.data == storage.data
    
    @pytest.mark.asyncio
    async def test_initialize_error_handling(self, storage):
        """Test initialization error handling"""
        with patch('os.makedirs') as mock_makedirs:
            mock_makedirs.side_effect = PermissionError("Permission denied")
            assert not await storage.initialize()
    
    @pytest.mark.asyncio
    async def test_corrupted_file_handling(self, storage, tmp_path):
        """Test handling of corrupted JSON file"""
        # Create a corrupted JSON file
        with open(storage.db_path, 'w', encoding='utf-8') as f:
            f.write('{"categories": {invalid json}')
        
        # Should handle corrupted file gracefully
        assert await storage.initialize()
        assert storage.data == {"categories": {}, "content_categories": {}}
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self, storage, test_categories):
        """Test concurrent operations"""
        await storage.initialize()
        
        # Store initial category
        parent = test_categories[0]
        await storage.store_category(parent)
        
        # Create multiple concurrent operations
        async def increment_usage():
            for _ in range(10):
                await storage._increment_category_usage(parent.id)
        
        # Run concurrent operations
        tasks = [increment_usage() for _ in range(5)]
        await asyncio.gather(*tasks)
        
        # Verify final count
        updated_cat = await storage.get_category_by_id(parent.id)
        assert updated_cat["count"] == 50  # 5 tasks * 10 increments
    
    @pytest.mark.asyncio
    async def test_large_data_handling(self, storage):
        """Test handling of large data sets"""
        await storage.initialize()
        
        # Create many categories
        categories = []
        primary_categories = []
        
        # First create primary categories
        for i in range(10):
            cat = Category.create_primary(
                name=f"Primary {i}",
                description=f"Description {i}",
                examples=[f"Example {i}"]
            )
            primary_categories.append(cat)
            categories.append(cat)
            await storage.store_category(cat)
        
        # Then create secondary categories
        for i in range(90):
            parent = primary_categories[i // 9]  # Distribute secondary categories among primary categories
            cat = Category.create_secondary(
                name=f"Secondary {i}",
                description=f"Description {i}",
                parent_id=parent.id,
                examples=[f"Example {i}"]
            )
            categories.append(cat)
            await storage.store_category(cat)
        
        # Verify storage and retrieval
        stored_categories = await storage.get_category_list()
        assert len(stored_categories) == 100
        
        # Test filtering
        primary_categories = await storage.get_category_list(CategoryLevel.PRIMARY)
        assert len(primary_categories) == 10
        
        secondary_categories = await storage.get_category_list(CategoryLevel.SECONDARY)
        assert len(secondary_categories) == 90
    
    @pytest.mark.asyncio
    async def test_special_characters(self, storage):
        """Test handling of special characters in category names and descriptions"""
        await storage.initialize()
        
        # Create category with special characters
        special_cat = Category.create_primary(
            name="Special Category !@#$%^&*()",
            description="Description with special chars: 你好，世界！",
            examples=["Example with emoji: 🌟"]
        )
        
        assert await storage.store_category(special_cat)
        
        # Verify storage and retrieval
        stored_cat = await storage.get_category_by_id(special_cat.id)
        assert stored_cat["name"] == special_cat.name
        assert stored_cat["description"] == special_cat.description
        assert stored_cat["examples"] == special_cat.examples
    
    @pytest.mark.asyncio
    async def test_store_and_get_categories(self, storage, test_categories):
        """Test storing and getting categories"""
        # Initialize storage
        await storage.initialize()
        
        # Store categories
        for category in test_categories:
            assert await storage.store_category(category)
        
        # Get all categories
        categories = await storage.get_category_list()
        
        # Verify loaded categories
        assert len(categories) == 3
        parent = next(cat for cat in categories if cat["level"] == CategoryLevel.PRIMARY.value)
        assert parent["name"] == "Parent Category"
        assert "children" in parent
        assert len(parent["children"]) == 2
        
        children = [cat for cat in categories if cat["level"] == CategoryLevel.SECONDARY.value]
        assert len(children) == 2
        assert all(child["parent_id"] == parent["id"] for child in children)
        
        # Verify data persistence
        storage2 = CategoryStorage(MagicMock(), storage.db_path)
        await storage2.initialize()
        categories2 = await storage2.get_category_list()
        assert len(categories2) == 3
    
    @pytest.mark.asyncio
    async def test_store_category_error_handling(self, storage, test_categories):
        """Test category storage error handling"""
        await storage.initialize()
        
        with patch('json.dump') as mock_dump:
            mock_dump.side_effect = IOError("Write error")
            assert not await storage.store_category(test_categories[0])
    
    @pytest.mark.asyncio
    async def test_update_category(self, storage, test_categories):
        """Test updating a category"""
        # Initialize storage
        await storage.initialize()
        
        # Store initial categories
        for category in test_categories:
            await storage.store_category(category)
        
        # Update a category
        parent = test_categories[0]
        parent.description = "Updated Description"
        assert await storage.update_category(parent)
        
        # Get and verify update
        categories = await storage.get_category_list()
        updated_parent = next(cat for cat in categories if cat["level"] == CategoryLevel.PRIMARY.value)
        assert updated_parent["description"] == "Updated Description"
        
        # Test updating non-existent category
        non_existent = Category.create_primary(
            name="Non Existent",
            description="Test",
            examples=["Test"]
        )
        assert not await storage.update_category(non_existent)
    
    @pytest.mark.asyncio
    async def test_delete_category(self, storage, test_categories):
        """Test deleting a category"""
        # Initialize storage
        await storage.initialize()
        
        # Store initial categories
        for category in test_categories:
            await storage.store_category(category)
        
        # Delete a category
        child = test_categories[1]
        assert await storage.delete_category(child.id)
        
        # Get and verify deletion
        categories = await storage.get_category_list()
        assert len(categories) == 2
        assert not any(cat["id"] == child.id for cat in categories)
        
        # Verify removed from parent's children list
        parent = next(cat for cat in categories if cat["level"] == CategoryLevel.PRIMARY.value)
        assert child.id not in parent["children"]
        
        # Test deleting non-existent category
        assert not await storage.delete_category("non_existent_id")
    
    @pytest.mark.asyncio
    async def test_get_category_by_id(self, storage, test_categories):
        """Test getting a category by ID"""
        # Initialize storage
        await storage.initialize()
        
        # Store categories
        for category in test_categories:
            await storage.store_category(category)
        
        # Get category by ID
        parent = test_categories[0]
        category = await storage.get_category_by_id(parent.id)
        
        assert category is not None
        assert category["id"] == parent.id
        assert category["name"] == parent.name
        assert category["level"] == CategoryLevel.PRIMARY.value
        assert "children" in category
        assert len(category["children"]) == 2
        
        # Test getting non-existent category
        assert await storage.get_category_by_id("non_existent_id") is None
    
    @pytest.mark.asyncio
    async def test_get_category_list(self, storage, test_categories):
        """Test getting category list with different filters"""
        await storage.initialize()
        
        # Store categories
        for category in test_categories:
            await storage.store_category(category)
        
        # Test getting all categories
        all_categories = await storage.get_category_list()
        assert len(all_categories) == 3
        
        # Test getting primary categories
        primary_categories = await storage.get_category_list(CategoryLevel.PRIMARY)
        assert len(primary_categories) == 1
        assert all(cat["level"] == CategoryLevel.PRIMARY.value for cat in primary_categories)
        
        # Test getting secondary categories
        secondary_categories = await storage.get_category_list(CategoryLevel.SECONDARY)
        assert len(secondary_categories) == 2
        assert all(cat["level"] == CategoryLevel.SECONDARY.value for cat in secondary_categories)
    
    @pytest.mark.asyncio
    async def test_store_content_category(self, storage, test_categories):
        """Test storing content category"""
        await storage.initialize()
        
        # Store categories
        for category in test_categories:
            await storage.store_category(category)
        
        # Store content category
        parent = test_categories[0]
        child = test_categories[1]
        message_id = "test_message_1"
        
        assert await storage.store_content_category(
            message_id=message_id,
            primary_cat_id=parent.id,
            secondary_cat_id=child.id,
            confidence=0.95
        )
        
        # Verify content category stored
        assert message_id in storage.data["content_categories"]
        content_cat = storage.data["content_categories"][message_id]
        assert content_cat["primary_id"] == parent.id
        assert content_cat["secondary_id"] == child.id
        assert content_cat["confidence"] == 0.95
        
        # Verify category counts updated
        parent_cat = storage.data["categories"][parent.id]
        child_cat = storage.data["categories"][child.id]
        assert parent_cat["count"] == 1
        assert child_cat["count"] == 1
        
        # Test storing with non-existent categories
        assert not await storage.store_content_category(
            message_id="test_message_2",
            primary_cat_id="non_existent",
            secondary_cat_id=None,
            confidence=0.95
        )
    
    @pytest.mark.asyncio
    async def test_increment_category_usage(self, storage, test_categories):
        """Test category usage increment"""
        await storage.initialize()
        
        # Store a category
        category = test_categories[0]
        await storage.store_category(category)
        
        # Test incrementing usage
        await storage._increment_category_usage(category.id)
        updated_cat = await storage.get_category_by_id(category.id)
        assert updated_cat["count"] == 1
        
        # Test incrementing non-existent category
        await storage._increment_category_usage("non_existent")
        assert "non_existent" not in storage.data["categories"]
    
    @pytest.mark.asyncio
    async def test_save_analysis_results(self, storage):
        """Test saving analysis results"""
        await storage.initialize()
        
        results = {
            "performance_metrics": {
                "accuracy": 0.95,
                "response_time": 0.5
            },
            "optimization_suggestions": [
                {"type": "merge", "message": "Merge similar categories"}
            ]
        }
        
        assert await storage.save_analysis_results(results)
        assert storage.data["analysis_results"] == results
        
        # Test error handling
        with patch('json.dump') as mock_dump:
            mock_dump.side_effect = IOError("Write error")
            assert not await storage.save_analysis_results(results)
    
    @pytest.mark.asyncio
    async def test_data_consistency(self, storage, test_categories):
        """Test data consistency after multiple operations"""
        await storage.initialize()
        
        # Store initial data
        for category in test_categories:
            await storage.store_category(category)
        
        # Store content categories
        parent = test_categories[0]
        child = test_categories[1]
        message_ids = [f"message_{i}" for i in range(5)]
        
        for msg_id in message_ids:
            await storage.store_content_category(
                message_id=msg_id,
                primary_cat_id=parent.id,
                secondary_cat_id=child.id,
                confidence=0.95
            )
        
        # Verify data consistency
        parent_cat = await storage.get_category_by_id(parent.id)
        child_cat = await storage.get_category_by_id(child.id)
        
        assert parent_cat["count"] == 5
        assert child_cat["count"] == 5
        assert len(storage.data["content_categories"]) == 5
        assert all(msg_id in storage.data["content_categories"] for msg_id in message_ids)
        
        # Verify parent-child relationship
        assert child.id in parent_cat["children"]
        assert child_cat["parent_id"] == parent.id
