"""
测试AI客户端模块
"""
import os
import sys
import asyncio
import json
import traceback
from dotenv import load_dotenv

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.analyzers.ai_client import AIClient
from app.processors.content_extractor import ContentExtractor
from loguru import logger

# 加载环境变量
load_dotenv()

async def test_ai_client_basic():
    """测试AI客户端基本功能"""
    print("\n=== 测试AI客户端基本功能 ===")
    
    # 检查API密钥
    deepseek_key = os.getenv("DEEPSEEK_API_KEY")
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    
    print(f"API密钥状态:")
    print(f"- OpenAI: {'已配置' if openai_key else '未配置'}")
    print(f"- OpenRouter: {'已配置' if openrouter_key else '未配置'}")
    print(f"- DeepSeek: {'已配置' if deepseek_key else '未配置'}")
    
    if not openai_key and not deepseek_key and not openrouter_key:
        print("跳过AI测试: 未设置任何API密钥")
        return
    
    # 确定使用哪个提供商和密钥
    if openrouter_key:
        provider = "openrouter"
        api_key = openrouter_key
    elif deepseek_key:
        provider = "deepseek"
        api_key = deepseek_key
    else:
        provider = "openai"
        api_key = openai_key
    
    print(f"使用提供商: {provider}")
    
    # 获取环境变量中的代理设置
    proxy_url = os.getenv("HTTP_PROXY", os.getenv("HTTPS_PROXY"))
    if proxy_url:
        print(f"当前环境变量中的代理设置: {proxy_url}")
    
    # 初始化客户端
    try:
        client = AIClient(
            api_key=api_key,
            provider=provider,
            proxy_url=proxy_url
        )
    except Exception as e:
        print(f"AI客户端初始化失败: {str(e)}")
        traceback.print_exc()
        return
    
    # 简单的分析请求
    system_prompt = """
    你是一个内容分析专家。请分析用户提供的文本，并返回以下格式的JSON：
    {
        "content_type": "文章/问答/广告/新闻/其他",
        "category": "主题分类（如技术、健康、娱乐等）",
        "sentiment": "情感倾向（积极/消极/中性）",
        "keywords": ["关键词1", "关键词2", "关键词3"],
        "summary": "50字以内的内容摘要"
    }
    """
    
    content = """
    Python是一种广泛使用的解释型、高级编程语言。Python的设计强调代码的可读性，它的语法允许程序员用更少的代码表达想法。
    Python支持多种编程范式，包括面向对象、命令式、函数式和过程式编程。它拥有动态类型系统和垃圾回收功能，能够自动管理内存使用。
    近年来，Python在人工智能、数据科学和Web开发领域的应用越来越广泛，成为最受欢迎的编程语言之一。
    """
    
    print(f"\n正在使用{client.model}模型发送分析请求...")
    try:
        success, result = await client.analyze(content, system_prompt)
        
        if success:
            print("\n分析成功！结果:")
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"\n分析失败: {result.get('error', '未知错误')}")
            if "raw_content" in result:
                print(f"\n原始内容预览: {result['raw_content'][:200]}...")
    except Exception as e:
        print(f"\n发生错误: {str(e)}")
        traceback.print_exc()
    
    # 关闭客户端
    try:
        await client.close()
    except Exception as e:
        print(f"关闭客户端时出错: {str(e)}")

async def test_content_extraction():
    """测试内容提取器"""
    print("\n=== 测试内容提取器 ===")
    
    # 初始化内容提取器
    proxy_url = os.getenv("HTTP_PROXY", os.getenv("HTTPS_PROXY"))
    extractor = ContentExtractor(proxy_url=proxy_url)
    
    # 测试从网页提取内容
    url = "https://www.python.org/about/"
    print(f"正在从URL提取内容: {url}")
    
    success, result = await extractor.extract_from_url(url)
    
    if success:
        print("\n提取成功！")
        print(f"标题: {result.get('title')}")
        print(f"内容长度: {len(result.get('content', ''))}字符")
        print(f"内容预览: {result.get('content', '')[:200]}...")
    else:
        print(f"\n提取失败: {result.get('error', '未知错误')}")
    
    # 测试从文本提取URL
    text = "请访问 https://www.python.org 和 https://github.com 获取更多信息。"
    urls = extractor.extract_urls_from_text(text)
    
    print("\n从文本提取URL:")
    for url in urls:
        print(f"- {url}")
    
    # 关闭提取器
    await extractor.close()

async def main():
    """主函数"""
    print("开始测试内容提取和AI分析模块...\n")
    
    # 测试内容提取器
    await test_content_extraction()
    
    # 始终尝试测试AI客户端，会在函数内部检查API密钥
    await test_ai_client_basic()
    
    print("\n测试完成！")

if __name__ == "__main__":
    asyncio.run(main()) 