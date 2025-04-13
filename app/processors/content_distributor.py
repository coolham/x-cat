"""
Content distributor module
"""
from typing import Any, Dict, List, Optional
from loguru import logger
from prefect import task
from .base_processor import BaseProcessor
import json


class ContentDistributor(BaseProcessor):
    """Content distributor that distributes content to different channels"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化内容分发器
        
        Args:
            config: 配置信息
        """
        super().__init__(config)
        self.distribution_rules = self.config.get("distribution_rules", {
            "技术": ["local", "feishu"],
            "业务": ["local", "feishu"],
            "管理": ["local", "feishu"],
            "其他": ["local"]
        })
        self.confidence_threshold = self.config.get("confidence_threshold", 0.5)
        logger.info(f"内容分发器初始化完成，配置: {self.config}")

    def initialize(self) -> bool:
        """Initialize the distributor
        
        Returns:
            bool: Whether initialization was successful
        """
        try:
            logger.info("Initializing content distributor")
            super().initialize()
            return True
        except Exception as e:
            logger.error(f"Error initializing content distributor: {str(e)}")
            return False
        
    def cleanup(self) -> None:
        """Cleanup distributor resources"""
        logger.info("Cleaning up content distributor")
        super().cleanup()
        
    @task
    def process(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Distribute content
        
        Args:
            content: Content to distribute
            
        Returns:
            Distributed content
        """
        if not self._initialized:
            self.initialize()
            
        try:
            # 获取配置
            category_channels = self.config.get("category_channels", {})
            default_channel = self.config.get("default_channel", "其他")
            
            # 获取分类
            category = content.get("classification", {}).get("category", default_channel)
            
            # 获取目标频道
            target_channel = category_channels.get(category, default_channel)
            
            # 更新内容
            content["distribution"] = {
                "target_channel": target_channel,
                "category": category
            }
            
            logger.debug(f"Content distributed: {content}")
            return content
            
        except Exception as e:
            logger.error(f"Error distributing content: {str(e)}")
            raise 

    def _determine_distribution_targets(self, categories: Dict[str, float]) -> List[str]:
        """
        确定分发目标
        
        Args:
            categories: 分类结果，键为类别，值为置信度
            
        Returns:
            分发目标列表
        """
        # 初始化分发目标
        distribution_targets = set()
        
        # 根据分类结果确定分发目标
        for category, confidence in categories.items():
            if confidence >= self.confidence_threshold:
                if category in self.distribution_rules:
                    distribution_targets.update(self.distribution_rules[category])
        
        # 如果没有分发目标，默认为本地存储
        if not distribution_targets:
            distribution_targets.add("local")
        
        return list(distribution_targets) 