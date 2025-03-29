"""
缓存管理器
用于在数据源和内容预处理之间持久化数据
"""
import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from loguru import logger

class CacheManager:
    """缓存管理器"""
    
    def __init__(self, cache_dir: str = "cache"):
        """
        初始化缓存管理器
        
        Args:
            cache_dir: 缓存目录路径
        """
        self.cache_dir = cache_dir
        self._ensure_cache_dir()
    
    def _ensure_cache_dir(self):
        """确保缓存目录存在"""
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
    
    def _get_cache_path(self, url: str) -> str:
        """
        获取缓存文件路径
        
        Args:
            url: URL
            
        Returns:
            缓存文件路径
        """
        # 使用URL的哈希值作为文件名
        import hashlib
        url_hash = hashlib.md5(url.encode()).hexdigest()
        return os.path.join(self.cache_dir, f"{url_hash}.json")
    
    def save(self, url: str, data: Dict[str, Any]) -> bool:
        """
        保存数据到缓存
        
        Args:
            url: URL
            data: 要缓存的数据
            
        Returns:
            是否保存成功
        """
        try:
            # 验证URL
            if not url or not isinstance(url, str):
                logger.error(f"无效的URL: {url}")
                return False
                
            cache_path = self._get_cache_path(url)
            # 添加时间戳
            data['cached_at'] = datetime.now().isoformat()
            
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"数据已缓存: {url}")
            return True
        except Exception as e:
            logger.error(f"缓存数据失败: {url} - {str(e)}")
            return False
    
    def load(self, url: str) -> Optional[Dict[str, Any]]:
        """
        从缓存加载数据
        
        Args:
            url: URL
            
        Returns:
            缓存的数据，如果不存在则返回None
        """
        try:
            # 验证URL
            if not url or not isinstance(url, str):
                logger.error(f"无效的URL: {url}")
                return None
                
            cache_path = self._get_cache_path(url)
            if not os.path.exists(cache_path):
                return None
            
            with open(cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            logger.info(f"从缓存加载数据: {url}")
            return data
        except Exception as e:
            logger.error(f"加载缓存数据失败: {url} - {str(e)}")
            return None
    
    def exists(self, url: str) -> bool:
        """
        检查URL是否已缓存
        
        Args:
            url: URL
            
        Returns:
            是否已缓存
        """
        # 验证URL
        if not url or not isinstance(url, str):
            logger.error(f"无效的URL: {url}")
            return False
            
        cache_path = self._get_cache_path(url)
        return os.path.exists(cache_path)
    
    def clear(self, url: Optional[str] = None) -> bool:
        """
        清除缓存
        
        Args:
            url: 要清除的URL，如果为None则清除所有缓存
            
        Returns:
            是否清除成功
        """
        try:
            if url:
                # 验证URL
                if not isinstance(url, str):
                    logger.error(f"无效的URL: {url}")
                    return False
                    
                cache_path = self._get_cache_path(url)
                if os.path.exists(cache_path):
                    os.remove(cache_path)
                    logger.info(f"已清除缓存: {url}")
            else:
                for filename in os.listdir(self.cache_dir):
                    if filename.endswith('.json'):
                        os.remove(os.path.join(self.cache_dir, filename))
                logger.info("已清除所有缓存")
            return True
        except Exception as e:
            logger.error(f"清除缓存失败: {str(e)}")
            return False 