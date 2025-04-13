# -*- coding: utf-8 -*-
"""
分类管理器
负责管理消息分类系统
"""
import os
import json
from typing import Dict, Any, Optional, List
from loguru import logger
from prefect import task

class CategoryManager:
    """分类管理器"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化分类管理器
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.categories = {}
        self._initialized = False
    
    async def initialize(self) -> bool:
        """
        初始化分类管理器
        
        Returns:
            初始化是否成功
        """
        try:
            # 加载分类配置
            if "categories" not in self.config:
                logger.warning("配置中没有categories字段，将使用默认分类")
                self.categories = {
                    "default": {
                        "name": "默认分类",
                        "description": "未分类的消息",
                        "keywords": []
                    }
                }
            else:
                self.categories = self.config["categories"]
            
            self._initialized = True
            logger.info("分类管理器初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"分类管理器初始化失败: {str(e)}")
            return False
    
    @task(name="get_category")
    def get_category(self, message: Dict[str, Any]) -> str:
        """
        获取消息的分类
        
        Args:
            message: 消息数据
            
        Returns:
            消息的分类
        """
        if not self._initialized:
            logger.error("分类管理器未初始化")
            return "default"
            
        try:
            # 提取消息内容
            content = message.get("text", "").lower()
            
            # 遍历所有分类，检查关键词匹配
            for category_id, category in self.categories.items():
                keywords = category.get("keywords", [])
                for keyword in keywords:
                    if keyword.lower() in content:
                        return category_id
            
            # 如果没有匹配的分类，返回默认分类
            return "default"
            
        except Exception as e:
            logger.error(f"获取消息分类时出错: {str(e)}")
            return "default"
    
    @task(name="add_category")
    def add_category(self, category_id: str, category_data: Dict[str, Any]) -> bool:
        """
        添加新的分类
        
        Args:
            category_id: 分类ID
            category_data: 分类数据
            
        Returns:
            是否添加成功
        """
        if not self._initialized:
            logger.error("分类管理器未初始化")
            return False
            
        try:
            # 检查分类ID是否已存在
            if category_id in self.categories:
                logger.warning(f"分类ID已存在: {category_id}")
                return False
            
            # 添加新分类
            self.categories[category_id] = category_data
            logger.info(f"成功添加新分类: {category_id}")
            return True
            
        except Exception as e:
            logger.error(f"添加分类时出错: {str(e)}")
            return False
    
    @task(name="update_category")
    def update_category(self, category_id: str, category_data: Dict[str, Any]) -> bool:
        """
        更新分类
        
        Args:
            category_id: 分类ID
            category_data: 新的分类数据
            
        Returns:
            是否更新成功
        """
        if not self._initialized:
            logger.error("分类管理器未初始化")
            return False
            
        try:
            # 检查分类ID是否存在
            if category_id not in self.categories:
                logger.warning(f"分类ID不存在: {category_id}")
                return False
            
            # 更新分类
            self.categories[category_id].update(category_data)
            logger.info(f"成功更新分类: {category_id}")
            return True
            
        except Exception as e:
            logger.error(f"更新分类时出错: {str(e)}")
            return False
    
    @task(name="delete_category")
    def delete_category(self, category_id: str) -> bool:
        """
        删除分类
        
        Args:
            category_id: 分类ID
            
        Returns:
            是否删除成功
        """
        if not self._initialized:
            logger.error("分类管理器未初始化")
            return False
            
        try:
            # 检查分类ID是否存在
            if category_id not in self.categories:
                logger.warning(f"分类ID不存在: {category_id}")
                return False
            
            # 不允许删除默认分类
            if category_id == "default":
                logger.warning("不能删除默认分类")
                return False
            
            # 删除分类
            del self.categories[category_id]
            logger.info(f"成功删除分类: {category_id}")
            return True
            
        except Exception as e:
            logger.error(f"删除分类时出错: {str(e)}")
            return False
    
    def get_all_categories(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有分类
        
        Returns:
            所有分类的字典
        """
        return self.categories.copy()
