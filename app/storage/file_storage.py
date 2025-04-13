"""
基于文件的本地存储实现
"""
import os
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from loguru import logger

from .base import StorageBackend


class FileStorage(StorageBackend):
    """基于文件的本地存储实现"""
    
    def __init__(self, storage_path: str = None):
        """
        初始化本地存储
        
        Args:
            storage_path: 存储路径，如果为 None，则使用环境变量 PREFECT_LOCAL_STORAGE_PATH
        """
        self.storage_path = storage_path or os.environ.get("PREFECT_LOCAL_STORAGE_PATH", "./prefect_storage")
        os.makedirs(self.storage_path, exist_ok=True)
        
        # 使用单个文件保存所有记录
        self.log_file = os.path.join(self.storage_path, "data_log.json")
        
        # 如果文件不存在，创建一个空列表
        if not os.path.exists(self.log_file):
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False, indent=2)
        
        logger.info(f"文件存储初始化完成，路径: {self.storage_path}，日志文件: {self.log_file}")
    
    def save(self, analyzed_content: Dict[str, Any]) -> bool:
        """
        保存内容到本地文件
        
        Args:
            analyzed_content: 要存储的内容
            
        Returns:
            是否成功保存
        """
        try:
            # 读取现有数据
            with open(self.log_file, 'r', encoding='utf-8') as f:
                data_list = json.load(f)
            
            # 添加新数据
            data_list.append(analyzed_content)
            
            # 保存更新后的数据
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump(data_list, f, ensure_ascii=False, indent=2)
            
            logger.info(f"数据已追加到日志文件: {self.log_file}")
            return True
        except Exception as e:
            logger.error(f"本地存储失败: {str(e)}")
            return False
    
    def get_by_id(self, content_id: str) -> Dict[str, Any]:
        """
        通过ID获取内容
        
        Args:
            content_id: 内容ID
            
        Returns:
            获取的内容
        """
        try:
            # 读取所有数据
            with open(self.log_file, 'r', encoding='utf-8') as f:
                data_list = json.load(f)
            
            # 查找匹配ID的内容
            for item in data_list:
                if item.get('id') == content_id:
                    return item
            
            logger.warning(f"未找到ID为 {content_id} 的内容")
            return {}
        except Exception as e:
            logger.error(f"获取内容失败: {str(e)}")
            return {}
    
    def get_by_category(self, category: str) -> List[Dict[str, Any]]:
        """
        获取特定类别的所有内容
        
        Args:
            category: 内容类别
            
        Returns:
            内容列表
        """
        result = []
        try:
            # 读取所有数据
            with open(self.log_file, 'r', encoding='utf-8') as f:
                data_list = json.load(f)
            
            # 筛选匹配类别的内容
            for item in data_list:
                if item.get('category') == category:
                    result.append(item)
            
            return result
        except Exception as e:
            logger.error(f"获取类别内容失败: {str(e)}")
            return []
    
    def store(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        存储数据并返回结果
        
        Args:
            data: 要存储的数据
            
        Returns:
            存储结果，包含成功/失败状态和文件路径
        """
        logger.info(f"开始本地存储数据: {data}")
        try:
            # 创建可序列化的数据副本
            serializable_data = {}
            for key, value in data.items():
                # 处理非 JSON 可序列化的对象
                if hasattr(value, '__dict__'):
                    # 如果是对象，尝试转换为字典
                    serializable_data[key] = value.__dict__
                elif hasattr(value, 'isoformat'):
                    # 如果是日期时间对象
                    serializable_data[key] = value.isoformat()
                elif hasattr(value, 'name') and hasattr(value, 'value'):
                    # 如果是枚举类型
                    serializable_data[key] = value.name
                else:
                    # 其他类型直接复制
                    serializable_data[key] = value
            
            # 尝试读取现有数据，如果文件为空或格式错误，则创建一个空列表
            try:
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:
                        data_list = json.loads(content)
                    else:
                        data_list = []
            except (json.JSONDecodeError, FileNotFoundError):
                logger.warning(f"日志文件 {self.log_file} 不存在或格式错误，将创建新文件")
                data_list = []
            
            # 添加新数据
            data_list.append(serializable_data)
            
            # 保存更新后的数据
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump(data_list, f, ensure_ascii=False, indent=2)
            
            logger.info(f"数据已追加到日志文件: {self.log_file}")
            return {"local_storage": "success", "path": self.log_file}
        except Exception as e:
            logger.error(f"本地存储失败: {str(e)}")
            return {"local_storage": "failed", "error": str(e)} 