"""
Content storage module
"""
import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional
from loguru import logger
from prefect import task
from .base_processor import BaseProcessor

class ContentStorage(BaseProcessor):
    """Content storage that stores content in a database"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize storage
        
        Args:
            config: Storage configuration
        """
        super().__init__(config)
        self.db_path = config.get("db_path", "data/storage.db")
        self.backup_dir = config.get("backup_dir", "data/backups")
        
    def initialize(self) -> bool:
        """Initialize the storage
        
        Returns:
            bool: Whether initialization was successful
        """
        try:
            logger.info("Initializing content storage")
            
            # 确保目录存在
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            os.makedirs(self.backup_dir, exist_ok=True)
            super().initialize()
            return True
        except Exception as e:
            logger.error(f"Error initializing content storage: {str(e)}")
            return False
        
    def cleanup(self) -> None:
        """Cleanup storage resources"""
        logger.info("Cleaning up content storage")
        super().cleanup()
        
    @task
    def process(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Store content
        
        Args:
            content: Content to store
            
        Returns:
            Stored content
        """
        if not self._initialized:
            self.initialize()
            
        try:
            # 添加存储时间戳
            content["storage"] = {
                "timestamp": datetime.now().isoformat(),
                "db_path": self.db_path
            }
            
            # 保存到文件
            file_path = os.path.join(
                os.path.dirname(self.db_path),
                f"content_{content['metadata']['message_id']}.json"
            )
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(content, f, ensure_ascii=False, indent=2)
            
            logger.debug(f"Content stored: {file_path}")
            return content
            
        except Exception as e:
            logger.error(f"Error storing content: {str(e)}")
            raise 