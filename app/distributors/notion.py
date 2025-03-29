# -*- coding: utf-8 -*-
"""
Notion分发器
将内容同步到Notion数据库
"""
import os
from typing import Dict
from loguru import logger
from notion_client import Client

from .base import Distributor

class NotionDistributor(Distributor):
    """Notion分发器"""
    
    def __init__(self):
        """初始化Notion分发器"""
        super().__init__()
        
        # 从配置获取设置
        config = self.config.get_distributor_config(self.name)
        self.database_id = config.get('database_id') or os.getenv('NOTION_DATABASE_ID')
        self.token = os.getenv('NOTION_TOKEN')
        
        if not self.token or not self.database_id:
            raise ValueError("未配置Notion API信息")
        
        # 初始化Notion客户端
        self.client = Client(auth=self.token)
        
        # 缓存数据库结构
        self._cache_database_schema()
    
    def _cache_database_schema(self):
        """缓存数据库结构"""
        try:
            # 获取数据库信息
            database = self.client.databases.retrieve(self.database_id)
            
            # 提取属性定义
            self.properties = database['properties']
            
            # 记录支持的属性
            self.supported_properties = {
                'title': '标题',
                'rich_text': '富文本',
                'number': '数字',
                'select': '选择',
                'multi_select': '多选',
                'date': '日期',
                'checkbox': '复选框'
            }
            
            logger.info("已缓存Notion数据库结构")
            
        except Exception as e:
            logger.error(f"缓存数据库结构失败: {str(e)}")
            self.properties = {}
            self.supported_properties = {}
    
    def _format_notion_page(self, content: Dict) -> Dict:
        """格式化Notion页面数据
        
        Args:
            content: 内容信息
            
        Returns:
            Dict: Notion页面数据
        """
        try:
            # 格式化内容
            formatted = self._format_content(content)
            
            # 构建页面属性
            properties = {
                '标题': {
                    'title': [
                        {
                            'text': {
                                'content': formatted['text'][:100]  # 限制标题长度
                            }
                        }
                    ]
                },
                '来源': {
                    'select': {
                        'name': formatted['source']
                    }
                },
                '分类': {
                    'select': {
                        'name': formatted['classification']['primary']
                    }
                },
                '二级分类': {
                    'select': {
                        'name': formatted['classification']['secondary']
                    }
                },
                '置信度': {
                    'number': formatted['classification']['confidence']
                },
                '分类理由': {
                    'rich_text': [
                        {
                            'text': {
                                'content': formatted['classification']['reasoning']
                            }
                        }
                    ]
                },
                '时间': {
                    'date': {
                        'start': formatted['timestamp']
                    }
                }
            }
            
            # 构建页面内容
            children = [
                {
                    'object': 'block',
                    'type': 'paragraph',
                    'paragraph': {
                        'rich_text': [
                            {
                                'type': 'text',
                                'text': {
                                    'content': formatted['text']
                                }
                            }
                        ]
                    }
                }
            ]
            
            return {
                'parent': {'database_id': self.database_id},
                'properties': properties,
                'children': children
            }
            
        except Exception as e:
            logger.error(f"格式化Notion页面数据失败: {str(e)}")
            return None
    
    async def distribute(self, content: Dict) -> bool:
        """分发内容到Notion
        
        Args:
            content: 内容信息
            
        Returns:
            bool: 是否分发成功
        """
        try:
            # 格式化页面数据
            page_data = self._format_notion_page(content)
            if not page_data:
                return False
            
            # 检查是否已存在
            query = {
                'database_id': self.database_id,
                'filter': {
                    'property': '标题',
                    'title': {
                        'equals': content['id']
                    }
                }
            }
            
            existing = self.client.databases.query(**query)
            if existing['results']:
                logger.warning(f"内容已存在，跳过: {content['id']}")
                return True
            
            # 创建页面
            page = self.client.pages.create(**page_data)
            
            logger.info(f"内容已同步到Notion: {page['id']}")
            return True
            
        except Exception as e:
            logger.error(f"同步内容到Notion失败: {str(e)}")
            return False 