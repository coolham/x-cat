#!/usr/bin/env python
"""
内容分析器示例
演示如何直接使用内容分析器分析消息
"""
import os
import sys
import json
import asyncio
import argparse
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.runtime import Runtime
from app.analyzers.content_analyzer_module import ContentAnalyzerModule
from app.storage.storage_module import StorageModule


def load_config(config_file='config.json'):
    """加载配置文件"""
    config_path = Path(config_file)
    if not config_path.exists():
        example_path = Path(f"{config_file}.example")
        if example_path.exists():
            print(f"配置文件 {config_file} 不存在，使用示例配置 {example_path}")
            with open(example_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            raise FileNotFoundError(f"配置文件不存在: {config_file} 或 {example_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


async def analyze_text(text, config):
    """分析文本内容"""
    # 创建运行时环境
    runtime = Runtime()
    
    # 创建内容分析器模块
    analyzer = ContentAnalyzerModule(runtime, "content_analyzer")
    
    # 初始化和启动模块
    await analyzer.initialize(config)
    await analyzer.start()
    
    try:
        # 构造消息
        message = {
            "message_id": "example_message",
            "text": text,
            "sender_name": "示例用户",
            "chat_title": "示例聊天"
        }
        
        # 分析消息
        print(f"正在分析文本: {text[:100]}...")
        result = await analyzer.analyze_message(message)
        
        return result
    finally:
        # 关闭模块
        await analyzer.stop()


async def analyze_url(url, config):
    """分析URL内容"""
    # 构造包含URL的消息
    return await analyze_text(f"请分析这个URL内容: {url}", config)


def format_result(result):
    """格式化结果输出"""
    if not result.get("success", False):
        return f"分析失败: {result.get('error', '未知错误')}"
    
    output = [
        "分析结果:",
        f"  内容类型: {result.get('content_type', '未知')}",
        f"  分类: {result.get('category', '未知')}",
        f"  子分类: {result.get('subcategory', '未知')}",
        f"  情感: {result.get('sentiment', '未知')}",
        f"  语言: {result.get('language', '未知')}",
        f"  关键词: {', '.join(result.get('keywords', []))}",
        "",
        "摘要:",
        f"{result.get('summary', '无摘要')}"
    ]
    
    return "\n".join(output)


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="内容分析器示例")
    parser.add_argument("--config", "-c", default="config.json", help="配置文件路径")
    parser.add_argument("--text", "-t", help="要分析的文本")
    parser.add_argument("--url", "-u", help="要分析的URL")
    parser.add_argument("--output", "-o", help="输出结果到文件")
    args = parser.parse_args()
    
    if not args.text and not args.url:
        parser.error("必须提供 --text 或 --url 参数")
    
    try:
        # 加载配置
        config = load_config(args.config)
        
        # 分析内容
        if args.url:
            result = await analyze_url(args.url, config)
        else:
            result = await analyze_text(args.text, config)
        
        # 格式化并输出结果
        formatted_result = format_result(result)
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(formatted_result)
                print(f"结果已保存到: {args.output}")
        else:
            print(formatted_result)
            
    except Exception as e:
        print(f"错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main())) 