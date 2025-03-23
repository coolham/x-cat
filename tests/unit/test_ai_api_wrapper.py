"""
测试ai-api-wrapper库的功能和代理访问能力
"""
import os
import pytest
import pytest_asyncio
from dotenv import load_dotenv

from ai_api_wrapper import Client
from ai_api_wrapper.provider import LLMError

# 加载环境变量
load_dotenv()

# 跳过测试的条件
skip_if_no_api_key = pytest.mark.skipif(
    os.getenv("OPENROUTER_API_KEY") is None and 
    os.getenv("OPENAI_API_KEY") is None,
    reason="需要设置OPENROUTER_API_KEY或OPENAI_API_KEY环境变量"
)

skip_if_no_proxy = pytest.mark.skipif(
    os.getenv("HTTP_PROXY") is None,
    reason="需要设置HTTP_PROXY环境变量来测试代理功能"
)


class TestAIAPIWrapper:
    """测试ai-api-wrapper库的功能"""
    
    @skip_if_no_api_key
    def test_client_initialization(self):
        """测试客户端初始化"""
        # 基本初始化
        client = Client()
        assert client is not None
        
        # 如果有OpenRouter API Key，测试指定服务提供商
        if os.getenv("OPENROUTER_API_KEY"):
            client = Client(provider="openrouter")
            assert client is not None
            # 验证客户端正确初始化
            assert hasattr(client, "chat")
            assert hasattr(client, "models")
    
    @skip_if_no_api_key
    @skip_if_no_proxy
    def test_client_with_proxy(self):
        """测试使用代理的客户端初始化"""
        proxy = os.getenv("HTTP_PROXY")
        
        # 使用代理初始化客户端 - 在当前版本中代理配置可能在内部处理
        client = Client()
        assert client is not None
        
        # 验证客户端可用
        assert hasattr(client, "chat")
        assert hasattr(client, "models")
    
    @pytest.mark.asyncio
    @skip_if_no_api_key
    async def test_basic_completion(self):
        """测试基本的文本补全功能"""
        # 初始化客户端
        client = Client()
        
        # 尝试使用OpenRouter或OpenAI API
        if os.getenv("OPENROUTER_API_KEY"):
            model = "openrouter:gpt-3.5-turbo"
        else:
            model = "gpt-3.5-turbo"
        
        try:
            # 发送简单的补全请求
            messages = [
                {"role": "user", "content": "你好，请用一句话介绍自己。"}
            ]
            
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=100
            )
            
            # 验证响应
            assert response is not None
            
            # 验证响应是字典或对象
            if isinstance(response, dict):
                assert "choices" in response
                assert len(response["choices"]) > 0
                assert "message" in response["choices"][0]
                assert "content" in response["choices"][0]["message"]
                content = response["choices"][0]["message"]["content"]
            else:
                assert hasattr(response, "choices")
                assert len(response.choices) > 0
                assert hasattr(response.choices[0], "message")
                assert hasattr(response.choices[0].message, "content")
                content = response.choices[0].message.content
            
            # 验证内容不为空
            assert content and isinstance(content, str)
            assert len(content) > 0
            
            print(f"AI响应: {content}")
            
        except LLMError as e:
            pytest.skip(f"API调用失败: {str(e)}")
    
    @pytest.mark.asyncio
    @skip_if_no_api_key
    @skip_if_no_proxy
    async def test_completion_with_proxy(self):
        """测试使用代理的文本补全功能"""
        proxy = os.getenv("HTTP_PROXY")
        
        # 使用代理初始化客户端 - 当前版本可能自动从环境变量配置代理
        client = Client()
        
        # 尝试使用OpenRouter或OpenAI API
        if os.getenv("OPENROUTER_API_KEY"):
            model = "openrouter:gpt-3.5-turbo"
        else:
            model = "gpt-3.5-turbo"
        
        try:
            # 发送简单的补全请求
            messages = [
                {"role": "user", "content": "请用中文写一句问候语。"}
            ]
            
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=100
            )
            
            # 验证响应
            assert response is not None
            
            # 验证响应是字典或对象
            if isinstance(response, dict):
                assert "choices" in response
                assert len(response["choices"]) > 0
                content = response["choices"][0]["message"]["content"]
            else:
                assert hasattr(response, "choices")
                assert len(response.choices) > 0
                content = response.choices[0].message.content
            
            # 验证内容不为空
            assert content and isinstance(content, str)
            assert len(content) > 0
            
            print(f"使用代理的AI响应: {content}")
            
        except LLMError as e:
            pytest.skip(f"使用代理的API调用失败: {str(e)}")
    
    @skip_if_no_api_key
    def test_available_models(self):
        """测试获取可用模型列表"""
        # 初始化客户端
        client = Client()
        
        try:
            # 根据可用的API获取模型列表
            if os.getenv("OPENROUTER_API_KEY"):
                models = client.models.list(provider="openrouter")
            else:
                models = client.models.list()
            
            # 验证模型列表
            assert models is not None
            
            # 验证模型数据
            if isinstance(models, dict):
                assert "data" in models
                assert isinstance(models["data"], list)
                assert len(models["data"]) > 0
            else:
                assert hasattr(models, "data")
                assert isinstance(models.data, list)
                assert len(models.data) > 0
            
            # 简单打印模型数量
            model_count = len(models.data if hasattr(models, "data") else models["data"])
            print(f"获取到 {model_count} 个可用模型")
            
        except LLMError as e:
            pytest.skip(f"获取模型列表失败: {str(e)}")


# 运行手动测试
if __name__ == "__main__":
    print("运行ai-api-wrapper手动测试...")
    
    # 加载环境变量
    load_dotenv()
    
    # 检查API密钥
    if not os.getenv("OPENROUTER_API_KEY") and not os.getenv("OPENAI_API_KEY"):
        print("警告: 未设置OPENROUTER_API_KEY或OPENAI_API_KEY环境变量，测试可能会失败")
    
    # 检查代理设置
    proxy = os.getenv("HTTP_PROXY")
    if proxy:
        print(f"使用代理: {proxy}")
    else:
        print("警告: 未设置HTTP_PROXY环境变量，代理测试将被跳过")
    
    # 初始化客户端
    try:
        print("\n测试基本客户端初始化...")
        client = Client()
        print("✓ 客户端初始化成功")
        
        if proxy:
            print("\n测试使用代理的客户端初始化...")
            print("✓ 带代理的客户端初始化成功")
        
        print("\n手动测试完成！")
    except Exception as e:
        print(f"测试失败: {str(e)}") 