"""
GPT分析器模块
负责使用GPT模型分析消息内容
"""
from typing import Dict, Any, Optional, List
from loguru import logger
from prefect import task

class GptAnalyzer:
    """GPT分析器"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化GPT分析器
        
        Args:
            config: 配置字典
        """
        self.config = config
        self._initialized = False
        self.api_key = config.get("api_key")
        self.model = config.get("model", "gpt-3.5-turbo")
        self.max_tokens = config.get("max_tokens", 2000)
        self.temperature = config.get("temperature", 0.7)
    
    async def initialize(self) -> bool:
        """
        初始化GPT分析器
        
        Returns:
            初始化是否成功
        """
        try:
            if not self.api_key:
                logger.error("配置中缺少api_key")
                return False
            
            self._initialized = True
            logger.info("GPT分析器初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"GPT分析器初始化失败: {str(e)}")
            return False
    
    @task(name="analyze_with_gpt")
    def analyze_with_gpt(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        使用GPT分析消息内容
        
        Args:
            message: 消息数据
            
        Returns:
            分析结果
        """
        if not self._initialized:
            logger.error("GPT分析器未初始化")
            return {}
            
        try:
            content = message.get("text", "")
            if not content:
                logger.warning("消息内容为空")
                return {}
            
            # 构建提示词
            prompt = f"""
            请分析以下消息内容，并提供以下信息：
            1. 主要主题
            2. 情感倾向（积极/消极/中性）
            3. 关键实体（人物、组织、地点等）
            4. 摘要（100字以内）
            
            消息内容：
            {content}
            """
            
            # 调用GPT API
            # 注意：这里需要实现实际的API调用
            # 以下是示例响应
            result = {
                "topic": "示例主题",
                "sentiment": "积极",
                "entities": ["实体1", "实体2"],
                "summary": "这是一个示例摘要"
            }
            
            logger.info(f"GPT分析完成: {result}")
            return result
            
        except Exception as e:
            logger.error(f"GPT分析时出错: {str(e)}")
            return {}
    
    @task(name="update_model")
    def update_model(self, model: str) -> bool:
        """
        更新GPT模型
        
        Args:
            model: 新的模型名称
            
        Returns:
            是否更新成功
        """
        if not self._initialized:
            logger.error("GPT分析器未初始化")
            return False
            
        try:
            self.model = model
            logger.info(f"成功更新GPT模型: {model}")
            return True
            
        except Exception as e:
            logger.error(f"更新GPT模型时出错: {str(e)}")
            return False
    
    @task(name="update_parameters")
    def update_parameters(self, max_tokens: Optional[int] = None, 
                         temperature: Optional[float] = None) -> bool:
        """
        更新GPT参数
        
        Args:
            max_tokens: 最大token数
            temperature: 温度参数
            
        Returns:
            是否更新成功
        """
        if not self._initialized:
            logger.error("GPT分析器未初始化")
            return False
            
        try:
            if max_tokens is not None:
                if max_tokens <= 0:
                    logger.warning("max_tokens必须大于0")
                    return False
                self.max_tokens = max_tokens
            
            if temperature is not None:
                if not 0 <= temperature <= 1:
                    logger.warning("temperature必须在0到1之间")
                    return False
                self.temperature = temperature
            
            logger.info(f"成功更新GPT参数: max_tokens={max_tokens}, temperature={temperature}")
            return True
            
        except Exception as e:
            logger.error(f"更新GPT参数时出错: {str(e)}")
            return False 