"""
测试AI内容分析模块
包括ContentAnalyzer类的单元测试
"""
import pytest
import json
import os
import sys
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.analyzers.content_analyzer import ContentAnalyzer
from app.analyzers.ai_client import AIClient


class TestContentAnalyzer:
    """测试内容分析器类"""
    
    def setup_method(self):
        """设置测试环境"""
        # 使用模拟AIClient初始化
        with patch('app.analyzers.content_analyzer.AIClient') as mock_ai_client:
            self.mock_ai_client_instance = MagicMock()
            mock_ai_client.return_value = self.mock_ai_client_instance
            
            # 修复：将analyze方法设置为异步模拟对象
            self.mock_ai_client_instance.analyze = AsyncMock()
            
            self.content_analyzer = ContentAnalyzer(
                api_key="test_key",
                provider="test_provider",
                model="test_model",
                max_tokens=500,
                temperature=0.5
            )
    
    @pytest.mark.asyncio
    async def test_analyze_success(self):
        """测试成功分析内容"""
        # 创建测试内容
        assembled_content = {
            "content": "这是一个测试内容，包含一个URL：https://example.com",
            "metadata": {
                "message_id": "test123",
                "sender_name": "测试发送者",
                "chat_title": "测试聊天"
            },
            "urls": ["https://example.com"],
            "content_format": "text_with_url",
            "has_web_content": True
        }
        
        # 模拟AIClient.analyze方法的成功返回
        mock_result = {
            "content_type": "文章",
            "category": "技术",
            "subcategory": "测试",
            "sentiment": "中性",
            "keywords": ["测试", "URL", "示例"],
            "summary": "这是一个测试内容，包含一个URL链接到example.com",
            "language": "zh",
            "urls": ["https://example.com"]
        }
        self.mock_ai_client_instance.analyze.return_value = (True, mock_result)
        
        # 执行测试
        result = await self.content_analyzer.analyze(assembled_content)
        
        # 验证结果
        assert result["success"] is True
        assert result["content_type"] == "文章"
        assert result["category"] == "技术"
        assert result["subcategory"] == "测试"
        assert result["sentiment"] == "中性"
        assert "测试" in result["keywords"]
        assert result["language"] == "zh"
        assert "https://example.com" in result["urls"]
        assert result["source"]["message_id"] == "test123"
        
        # 验证AIClient.analyze被正确调用
        self.mock_ai_client_instance.analyze.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_analyze_failure(self):
        """测试分析失败的情况"""
        # 创建测试内容
        assembled_content = {
            "content": "测试内容",
            "metadata": {},
            "urls": [],
            "content_format": "text_only",
            "has_web_content": False
        }
        
        # 模拟AIClient.analyze方法的失败返回
        error_result = {"error": "API调用失败"}
        self.mock_ai_client_instance.analyze.return_value = (False, error_result)
        
        # 执行测试
        result = await self.content_analyzer.analyze(assembled_content)
        
        # 验证结果
        assert result["success"] is False
        assert "API调用失败" in result["error"]
    
    @pytest.mark.asyncio
    async def test_analyze_empty_content(self):
        """测试空内容的情况"""
        # 创建测试内容
        assembled_content = {
            "content": "",
            "metadata": {},
            "urls": [],
            "content_format": "text_only",
            "has_web_content": False
        }
        
        # 执行测试
        result = await self.content_analyzer.analyze(assembled_content)
        
        # 验证结果
        assert result["success"] is False
        assert "内容为空" in result["error"]
        
        # 验证AIClient.analyze没有被调用
        self.mock_ai_client_instance.analyze.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_ensure_result_fields(self):
        """测试确保结果字段完整的功能"""
        # 创建不完整的结果字典
        incomplete_result = {
            "content_type": "文章",
            "category": "技术"
            # 缺少其他必要字段
        }
        
        # 模拟AIClient.analyze返回不完整的结果
        self.mock_ai_client_instance.analyze.return_value = (True, incomplete_result)
        
        # 创建测试内容
        assembled_content = {
            "content": "测试内容",
            "metadata": {},
            "urls": [],
            "content_format": "text_only",
            "has_web_content": False
        }
        
        # 执行测试
        result = await self.content_analyzer.analyze(assembled_content)
        
        # 验证结果包含所有必要字段
        assert result["success"] is True
        assert "subcategory" in result
        assert "sentiment" in result
        assert "keywords" in result
        assert isinstance(result["keywords"], list)
        assert "summary" in result
        assert "language" in result
        assert "urls" in result
        assert isinstance(result["urls"], list) 

    
if __name__ == "__main__":
    async def run_tests():
        """直接运行测试函数"""
        print("===== 直接运行内容分析器测试 =====")
        # 创建测试实例
        test = TestContentAnalyzer()
        
        # 设置测试环境
        test.setup_method()
        
        try:
            # 运行所有测试方法
            print("\n----- 测试成功分析内容 -----")
            await test.test_analyze_success()
            print("✓ 测试通过")
            
            print("\n----- 测试分析失败情况 -----")
            await test.test_analyze_failure()
            print("✓ 测试通过")
            
            print("\n----- 测试空内容分析 -----")
            await test.test_analyze_empty_content()
            print("✓ 测试通过")
            
            print("\n----- 测试结果字段完整性 -----")
            await test.test_ensure_result_fields()
            print("✓ 测试通过")
            
            print("\n===== 所有测试通过 =====")
        except AssertionError as e:
            print(f"✗ 测试失败: {e}")
        except Exception as e:
            print(f"✗ 运行出错: {e}")
            import traceback
            traceback.print_exc()
    
    # 运行测试
    asyncio.run(run_tests())

