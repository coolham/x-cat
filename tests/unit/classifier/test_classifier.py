# -*- coding: utf-8 -*-
"""
Test cases for AI Classifier
"""
import sys
import os
import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from typing import Dict, List

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.category_system.models.category import CategoryLevel
from app.category_system.models.category_manager import CategoryManager

@pytest.fixture
def mock_category_manager():
    """Mock category manager"""
    manager = Mock(spec=CategoryManager)
    manager.get_ai_prompt.return_value = "测试提示词"
    manager.get_category_by_id.return_value = {
        "id": "cat1",
        "name": "Technology",
        "description": "Tech related content"
    }
    return manager

@pytest.fixture
def classifier(mock_category_manager):
    """Create classifier instance"""
    from app.category_system.ai.classifier import AIClassifier
    return AIClassifier(mock_category_manager)

def test_initialize(classifier):
    """Test classifier initialization"""
    assert classifier.category_manager is not None
    assert isinstance(classifier.category_manager, Mock)

def test_classify_content(classifier):
    """Test content classification"""
    # Test content classification
    result = classifier.classify(
        content="This is a test content about AI and machine learning."
    )
    
    assert result is not None
    assert result["primary_category"] == "Technology"
    assert result["confidence"] > 0
    assert "reasoning" in result

def test_classify_content_with_multiple_languages(classifier):
    """Test content classification with multiple languages"""
    # Test Chinese content
    zh_result = classifier.classify(
        content="这是一篇关于人工智能的文章",
        language="zh"
    )
    assert zh_result is not None
    assert zh_result["primary_category"] == "Technology"
    
    # Test English content
    en_result = classifier.classify(
        content="This is an article about artificial intelligence",
        language="en"
    )
    assert en_result is not None
    assert en_result["primary_category"] == "Technology"

def test_classify_content_with_error_handling(classifier):
    """Test content classification error handling"""
    # Test invalid content type
    try:
        classifier.classify(content=None, language="zh")
    except TypeError as e:
        assert "content" in str(e)
    
    # Test empty content
    result = classifier.classify(content="", language="zh")
    assert result is not None
    assert result["primary_category"] == "其它"
    assert result["secondary_category"] == "待分类内容"
    assert result["confidence"] == 0.0

def test_classify_content_with_keywords(classifier):
    """Test content classification with different keywords"""
    # Test AI keywords
    ai_result = classifier.classify(
        content="This is about artificial intelligence and deep learning",
        language="en"
    )
    assert ai_result["primary_category"] == "Technology"
    
    # Test programming keywords
    prog_result = classifier.classify(
        content="This is about programming and software development",
        language="en"
    )
    assert prog_result["primary_category"] == "Technology"
    
    # Test unknown content
    unknown_result = classifier.classify(
        content="This is completely unknown content",
        language="en"
    )
    assert unknown_result["primary_category"] == "其它"
    assert unknown_result["secondary_category"] == "待分类内容"

def test_classify_content_with_special_characters(classifier):
    """Test content classification with special characters"""
    result = classifier.classify(
        content="This is a test content with special chars: !@#$%^&*()",
        language="en"
    )
    assert result is not None
    assert result["primary_category"] == "其它"
    assert result["secondary_category"] == "待分类内容"

def test_classify_content_with_long_content(classifier):
    """Test content classification with long content"""
    long_content = "This is a very long content " * 100
    result = classifier.classify(content=long_content, language="en")
    assert result is not None
    assert result["primary_category"] == "其它"
    assert result["secondary_category"] == "待分类内容"

def test_classify_content_with_mixed_language(classifier):
    """Test content classification with mixed language content"""
    result = classifier.classify(
        content="This is a mixed content with 中文 and English",
        language="zh"
    )
    assert result is not None
    assert result["primary_category"] == "其它"
    assert result["secondary_category"] == "待分类内容" 