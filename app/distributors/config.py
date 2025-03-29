# -*- coding: utf-8 -*-
"""
分发器配置管理
"""
import os
from typing import Dict, List, Optional
from pathlib import Path
import yaml
from loguru import logger

class DistributorConfig:
    """分发器配置管理"""
    
    def __init__(self):
        """初始化配置管理"""
        self.config_dir = Path('config')
        self.config_file = self.config_dir / 'distributors.yaml'
        self.config = self._load_config()
    
    def _load_config(self) -> Dict:
        """加载配置文件
        
        Returns:
            Dict: 配置信息
        """
        try:
            if not self.config_file.exists():
                return self._create_default_config()
            
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
                
        except Exception as e:
            logger.error(f"加载分发器配置失败: {str(e)}")
            return self._create_default_config()
    
    def _create_default_config(self) -> Dict:
        """创建默认配置
        
        Returns:
            Dict: 默认配置信息
        """
        config = {
            'local': {
                'enabled': True,
                'base_dir': 'data/contents',
                'retry': {
                    'max_attempts': 3,
                    'delay': 1
                }
            },
            'notion': {
                'enabled': False,
                'database_id': os.getenv('NOTION_DATABASE_ID', ''),
                'retry': {
                    'max_attempts': 3,
                    'delay': 2
                }
            }
        }
        
        # 保存默认配置
        self.config_dir.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True, indent=2)
        
        return config
    
    def get_distributor_config(self, name: str) -> Optional[Dict]:
        """获取分发器配置
        
        Args:
            name: 分发器名称
            
        Returns:
            Optional[Dict]: 分发器配置
        """
        return self.config.get(name)
    
    def is_distributor_enabled(self, name: str) -> bool:
        """检查分发器是否启用
        
        Args:
            name: 分发器名称
            
        Returns:
            bool: 是否启用
        """
        return self.config.get(name, {}).get('enabled', False)
    
    def get_retry_config(self, name: str) -> Dict:
        """获取重试配置
        
        Args:
            name: 分发器名称
            
        Returns:
            Dict: 重试配置
        """
        return self.config.get(name, {}).get('retry', {
            'max_attempts': 3,
            'delay': 1
        })
    
    def update_config(self, name: str, config: Dict) -> bool:
        """更新分发器配置
        
        Args:
            name: 分发器名称
            config: 新配置
            
        Returns:
            bool: 是否更新成功
        """
        try:
            if name not in self.config:
                self.config[name] = {}
            
            self.config[name].update(config)
            
            # 保存配置
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, allow_unicode=True, indent=2)
            
            return True
            
        except Exception as e:
            logger.error(f"更新分发器配置失败: {str(e)}")
            return False 