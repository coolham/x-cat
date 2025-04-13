"""
Configuration loader module
"""
import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path
from loguru import logger
from dotenv import load_dotenv

def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load configuration from YAML file
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Configuration dictionary
    """
    try:
        # 加载 YAML 配置
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # 替换配置中的环境变量占位符
        replace_env_vars(config)
        
        return config
    except Exception as e:
        logger.error(f"Error loading configuration: {str(e)}")
        raise

def replace_env_vars(config: Dict[str, Any]) -> None:
    """
    Recursively replace environment variable placeholders in configuration
    
    Args:
        config: Configuration dictionary to process
    """
    for key, value in config.items():
        if isinstance(value, dict):
            replace_env_vars(value)
        elif isinstance(value, str) and value.startswith("${") and value.endswith("}"):
            env_var = value[2:-1]
            if env_var in os.environ:
                config[key] = os.environ[env_var]
            else:
                logger.warning(f"Environment variable {env_var} not found")

def get_config_value(config: Dict[str, Any], key: str, default: Any = None) -> Any:
    """
    Get configuration value by key
    
    Args:
        config: Configuration dictionary
        key: Configuration key
        default: Default value if key not found
        
    Returns:
        Configuration value
    """
    return config.get(key, default)

def get_nested_config_value(config: Dict[str, Any], *keys: str, default: Any = None) -> Any:
    """
    Get nested configuration value by keys
    
    Args:
        config: Configuration dictionary
        keys: Configuration keys
        default: Default value if key not found
        
    Returns:
        Configuration value
    """
    value = config
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return default
    return value 