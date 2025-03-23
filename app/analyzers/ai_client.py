"""
AI客户端模块 - 基于ai-api-wrapper库的封装
提供多种AI模型的统一访问接口，支持代理服务器配置
"""
import os
import asyncio
import json
from typing import Dict, Any, List, Optional, Tuple, Union
import traceback

from loguru import logger
from ai_api_wrapper import Client
from ai_api_wrapper.provider import LLMError

class AIClient:
    """
    AI客户端
    基于ai-api-wrapper库封装，提供多种AI模型的统一访问接口
    支持代理服务器配置，可选择不同的AI服务提供商
    
    属性:
        client: ai-api-wrapper客户端实例
        model: 默认使用的模型
        default_provider: 默认使用的AI服务提供商
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        provider: str = "openai",
        proxy_url: Optional[str] = None,
        max_tokens: int = 4000,
        temperature: float = 0.7
    ):
        """
        初始化AI客户端
        
        Args:
            api_key: API密钥 (可选，如不提供则从环境变量获取)
            model: 使用的模型名称 (可选，默认由provider决定)
            provider: AI服务提供商，支持"openai"、"openrouter"、"deepseek"
            proxy_url: 代理服务器URL (可选，建议通过环境变量设置)
            max_tokens: 最大生成token数，默认为4000
            temperature: 温度参数，控制生成文本的随机性，默认为0.7
        """
        self.provider = provider
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.proxy_url = proxy_url
        
        # 确定API密钥
        if not api_key:
            if provider == "openrouter":
                api_key = os.getenv("OPENROUTER_API_KEY")
                if not api_key:
                    raise ValueError("未提供OPENROUTER_API_KEY，请在配置中设置或通过环境变量提供")
            elif provider == "deepseek":
                api_key = os.getenv("DEEPSEEK_API_KEY")
                if not api_key:
                    raise ValueError("未提供DEEPSEEK_API_KEY，请在配置中设置或通过环境变量提供")
            else:
                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    raise ValueError("未提供OPENAI_API_KEY，请在配置中设置或通过环境变量提供")
        
        # 确定模型
        if not model:
            if provider == "openrouter":
                self.model = "openrouter:gpt-4o"
            elif provider == "deepseek":
                self.model = "deepseek:deepseek-chat"
            else:
                self.model = "openai:gpt-3.5-turbo-0125"
        else:
            # 如果用户提供的模型名称中没有包含":"，则添加提供商前缀
            if ":" not in model:
                self.model = f"{provider}:{model}"
            else:
                self.model = model
        
        # 处理代理设置
        # 注意: ai-api-wrapper库通过环境变量控制代理，如DEEPSEEK_USE_PROXY=false
        # 不是通过初始化参数直接设置
        if proxy_url:
            logger.info(f"代理设置已提供: {proxy_url}，请确保相关环境变量已正确设置")
            logger.info(f"可在.env文件中设置以下变量控制代理:")
            logger.info(f"HTTP_PROXY={proxy_url}")
            logger.info(f"HTTPS_PROXY={proxy_url}")
            logger.info(f"对于特定提供商，可设置<PROVIDER>_USE_PROXY=true/false来控制是否使用代理")
        
        # 初始化客户端
        try:
            # 尝试初始化客户端，ai-api-wrapper会自动处理环境变量中的代理设置
            self.client = Client(api_key=api_key)
            
            # 确保API密钥正确设置
            if hasattr(self.client, "api_key") and self.client.api_key != api_key:
                self.client.api_key = api_key
                
        except Exception as e:
            error_msg = f"初始化AI客户端失败: {str(e)}"
            logger.error(error_msg)
            logger.debug(traceback.format_exc())
            raise ValueError(error_msg)
        
        logger.debug(f"AI客户端初始化成功: provider={provider}, model={self.model}")
    
    async def analyze(
        self, 
        content: str, 
        system_prompt: str,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        分析内容
        
        Args:
            content: 要分析的内容
            system_prompt: 系统提示词
            model: 使用的模型 (可选，默认使用实例化时指定的模型)
            temperature: 温度参数 (可选，默认使用实例化时指定的温度)
            max_tokens: 最大生成token数 (可选，默认使用实例化时指定的值)
            
        Returns:
            (成功标志, 分析结果或错误信息)
        """
        try:
            # 使用默认参数
            model = model or self.model
            temperature = temperature or self.temperature
            max_tokens = max_tokens or self.max_tokens
            
            # 构建消息
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": content}
            ]
            
            logger.debug(f"正在使用{model}分析内容，内容长度:{len(content)}字符")
            
            # 根据不同的provider构建请求参数
            params = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            # 尝试添加response_format参数（某些模型支持）
            try:
                params["response_format"] = {"type": "json_object"}
            except Exception as e:
                logger.warning(f"设置response_format失败，将继续请求: {str(e)}")
            
            # 发送请求
            try:
                # 尝试使用标准API
                response = self.client.chat.completions.create(**params)
            except (AttributeError, TypeError) as e:
                # 如果标准API失败，尝试直接调用completions方法
                logger.warning(f"使用标准API失败: {str(e)}，尝试替代方法")
                
                if hasattr(self.client, "completions"):
                    # 直接使用completions方法
                    response = self.client.completions(**params)
                else:
                    # 最后尝试直接调用__call__方法
                    response = self.client(messages=messages, model=model)
            
            # 解析响应
            if isinstance(response, dict):
                # 字典形式的响应
                content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
                if not content and "text" in response.get("choices", [{}])[0]:
                    # 某些API返回的是text而不是message.content
                    content = response.get("choices", [{}])[0].get("text", "")
            else:
                # 对象形式的响应
                try:
                    content = response.choices[0].message.content
                except (AttributeError, IndexError):
                    try:
                        # 尝试其他可能的属性路径
                        content = response.choices[0].text
                    except (AttributeError, IndexError):
                        return False, {"error": "无法从响应中提取内容"}
            
            # 尝试解析JSON结果
            try:
                # 清理可能的前缀和后缀
                content = content.strip()
                if content.startswith("```json"):
                    content = content[7:]
                if content.startswith("```"):
                    content = content[3:]
                if content.endswith("```"):
                    content = content[:-3]
                content = content.strip()
                
                result = json.loads(content)
                return True, result
            except json.JSONDecodeError:
                logger.warning(f"返回结果不是有效的JSON: {content[:100]}...")
                return False, {"error": "返回结果不是有效的JSON", "raw_content": content}
            
        except LLMError as e:
            error_msg = f"AI分析请求失败: {str(e)}"
            logger.error(error_msg)
            return False, {"error": error_msg}
            
        except Exception as e:
            error_msg = f"分析时发生错误: {str(e)}"
            logger.error(error_msg)
            logger.debug(traceback.format_exc())
            return False, {"error": error_msg}
    
    async def close(self):
        """关闭客户端连接"""
        # 目前ai-api-wrapper不需要显式关闭，此方法为预留
        pass
    
    async def get_available_models(self) -> List[Dict[str, Any]]:
        """
        获取可用模型列表
        
        Returns:
            可用模型列表
        """
        try:
            # 获取模型列表
            models = self.client.models.list(provider=self.provider)
            
            # 解析响应
            if isinstance(models, dict):
                return models.get("data", [])
            else:
                return models.data
                
        except Exception as e:
            logger.error(f"获取模型列表失败: {str(e)}")
            return [] 