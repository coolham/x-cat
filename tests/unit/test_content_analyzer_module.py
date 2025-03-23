"""
测试内容分析器模块
包括ContentAnalyzerModule类的单元测试
"""
import pytest
import json
import os
import sys
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.analyzers.content_analyzer_module import ContentAnalyzerModule
from app.core.module import ModuleState, Event


class TestContentAnalyzerModule:
    """测试内容分析器模块类"""
    
    def setup_method(self):
        """设置测试环境"""
        # 创建模拟运行时环境
        self.mock_runtime = MagicMock()
        self.mock_event_bus = AsyncMock()
        self.mock_runtime.event_bus = self.mock_event_bus
        self.mock_event_bus.publish = AsyncMock()
        
        # 添加publish_event方法
        self.mock_runtime.publish_event = AsyncMock()
        
        # 创建模拟存储模块
        self.mock_storage = AsyncMock()
        self.mock_storage.has_analysis = AsyncMock(return_value=False)
        self.mock_storage.store_analysis = AsyncMock()
        self.mock_runtime.has_module.return_value = True
        self.mock_runtime.get_module.return_value = self.mock_storage
        
        # 创建MCP服务实例的模拟对象
        self.mock_mcp_service_instance = AsyncMock()
        self.mock_mcp_service_instance.close = AsyncMock()
        self.mock_mcp_service_instance.process = AsyncMock()
        
        # 模拟MCP服务类
        self.patcher = patch('app.analyzers.content_analyzer_module.ContentAnalysisMCPService', return_value=self.mock_mcp_service_instance)
        self.mock_mcp_service_class = self.patcher.start()
        
        # 初始化模块
        self.analyzer_module = ContentAnalyzerModule(self.mock_runtime)
    
    def teardown_method(self):
        """清理测试环境"""
        self.patcher.stop()
    
    @pytest.mark.asyncio
    async def test_initialize(self):
        """测试模块初始化"""
        # 创建配置
        config = {
            "content_analyzer": {
                "api_key": "test_key",
                "provider": "test_provider",
                "model": "test_model",
                "max_tokens": 1000,
                "temperature": 0.7,
                "max_content_length": 8000,
                "max_total_length": 15000,
                "max_urls": 3,
                "format_type": "markdown"
            }
        }
        
        # 执行初始化
        result = await self.analyzer_module.initialize(config)
        
        # 验证结果
        assert result is True
        assert self.analyzer_module.state == ModuleState.INITIALIZED
        assert self.analyzer_module.api_key == "test_key"
        assert self.analyzer_module.provider == "test_provider"
        assert self.analyzer_module.model == "test_model"
        
        # 验证MCP服务被正确初始化
        self.mock_mcp_service_class.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_initialize_with_top_level_config(self):
        """测试使用顶级配置进行初始化"""
        # 创建顶级配置
        config = {
            "api_key": "test_key",
            "provider": "test_provider",
            "model": "test_model",
            "max_tokens": 1000
        }
        
        # 执行初始化
        result = await self.analyzer_module.initialize(config)
        
        # 验证结果
        assert result is True
        assert self.analyzer_module.state == ModuleState.INITIALIZED
        assert self.analyzer_module.api_key == "test_key"
        assert self.analyzer_module.provider == "test_provider"
        assert self.analyzer_module.model == "test_model"
    
    @pytest.mark.asyncio
    async def test_start_and_stop(self):
        """测试模块启动和停止"""
        # 首先初始化模块
        config = {
            "content_analyzer": {
                "api_key": "test_key"
            }
        }
        await self.analyzer_module.initialize(config)
        
        # 测试启动
        result = await self.analyzer_module.start()
        assert result is True
        assert self.analyzer_module.state == ModuleState.RUNNING
        
        # 测试停止
        result = await self.analyzer_module.stop()
        assert result is True
        assert self.analyzer_module.state == ModuleState.STOPPED
        
        # 验证MCP服务被关闭
        self.mock_mcp_service_instance.close.assert_awaited_once()
    
    @pytest.mark.asyncio
    async def test_start_without_initialization(self):
        """测试未初始化就启动"""
        # 不先初始化模块
        result = await self.analyzer_module.start()
        assert result is False
        assert self.analyzer_module.state != ModuleState.RUNNING
    
    @pytest.mark.asyncio
    async def test_handle_new_message(self):
        """测试处理新消息"""
        # 首先初始化并启动模块
        config = {"content_analyzer": {"api_key": "test_key"}}
        await self.analyzer_module.initialize(config)
        await self.analyzer_module.start()
        
        # 创建测试消息
        message = {
            "message_id": "test123",
            "text": "这是一个测试消息",
            "sender_name": "测试发送者",
            "chat_title": "测试聊天"
        }
        
        # 创建事件对象
        event = Event("new_message", "test_module", message)
        
        # 设置模拟返回值
        self.mock_storage.has_analysis = AsyncMock(return_value=False)
        
        analysis_result = {
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
        self.mock_mcp_service_instance.process = AsyncMock(return_value=analysis_result)
        
        # 处理消息
        await self.analyzer_module.handle_new_message(event)
        
        # 验证存储和事件发布
        self.mock_storage.has_analysis.assert_awaited_with("test123")
        self.mock_storage.store_analysis.assert_awaited_once()
        self.mock_runtime.publish_event.assert_awaited_once()
        
        # 验证MCP服务被调用
        self.mock_mcp_service_instance.process.assert_awaited_once_with(message)
    
    @pytest.mark.asyncio
    async def test_skip_already_analyzed_message(self):
        """测试跳过已分析的消息"""
        # 首先初始化并启动模块
        config = {"content_analyzer": {"api_key": "test_key"}}
        await self.analyzer_module.initialize(config)
        await self.analyzer_module.start()
        
        # 创建测试消息
        message = {
            "message_id": "test456",
            "text": "这是一个已分析的消息",
            "sender_name": "测试发送者",
            "chat_title": "测试聊天"
        }
        
        # 创建事件对象
        event = Event("new_message", "test_module", message)
        
        # 设置消息已分析，使用AsyncMock确保可以被awaited
        self.mock_storage.has_analysis = AsyncMock(return_value=True)
        
        # 处理消息
        await self.analyzer_module.handle_new_message(event)
        
        # 验证MCP服务没有被调用
        self.mock_mcp_service_instance.process.assert_not_called()
        self.mock_storage.store_analysis.assert_not_called()
        self.mock_event_bus.publish.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_handle_message_when_not_running(self):
        """测试模块未运行时处理消息"""
        # 创建测试消息
        message = {
            "message_id": "test789",
            "text": "这是一个测试消息",
            "sender_name": "测试发送者",
            "chat_title": "测试聊天"
        }
        
        # 创建事件对象
        event = Event("new_message", "test_module", message)
        
        # 不初始化和启动模块
        
        # 处理消息
        await self.analyzer_module.handle_new_message(event)
        
        # 验证MCP服务没有被调用
        self.mock_mcp_service_instance.process.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_analyze_message_direct(self):
        """测试直接分析消息"""
        # 首先初始化并启动模块
        config = {"content_analyzer": {"api_key": "test_key"}}
        await self.analyzer_module.initialize(config)
        await self.analyzer_module.start()
        
        # 创建测试消息
        message = {
            "message_id": "test999",
            "text": "这是一个直接分析的消息",
            "sender_name": "测试发送者",
            "chat_title": "测试聊天"
        }
        
        # 设置模拟返回值，使用AsyncMock确保可以被awaited
        mock_result = {
            "success": True,
            "content_type": "文本",
            "category": "聊天",
            "subcategory": "一般对话",
            "sentiment": "中性",
            "keywords": ["测试", "消息", "直接", "分析"],
            "summary": "一个需要直接分析的测试消息",
            "language": "zh",
            "urls": []
        }
        self.mock_mcp_service_instance.process = AsyncMock(return_value=mock_result)
        
        # 执行直接分析
        # 不需要重置mock，因为我们已经创建了新的AsyncMock
        
        result = await self.analyzer_module.analyze_message(message)
        
        # 验证MCP服务被调用
        self.mock_mcp_service_instance.process.assert_awaited_once_with(message)
        
        # 由于我们正确模拟了process方法，此处不应该有实际API调用
        # 因此测试结果应该与mock_result相同
        assert result == mock_result


if __name__ == "__main__":
    async def run_tests():
        """直接运行测试函数"""
        # 创建日志文件
        with open("content_analyzer_test_results.log", "w", encoding="utf-8") as log_file:
            def log(msg):
                print(msg)
                log_file.write(msg + "\n")
                log_file.flush()
                
            log("===== 直接运行内容分析器测试 =====")
            
            # 创建测试实例
            test = TestContentAnalyzerModule()
            
            # 测试函数列表
            test_functions = [
                ("test_initialize", test.test_initialize),
                ("test_initialize_with_top_level_config", test.test_initialize_with_top_level_config),
                ("test_start_and_stop", test.test_start_and_stop),
                ("test_start_without_initialization", test.test_start_without_initialization),
                ("test_handle_new_message", test.test_handle_new_message),
                ("test_skip_already_analyzed_message", test.test_skip_already_analyzed_message),
                ("test_handle_message_when_not_running", test.test_handle_message_when_not_running),
                ("test_analyze_message_direct", test.test_analyze_message_direct)
            ]
            
            # 追踪测试结果
            passed = 0
            failed = 0
            failures = []
            
            # 执行每个测试
            for test_name, test_func in test_functions:
                log(f"\n----- 测试 {test_name} -----")
                
                # 每个测试前重新设置环境
                test.setup_method()
                
                try:
                    # 执行测试
                    await test_func()
                    log(f"✓ 测试通过")
                    passed += 1
                except Exception as e:
                    log(f"✗ 测试失败: {str(e)}")
                    import traceback
                    error_trace = traceback.format_exc()
                    log(error_trace)
                    failed += 1
                    failures.append(test_name)
                finally:
                    # 每个测试后清理环境
                    test.teardown_method()
            
            # 打印测试结果摘要
            log("\n===== 测试结果摘要 =====")
            log(f"通过: {passed}")
            log(f"失败: {failed}")
            if failures:
                log(f"失败的测试: {', '.join(failures)}")
                log("\n===== 测试失败 =====")
            else:
                log("\n===== 所有测试通过 =====")
            
            log("\n测试完成，详细结果已保存到文件: content_analyzer_test_results.log")

    # 运行测试
    asyncio.run(run_tests())
    

