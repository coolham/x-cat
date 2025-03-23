"""
内容分析器集成测试
测试内容分析器在系统中的集成功能
"""
import os
import sys
import json
import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# 检查必要依赖是否可用
pytest.importorskip("app.core.runtime")
pytest.importorskip("app.analyzers.content_analyzer_module")
pytest.importorskip("app.storage.storage_module")
pytest.importorskip("app.services.mcp_service")

from app.core import Event
from app.core.runtime import Runtime
from app.core.module import ModuleState
from app.analyzers.content_analyzer_module import ContentAnalyzerModule
from app.storage.storage_module import StorageModule
from app.services.mcp_service import ContentAnalysisMCPService
from app.analyzers.content_analyzer import ContentAnalyzer
from app.analyzers.ai_client import AIClient

# 用于测试的类
class MockStorage:
    """模拟存储模块"""
    def __init__(self, runtime, module_id):
        self.runtime = runtime
        self.module_id = module_id
        self.analyzed_messages = {}
        self.state = ModuleState.RUNNING
        self.has_analysis_calls = []
        self.store_analysis_calls = []

    async def get_analysis_by_message_id(self, message_id):
        return self.analyzed_messages.get(message_id)

    async def set_message_analyzed(self, message_id, analysis_result):
        self.analyzed_messages[message_id] = analysis_result
        return True
        
    async def has_analysis(self, message_id):
        """记录调用并返回是否已分析"""
        self.has_analysis_calls.append(message_id)
        return message_id in self.analyzed_messages
    
    async def store_analysis(self, message_id, analysis):
        """记录调用并存储分析结果"""
        self.store_analysis_calls.append((message_id, analysis))
        self.analyzed_messages[message_id] = analysis

    async def initialize(self, config):
        return True

    async def start(self):
        return True

    async def stop(self):
        return True

    async def health_check(self):
        return True


@pytest.mark.asyncio
async def test_content_analyzer_integration(mock_mcp_service_class=None):
    """测试内容分析器模块集成"""
    # 如果没有提供mock，则创建一个
    if mock_mcp_service_class is None:
        mock_mcp_service_class = MagicMock()
        mock_instance = AsyncMock()
        mock_instance.process = AsyncMock()
        mock_instance.process.return_value = {
            "success": True,
            "content_type": "文章",
            "category": "技术",
            "subcategory": "人工智能",
            "sentiment": "积极",
            "keywords": ["AI", "分析", "测试", "集成"],
            "summary": "这是一个测试分析的摘要内容",
            "language": "中文",
            "urls": []
        }
        mock_mcp_service_class.return_value = mock_instance
        
        # 使用补丁
        with patch('app.analyzers.content_analyzer_module.ContentAnalysisMCPService', mock_mcp_service_class):
            return await _test_content_analyzer_integration(mock_mcp_service_class)
    else:
        return await _test_content_analyzer_integration(mock_mcp_service_class)


async def _test_content_analyzer_integration(mock_mcp_service_class):
    """测试内容分析器模块集成的实际实现"""
    # 创建MCP服务实例的模拟
    mock_mcp_instance = mock_mcp_service_class.return_value
    
    # 创建配置
    config = {
        "content_analyzer": {
            "api_key": "test_key",
            "provider": "test_provider",
            "model": "test_model",
            "max_tokens": 1000,
            "temperature": 0.5
        }
    }
    
    # 创建运行时环境
    runtime = Runtime()
    
    # 初始化事件订阅系统
    if not hasattr(runtime, 'event_subscribers'):
        runtime.event_subscribers = {}
    
    # 创建模拟存储模块
    storage = MockStorage(runtime, "storage")
    runtime.modules["storage"] = storage
    
    # 创建内容分析器模块
    content_analyzer = ContentAnalyzerModule(runtime, "content_analyzer")
    
    # 初始化和启动内容分析器模块
    await content_analyzer.initialize(config)
    await content_analyzer.start()
    
    # 确认模块状态
    assert content_analyzer.state == ModuleState.RUNNING
    
    # 创建测试消息
    test_message = {
        "message_id": "test123",
        "text": "这是一个测试消息",
        "sender_name": "测试发送者",
        "chat_title": "测试聊天"
    }
    
    # 发布新消息事件
    event = Event("new_message", None, test_message)
    await runtime.publish_event(event)
    
    # 等待事件处理完成
    await asyncio.sleep(0.1)
    
    # 确认MCP服务的process方法被调用
    mock_mcp_instance.process.assert_called_once_with(test_message)
    
    # 停止模块
    await content_analyzer.stop()


@pytest.mark.asyncio
async def test_content_analyzer_skips_analyzed_messages(mock_mcp_service_class=None):
    """测试内容分析器跳过已分析的消息"""
    # 如果没有提供mock，则创建一个
    if mock_mcp_service_class is None:
        mock_mcp_service_class = MagicMock()
        mock_instance = AsyncMock()
        mock_instance.process = AsyncMock()
        mock_instance.process.return_value = {
            "success": True,
            "content_type": "文章",
            "category": "技术",
            "summary": "这是一个测试摘要"
        }
        mock_mcp_service_class.return_value = mock_instance
        
        # 使用补丁
        with patch('app.analyzers.content_analyzer_module.ContentAnalysisMCPService', mock_mcp_service_class):
            return await _test_content_analyzer_skips_analyzed_messages(mock_mcp_service_class)
    else:
        return await _test_content_analyzer_skips_analyzed_messages(mock_mcp_service_class)


async def _test_content_analyzer_skips_analyzed_messages(mock_mcp_service_class):
    """测试内容分析器跳过已分析的消息的实际实现"""
    # 创建MCP服务实例的模拟
    mock_mcp_instance = mock_mcp_service_class.return_value
    
    # 创建配置
    config = {
        "content_analyzer": {
            "api_key": "test_key",
            "provider": "test_provider",
            "model": "test_model"
        }
    }
    
    # 创建运行时环境
    runtime = Runtime()
    
    # 初始化事件订阅系统
    if not hasattr(runtime, 'event_subscribers'):
        runtime.event_subscribers = {}
    
    # 创建内容分析器模块
    content_analyzer = ContentAnalyzerModule(runtime, "content_analyzer")
    
    # 创建模拟存储模块并设置已分析的消息
    storage = MockStorage(runtime, "storage")
    runtime.modules["storage"] = storage
    
    # 设置已分析的消息
    existing_message = {
        "message_id": "existing123",
        "text": "这是一个已分析的消息",
        "sender_name": "测试发送者",
        "chat_title": "测试聊天"
    }
    
    await storage.set_message_analyzed("existing123", {
        "success": True,
        "content_type": "文章",
        "summary": "已分析的消息摘要"
    })
    
    # 初始化和启动
    await content_analyzer.initialize(config)
    await content_analyzer.start()
    
    # 发布已分析的消息事件
    event = Event("new_message", None, existing_message)
    await runtime.publish_event(event)
    
    # 等待事件处理完成
    await asyncio.sleep(0.1)
    
    # 确认处理函数没有被调用（因为消息已经分析过）
    mock_mcp_instance.process.assert_not_called()
    
    # 创建新消息
    new_message = {
        "message_id": "new123",
        "text": "这是一个新消息",
        "sender_name": "测试发送者",
        "chat_title": "测试聊天"
    }
    
    # 发布新消息事件
    event = Event("new_message", None, new_message)
    await runtime.publish_event(event)
    
    # 等待事件处理完成
    await asyncio.sleep(0.1)
    
    # 确认处理函数被调用了一次，并且参数正确
    mock_mcp_instance.process.assert_called_once_with(new_message)
    
    # 停止模块
    await content_analyzer.stop()


@pytest.mark.asyncio
async def test_direct_analyze_message(mock_mcp_service_class=None):
    """测试直接分析消息功能"""
    # 如果没有提供mock，则创建一个
    if mock_mcp_service_class is None:
        mock_mcp_service_class = MagicMock()
        mock_instance = AsyncMock()
        mock_instance.process = AsyncMock()
        mock_instance.process.return_value = {
            "success": True,
            "content_type": "文章",
            "category": "技术",
            "summary": "这是一个直接分析的摘要"
        }
        mock_mcp_service_class.return_value = mock_instance
        
        # 使用补丁
        with patch('app.analyzers.content_analyzer_module.ContentAnalysisMCPService', mock_mcp_service_class):
            return await _test_direct_analyze_message(mock_mcp_service_class)
    else:
        return await _test_direct_analyze_message(mock_mcp_service_class)


async def _test_direct_analyze_message(mock_mcp_service_class):
    """测试直接分析消息功能的实际实现"""
    # 创建MCP服务实例的模拟
    mock_mcp_instance = mock_mcp_service_class.return_value
    
    # 创建配置
    config = {
        "content_analyzer": {
            "api_key": "test_key",
            "provider": "test_provider",
            "model": "test_model"
        }
    }
    
    # 创建运行时环境
    runtime = Runtime()
    
    # 初始化事件订阅系统
    if not hasattr(runtime, 'event_subscribers'):
        runtime.event_subscribers = {}
    
    # 创建内容分析器模块
    content_analyzer = ContentAnalyzerModule(runtime, "content_analyzer")
    
    # 添加模拟存储模块
    storage = MockStorage(runtime, "storage")
    runtime.modules["storage"] = storage
    
    # 初始化和启动
    await content_analyzer.initialize(config)
    await content_analyzer.start()
    
    # 创建测试消息
    test_message = {
        "message_id": "direct123",
        "text": "这是一个直接分析的消息",
        "sender_name": "测试发送者",
        "chat_title": "测试聊天"
    }
    
    # 直接调用分析方法
    result = await content_analyzer.analyze_message(test_message)
    
    # 验证结果
    assert result["success"] is True
    assert result["content_type"] == "文章"
    assert result["category"] == "技术"
    assert result["summary"] == "这是一个直接分析的摘要"
    
    # 验证调用
    mock_mcp_instance.process.assert_called_once_with(test_message)
    
    # 停止模块
    await content_analyzer.stop()


async def run_integration_tests():
    """运行所有集成测试"""
    print("\n===== 运行内容分析器集成测试 =====")
    
    try:
        # 为第一个测试创建mock
        mock_mcp_service1 = MagicMock()
        mock_instance1 = AsyncMock()
        mock_instance1.process = AsyncMock()
        mock_instance1.process.return_value = {
            "success": True,
            "content_type": "文章",
            "category": "技术",
            "summary": "这是测试摘要"
        }
        mock_mcp_service1.return_value = mock_instance1
        
        # 执行第一个测试
        with patch('app.analyzers.content_analyzer_module.ContentAnalysisMCPService', mock_mcp_service1):
            print("\n----- 测试内容分析器模块集成 -----")
            await test_content_analyzer_integration(mock_mcp_service1)
            print("✓ 测试通过: 内容分析器模块集成")
        
        # 为第二个测试创建mock
        mock_mcp_service2 = MagicMock()
        mock_instance2 = AsyncMock()
        mock_instance2.process = AsyncMock()
        mock_instance2.process.return_value = {
            "success": True,
            "content_type": "文章",
            "category": "技术",
            "summary": "这是测试摘要"
        }
        mock_mcp_service2.return_value = mock_instance2
            
        # 执行第二个测试
        with patch('app.analyzers.content_analyzer_module.ContentAnalysisMCPService', mock_mcp_service2):
            print("\n----- 测试内容分析器跳过已分析的消息 -----")
            await test_content_analyzer_skips_analyzed_messages(mock_mcp_service2)
            print("✓ 测试通过: 内容分析器跳过已分析的消息")
        
        # 为第三个测试创建mock
        mock_mcp_service3 = MagicMock()
        mock_instance3 = AsyncMock()
        mock_instance3.process = AsyncMock()
        mock_instance3.process.return_value = {
            "success": True,
            "content_type": "文章",
            "category": "技术",
            "summary": "这是一个直接分析的摘要"
        }
        mock_mcp_service3.return_value = mock_instance3
            
        # 执行第三个测试
        with patch('app.analyzers.content_analyzer_module.ContentAnalysisMCPService', mock_mcp_service3):
            print("\n----- 测试直接分析消息功能 -----")
            await test_direct_analyze_message(mock_mcp_service3)
            print("✓ 测试通过: 直接分析消息功能")
        
        print("\n===== 所有测试通过 =====")
        
    except Exception as e:
        print(f"\n✗ 测试失败: {str(e)}")
        import traceback
        print(traceback.format_exc())
        print("\n===== 测试失败 =====")


if __name__ == "__main__":
    asyncio.run(run_integration_tests())

