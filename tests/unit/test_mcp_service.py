"""
测试MCP服务模块
包括ContentAnalysisMCPService类的单元测试
"""
import pytest
import time
import os
import sys
from unittest.mock import patch, MagicMock, AsyncMock

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.services.mcp_service import ContentAnalysisMCPService
from app.processors.preprocessor import PreProcessor
from app.processors.content_fetcher import ContentFetcher
from app.processors.content_assembler import ContentAssembler
from app.analyzers.content_analyzer import ContentAnalyzer


class TestContentAnalysisMCPService:
    """测试内容分析MCP服务类"""
    
    def setup_method(self):
        """设置测试环境"""
        # 模拟各个组件
        with patch('app.services.mcp_service.PreProcessor') as mock_preprocessor, \
             patch('app.services.mcp_service.ContentFetcher') as mock_fetcher, \
             patch('app.services.mcp_service.ContentAssembler') as mock_assembler, \
             patch('app.services.mcp_service.ContentAnalyzer') as mock_analyzer:
            
            # 设置各个组件的模拟实例
            self.mock_preprocessor_instance = AsyncMock()
            self.mock_fetcher_instance = AsyncMock()
            self.mock_assembler_instance = MagicMock()
            self.mock_analyzer_instance = AsyncMock()
            
            mock_preprocessor.return_value = self.mock_preprocessor_instance
            mock_fetcher.return_value = self.mock_fetcher_instance
            mock_assembler.return_value = self.mock_assembler_instance
            mock_analyzer.return_value = self.mock_analyzer_instance
            
            # 初始化服务
            self.mcp_service = ContentAnalysisMCPService(
                api_key="test_key",
                provider="test_provider",
                model="test_model",
                max_tokens=1000,
                temperature=0.7,
                max_content_length=8000,
                max_total_length=15000,
                max_urls=3,
                format_type="markdown"
            )
    
    @pytest.mark.asyncio
    async def test_process_simple_message(self):
        """测试处理普通文本消息"""
        # 创建测试消息
        message = {
            "message_id": "test123",
            "text": "这是一个测试消息",
            "sender_name": "测试发送者",
            "chat_title": "测试聊天"
        }
        
        # 设置各个模拟组件的返回值
        self.mock_preprocessor_instance.process.return_value = {
            "success": True,
            "original_message": message,
            "content_format": "text_only",
            "urls": [],
            "valid_urls": [],
            "text_content": "这是一个测试消息",
            "analysis_value": 5,
            "metadata": {
                "lang_hint": "zh",
                "has_hashtags": False,
                "has_mentions": False
            }
        }
        
        self.mock_assembler_instance.assemble.return_value = {
            "content": "## 原始消息\n\n这是一个测试消息",
            "metadata": {
                "message_id": "test123",
                "sender_name": "测试发送者",
                "chat_title": "测试聊天",
                "content_format": "text_only",
                "content_metadata": {
                    "lang_hint": "zh",
                    "has_hashtags": False,
                    "has_mentions": False
                }
            },
            "urls": [],
            "content_format": "text_only",
            "has_web_content": False
        }
        
        self.mock_analyzer_instance.analyze.return_value = {
            "success": True,
            "content_type": "文本",
            "category": "聊天",
            "subcategory": "一般对话",
            "sentiment": "中性",
            "keywords": ["测试", "消息"],
            "summary": "简单的测试消息",
            "language": "zh",
            "urls": []
        }
        
        # 执行测试
        result = await self.mcp_service.process(message)
        
        # 验证结果
        assert result["success"] is True
        assert result["content_type"] == "文本"
        assert result["category"] == "聊天"
        assert "processing" in result
        assert isinstance(result["processing"]["duration"], float)
        
        # 验证各个组件方法被调用
        self.mock_preprocessor_instance.process.assert_called_once_with(message)
        self.mock_fetcher_instance.fetch.assert_not_called()  # 没有URL，不应该调用fetch
        self.mock_assembler_instance.assemble.assert_called_once()
        self.mock_analyzer_instance.analyze.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_message_with_url(self):
        """测试处理包含URL的消息"""
        # 创建测试消息
        message = {
            "message_id": "test456",
            "text": "这是一个带链接的测试消息: https://example.com",
            "sender_name": "测试发送者",
            "chat_title": "测试聊天"
        }
        
        # 设置各个模拟组件的返回值
        self.mock_preprocessor_instance.process.return_value = {
            "success": True,
            "original_message": message,
            "content_format": "text_with_url",
            "urls": ["https://example.com"],
            "valid_urls": ["https://example.com"],
            "text_content": "这是一个带链接的测试消息: https://example.com",
            "analysis_value": 6,
            "metadata": {
                "lang_hint": "zh",
                "has_hashtags": False,
                "has_mentions": False
            }
        }
        
        self.mock_fetcher_instance.fetch.return_value = [{
            "url": "https://example.com",
            "success": True,
            "content": "这是示例网页内容",
            "title": "示例网页",
            "type": "html"
        }]
        
        self.mock_assembler_instance.assemble.return_value = {
            "content": "## 原始消息\n\n这是一个带链接的测试消息: https://example.com\n\n### 网页 1: 示例网页\n\nURL: https://example.com\n\n这是示例网页内容",
            "metadata": {
                "message_id": "test456",
                "sender_name": "测试发送者",
                "chat_title": "测试聊天",
                "content_format": "text_with_url",
                "content_metadata": {
                    "lang_hint": "zh",
                    "has_hashtags": False,
                    "has_mentions": False
                }
            },
            "urls": ["https://example.com"],
            "content_format": "text_with_url",
            "has_web_content": True
        }
        
        self.mock_analyzer_instance.analyze.return_value = {
            "success": True,
            "content_type": "文章",
            "category": "技术",
            "subcategory": "网页内容",
            "sentiment": "中性",
            "keywords": ["示例", "网页", "内容"],
            "summary": "带有链接的测试消息，链接指向一个包含'示例网页内容'的页面",
            "language": "zh",
            "urls": ["https://example.com"]
        }
        
        # 执行测试
        result = await self.mcp_service.process(message)
        
        # 验证结果
        assert result["success"] is True
        assert result["content_type"] == "文章"
        assert result["category"] == "技术"
        assert result["subcategory"] == "网页内容"
        assert "https://example.com" in result["urls"]
        assert "processing" in result
        assert result["processing"]["urls_processed"] == 1
        
        # 验证各个组件方法被调用
        self.mock_preprocessor_instance.process.assert_called_once_with(message)
        self.mock_fetcher_instance.fetch.assert_called_once()
        self.mock_assembler_instance.assemble.assert_called_once()
        self.mock_analyzer_instance.analyze.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_preprocessing_failure(self):
        """测试预处理失败的情况"""
        # 创建测试消息
        message = {
            "message_id": "test789",
            "text": "",  # 空消息
            "sender_name": "测试发送者",
            "chat_title": "测试聊天"
        }
        
        # 设置预处理失败的返回值
        self.mock_preprocessor_instance.process.return_value = {
            "success": False,
            "error": "消息内容为空",
            "original_message": message
        }
        
        # 执行测试
        result = await self.mcp_service.process(message)
        
        # 验证结果
        assert result["success"] is False
        assert "消息内容为空" in result["error"]
        
        # 验证只有预处理被调用
        self.mock_preprocessor_instance.process.assert_called_once_with(message)
        self.mock_fetcher_instance.fetch.assert_not_called()
        self.mock_assembler_instance.assemble.assert_not_called()
        self.mock_analyzer_instance.analyze.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_process_analysis_failure(self):
        """测试内容分析失败的情况"""
        # 创建测试消息
        message = {
            "message_id": "test999",
            "text": "这是一个测试消息",
            "sender_name": "测试发送者",
            "chat_title": "测试聊天"
        }
        
        # 设置各个模拟组件的返回值
        self.mock_preprocessor_instance.process.return_value = {
            "success": True,
            "original_message": message,
            "content_format": "text_only",
            "urls": [],
            "valid_urls": [],
            "text_content": "这是一个测试消息",
            "analysis_value": 5,
            "metadata": {}
        }
        
        self.mock_assembler_instance.assemble.return_value = {
            "content": "## 原始消息\n\n这是一个测试消息",
            "metadata": {},
            "urls": [],
            "content_format": "text_only",
            "has_web_content": False
        }
        
        # 设置分析失败
        self.mock_analyzer_instance.analyze.return_value = {
            "success": False,
            "error": "AI分析失败",
            "raw_content": "这是一个测试消息"
        }
        
        # 执行测试
        result = await self.mcp_service.process(message)
        
        # 验证结果
        assert result["success"] is False
        assert "AI分析失败" in result["error"]
        assert "processing" in result
        
        # 验证所有组件除了fetch被调用
        self.mock_preprocessor_instance.process.assert_called_once_with(message)
        self.mock_fetcher_instance.fetch.assert_not_called()
        self.mock_assembler_instance.assemble.assert_called_once()
        self.mock_analyzer_instance.analyze.assert_called_once() 