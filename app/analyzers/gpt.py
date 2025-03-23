"""
GPT分析器模块
用于调用GPT API分析文本内容
"""
import os
import json
import asyncio
from typing import Dict, Any, List, Optional, Tuple

from loguru import logger
import httpx

class GptAnalyzer:
    """
    GPT分析器
    用于调用GPT API分析文本内容，支持异步调用
    
    属性:
        api_key: OpenAI API密钥
        model: 使用的GPT模型名称
        proxy_url: 代理服务器URL (可选)
        max_tokens: 最大生成token数
        temperature: 温度参数，控制生成文本的随机性
    """
    
    def __init__(
        self, 
        api_key: str, 
        model: str = "gpt-3.5-turbo", 
        proxy_url: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7
    ):
        """
        初始化GPT分析器
        
        Args:
            api_key: OpenAI API密钥
            model: 使用的GPT模型名称，默认为gpt-3.5-turbo
            proxy_url: 代理服务器URL (可选)
            max_tokens: 最大生成token数，默认为1024
            temperature: 温度参数，控制生成文本的随机性，默认为0.7
        """
        self.api_key = api_key
        self.model = model
        self.proxy_url = proxy_url
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.api_base = "https://api.openai.com/v1"
        
        # 创建异步HTTP客户端 - 适配回退到httpx 0.23.3版本
        if proxy_url:
            proxies = {"http://": proxy_url, "https://": proxy_url}
            self.client = httpx.AsyncClient(proxies=proxies, timeout=60.0)
        else:
            self.client = httpx.AsyncClient(timeout=60.0)
        
        logger.debug(f"GPT analyzer initialized: model={model}, proxy={proxy_url is not None}")
    
    async def analyze_text(self, text: str, task_prompt: str) -> Tuple[bool, str]:
        """
        分析文本内容
        
        Args:
            text: 要分析的文本内容
            task_prompt: 分析任务提示词
            
        Returns:
            (成功标志, 分析结果或错误信息)
        """
        try:
            # 构建消息
            messages = [
                {"role": "system", "content": task_prompt},
                {"role": "user", "content": text}
            ]
            
            # 构建请求数据
            data = {
                "model": self.model,
                "messages": messages,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature
            }
            
            # 构建请求头
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            # 发送请求
            endpoint = f"{self.api_base}/chat/completions"
            response = await self.client.post(endpoint, json=data, headers=headers)
            
            # 检查状态码
            if response.status_code != 200:
                error_msg = f"API错误: HTTP {response.status_code} - {response.text}"
                logger.error(error_msg)
                return False, error_msg
            
            # 解析响应
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            return True, content
            
        except Exception as e:
            error_msg = f"分析失败: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    async def close(self):
        """关闭HTTP客户端"""
        await self.client.aclose() 