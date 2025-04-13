"""
飞书原始消息存储模块
负责将原始消息保存到飞书文档
"""
import os
import json
from datetime import datetime
from typing import Dict, Any, Optional
from loguru import logger
from prefect import task

from app.infrastructure.feishu.client import FeishuClient


class FeishuRawStorage:
    """飞书原始消息存储模块"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化飞书原始消息存储模块
        
        Args:
            config: 配置字典
        """
        self.feishu_client = None
        self.raw_message_folder = None
        self.config = config
        self._initialized = False
    
    async def initialize(self) -> bool:
        """
        初始化飞书原始消息存储模块
        
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
            
            # 获取原始消息存储文件夹
            self.raw_message_folder = feishu_config.get("raw_message_folder")
            if not self.raw_message_folder:
                logger.warning("未指定原始消息存储文件夹，将使用默认文件夹")
                self.raw_message_folder = "原始消息"
            
            self._initialized = True
            logger.info("飞书原始消息存储模块初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"飞书原始消息存储模块初始化失败: {str(e)}")
            return False
    
    @task(name="store_raw_message")
    async def store_raw_message(self, message_data: Dict[str, Any]) -> bool:
        """
        保存原始消息到飞书
        
        Args:
            message_data: 消息数据
            
        Returns:
            是否保存成功
        """
        if not self._initialized:
            logger.error("飞书原始消息存储模块未初始化")
            return False
            
        try:
            # 提取消息信息
            message_id = message_data.get("message_id", "unknown")
            chat_title = message_data.get("chat_title", "未知频道")
            sender_name = message_data.get("sender_name", "未知发送者")
            content = message_data.get("text", "")
            received_at = message_data.get("date", datetime.now().isoformat())
            
            # 构建文档标题
            title = f"{chat_title} - {sender_name} - {received_at}"
            
            # 构建文档内容
            doc_content = f"""
# {title}

## 消息信息
- 消息ID: {message_id}
- 发送者: {sender_name}
- 频道: {chat_title}
- 接收时间: {received_at}

## 消息内容
{content}

## 原始数据
```json
{json.dumps(message_data, ensure_ascii=False, indent=2)}
```
"""
            
            # 保存到飞书
            result = await self.feishu_client.create_document(
                folder_token=self.raw_message_folder,
                title=title,
                content=doc_content
            )
            
            if result.get("success", False):
                logger.info(f"原始消息已保存到飞书: {message_id}")
                return True
            else:
                logger.error(f"保存原始消息到飞书失败: {result.get('error', '未知错误')}")
                return False
                
        except Exception as e:
            logger.error(f"保存原始消息到飞书时出错: {str(e)}")
            return False 