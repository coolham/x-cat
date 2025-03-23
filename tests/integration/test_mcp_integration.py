"""
MCP服务架构集成测试
测试整个内容分析管道集成功能
"""
import pytest
import os
import json
from unittest.mock import patch, MagicMock, AsyncMock

from app.processors.preprocessor import PreProcessor
from app.processors.content_fetcher import ContentFetcher
from app.processors.content_assembler import ContentAssembler
from app.analyzers.content_analyzer import ContentAnalyzer
from app.services.mcp_service import ContentAnalysisMCPService


@pytest.mark.integration
class TestMCPIntegration:
    """测试MCP服务集成功能"""
    
    @pytest.fixture
    def api_key(self):
        """获取API密钥"""
        # 从环境变量获取API密钥
        api_key = os.environ.get("TEST_API_KEY")
        if not api_key:
            pytest.skip("需要设置TEST_API_KEY环境变量")
        return api_key
    
    @pytest.fixture
    def proxy_url(self):
        """获取代理URL"""
        return os.environ.get("TEST_PROXY_URL")
    
    @pytest.fixture
    async def mcp_service(self, api_key, proxy_url):
        """创建MCP服务实例"""
        service = ContentAnalysisMCPService(
            api_key=api_key,
            provider="openrouter",  # 使用OpenRouter作为默认提供商
            model=None,  # 使用默认模型
            proxy_url=proxy_url,
            max_tokens=1000,
            temperature=0.7,
            max_content_length=1000,  # 较小的内容长度，用于测试
            max_total_length=2000,    # 较小的总长度，用于测试
            max_urls=2,               # 较小的URL数量，用于测试
            format_type="markdown"
        )
        
        yield service
        
        # 测试后清理
        await service.close()
    
    @pytest.mark.asyncio
    async def test_text_only_message_integration(self, mcp_service):
        """测试纯文本消息集成处理"""
        # 创建测试消息
        message = {
            "message_id": "integration_test_1",
            "text": "这是一条集成测试消息，测试内容分析服务的端到端功能。",
            "sender_name": "集成测试",
            "chat_title": "测试聊天"
        }
        
        # 处理消息
        result = await mcp_service.process(message)
        
        # 验证基本结果
        assert result["success"] is True
        assert "content_type" in result
        assert "category" in result
        assert "sentiment" in result
        assert "keywords" in result
        assert isinstance(result["keywords"], list)
        assert "summary" in result
        assert "language" in result
        assert "processing" in result
        assert "duration" in result["processing"]
    
    @pytest.mark.asyncio
    @patch('app.processors.content_fetcher.ContentFetcher.fetch')
    async def test_message_with_url_integration(self, mock_fetch, mcp_service):
        """测试带URL的消息集成处理"""
        # 模拟网页内容获取
        mock_fetch.return_value = [{
            "url": "https://example.com",
            "success": True,
            "content": "这是一个示例网页内容，用于测试带URL的消息处理。",
            "title": "示例网页",
            "type": "html"
        }]
        
        # 创建测试消息
        message = {
            "message_id": "integration_test_2",
            "text": "这是带链接的测试消息: https://example.com",
            "sender_name": "集成测试",
            "chat_title": "测试聊天"
        }
        
        # 处理消息
        result = await mcp_service.process(message)
        
        # 验证基本结果
        assert result["success"] is True
        assert "content_type" in result
        assert "category" in result
        assert "sentiment" in result
        assert "keywords" in result
        assert "summary" in result
        assert "urls" in result
        assert "https://example.com" in result["urls"]
        assert "processing" in result
        assert "urls_processed" in result["processing"]
        assert result["processing"]["urls_processed"] == 1
    
    @pytest.mark.asyncio
    async def test_empty_message_integration(self, mcp_service):
        """测试空消息集成处理"""
        # 创建测试消息
        message = {
            "message_id": "integration_test_3",
            "text": "",
            "sender_name": "集成测试",
            "chat_title": "测试聊天"
        }
        
        # 处理消息
        result = await mcp_service.process(message)
        
        # 验证结果
        assert result["success"] is False
        assert "error" in result
        assert "消息内容为空" in result["error"]
    
    @pytest.mark.asyncio
    async def test_long_message_integration(self, mcp_service):
        """测试长消息集成处理"""
        # 创建长测试消息
        long_text = "测试" * 1000  # 足够长的消息，以测试截断功能
        
        message = {
            "message_id": "integration_test_4",
            "text": long_text,
            "sender_name": "集成测试",
            "chat_title": "测试聊天"
        }
        
        # 处理消息
        result = await mcp_service.process(message)
        
        # 验证结果
        assert result["success"] is True
        assert "content_type" in result
        assert "category" in result
        assert "summary" in result  # 应该能够提供摘要
        
        # 检查处理时间，长消息处理可能需要更多时间
        assert "processing" in result
        assert "duration" in result["processing"] 