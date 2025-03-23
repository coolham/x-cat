"""
测试内容分析器模块
"""
import os
import sys
import asyncio
import json
import traceback
from dotenv import load_dotenv

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    print("正在导入ContentAnalyzer...")
    from app.analyzers.content_analyzer import ContentAnalyzer
    print("导入ContentAnalyzer成功")
except Exception as e:
    print(f"导入ContentAnalyzer失败: {str(e)}")
    traceback.print_exc()
    sys.exit(1)

try:
    from loguru import logger
except Exception as e:
    print(f"导入logger失败: {str(e)}")
    traceback.print_exc()
    sys.exit(1)

# 加载环境变量
load_dotenv()

# 测试样本
SAMPLE_TEXT_ONLY = {
    "message_id": "text_only_1",
    "text": """Best resources for webdesigners 👨‍💻

- items. design - graphic assets
- grainient .supply - backgrounds
- framer .com - website builder
- frameblox .com - UI kit for Framer
- supahero .io - webdesign isnpirations
- shots .so - mockup generator
- mockuply .pro - mockups
- contentcore .xyz - 3D mockups
- shapefest .com - 3D shapes
- uncut .wtf - fonts
- jitter .video - video animation""",
    "sender_name": "WebDesignMaster",
    "chat_title": "Web Design Resources"
}

SAMPLE_TEXT_WITH_URL = {
    "message_id": "text_url_1",
    "text": """2025年了，Chrome终于支持了直接用 CSS 创建轮播和滚动界面，不需要用到JavaScript！
https://developer.chrome.com/blog/carousels-with-css?hl=zh-cn""",
    "sender_name": "FrontEndDev",
    "chat_title": "前端开发日报"
}

SAMPLE_URL_ONLY = {
    "message_id": "url_only_1",
    "text": "@https://x.com/dotey/status/1903339286360936518",
    "sender_name": "NewsBot",
    "chat_title": "Tech News"
}

async def test_analyze_text_only():
    """测试分析纯文本内容"""
    print("\n=== 测试分析纯文本内容 ===")
    
    # 获取提供商和API密钥
    provider, api_key = get_provider_and_key()
    if not api_key:
        print("跳过测试: 未设置OpenRouter或DeepSeek API密钥")
        return
    
    # 初始化内容分析器
    analyzer = ContentAnalyzer(api_key=api_key, provider=provider)
    
    try:
        # 分析纯文本内容
        print(f"正在分析纯文本内容...")
        result = await analyzer.analyze(SAMPLE_TEXT_ONLY)
        
        # 打印结果
        print_analysis_result(result)
        
    except Exception as e:
        print(f"测试失败: {str(e)}")
    
    # 关闭分析器
    await analyzer.close()

async def test_analyze_text_with_url():
    """测试分析带URL的文本内容"""
    print("\n=== 测试分析带URL的文本内容 ===")
    
    # 获取提供商和API密钥
    provider, api_key = get_provider_and_key()
    if not api_key:
        print("跳过测试: 未设置OpenRouter或DeepSeek API密钥")
        return
    
    # 初始化内容分析器
    analyzer = ContentAnalyzer(api_key=api_key, provider=provider)
    
    try:
        # 分析带URL的文本内容
        print(f"正在分析带URL的文本内容...")
        result = await analyzer.analyze(SAMPLE_TEXT_WITH_URL)
        
        # 打印结果
        print_analysis_result(result)
        
    except Exception as e:
        print(f"测试失败: {str(e)}")
    
    # 关闭分析器
    await analyzer.close()

async def test_analyze_url_only():
    """测试分析纯URL内容"""
    print("\n=== 测试分析纯URL内容 ===")
    
    # 获取提供商和API密钥
    provider, api_key = get_provider_and_key()
    if not api_key:
        print("跳过测试: 未设置OpenRouter或DeepSeek API密钥")
        return
    
    # 初始化内容分析器
    analyzer = ContentAnalyzer(api_key=api_key, provider=provider)
    
    try:
        # 分析纯URL内容
        print(f"正在分析纯URL内容...")
        result = await analyzer.analyze(SAMPLE_URL_ONLY)
        
        # 打印结果
        print_analysis_result(result)
        
    except Exception as e:
        print(f"测试失败: {str(e)}")
    
    # 关闭分析器
    await analyzer.close()

def print_analysis_result(result):
    """打印分析结果"""
    if result.get("success", False):
        print("\n分析成功!")
        print(f"内容格式: {result.get('content_format', '未知')}")
        print(f"内容类型: {result.get('content_type', '未知')}")
        print(f"主题分类: {result.get('category', '未知')} / {result.get('subcategory', '未知')}")
        print(f"语言: {result.get('language', '未知')}")
        print(f"情感倾向: {result.get('sentiment', '未知')}")
        
        # 关键词
        keywords = result.get("keywords", [])
        if keywords:
            print("关键词:")
            for keyword in keywords:
                print(f"  - {keyword}")
        
        # URL
        urls = result.get("urls", [])
        if urls:
            print("URL列表:")
            for url in urls:
                print(f"  - {url}")
        
        # 摘要
        summary = result.get("summary", "")
        if summary:
            print("\n摘要:")
            print(summary)
    else:
        print("\n分析失败!")
        print(f"错误信息: {result.get('error', '未知错误')}")
        if "raw_content" in result:
            print("\n原始内容片段:")
            content = result.get("raw_content", "")
            print(content[:200] + "..." if len(content) > 200 else content)

def get_provider_and_key():
    """获取可用的提供商和API密钥，只使用OpenRouter和DeepSeek"""
    # 按优先级检查
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    if openrouter_key:
        print("使用OpenRouter API")
        return "openrouter", openrouter_key
    
    deepseek_key = os.getenv("DEEPSEEK_API_KEY")
    if deepseek_key:
        print("使用DeepSeek API")
        return "deepseek", deepseek_key
    
    # 如果都没有找到，返回默认值
    print("未找到OpenRouter或DeepSeek密钥")
    return "openrouter", None

def get_any_api_key():
    """获取任何可用的API密钥，只使用OpenRouter和DeepSeek"""
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    deepseek_key = os.getenv("DEEPSEEK_API_KEY")
    
    # 按优先级返回
    if openrouter_key:
        print("使用OpenRouter API密钥")
        return openrouter_key
    elif deepseek_key:
        print("使用DeepSeek API密钥")
        return deepseek_key
    
    return None

async def main():
    """主函数"""
    print("开始测试内容分析器...")
    
    # 测试不同格式的内容
    await test_analyze_text_only()
    await test_analyze_text_with_url()
    await test_analyze_url_only()
    
    print("\n测试完成!")

if __name__ == "__main__":
    asyncio.run(main()) 