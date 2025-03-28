#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Unit tests for category models
"""

import pytest
from datetime import datetime
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from app.category_system.models.category import Category, CategoryLevel

class TestCategory:
    """Test category model"""
    
    def test_create_primary_category(self):
        """Test creating a primary category"""
        # Create a primary category
        primary = Category.create_primary(
            name="Test Category",
            description="Test Description",
            examples=["Example 1", "Example 2"]
        )
        
        assert primary.name == "Test Category"
        assert primary.description == "Test Description"
        assert primary.level == CategoryLevel.PRIMARY
        assert primary.parent_id is None
        assert primary.examples == ["Example 1", "Example 2"]
        assert primary.count == 0
        assert isinstance(primary.created_at, int)
        assert isinstance(primary.updated_at, int)
        assert primary.id.startswith("p_")
    
    def test_create_secondary_category(self):
        """Test creating a secondary category"""
        # Create a primary category first
        parent = Category.create_primary(
            name="Parent Category",
            description="Parent Description",
            examples=["Parent Example"]
        )
        
        # Create a secondary category
        secondary = Category.create_secondary(
            name="Child Category",
            description="Child Description",
            parent_id=parent.id,
            examples=["Child Example"]
        )
        
        assert secondary.name == "Child Category"
        assert secondary.description == "Child Description"
        assert secondary.level == CategoryLevel.SECONDARY
        assert secondary.parent_id == parent.id
        assert secondary.examples == ["Child Example"]
        assert secondary.count == 0
        assert isinstance(secondary.created_at, int)
        assert isinstance(secondary.updated_at, int)
        assert secondary.id.startswith("s_")
    
    def test_category_to_dict(self):
        """Test category to dictionary conversion"""
        category = Category.create_primary(
            name="Test Category",
            description="Test Description",
            examples=["Example 1"]
        )
        
        category_dict = category.to_dict()
        
        assert category_dict["id"] == category.id
        assert category_dict["name"] == "Test Category"
        assert category_dict["description"] == "Test Description"
        assert category_dict["level"] == CategoryLevel.PRIMARY.value
        assert category_dict["parent_id"] is None
        assert category_dict["examples"] == ["Example 1"]
        assert category_dict["count"] == 0
        assert "created_at" in category_dict
        assert "updated_at" in category_dict
    
    def test_category_from_dict(self):
        """Test category creation from dictionary"""
        category_dict = {
            "id": "p_12345678",
            "name": "Test Category",
            "description": "Test Description",
            "level": CategoryLevel.PRIMARY.value,
            "parent_id": None,
            "examples": ["Example 1"],
            "created_at": int(datetime.now().timestamp()),
            "updated_at": int(datetime.now().timestamp()),
            "count": 5
        }
        
        category = Category.from_dict(category_dict)
        
        assert category.id == "p_12345678"
        assert category.name == "Test Category"
        assert category.description == "Test Description"
        assert category.level == CategoryLevel.PRIMARY
        assert category.parent_id is None
        assert category.examples == ["Example 1"]
        assert category.count == 5
        assert isinstance(category.created_at, int)
        assert isinstance(category.updated_at, int)

if __name__ == "__main__":
    pytest.main()


