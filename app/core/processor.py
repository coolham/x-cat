# -*- coding: utf-8 -*-
"""
核心应用逻辑
协调信息源处理、分类和分发模块
"""
import asyncio
from typing import Dict, List
from loguru import logger

from app.sources.telegram import TelegramSource
# from app.category_system.services.category_service import CategoryService
# from app.distributors.notion import NotionDistributor
# from app.distributors.local import LocalDistributor

class ContentProcessor:
    """内容处理器，协调各个模块的工作"""
    
    def __init__(self):
        """初始化内容处理器"""
        # 初始化分类服务
        # self.category_service = CategoryService()
        
        # 初始化信息源
        self.sources = [
            TelegramSource(content_processor=self)
        ]
        
        # 初始化分发器
        # self.distributors = [
        #     LocalDistributor(),
        #     NotionDistributor()
        # ]
    
    async def initialize(self) -> bool:
        """初始化内容处理器
        
        Returns:
            bool: 是否初始化成功
        """
        try:
            # 初始化所有信息源
            for source in self.sources:
                if not await source.initialize():
                    logger.error(f"初始化信息源失败: {source.__class__.__name__}")
                    return False
            return True
        except Exception as e:
            logger.error(f"初始化内容处理器失败: {str(e)}")
            return False
    
    async def process_content(self, content: Dict) -> bool:
        """处理内容
        
        Args:
            content: 内容信息，包含以下字段：
                - id: 内容ID
                - text: 内容文本
                - source: 来源
                - metadata: 元数据
                
        Returns:
            bool: 是否处理成功
        """
        try:
            # 1. 分类
            # classification = self.category_service.classify_content(
            #     content['text'],
            #     content['id'],
            #     content.get('language', 'zh')
            # )
            
            # 2. 分发
            # for distributor in self.distributors:
            #     try:
            #         await distributor.distribute({
            #             **content,
            #             'classification': classification
            #         })
            #     except Exception as e:
            #         logger.error(f"分发失败 ({distributor.__class__.__name__}): {str(e)}")
            
            # 暂时只打印接收到的消息
            print("\n=== 收到新消息 ===")
            print(f"消息ID: {content.get('id')}")
            print(f"消息内容: {content.get('text', '')}")
            print(f"消息来源: {content.get('source', '')}")
            print(f"元数据: {content.get('metadata', {})}")
            print("================\n")
            
            return True
            
        except Exception as e:
            logger.error(f"内容处理失败: {str(e)}")
            return False
    
    async def run(self):
        """运行内容处理器"""
        print("开始运行 Telegram 消息接收服务...")
        
        # 初始化
        if not await self.initialize():
            logger.error("初始化失败")
            return
            
        while True:
            try:
                # 从各个信息源获取内容
                for source in self.sources:
                    try:
                        contents = await source.get_contents()
                        for content in contents:
                            await self.process_content(content)
                    except Exception as e:
                        logger.error(f"从信息源获取内容失败 ({source.__class__.__name__}): {str(e)}")
                
                # 等待一段时间后继续
                await asyncio.sleep(60)  # 每分钟检查一次
                
            except Exception as e:
                logger.error(f"主循环异常: {str(e)}")
                await asyncio.sleep(300)  # 发生错误时等待5分钟后重试 