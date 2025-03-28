# -*- coding: utf-8 -*-
"""
Test cases for AI Classifier
"""
import sys
import os
import pytest
import pytest_asyncio
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, List

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.category_system.models.category import CategoryLevel

@pytest_asyncio.fixture
async def mock_storage():
    """Mock category storage"""
    storage = AsyncMock()
    storage.get_category_list = AsyncMock()
    return storage

@pytest_asyncio.fixture
async def mock_runtime():
    """Mock runtime"""
    runtime = Mock()
    return runtime

@pytest_asyncio.fixture
async def mock_mcp_service():
    """Mock MCP service"""
    with patch('app.category_system.ai.classifier.ContentAnalysisMCPService') as mock:
        service = AsyncMock()
        service.analyze_content = AsyncMock(return_value='''
        {
            "primary_category": "Technology",
            "secondary_category": "AI",
            "confidence": 0.85,
            "reasoning": "Content discusses AI and machine learning"
        }
        ''')
        mock.return_value = service
        yield service

@pytest_asyncio.fixture
async def classifier(mock_storage, mock_runtime, mock_mcp_service):
    """Create and initialize classifier instance"""
    from app.category_system.ai.classifier import AIClassifier
    classifier = AIClassifier(mock_runtime, mock_storage)
    
    # Initialize classifier
    config = {
        "content_analyzer": {
            "api_key": "test_key",
            "provider": "openrouter",
            "model": "test_model",
            "max_tokens": 2000
        }
    }
    await classifier.initialize(config)
    return classifier

@pytest.mark.asyncio
async def test_initialize(classifier, mock_mcp_service):
    """Test classifier initialization"""
    assert classifier.mcp_service is not None
    assert isinstance(classifier.mcp_service, Mock)

@pytest.mark.asyncio
async def test_get_primary_categories(classifier, mock_storage):
    """Test getting primary categories"""
    # Mock storage response
    mock_storage.get_category_list.return_value = [
        {
            "id": "cat1",
            "name": "Technology",
            "level": CategoryLevel.PRIMARY.value,
            "description": "Tech related content",
            "examples": ["AI", "Programming"]
        }
    ]
    
    categories = await classifier._get_primary_categories()
    assert len(categories) == 1
    assert "Technology" in categories
    assert categories["Technology"]["id"] == "cat1"

@pytest.mark.asyncio
async def test_get_secondary_categories(classifier, mock_storage):
    """Test getting secondary categories"""
    # Mock storage response
    mock_storage.get_category_list.return_value = [
        {
            "id": "subcat1",
            "name": "AI",
            "level": CategoryLevel.SECONDARY.value,
            "description": "AI related content",
            "parent_id": "cat1",
            "examples": ["Machine Learning", "Deep Learning"]
        }
    ]
    
    categories = await classifier._get_secondary_categories()
    assert len(categories) == 1
    assert "AI" in categories
    assert categories["AI"]["id"] == "subcat1"

@pytest.mark.asyncio
async def test_prepare_classification_prompt(classifier, mock_storage):
    """Test preparing classification prompt"""
    # Mock storage responses
    mock_storage.get_category_list.side_effect = [
        # Primary categories
        [
            {
                "id": "cat1",
                "name": "Technology",
                "level": CategoryLevel.PRIMARY.value,
                "description": "Tech related content",
                "examples": ["AI", "Programming"]
            }
        ],
        # Secondary categories
        [
            {
                "id": "subcat1",
                "name": "AI",
                "level": CategoryLevel.SECONDARY.value,
                "description": "AI related content",
                "parent_id": "cat1",
                "examples": ["Machine Learning", "Deep Learning"]
            }
        ]
    ]
    
    content = "This is a test content about AI and machine learning."
    prompt = classifier._prepare_classification_prompt(
        content=content,
        primary_categories={"Technology": {
            "id": "cat1",
            "name": "Technology",
            "description": "Tech related content",
            "examples": ["AI", "Programming"]
        }},
        secondary_categories={"AI": {
            "id": "subcat1",
            "name": "AI",
            "description": "AI related content",
            "parent_id": "cat1",
            "examples": ["Machine Learning", "Deep Learning"]
        }}
    )
    
    assert "Technology" in prompt
    assert "AI" in prompt
    assert "Machine Learning" in prompt
    assert content in prompt

@pytest.mark.asyncio
async def test_parse_classification_result(classifier):
    """Test parsing classification result"""
    response = '''
    {
        "primary_category": "Technology",
        "secondary_category": "AI",
        "confidence": 0.85,
        "reasoning": "Content discusses AI and machine learning"
    }
    '''
    
    primary_categories = {
        "Technology": {
            "id": "cat1",
            "name": "Technology",
            "description": "Tech related content"
        }
    }
    
    secondary_categories = {
        "AI": {
            "id": "subcat1",
            "name": "AI",
            "description": "AI related content",
            "parent_id": "cat1"
        }
    }
    
    result = classifier._parse_classification_result(
        response=response,
        primary_categories=primary_categories,
        secondary_categories=secondary_categories
    )
    
    assert result is not None
    assert result["primary_category"] == "Technology"
    assert result["primary_category_id"] == "cat1"
    assert result["secondary_category"] == "AI"
    assert result["secondary_category_id"] == "subcat1"
    assert result["confidence"] == 0.85
    assert "reasoning" in result

@pytest.mark.asyncio
async def test_classify_content(classifier, mock_mcp_service):
    """Test content classification"""
    # Mock storage responses
    classifier.category_storage.get_category_list.side_effect = [
        # Primary categories
        [
            {
                "id": "cat1",
                "name": "Technology",
                "level": CategoryLevel.PRIMARY.value,
                "description": "Tech related content",
                "examples": ["AI", "Programming"]
            }
        ],
        # Secondary categories
        [
            {
                "id": "subcat1",
                "name": "AI",
                "level": CategoryLevel.SECONDARY.value,
                "description": "AI related content",
                "parent_id": "cat1",
                "examples": ["Machine Learning", "Deep Learning"]
            }
        ]
    ]
    
    # Mock MCP service response
    mock_mcp_service.analyze_content.return_value = '''
    {
        "primary_category": "Technology",
        "secondary_category": "AI",
        "confidence": 0.85,
        "reasoning": "Content discusses AI and machine learning"
    }
    '''
    
    result = await classifier.classify_content(
        message_id="test_msg",
        content="This is a test content about AI and machine learning."
    )
    
    assert result is not None
    assert result["primary_category"] == "Technology"
    assert result["primary_category_id"] == "cat1"
    assert result["secondary_category"] == "AI"
    assert result["secondary_category_id"] == "subcat1"
    assert result["confidence"] == 0.85
    assert "reasoning" in result

@pytest.mark.asyncio
async def test_classify_content_with_full_analysis(classifier, mock_mcp_service):
    """Test content classification with full analysis"""
    # Mock storage responses
    classifier.category_storage.get_category_list.side_effect = [
        # Primary categories
        [
            {
                "id": "cat1",
                "name": "Technology",
                "level": CategoryLevel.PRIMARY.value,
                "description": "Tech related content",
                "examples": ["AI", "Programming"]
            }
        ],
        # Secondary categories
        [
            {
                "id": "subcat1",
                "name": "AI",
                "level": CategoryLevel.SECONDARY.value,
                "description": "AI related content",
                "parent_id": "cat1",
                "examples": ["Machine Learning", "Deep Learning"]
            }
        ]
    ]
    
    # Mock MCP service response
    mock_mcp_service.analyze_content.return_value = '''
    {
        "primary_category": "Technology",
        "secondary_category": "AI",
        "confidence": 0.85,
        "reasoning": "Content discusses AI and machine learning"
    }
    '''
    
    full_analysis = {
        "title": "AI and Machine Learning Overview",
        "summary": "A comprehensive overview of AI and machine learning technologies",
        "keywords": ["AI", "Machine Learning", "Deep Learning", "Technology"]
    }
    
    result = await classifier.classify_content(
        message_id="test_msg",
        content="This is a test content about AI and machine learning.",
        full_analysis=full_analysis
    )
    
    assert result is not None
    assert result["primary_category"] == "Technology"
    assert result["primary_category_id"] == "cat1"
    assert result["secondary_category"] == "AI"
    assert result["secondary_category_id"] == "subcat1"
    assert result["confidence"] == 0.85
    assert "reasoning" in result

@pytest.mark.asyncio
async def test_classify_content_fuzzy_matching(classifier, mock_mcp_service):
    """Test content classification with fuzzy matching"""
    # Mock storage responses
    classifier.category_storage.get_category_list.side_effect = [
        # Primary categories
        [
            {
                "id": "cat1",
                "name": "Technology",
                "level": CategoryLevel.PRIMARY.value,
                "description": "Tech related content",
                "examples": ["AI", "Programming"]
            }
        ],
        # Secondary categories
        [
            {
                "id": "subcat1",
                "name": "AI",
                "level": CategoryLevel.SECONDARY.value,
                "description": "AI related content",
                "parent_id": "cat1",
                "examples": ["Machine Learning", "Deep Learning"]
            }
        ]
    ]
    
    # Mock MCP service response with slightly different category names
    mock_mcp_service.analyze_content.return_value = '''
    {
        "primary_category": "Tech",
        "secondary_category": "Artificial Intelligence",
        "confidence": 0.85,
        "reasoning": "Content discusses AI and machine learning"
    }
    '''
    
    result = await classifier.classify_content(
        message_id="test_msg",
        content="This is a test content about AI and machine learning."
    )
    
    assert result is not None
    assert result["primary_category"] == "Technology"  # Should match "Tech"
    assert result["primary_category_id"] == "cat1"
    assert result["secondary_category"] == "AI"  # Should match "Artificial Intelligence"
    assert result["secondary_category_id"] == "subcat1"
    assert result["confidence"] == 0.85
    assert "reasoning" in result 