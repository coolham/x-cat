"""
内容分析器模块
负责分析消息内容并提取关键信息
"""
from typing import Dict, Any, Optional, List
from loguru import logger
from prefect import task

class ContentAnalyzer:
    """内容分析器"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化内容分析器
        
        Args:
            config: 配置字典
        """
        self.config = config
        self._initialized = False
        self.keywords = config.get("keywords", [])
        self.sentiment_threshold = config.get("sentiment_threshold", 0.5)
    
    async def initialize(self) -> bool:
        """
        初始化内容分析器
        
        Returns:
            初始化是否成功
        """
        try:
            # 加载关键词列表
            if not self.keywords:
                logger.warning("配置中没有keywords字段，将使用空列表")
                self.keywords = []
            
            self._initialized = True
            logger.info("内容分析器初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"内容分析器初始化失败: {str(e)}")
            return False
    
    @task(name="analyze_content")
    def analyze_content(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析消息内容
        
        Args:
            message: 消息数据
            
        Returns:
            分析结果
        """
        if not self._initialized:
            logger.error("内容分析器未初始化")
            return {}
            
        try:
            content = message.get("text", "")
            result = {
                "keywords": [],
                "sentiment": 0.0,
                "summary": "",
                "entities": []
            }
            
            # 提取关键词
            for keyword in self.keywords:
                if keyword.lower() in content.lower():
                    result["keywords"].append(keyword)
            
            # 简单情感分析
            positive_words = ["好", "棒", "赞", "喜欢", "优秀"]
            negative_words = ["差", "烂", "糟", "讨厌", "垃圾"]
            
            positive_count = sum(1 for word in positive_words if word in content)
            negative_count = sum(1 for word in negative_words if word in content)
            
            total = positive_count + negative_count
            if total > 0:
                result["sentiment"] = positive_count / total
            
            # 生成摘要
            if len(content) > 100:
                result["summary"] = content[:100] + "..."
            else:
                result["summary"] = content
            
            # 提取实体
            # 这里使用简单的规则，实际应用中可以使用更复杂的NLP工具
            words = content.split()
            for word in words:
                if word.startswith("@") or word.startswith("#"):
                    result["entities"].append(word)
            
            logger.info(f"内容分析完成: {result}")
            return result
            
        except Exception as e:
            logger.error(f"分析内容时出错: {str(e)}")
            return {}
    
    @task(name="update_keywords")
    def update_keywords(self, keywords: List[str]) -> bool:
        """
        更新关键词列表
        
        Args:
            keywords: 新的关键词列表
            
        Returns:
            是否更新成功
        """
        if not self._initialized:
            logger.error("内容分析器未初始化")
            return False
            
        try:
            self.keywords = keywords
            logger.info(f"成功更新关键词列表: {keywords}")
            return True
            
        except Exception as e:
            logger.error(f"更新关键词列表时出错: {str(e)}")
            return False
    
    @task(name="update_sentiment_threshold")
    def update_sentiment_threshold(self, threshold: float) -> bool:
        """
        更新情感分析阈值
        
        Args:
            threshold: 新的阈值
            
        Returns:
            是否更新成功
        """
        if not self._initialized:
            logger.error("内容分析器未初始化")
            return False
            
        try:
            if not 0 <= threshold <= 1:
                logger.warning("情感分析阈值必须在0到1之间")
                return False
                
            self.sentiment_threshold = threshold
            logger.info(f"成功更新情感分析阈值: {threshold}")
            return True
            
        except Exception as e:
            logger.error(f"更新情感分析阈值时出错: {str(e)}")
            return False 