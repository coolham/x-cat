"""
飞书 API 客户端
提供与飞书 API 交互的基础功能
"""
import os
import json
import aiohttp
from typing import Dict, Any, List, Optional
from loguru import logger
from lark_oapi.api.bitable.v1 import *
from lark_oapi.api.bitable.v1.model import (
    AppTableCreateHeader, AppTableFieldProperty, AppTableFieldPropertyOption,
    ReqTable, CreateAppTableRequestBody, PatchAppTableRequestBody
)
from lark_oapi import RequestOption

from app.infrastructure.feishu.token_manager import FeishuTokenManager


class FeishuClient:
    """飞书 API 客户端"""
    
    def __init__(self, app_id: Optional[str] = None, app_secret: Optional[str] = None, proxy_url: Optional[str] = None):
        """
        初始化飞书客户端
        
        Args:
            app_id: 飞书应用 ID
            app_secret: 飞书应用密钥
            proxy_url: 代理服务器 URL
        """
        self.token_manager = FeishuTokenManager(app_id, app_secret, proxy_url)
        self.session = None
        self.client = None
    
    async def initialize(self) -> bool:
        """
        初始化客户端
        
        Returns:
            初始化是否成功
        """
        try:
            # 初始化 Token 管理器
            if not await self.token_manager.initialize():
                return False
            
            # 创建 aiohttp session
            self.session = aiohttp.ClientSession()
            
            # 初始化 lark_oapi 客户端
            from lark_oapi import Client
            self.client = Client.builder() \
                .app_id(self.token_manager.app_id) \
                .app_secret(self.token_manager.app_secret) \
                .build()
            
            logger.info("飞书客户端初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"飞书客户端初始化失败: {str(e)}")
            return False
    
    async def cleanup(self) -> None:
        """清理资源"""
        if self.session:
            await self.session.close()
            self.session = None
        await self.token_manager.cleanup()
    
    async def create_document(self, folder_token: str, title: str, content: str) -> Dict[str, Any]:
        """
        创建文档
        
        Args:
            folder_token: 文件夹 token
            title: 文档标题
            content: 文档内容
            
        Returns:
            创建结果
        """
        try:
            if not self.session:
                if not await self.initialize():
                    return {"success": False, "error": "飞书客户端未初始化"}
            
            # 获取请求头
            headers = await self.token_manager.get_headers()
            if not headers:
                return {"success": False, "error": "获取请求头失败"}
            
            # 构建请求
            url = "https://open.feishu.cn/open-apis/doc/v2/documents"
            data = {
                "folder_token": folder_token,
                "title": title,
                "content": content
            }
            
            # 设置代理
            kwargs = {}
            if self.token_manager.proxy_url:
                kwargs["proxy"] = self.token_manager.proxy_url
            
            # 发送请求
            async with self.session.post(url, headers=headers, json=data, **kwargs) as response:
                result = await response.json()
                
                if result.get("code") == 0:
                    return {"success": True, "data": result.get("data")}
                else:
                    return {"success": False, "error": result.get("msg")}
                
        except Exception as e:
            logger.error(f"创建飞书文档时出错: {str(e)}")
            return {"success": False, "error": str(e)}
    
    # 表格相关功能
    async def list_tables(self, app_token: str, page_size: int = 20, page_token: Optional[str] = None) -> Dict[str, Any]:
        """
        列出数据表
        
        Args:
            app_token: 应用 token
            page_size: 每页数量
            page_token: 分页 token
            
        Returns:
            数据表列表
        """
        try:
            if not self.client:
                if not await self.initialize():
                    return {}
            
            request = ListAppTableRequest.builder() \
                .app_token(app_token) \
                .page_size(page_size)
            
            if page_token:
                request.page_token(page_token)
            
            response = self.client.bitable.v1.app_table.list(request.build())
            
            if response.code == 0:
                # 打印原始返回信息
                logger.info("原始返回信息:")
                logger.info(f"Response code: {response.code}")
                logger.info(f"Response msg: {response.msg}")
                logger.info(f"Response data: {response.data}")
                logger.info(f"Response data type: {type(response.data)}")
                if hasattr(response.data, 'items'):
                    logger.info(f"Items type: {type(response.data.items)}")
                    if response.data.items:
                        logger.info(f"First item type: {type(response.data.items[0])}")
                        logger.info(f"First item dir: {dir(response.data.items[0])}")
                
                items = []
                for item in response.data.items:
                    item_dict = {
                        "table_id": getattr(item, 'table_id', None),
                        "name": getattr(item, 'name', None),
                        "revision": getattr(item, 'revision', None)
                    }
                    items.append(item_dict)
                
                logger.info(f"成功获取数据表列表，共 {len(items)} 个")
                return {
                    "items": items,
                    "page_token": getattr(response.data, 'page_token', None),
                    "has_more": getattr(response.data, 'has_more', False)
                }
            else:
                logger.error(f"获取数据表列表失败: {response.msg}")
                return {}
                
        except Exception as e:
            logger.error(f"列出数据表时出错: {str(e)}")
            return {}
    
    def _build_field(self, field: Dict[str, Any]) -> AppTableCreateHeader:
        """
        构建字段
        
        Args:
            field: 字段信息
            
        Returns:
            字段对象
        """
        field_type = field.get("type", "text")
        field_name = field.get("name", "")
        
        if field_type == "text":
            return AppTableCreateHeader.builder() \
                .field_name(field_name) \
                .type(1) \
                .build()
        elif field_type == "number":
            return AppTableCreateHeader.builder() \
                .field_name(field_name) \
                .type(2) \
                .build()
        elif field_type == "select":
            options = field.get("property", {}).get("options", [])
            return AppTableCreateHeader.builder() \
                .field_name(field_name) \
                .type(3) \
                .ui_type("SingleSelect") \
                .property(AppTableFieldProperty.builder()
                    .options([AppTableFieldPropertyOption.builder()
                        .name(option.get("name", ""))
                        .color(i)
                        .build() for i, option in enumerate(options)])
                    .build()) \
                .build()
        elif field_type == "dateTime":
            return AppTableCreateHeader.builder() \
                .field_name(field_name) \
                .type(5) \
                .build()
        else:
            return AppTableCreateHeader.builder() \
                .field_name(field_name) \
                .type(1) \
                .build()
    
    async def create_table(self, app_token: str, name: str, fields: List[Dict[str, Any]]) -> Optional[str]:
        """
        创建数据表
        
        Args:
            app_token: 应用 token
            name: 数据表名称
            fields: 字段列表
            
        Returns:
            数据表 ID
        """
        try:
            if not self.client:
                if not await self.initialize():
                    return None
            
            # 构建请求
            request = CreateAppTableRequest.builder() \
                .request_body(CreateAppTableRequestBody.builder()
                    .table(ReqTable.builder()
                        .name(name)
                        .default_view_name("默认视图")
                        .fields([self._build_field(field) for field in fields])
                        .build())
                    .build()) \
                .build()
            
            # 构建请求选项
            option = RequestOption.builder().user_access_token(await self.token_manager.get_token()).build()
            
            # 发送请求
            response = self.client.bitable.v1.app_table.create(request, option)
            
            # 打印原始返回信息
            logger.info("原始返回信息:")
            logger.info(f"Response code: {response.code}")
            logger.info(f"Response msg: {response.msg}")
            logger.info(f"Response data: {response.data}")
            logger.info(f"Response data type: {type(response.data)}")
            
            if response.code == 0:
                logger.info(f"成功创建数据表: {name} (ID: {response.data.table_id})")
                return response.data.table_id
            else:
                logger.error(f"创建数据表失败: {response.msg}")
                return None
                
        except Exception as e:
            logger.error(f"创建数据表时出错: {str(e)}")
            return None
    
    async def update_table(self, app_token: str, table_id: str, name: str) -> bool:
        """
        更新数据表
        
        Args:
            app_token: 应用 token
            table_id: 数据表 ID
            name: 新的数据表名称
            
        Returns:
            是否成功
        """
        try:
            if not self.client:
                if not await self.initialize():
                    return False
            
            request = PatchAppTableRequest.builder() \
                .app_token(app_token) \
                .table_id(table_id) \
                .request_body(PatchAppTableRequestBody.builder()
                    .name(name)
                    .build()) \
                .build()
            
            response = await self.client.bitable.patch_app_table(request)
            
            if response.code == 0:
                logger.info(f"成功更新数据表: {name} (ID: {table_id})")
                return True
            else:
                logger.error(f"更新数据表失败: {response.msg}")
                return False
                
        except Exception as e:
            logger.error(f"更新数据表时出错: {str(e)}")
            return False
    
    def _build_record_fields(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        """
        构建记录字段
        
        Args:
            fields: 字段值
            
        Returns:
            记录字段
        """
        record_fields = {}
        for key, value in fields.items():
            record_fields[key] = value
        return record_fields
    
    async def add_record(self, app_token: str, table_id: str, fields: Dict[str, Any]) -> Optional[str]:
        """
        添加记录
        
        Args:
            app_token: 应用 token
            table_id: 数据表 ID
            fields: 字段值
            
        Returns:
            记录 ID
        """
        try:
            if not self.client:
                if not await self.initialize():
                    return None
            
            request = CreateAppTableRecordRequest.builder() \
                .app_token(app_token) \
                .table_id(table_id) \
                .record(Record.builder()
                    .fields(self._build_record_fields(fields))
                    .build()) \
                .build()
            
            response = await self.client.bitable.create_app_table_record(request)
            
            if response.code == 0:
                logger.info(f"成功添加记录: {response.data.record_id}")
                return response.data.record_id
            else:
                logger.error(f"添加记录失败: {response.msg}")
                return None
                
        except Exception as e:
            logger.error(f"添加记录时出错: {str(e)}")
            return None
    
    async def update_record(self, app_token: str, table_id: str, record_id: str, fields: Dict[str, Any]) -> bool:
        """
        更新记录
        
        Args:
            app_token: 应用 token
            table_id: 数据表 ID
            record_id: 记录 ID
            fields: 字段值
            
        Returns:
            是否成功
        """
        try:
            if not self.client:
                if not await self.initialize():
                    return False
            
            request = UpdateAppTableRecordRequest.builder() \
                .app_token(app_token) \
                .table_id(table_id) \
                .record_id(record_id) \
                .record(Record.builder()
                    .fields(self._build_record_fields(fields))
                    .build()) \
                .build()
            
            response = await self.client.bitable.update_app_table_record(request)
            
            if response.code == 0:
                logger.info(f"成功更新记录: {record_id}")
                return True
            else:
                logger.error(f"更新记录失败: {response.msg}")
                return False
                
        except Exception as e:
            logger.error(f"更新记录时出错: {str(e)}")
            return False
    
    async def delete_record(self, app_token: str, table_id: str, record_id: str) -> bool:
        """
        删除记录
        
        Args:
            app_token: 应用 token
            table_id: 数据表 ID
            record_id: 记录 ID
            
        Returns:
            是否成功
        """
        try:
            if not self.client:
                if not await self.initialize():
                    return False
            
            request = DeleteAppTableRecordRequest.builder() \
                .app_token(app_token) \
                .table_id(table_id) \
                .record_id(record_id) \
                .build()
            
            response = await self.client.bitable.delete_app_table_record(request)
            
            if response.code == 0:
                logger.info(f"成功删除记录: {record_id}")
                return True
            else:
                logger.error(f"删除记录失败: {response.msg}")
                return False
                
        except Exception as e:
            logger.error(f"删除记录时出错: {str(e)}")
            return False
    
    async def get_record(self, app_token: str, table_id: str, record_id: str) -> Optional[Dict[str, Any]]:
        """
        获取记录
        
        Args:
            app_token: 应用 token
            table_id: 数据表 ID
            record_id: 记录 ID
            
        Returns:
            记录信息
        """
        try:
            if not self.client:
                if not await self.initialize():
                    return None
            
            request = GetAppTableRecordRequest.builder() \
                .app_token(app_token) \
                .table_id(table_id) \
                .record_id(record_id) \
                .build()
            
            response = await self.client.bitable.get_app_table_record(request)
            
            if response.code == 0:
                logger.info(f"成功获取记录: {record_id}")
                return response.data.record
            else:
                logger.error(f"获取记录失败: {response.msg}")
                return None
                
        except Exception as e:
            logger.error(f"获取记录时出错: {str(e)}")
            return None
    
    async def list_records(self, app_token: str, table_id: str, page_size: int = 20, page_token: Optional[str] = None) -> Dict[str, Any]:
        """
        获取记录列表
        
        Args:
            app_token: 应用 token
            table_id: 数据表 ID
            page_size: 每页数量
            page_token: 分页 token
            
        Returns:
            记录列表
        """
        try:
            if not self.client:
                if not await self.initialize():
                    return {}
            
            request = ListAppTableRecordRequest.builder() \
                .app_token(app_token) \
                .table_id(table_id) \
                .page_size(page_size)
            
            if page_token:
                request.page_token(page_token)
            
            response = await self.client.bitable.list_app_table_record(request.build())
            
            if response.code == 0:
                logger.info(f"成功获取记录列表，共 {len(response.data.items)} 条")
                return {
                    "items": response.data.items,
                    "page_token": response.data.page_token,
                    "has_more": response.data.has_more
                }
            else:
                logger.error(f"获取记录列表失败: {response.msg}")
                return {}
                
        except Exception as e:
            logger.error(f"获取记录列表时出错: {str(e)}")
            return {}
    
    async def create_bitable_record(self, app_token: str, table_id: str, fields: Dict[str, Any]) -> Dict[str, Any]:
        """
        向飞书多维表格插入数据记录
        
        Args:
            app_token: 多维表格的 app_token
            table_id: 多维表格的 table_id
            fields: 要插入的字段数据，格式为 {"字段名": "字段值"}
            
        Returns:
            插入结果
        """
        try:
            if not self.client:
                if not await self.initialize():
                    return {"success": False, "error": "飞书客户端未初始化"}
            
            # 获取访问令牌
            tenant_access_token = await self.token_manager.get_tenant_access_token()
            if not tenant_access_token:
                return {"success": False, "error": "获取访问令牌失败"}
            
            # 确保fields是JSON格式数据
            if not isinstance(fields, dict):
                logger.error(f"fields参数必须是字典类型，当前类型: {type(fields)}")
                return {"success": False, "error": "fields参数必须是字典类型"}
            
            # 打印调试信息
            logger.info(f"准备写入多维表格数据: {json.dumps(fields, ensure_ascii=False)}")
            
            # 构造请求对象
            request = CreateAppTableRecordRequest.builder() \
                .app_token(app_token) \
                .table_id(table_id) \
                .user_id_type("user_id") \
                .request_body(AppTableRecord.builder()
                    .fields(fields)
                    .build()) \
                .build()
            
            # 发起请求
            option = RequestOption.builder().tenant_access_token(tenant_access_token).build()
            response = self.client.bitable.v1.app_table_record.create(request, option)
            
            # 处理失败返回
            if not response.success():
                error_msg = f"创建多维表格记录失败, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}"
                logger.error(error_msg)
                return {"success": False, "error": error_msg}
            
            # 处理业务结果 - 避免直接序列化response.data对象
            logger.info(f"成功创建多维表格记录，记录ID: {response.data.record.record_id}")
            return {
                "success": True,
                "record_id": response.data.record.record_id,
                "data": {
                    "record_id": response.data.record.record_id,
                    "fields": response.data.record.fields
                }
            }
            
        except Exception as e:
            print(str(e))
            error_msg = f"插入表格记录时出错: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg} 