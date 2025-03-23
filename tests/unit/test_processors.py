"""
测试处理器模块
包括预处理器、内容获取器和内容组装器的单元测试
"""
import pytest
import asyncio
import os
import sys
from unittest.mock import patch, MagicMock, AsyncMock

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.processors.preprocessor import PreProcessor
from app.processors.content_fetcher import ContentFetcher
from app.processors.content_assembler import ContentAssembler


class TestPreProcessor:
    """测试预处理器类"""
    
    def setup_method(self):
        """设置测试环境"""
        self.preprocessor = PreProcessor(max_urls=3)
    
    @pytest.mark.asyncio
    async def test_process_text_only(self):
        """测试处理纯文本消息"""
        message = {
            "message_id": "test123",
            "text": "这是一个测试消息，不包含URL",
            "sender_name": "测试发送者",
            "chat_title": "测试聊天"
        }
        
        result = await self.preprocessor.process(message)
        
        assert result["success"] is True
        assert result["content_format"] == "text_only"
        assert len(result["urls"]) == 0
        assert len(result["valid_urls"]) == 0
        assert result["text_content"] == message["text"]
        assert result["original_message"] == message
    
    @pytest.mark.asyncio
    async def test_process_with_url(self):
        """测试处理包含URL的消息"""
        message = {
            "message_id": "test456",
            "text": "这是一个测试消息，包含URL: https://example.com 和 https://test.org",
            "sender_name": "测试发送者",
            "chat_title": "测试聊天"
        }
        
        result = await self.preprocessor.process(message)
        
        assert result["success"] is True
        assert result["content_format"] == "text_with_url"
        assert len(result["urls"]) == 2
        assert len(result["valid_urls"]) <= 3  # 受max_urls限制
        assert "https://example.com" in result["valid_urls"]
        assert "https://test.org" in result["valid_urls"]
        assert result["text_content"] == message["text"]
    
    @pytest.mark.asyncio
    async def test_process_url_only(self):
        """测试处理纯URL消息"""
        message = {
            "message_id": "test789",
            "text": "https://example.com/article",
            "sender_name": "测试发送者",
            "chat_title": "测试聊天"
        }
        
        result = await self.preprocessor.process(message)
        
        assert result["success"] is True
        assert result["content_format"] == "url_only"
        assert len(result["urls"]) == 1
        assert result["valid_urls"][0] == "https://example.com/article"
    
    @pytest.mark.asyncio
    async def test_process_empty_message(self):
        """测试处理空消息"""
        message = {
            "message_id": "test000",
            "text": "",
            "sender_name": "测试发送者",
            "chat_title": "测试聊天"
        }
        
        result = await self.preprocessor.process(message)
        
        assert result["success"] is False
        assert "消息内容为空" in result["error"]


class TestContentFetcher:
    """测试内容获取器类"""
    
    def setup_method(self):
        """设置测试环境"""
        self.content_fetcher = ContentFetcher(timeout=1, max_retries=0)
    
    def teardown_method(self):
        """清理测试环境"""
        asyncio.run(self.content_fetcher.close())
    
    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession.get")
    async def test_fetch_generic(self, mock_get):
        """测试获取通用网页内容"""
        # 设置模拟响应
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.headers = {"Content-Type": "text/html"}
        mock_response.text.return_value = """
        <html>
            <head><title>测试页面</title></head>
            <body>
                <main>
                    <h1>测试内容</h1>
                    <p>这是一个测试段落。</p>
                </main>
            </body>
        </html>
        """
        
        # 设置模拟会话get方法返回值
        mock_get.return_value.__aenter__.return_value = mock_response
        
        # 运行测试
        urls = ["https://example.com/test"]
        results = await self.content_fetcher.fetch(urls)
        
        # 验证结果
        assert len(results) == 1
        result = results[0]
        assert result["success"] is True
        assert result["url"] == urls[0]
        assert "测试内容" in result["content"]
        assert "测试段落" in result["content"]
        assert result["title"] == "测试页面"
        assert result["type"] == "html"
    
    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession.get")
    async def test_fetch_error(self, mock_get):
        """测试获取内容失败的情况"""
        # 设置模拟错误
        mock_get.side_effect = Exception("测试错误")
        
        # 运行测试
        urls = ["https://example.com/error"]
        results = await self.content_fetcher.fetch(urls)
        
        # 验证结果
        assert len(results) == 1
        result = results[0]
        assert result["success"] is False
        assert result["url"] == urls[0]
        assert "测试错误" in result["error"]
        assert result["content"] == ""
        assert result["type"] == "error"
    
    @pytest.mark.asyncio
    async def test_fetch_empty_urls(self):
        """测试空URL列表"""
        results = await self.content_fetcher.fetch([])
        assert results == []


class TestContentAssembler:
    """测试内容组装器类"""
    
    def setup_method(self):
        """设置测试环境"""
        self.content_assembler = ContentAssembler(
            max_content_length=500,
            max_total_length=1000,
            format_type="markdown"
        )
    
    def test_assemble_text_only(self):
        """测试组装纯文本内容"""
        preprocessed_data = {
            "original_message": {
                "message_id": "test123",
                "sender_name": "测试发送者",
                "chat_title": "测试聊天"
            },
            "text_content": "这是一个测试消息",
            "content_format": "text_only",
            "valid_urls": [],
            "metadata": {
                "lang_hint": "zh",
                "has_hashtags": False,
                "has_mentions": False
            }
        }
        
        result = self.content_assembler.assemble(preprocessed_data)
        
        assert "## 原始消息" in result["content"]
        assert "这是一个测试消息" in result["content"]
        assert result["content_format"] == "text_only"
        assert result["has_web_content"] is False
    
    def test_assemble_text_with_url(self):
        """测试组装文本+URL内容"""
        preprocessed_data = {
            "original_message": {
                "message_id": "test456",
                "sender_name": "测试发送者",
                "chat_title": "测试聊天"
            },
            "text_content": "这是带链接的消息: https://example.com",
            "content_format": "text_with_url",
            "valid_urls": ["https://example.com"],
            "metadata": {
                "lang_hint": "zh",
                "has_hashtags": False,
                "has_mentions": False
            }
        }
        
        web_contents = [{
            "url": "https://example.com",
            "success": True,
            "content": "这是示例网页内容",
            "title": "示例网页",
            "type": "html"
        }]
        
        result = self.content_assembler.assemble(preprocessed_data, web_contents)
        
        assert "## 原始消息" in result["content"]
        assert "这是带链接的消息" in result["content"]
        assert "### 网页 1: 示例网页" in result["content"]
        assert "这是示例网页内容" in result["content"]
        assert result["content_format"] == "text_with_url"
        assert result["has_web_content"] is True
    
    def test_assemble_url_only(self):
        """测试组装纯URL内容"""
        preprocessed_data = {
            "original_message": {
                "message_id": "test789",
                "sender_name": "测试发送者",
                "chat_title": "测试聊天"
            },
            "text_content": "https://example.com",
            "content_format": "url_only",
            "valid_urls": ["https://example.com"],
            "metadata": {
                "lang_hint": "unknown",
                "has_hashtags": False,
                "has_mentions": False
            }
        }
        
        web_contents = [{
            "url": "https://example.com",
            "success": True,
            "content": "这是示例网页内容",
            "title": "示例网页",
            "type": "html"
        }]
        
        result = self.content_assembler.assemble(preprocessed_data, web_contents)
        
        assert "## 链接内容" in result["content"]
        assert "### 网页 1: 示例网页" in result["content"]
        assert "这是示例网页内容" in result["content"]
        assert "## 原始链接" in result["content"]
        assert "https://example.com" in result["content"]
        assert result["content_format"] == "url_only"
        assert result["has_web_content"] is True 