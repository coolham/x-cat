"""
配置加载器
"""
import os
import json
import logging
from typing import Dict, Any, Optional


class ConfigLoader:
    """配置加载器"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置加载器
        
        Args:
            config_path: 配置文件路径，如果为None则使用默认路径
        """
        self.logger = logging.getLogger(__name__)
        self.config_path = config_path or os.path.join('config', 'config.json')
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """
        加载配置文件
        
        Returns:
            配置字典
        """
        try:
            if not os.path.exists(self.config_path):
                self.logger.warning(f"配置文件不存在: {self.config_path}，将使用默认配置")
                return self.get_default_config()
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            self.logger.info(f"配置文件加载成功: {self.config_path}")
            return config
        except Exception as e:
            self.logger.error(f"加载配置文件失败: {str(e)}，将使用默认配置")
            return self.get_default_config()
    
    def get_default_config(self) -> Dict[str, Any]:
        """
        获取默认配置
        
        Returns:
            默认配置字典
        """
        return {
            "data_source": {
                "type": "telegram",
                "api_key": "YOUR_TELEGRAM_BOT_API_KEY",
                "channel_id": "YOUR_CHANNEL_ID"
            },
            "analyzer": {
                "type": "gpt",
                "api_key": "YOUR_GPT_API_KEY",
                "categories": ["AI", "Python", "电子设计", "数字货币", "其他"]
            },
            "storage": {
                "type": "local",
                "db_path": "data/xcat.db"
            },
            "logging": {
                "level": "INFO",
                "file": "logs/xcat.log"
            }
        }
    
    def save_config(self, config: Dict[str, Any]) -> bool:
        """
        保存配置到文件
        
        Args:
            config: 要保存的配置
            
        Returns:
            是否保存成功
        """
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(os.path.abspath(self.config_path)), exist_ok=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            
            self.config = config
            self.logger.info(f"配置保存成功: {self.config_path}")
            return True
        except Exception as e:
            self.logger.error(f"保存配置失败: {str(e)}")
            return False
    
    def get_config(self) -> Dict[str, Any]:
        """
        获取当前配置
        
        Returns:
            配置字典
        """
        return self.config 