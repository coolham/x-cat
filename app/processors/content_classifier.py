"""
Content classifier module
"""
from typing import Any, Dict, List, Optional
from loguru import logger
from prefect import task
from .base_processor import BaseProcessor
from app.analyzers.content_analyzer import ContentAnalyzer
import json

class ContentClassifier(BaseProcessor):
    """Content classifier that classifies content using AI"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize classifier
        
        Args:
            config: Classifier configuration
        """
        super().__init__(config or {})
        self.analyzer = None
        self.categories = self.config.get("categories", ["技术", "业务", "管理", "其他"])
        self.keyword_categories = self.config.get("keyword_categories", {
            "技术": ["代码", "编程", "开发", "测试", "部署", "架构", "算法", "数据库", "API", "接口"],
            "业务": ["需求", "产品", "用户", "市场", "销售", "客户", "服务", "运营", "分析", "报告"],
            "管理": ["会议", "计划", "项目", "团队", "资源", "预算", "目标", "绩效", "培训", "沟通"],
            "其他": []
        })
        logger.info(f"内容分类器初始化完成，配置: {self.config}")
        
    def initialize(self) -> bool:
        """Initialize the classifier
        
        Returns:
            bool: Whether initialization was successful
        """
        try:
            logger.info("Initializing content classifier")
            
            # 初始化内容分析器
            self.analyzer = ContentAnalyzer(
                api_key=self.config.get("api_key"),
                provider=self.config.get("provider", "openrouter"),
                model=self.config.get("model"),
                proxy_url=self.config.get("proxy_url"),
                max_tokens=self.config.get("max_tokens", 2000),
                temperature=self.config.get("temperature", 0.7)
            )
            super().initialize()
            return True
        except Exception as e:
            logger.error(f"Error initializing content classifier: {str(e)}")
            return False
        
    def cleanup(self) -> None:
        """Cleanup classifier resources"""
        logger.info("Cleaning up content classifier")
        if self.analyzer and hasattr(self.analyzer, 'cleanup'):
            self.analyzer.cleanup()
        super().cleanup()
        
    @task
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classify content
        
        Args:
            data: Content to classify
            
        Returns:
            Classified content
        """
        if not self._initialized:
            self.initialize()
            
        try:
            logger.info(f"开始分类内容: {data}")
            
            # 复制原始数据
            classified_data = data.copy()
            
            # 获取内容
            content = classified_data.get("content", "")
            if not content:
                logger.warning("数据中没有内容字段")
                return classified_data
            
            # 获取关键词
            keywords = classified_data.get("keywords", [])
            
            # 获取实体
            entities = classified_data.get("entities", {})
            
            # 获取摘要
            summary = classified_data.get("summary", "")
            
            # 分类内容
            categories = self._classify_content(
                content=content,
                keywords=keywords,
                entities=entities,
                summary=summary
            )
            
            # 更新分类后的内容
            classified_data["categories"] = categories
            
            # 添加分类标记
            classified_data["classified"] = True
            classified_data["classification_info"] = {
                "categories": self.categories,
                "keyword_categories": self.keyword_categories
            }
            
            logger.info(f"内容分类完成: {classified_data}")
            return classified_data
            
        except Exception as e:
            logger.error(f"Error classifying content: {str(e)}")
            raise
    
    def _classify_content(
        self, 
        content: str, 
        keywords: List[str], 
        entities: Dict[str, List[str]], 
        summary: str
    ) -> Dict[str, float]:
        """
        分类内容
        
        Args:
            content: 原始内容
            keywords: 关键词列表
            entities: 实体字典
            summary: 摘要
            
        Returns:
            分类结果，键为类别，值为置信度
        """
        # 初始化分类结果
        categories = {category: 0.0 for category in self.categories}
        
        # 基于关键词分类
        keyword_scores = self._classify_by_keywords(keywords)
        for category, score in keyword_scores.items():
            categories[category] += score * 0.6  # 关键词权重为0.6
        
        # 基于实体分类
        entity_scores = self._classify_by_entities(entities)
        for category, score in entity_scores.items():
            categories[category] += score * 0.4  # 实体权重为0.4
        
        # 归一化分数
        total_score = sum(categories.values())
        if total_score > 0:
            for category in categories:
                categories[category] /= total_score
        
        # 如果没有分类结果，默认为"其他"
        if all(score == 0 for score in categories.values()):
            categories["其他"] = 1.0
        
        return categories
    
    def _classify_by_keywords(self, keywords: List[str]) -> Dict[str, float]:
        """
        基于关键词分类
        
        Args:
            keywords: 关键词列表
            
        Returns:
            分类结果，键为类别，值为置信度
        """
        # 初始化分类结果
        categories = {category: 0.0 for category in self.categories}
        
        # 统计每个类别的关键词匹配数
        for keyword in keywords:
            for category, category_keywords in self.keyword_categories.items():
                if keyword in category_keywords:
                    categories[category] += 1
        
        # 归一化分数
        total_matches = sum(categories.values())
        if total_matches > 0:
            for category in categories:
                categories[category] /= total_matches
        
        return categories
    
    def _classify_by_entities(self, entities: Dict[str, List[str]]) -> Dict[str, float]:
        """
        基于实体分类
        
        Args:
            entities: 实体字典
            
        Returns:
            分类结果，键为类别，值为置信度
        """
        # 初始化分类结果
        categories = {category: 0.0 for category in self.categories}
        
        # 基于实体类型分类
        if "organization" in entities and entities["organization"]:
            categories["业务"] += 0.5
            categories["管理"] += 0.3
        
        if "person" in entities and entities["person"]:
            categories["管理"] += 0.3
            categories["业务"] += 0.2
        
        if "date" in entities and entities["date"]:
            categories["管理"] += 0.2
            categories["业务"] += 0.1
        
        if "number" in entities and entities["number"]:
            categories["技术"] += 0.2
            categories["业务"] += 0.2
        
        # 归一化分数
        total_score = sum(categories.values())
        if total_score > 0:
            for category in categories:
                categories[category] /= total_score
        
        return categories 