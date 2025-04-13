"""
缓存管理器
"""
import json
from typing import Dict, Any, Optional
from datetime import datetime
from loguru import logger

from .db import DatabaseManager
from .models import CacheEntry


class CacheManager:
    """缓存管理器"""
    
    def __init__(self, cache_dir: str = "cache"):
        """初始化缓存管理器
        
        Args:
            cache_dir: 缓存目录
        """
        self.db = DatabaseManager(f"{cache_dir}/cache.db")
        logger.info("缓存管理器初始化成功")
    
    def save(self, url: str, data: Dict[str, Any]) -> bool:
        """保存数据到缓存
        
        Args:
            url: URL
            data: 要缓存的数据
            
        Returns:
            bool: 是否保存成功
        """
        try:
            # 添加时间戳
            data['cached_at'] = datetime.now().isoformat()
            
            # 创建缓存条目
            entry = CacheEntry(
                url=url,
                data=json.dumps(data),
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            # 保存到数据库
            return self.db.save(entry)
        except Exception as e:
            logger.error(f"保存缓存失败: {str(e)}")
            return False
    
    def load(self, url: str) -> Optional[Dict[str, Any]]:
        """从缓存加载数据
        
        Args:
            url: URL
            
        Returns:
            Optional[Dict[str, Any]]: 缓存的数据，如果不存在则返回None
        """
        try:
            # 从数据库加载
            entry = self.db.load(url)
            if entry:
                # 解析数据
                data = json.loads(entry.data)
                logger.info(f"从缓存加载数据成功: {url}")
                return data
            return None
        except Exception as e:
            logger.error(f"加载缓存失败: {str(e)}")
            return None
    
    def exists(self, url: str) -> bool:
        """检查缓存是否存在
        
        Args:
            url: URL
            
        Returns:
            bool: 是否存在
        """
        return self.db.exists(url)
    
    def clear(self, url: Optional[str] = None) -> bool:
        """清除缓存
        
        Args:
            url: URL，如果为None则清除所有缓存
            
        Returns:
            bool: 是否清除成功
        """
        return self.db.clear(url)
    
    def get_all(self) -> list[Dict[str, Any]]:
        """获取所有缓存数据
        
        Returns:
            list[Dict[str, Any]]: 缓存数据列表
        """
        try:
            entries = self.db.get_all()
            return [json.loads(entry.data) for entry in entries]
        except Exception as e:
            logger.error(f"获取所有缓存数据失败: {str(e)}")
            return [] 