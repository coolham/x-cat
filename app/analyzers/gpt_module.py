"""
GPT分析器模块
基于OpenAI GPT的内容分析服务
"""
import os
import json
import asyncio
from typing import Dict, Any, Optional, List
import traceback

from loguru import logger

from app.analyzers.gpt import GptAnalyzer
from app.core.module import Module, ModuleState

class GptAnalyzerModule(Module):
    """
    GPT分析器模块
    实现基于OpenAI GPT的内容分析功能
    """
    
    def __init__(self, runtime=None, module_id: str = "gpt_analyzer"):
        """
        初始化GPT分析器模块
        
        Args:
            runtime: 运行时环境 (可选)
            module_id: 模块ID
        """
        super().__init__(runtime, module_id)
        self.analyzer = None
        self.api_key = None
        self.model = None
        self.proxy_url = None
        self.max_tokens = None
        self.temperature = None
        
        # 添加系统提示
        self.system_prompt = """
        你是一个专业的内容分析助手，负责分析互联网内容并进行分类。分析结果需包含以下内容：
        1. 内容类型：文章、问答、广告、新闻等
        2. 主题分类：科技、娱乐、教育、金融等
        3. 情感倾向：积极、消极、中性
        4. 关键词：最多5个关键词
        5. 摘要：100字以内的内容摘要
        
        请以JSON格式输出，格式如下：
        {
            "content_type": "文章/问答/广告/新闻/其他",
            "category": "主题分类",
            "sentiment": "积极/消极/中性",
            "keywords": ["关键词1", "关键词2", ...],
            "summary": "内容摘要"
        }
        """
        
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """
        初始化模块
        
        Args:
            config: 配置字典
            
        Returns:
            初始化是否成功
        """
        try:
            # 输出完整配置信息以进行调试
            logger.debug(f"收到配置: {list(config.keys())}")
            
            # 获取配置
            # 在config中直接查找gpt_analyzer键
            if "gpt_analyzer" not in config:
                # 为防止配置结构不当，尝试获取顶级键
                gpt_config = {}
                api_key = config.get("api_key")
                model = config.get("model")
                if api_key and model:
                    # 如果在顶级找到，则创建配置
                    gpt_config = {
                        "api_key": api_key,
                        "model": model,
                        "proxy_url": config.get("proxy_url"),
                        "max_tokens": config.get("max_tokens", 1024),
                        "temperature": config.get("temperature", 0.7)
                    }
                    logger.warning("在顶级配置中找到GPT参数")
                else:
                    logger.error("配置中找不到gpt_analyzer部分且无法从顶级配置构建")
                    # 使用示例API密钥以允许系统继续初始化（开发模式）
                    gpt_config = {
                        "api_key": "sk-example-key-for-dev-mode-only",
                        "model": "gpt-3.5-turbo",
                        "proxy_url": None,
                        "max_tokens": 1024,
                        "temperature": 0.7
                    }
                    logger.warning("使用开发模式示例配置")
            else:
                gpt_config = config["gpt_analyzer"]
                logger.debug(f"找到GPT分析器配置: {gpt_config}")
            
            # 保存配置
            self.api_key = gpt_config["api_key"]
            self.model = gpt_config["model"]
            self.proxy_url = gpt_config.get("proxy_url")
            self.max_tokens = gpt_config.get("max_tokens", 1024)
            self.temperature = gpt_config.get("temperature", 0.7)
            
            # 创建分析器
            self.analyzer = GptAnalyzer(
                api_key=self.api_key,
                model=self.model,
                proxy_url=self.proxy_url,
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            # 更新状态
            self.state = ModuleState.INITIALIZED
            logger.info("GPT分析器模块初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"GPT分析器模块初始化失败: {str(e)}")
            logger.debug(f"错误详情: {traceback.format_exc()}")
            return False
    
    async def start(self) -> bool:
        """
        启动模块
        
        Returns:
            启动是否成功
        """
        if self.state != ModuleState.INITIALIZED:
            logger.error("GPT分析器模块未初始化")
            return False
        
        try:
            # 模块已准备好运行
            self.state = ModuleState.RUNNING
            logger.info("GPT分析器模块已启动")
            return True
            
        except Exception as e:
            logger.error(f"GPT分析器模块启动失败: {str(e)}")
            self.state = ModuleState.ERROR
            return False
    
    async def stop(self) -> bool:
        """
        停止模块
        
        Returns:
            停止是否成功
        """
        if self.state != ModuleState.RUNNING:
            return True
        
        try:
            # 关闭分析器
            if self.analyzer:
                await self.analyzer.close()
            
            # 更新状态
            self.state = ModuleState.STOPPED
            logger.info("GPT分析器模块已停止")
            return True
            
        except Exception as e:
            logger.error(f"GPT分析器模块停止失败: {str(e)}")
            self.state = ModuleState.ERROR
            return False
    
    async def health_check(self) -> bool:
        """
        健康检查
        
        Returns:
            模块是否健康
        """
        return self.state == ModuleState.RUNNING and self.analyzer is not None
    
    async def analyze_content(self, content: str) -> Dict[str, Any]:
        """
        分析内容
        
        Args:
            content: 要分析的内容
            
        Returns:
            分析结果字典
        """
        if self.state != ModuleState.RUNNING:
            error_msg = "GPT分析器模块未运行"
            logger.error(error_msg)
            return self._get_error_result(error_msg)
        
        try:
            # 调用分析器
            success, result = await self.analyzer.analyze_text(content, self.system_prompt)
            
            if not success:
                return self._get_error_result(result)
            
            # 尝试解析JSON结果
            try:
                result_dict = json.loads(result)
                return result_dict
            except json.JSONDecodeError:
                logger.warning(f"GPT响应不是有效的JSON: {result}")
                return self._extract_result_from_text(result)
                
        except Exception as e:
            error_msg = f"分析内容失败: {str(e)}"
            logger.error(error_msg)
            return self._get_error_result(error_msg)
    
    def _extract_result_from_text(self, text: str) -> Dict[str, Any]:
        """
        从文本中提取分析结果
        
        Args:
            text: GPT返回的非JSON文本
            
        Returns:
            提取的结果字典
        """
        # 简单实现，实际可能需要更复杂的解析逻辑
        result = {
            "content_type": "未知",
            "category": "未知",
            "sentiment": "中性",
            "keywords": [],
            "summary": "无法提取摘要"
        }
        
        # 尝试从文本中提取信息
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if "内容类型" in line or "content_type" in line:
                parts = line.split(":")
                if len(parts) > 1:
                    result["content_type"] = parts[1].strip().strip('",')
            
            elif "主题分类" in line or "category" in line:
                parts = line.split(":")
                if len(parts) > 1:
                    result["category"] = parts[1].strip().strip('",')
            
            elif "情感倾向" in line or "sentiment" in line:
                parts = line.split(":")
                if len(parts) > 1:
                    result["sentiment"] = parts[1].strip().strip('",')
            
            elif "关键词" in line or "keywords" in line:
                parts = line.split(":")
                if len(parts) > 1:
                    keywords_text = parts[1].strip()
                    # 尝试提取关键词列表
                    keywords = [k.strip().strip('",[]') for k in keywords_text.split(',')]
                    result["keywords"] = [k for k in keywords if k]
            
            elif "摘要" in line or "summary" in line:
                parts = line.split(":")
                if len(parts) > 1:
                    result["summary"] = parts[1].strip().strip('",')
        
        return result
    
    def _get_error_result(self, error_message: str) -> Dict[str, Any]:
        """
        生成错误结果
        
        Args:
            error_message: 错误信息
            
        Returns:
            错误结果字典
        """
        return {
            "content_type": "错误",
            "category": "错误",
            "sentiment": "中性",
            "keywords": [],
            "summary": f"分析过程中发生错误: {error_message}",
            "error": error_message
        } 