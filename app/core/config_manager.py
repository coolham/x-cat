"""
配置管理模块
负责加载和管理系统配置
"""
import os
import json
import yaml
from typing import Dict, Any, Optional, List
from loguru import logger
from dotenv import load_dotenv

class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_dir: str = "config", env_file: str = ".env"):
        """初始化配置管理器
        
        Args:
            config_dir: 配置文件目录
            env_file: 环境变量文件路径
        """
        self.config_dir = config_dir
        self.env_file = env_file
        self.config = {}
        self.secrets = {}
        
    def load(self) -> Dict[str, Any]:
        """加载所有配置
        
        Returns:
            合并后的配置字典
        """
        # 1. 加载环境变量
        self._load_env()
        
        # 2. 加载基础配置
        self._load_base_config()
        
        # 3. 加载模块配置
        self._load_module_configs()
        
        # 4. 合并配置
        merged_config = self._merge_configs()
        
        return merged_config
        
    def _load_env(self) -> None:
        """加载环境变量"""
        # 加载.env文件
        load_dotenv(self.env_file)
        
        # 提取所有环境变量
        for key, value in os.environ.items():
            # 处理代理设置
            if key in ['HTTP_PROXY', 'HTTPS_PROXY']:
                self.secrets[key.lower()] = value
                logger.info(f"加载代理设置: {key}={value}")
                # 确保环境变量被正确设置
                os.environ[key] = value
                continue
                
            # 处理其他XCAT_前缀的环境变量
            if key.startswith("XCAT_"):
                # 移除前缀并转换为小写
                config_key = key[5:].lower()
                self.secrets[config_key] = value
                
        # 特别检查代理设置
        http_proxy = os.environ.get('HTTP_PROXY', '')
        https_proxy = os.environ.get('HTTPS_PROXY', '')
        logger.info(f"当前环境变量中的代理设置: HTTP_PROXY={http_proxy}, HTTPS_PROXY={https_proxy}")
        
        logger.info(f"已加载 {len(self.secrets)} 个环境变量")
        
    def _load_base_config(self) -> None:
        """加载基础配置"""
        base_config_path = os.path.join(self.config_dir, "base.yaml")
        
        if os.path.exists(base_config_path):
            with open(base_config_path, "r", encoding="utf-8") as f:
                self.config["base"] = yaml.safe_load(f)
            logger.info(f"已加载基础配置: {base_config_path}")
        else:
            self.config["base"] = self._get_default_base_config()
            logger.warning(f"基础配置文件不存在: {base_config_path}，使用默认配置")
            
    def _load_module_configs(self) -> None:
        """加载模块配置"""
        # 加载所有yaml配置文件
        for filename in os.listdir(self.config_dir):
            if filename.endswith(".yaml") and filename != "base.yaml":
                module_name = filename[:-5]  # 移除.yaml后缀
                config_path = os.path.join(self.config_dir, filename)
                
                with open(config_path, "r", encoding="utf-8") as f:
                    self.config[module_name] = yaml.safe_load(f)
                logger.info(f"已加载模块配置: {config_path}")
                
    def _merge_configs(self) -> Dict[str, Any]:
        """合并所有配置
        
        Returns:
            合并后的配置字典
        """
        # 从基础配置开始
        merged = self.config.get("base", {}).copy()
        
        # 合并模块配置
        for module, config in self.config.items():
            if module != "base":
                self._deep_update(merged, {module: config})
                
        # 使用环境变量覆盖配置
        self._apply_env_overrides(merged)
        
        return merged
        
    def _deep_update(self, d: Dict[str, Any], u: Dict[str, Any]) -> Dict[str, Any]:
        """深度更新字典
        
        Args:
            d: 目标字典
            u: 源字典
            
        Returns:
            更新后的字典
        """
        for k, v in u.items():
            if isinstance(v, dict) and k in d and isinstance(d[k], dict):
                d[k] = self._deep_update(d[k], v)
            else:
                d[k] = v
        return d
        
    def _apply_env_overrides(self, config: Dict[str, Any]) -> None:
        """应用环境变量覆盖
        
        Args:
            config: 要更新的配置字典
        """
        # 将环境变量应用到配置中
        for key, value in self.secrets.items():
            # 处理代理设置
            if key in ['http_proxy', 'https_proxy']:
                config['proxy'] = config.get('proxy', {})
                config['proxy'][key] = value
                continue
                
            # 将key转换为配置路径 (例如: "telegram_api_key" -> ["telegram", "api_key"])
            path = key.split("_")
            
            # 遍历路径并更新配置
            current = config
            for i, part in enumerate(path[:-1]):
                if part not in current:
                    current[part] = {}
                current = current[part]
                
            # 设置最终值
            current[path[-1]] = value
            
    def _get_default_base_config(self) -> Dict[str, Any]:
        """获取默认基础配置
        
        Returns:
            默认基础配置字典
        """
        return {
            "system": {
                "log_level": "INFO",
                "log_file": "logs/xcat.log",
                "data_dir": "data",
                "worker_threads": 4,
                "timezone": "Asia/Shanghai",
                "health_check_interval": 60
            },
            "telegram": {
                "enabled": True,
                "channel_id": "",
                "polling_interval": 60,
                "processed_messages_file": "data/processed_messages.json"
            },
            "content_analyzer": {
                "provider": "openai",
                "model": "gpt-4",
                "max_tokens": 2000,
                "temperature": 0.7,
                "max_content_length": 8000,
                "max_total_length": 15000,
                "max_concurrency": 1,
                "cache_dir": "data/analyzer_cache"
            },
            "storage": {
                "db_type": "sqlite",
                "db_path": "data/storage.db",
                "backup_dir": "data/backups",
                "backup_interval": 86400,
                "max_backups": 7
            }
        }
        
    def save_config(self, config: Dict[str, Any], filename: str) -> bool:
        """保存配置到文件
        
        Args:
            config: 要保存的配置
            filename: 文件名
            
        Returns:
            是否保存成功
        """
        try:
            # 确保目录存在
            os.makedirs(self.config_dir, exist_ok=True)
            
            # 保存为YAML格式
            config_path = os.path.join(self.config_dir, filename)
            with open(config_path, "w", encoding="utf-8") as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
                
            logger.info(f"配置已保存到: {config_path}")
            return True
            
        except Exception as e:
            logger.error(f"保存配置失败: {str(e)}")
            return False
            
    def get_config(self) -> Dict[str, Any]:
        """获取当前配置
        
        Returns:
            当前配置字典
        """
        return self.config 