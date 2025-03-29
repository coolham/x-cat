# -*- coding: utf-8 -*-
"""
本地存储分发器
将内容保存到本地文件系统
"""
import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict
from loguru import logger

from .base import Distributor

class LocalDistributor(Distributor):
    """本地存储分发器"""
    
    def __init__(self):
        """初始化本地存储分发器"""
        super().__init__()
        
        # 从配置获取存储路径
        config = self.config.get_distributor_config(self.name)
        self.base_dir = Path(config.get('base_dir', 'data/contents'))
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建分类目录
        self._create_category_dirs()
    
    def _create_category_dirs(self):
        """创建分类目录"""
        try:
            # 读取分类定义
            from category_system.models.category_manager import CategoryManager
            manager = CategoryManager()
            categories = manager.get_primary_categories()
            
            # 创建分类目录
            for category in categories:
                category_dir = self.base_dir / category['id']
                category_dir.mkdir(exist_ok=True)
                
                # 创建二级分类目录
                subcategories = manager.get_secondary_categories(category['id'])
                for subcategory in subcategories:
                    subcategory_dir = category_dir / subcategory['id']
                    subcategory_dir.mkdir(exist_ok=True)
                    
        except Exception as e:
            logger.error(f"创建分类目录失败: {str(e)}")
    
    async def distribute(self, content: Dict) -> bool:
        """分发内容到本地存储
        
        Args:
            content: 内容信息
            
        Returns:
            bool: 是否分发成功
        """
        try:
            # 格式化内容
            formatted = self._format_content(content)
            
            # 获取分类信息
            primary = formatted['classification']['primary']
            secondary = formatted['classification']['secondary']
            
            # 构建存储路径
            date = datetime.fromisoformat(formatted['timestamp']).strftime('%Y-%m-%d')
            filename = f"{formatted['id']}.json"
            
            # 保存到对应分类目录
            content_dir = self.base_dir / primary / secondary / date
            content_dir.mkdir(parents=True, exist_ok=True)
            
            content_path = content_dir / filename
            
            # 检查文件是否已存在
            if content_path.exists():
                logger.warning(f"内容已存在，跳过: {content_path}")
                return True
            
            # 保存内容
            with open(content_path, 'w', encoding='utf-8') as f:
                json.dump(formatted, f, ensure_ascii=False, indent=2)
            
            logger.info(f"内容已保存到本地: {content_path}")
            return True
            
        except Exception as e:
            logger.error(f"保存内容到本地失败: {str(e)}")
            return False 