"""
飞书存储模块
负责将数据存储到飞书文档
"""
import os
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from loguru import logger
from prefect import task

from app.infrastructure.feishu.client import FeishuClient


class FeishuRawStorage:
    """飞书存储模块"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化飞书存储模块
        
        Args:
            config: 配置字典
        """
        self.feishu_client = None
        self.folder_token = None
        self.config = config
        self.app_token = 'ZP1BbR6fqaCpDosf3gXc9OZhnJb'
        self.table_id = 'tblHKTdD3z2gHGNP'
        self._initialized = False
        self.log_file = None  # 用于记录已存储的文档信息
    
    async def initialize(self) -> bool:
        """
        初始化飞书存储模块
        
        Returns:
            初始化是否成功
        """
        try:
            # 获取飞书配置
            if "feishu" not in self.config:
                logger.warning("配置中没有feishu字段，将使用默认配置")
                feishu_config = {}
            else:
                feishu_config = self.config["feishu"]
            
            # 初始化飞书客户端
            self.feishu_client = FeishuClient(
                app_id=feishu_config.get("app_id"),
                app_secret=feishu_config.get("app_secret"),
                proxy_url=feishu_config.get("proxy_url")
            )
            
            # 获取文件夹token
            self.folder_token = feishu_config.get("folder_token")
            if not self.folder_token:
                logger.warning("未指定飞书文件夹token，将使用默认文件夹")
                self.folder_token = "default_folder"
            
            # 初始化日志文件
            storage_path = os.environ.get("PREFECT_LOCAL_STORAGE_PATH", "./prefect_storage")
            os.makedirs(storage_path, exist_ok=True)
            self.log_file = os.path.join(storage_path, "feishu_storage_log.json")
            
            # 如果日志文件不存在，创建一个空列表
            if not os.path.exists(self.log_file):
                with open(self.log_file, 'w', encoding='utf-8') as f:
                    json.dump([], f, ensure_ascii=False, indent=2)
            
            self._initialized = True
            logger.info("飞书存储模块初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"飞书存储模块初始化失败: {str(e)}")
            return False
    
    @task(name="store_to_feishu")
    async def store_to_feishu(self, app_token: str, table_id: str, data: Dict[str, Any]) -> bool:
        """
        存储数据到飞书
        
        Args:
            data: 要存储的数据
            
        Returns:
            是否存储成功
        """
        if not self._initialized:
            logger.error("飞书存储模块未初始化")
            return False
            
        
        self.config["feishu"]["bitable"] = {
            "app_token": 'ZP1BbR6fqaCpDosf3gXc9OZhnJb',
            "table_id": 'tblHKTdD3z2gHGNP'
        }
        #存储到多维表格
        if "feishu" in self.config and "bitable" in self.config["feishu"]:
            bitable_config = self.config["feishu"]["bitable"]
            if "app_token" in bitable_config and "table_id" in bitable_config:
                # 构建字段数据，确保字段名称与飞书多维表格中的字段名称一致
                fields = {
                    "原始内容": data.get("content", ""),
                    "数据类型": data.get("content_type", "TEXT"),
                    "来源": data.get("source_type", "unknown"),
                }
                
                # 保存到飞书多维表格
                bitable_result = await self.feishu_client.create_bitable_record(
                    app_token=bitable_config["app_token"],
                    table_id=bitable_config["table_id"],
                    fields=fields
                )
                
                if bitable_result.get("success", False):
                    # 记录存储信息
                    record_info = {
                        "id": data.get("id", ""),
                        "record_id": bitable_result.get("record_id", ""),
                        "category": data.get("category", ""),
                        "created_at": datetime.now().isoformat()
                    }
                    
                    # 更新本地日志
                    self._update_storage_log(record_info)
                    
                    logger.info(f"数据已保存到飞书多维表格: {data.get('id', '')}")
                else:
                    logger.error(f"保存数据到飞书多维表格失败: {bitable_result.get('error', '未知错误')}")
        
                return True
            else:
                logger.error(f"保存数据到飞书失败")
                return False
    
    def _update_storage_log(self, doc_info: Dict[str, Any]) -> None:
        """
        更新存储日志
        
        Args:
            doc_info: 文档信息
        """
        try:
            # 读取现有日志
            with open(self.log_file, 'r', encoding='utf-8') as f:
                log_data = json.load(f)
            
            # 添加新记录
            log_data.append(doc_info)
            
            # 保存更新后的日志
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, ensure_ascii=False, indent=2)
                
            logger.debug(f"存储日志已更新: {doc_info.get('title', '')}")
        except Exception as e:
            logger.error(f"更新存储日志失败: {str(e)}")
    
    def get_by_id(self, content_id: str) -> Dict[str, Any]:
        """
        通过ID获取内容
        
        Args:
            content_id: 内容ID
            
        Returns:
            获取的内容
        """
        try:
            # 读取存储日志
            with open(self.log_file, 'r', encoding='utf-8') as f:
                log_data = json.load(f)
            
            # 查找匹配ID的内容
            for item in log_data:
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
            # 读取存储日志
            with open(self.log_file, 'r', encoding='utf-8') as f:
                log_data = json.load(f)
            
            # 筛选匹配类别的内容
            for item in log_data:
                if item.get('category') == category:
                    result.append(item)
            
            return result
        except Exception as e:
            logger.error(f"获取类别内容失败: {str(e)}")
            return []
    
    async def store(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        存储数据并返回结果
        
        Args:
            data: 要存储的数据
            
        Returns:
            存储结果，包含成功/失败状态和文档信息
        """
        logger.info(f"开始飞书存储数据: {data}")
        try:
            # 存储到飞书
            app_token = 'ZP1BbR6fqaCpDosf3gXc9OZhnJb'
            table_id = 'tblHKTdD3z2gHGNP'
            success = await self.store_to_feishu(app_token, table_id, data)
            
            if success:
                # 获取最新存储的文档信息
                doc_info = self.get_by_id(data.get("id", ""))
                return {
                    "feishu_storage": "success", 
                    "doc_info": doc_info
                }
            else:
                return {
                    "feishu_storage": "failed", 
                    "error": "存储到飞书失败"
                }
        except Exception as e:
            logger.error(f"飞书存储失败: {str(e)}")
            return {
                "feishu_storage": "failed", 
                "error": str(e)
            } 