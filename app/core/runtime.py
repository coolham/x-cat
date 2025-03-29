"""
X-Cat Runtime Module
核心运行时组件，负责管理组件生命周期和协调组件间通信
"""
import os
import time
import asyncio
import signal
import traceback
from typing import Dict, List, Any, Optional, Set, Type, Callable
from loguru import logger
from datetime import datetime

from app.extractors.base import BaseExtractor
from app.extractors.telegram import TelegramExtractor
from app.extractors.url import URLExtractor
from app.preprocessor.content_preprocessor import ContentPreprocessor
from app.category_system.ai.classifier import AIClassifier
from app.category_system.models.category_manager import CategoryManager
from app.storage.storage import Storage
from app.distributor.distributor import Distributor
from app.core.pipeline import Pipeline, PipelineStage


class Runtime:
    """
    系统运行时
    负责管理组件生命周期和协调组件间通信
    """
    
    def __init__(self, config: Dict[str, Any]):
        """初始化运行时
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.running = False
        self.tasks = []
        
        # 初始化信号处理
        signal.signal(signal.SIGINT, self._handle_interrupt)
        signal.signal(signal.SIGTERM, self._handle_interrupt)
        
        # 初始化组件
        self.extractors = {}  # 内容提取器
        self.preprocessor = None  # 内容预处理器
        self.classifier = None  # AI分类器
        self.distributor = None  # 分发器
        self.storage = None  # 存储组件
        
        # 分类管理器将在initialize中创建
        self.category_manager = None
        
        # 流水线
        self.pipeline = Pipeline()
        
        self.start_time = datetime.now()
        self.health_check_interval = config.get('health_check_interval', 60)
        self._health_check_task: Optional[asyncio.Task] = None
        self._is_healthy = True
        
    def _handle_interrupt(self, sig, frame):
        """处理中断信号"""
        logger.info("收到中断信号，正在关闭系统...")
        self.running = False
        
    async def initialize(self) -> bool:
        """初始化运行时环境
        
        Returns:
            bool: 是否初始化成功
        """
        try:
            # 1. 初始化分类管理器
            self.category_manager = CategoryManager()
            if not await self.category_manager.initialize():
                logger.error("分类管理器初始化失败")
                return False
                
            # 2. 初始化提取器
            telegram_config = self.config.get('telegram_adapter', {})
            self.extractors['telegram'] = TelegramExtractor(telegram_config)
            if not await self.extractors['telegram'].initialize():
                logger.error("Telegram 提取器初始化失败")
                return False
                
            self.extractors['url'] = URLExtractor(self.config.get('url_extractor', {}))
            
            # 3. 初始化预处理器
            preprocessor_config = self.config.get('preprocessor', {
                'proxy_url': self.config.get('system', {}).get('proxy_url'),
                'timeout': 30,
                'max_content_length': 8000,
            })
            self.preprocessor = ContentPreprocessor(
                config=self.config,  # 传入完整的配置
                runtime=self,
                **preprocessor_config
            )
            if not await self.preprocessor.initialize():
                logger.error("预处理器初始化失败")
                return False
                
            # 4. 初始化分类器
            self.classifier = AIClassifier(
                config=self.config.get('classifier', {}),
                runtime=self
            )
            if not await self.classifier.initialize():
                logger.error("分类器初始化失败")
                return False
                
            # 5. 初始化分发器
            self.distributor = Distributor(self.config.get('distributor', {}))
            if not await self.distributor.initialize():
                logger.error("分发器初始化失败")
                return False
                
            # 6. 初始化存储组件
            self.storage = Storage(self.config.get('storage', {}))
            if not await self.storage.initialize():
                logger.error("存储组件初始化失败")
                return False
                
            # 7. 构建流水线
            self.pipeline.add_stage("提取", self._extract_content)
            self.pipeline.add_stage("预处理", self._preprocess_content)
            self.pipeline.add_stage("分类", self._classify_content)
            self.pipeline.add_stage("分发", self._distribute_content)
            self.pipeline.add_stage("存储", self._store_content)
            
            # 启动健康检查
            self._health_check_task = asyncio.create_task(self._health_check_loop())
            
            logger.info("运行时环境初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"运行时环境初始化失败: {str(e)}")
            logger.debug(traceback.format_exc())
            return False
            
    async def _extract_content(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """提取内容
        
        Args:
            data: 输入数据
            
        Returns:
            Dict[str, Any]: 提取结果
        """
        try:
            source_type = data.get('source_type')
            if not source_type:
                logger.warning("未指定源类型，跳过提取")
                return data
                
            if source_type not in self.extractors:
                logger.warning(f"不支持的源类型: {source_type}")
                return data
                
            extractor = self.extractors[source_type]
            if not extractor:
                logger.warning(f"提取器未初始化: {source_type}")
                return data
                
            result = await extractor.extract(data)
            if not result:
                logger.warning(f"提取结果为空: {source_type}")
                return data
                
            return result
            
        except Exception as e:
            logger.error(f"内容提取失败: {str(e)}")
            logger.debug(traceback.format_exc())
            return data
            
    async def _preprocess_content(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """预处理内容
        
        Args:
            data: 输入数据
            
        Returns:
            Dict[str, Any]: 预处理结果
        """
        try:
            if not self.preprocessor:
                raise RuntimeError("预处理器未初始化")
                
            return await self.preprocessor.process(data)
            
        except Exception as e:
            logger.error(f"内容预处理失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'data': data
            }
            
    async def _classify_content(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """分类内容
        
        Args:
            data: 输入数据
            
        Returns:
            Dict[str, Any]: 分类结果
        """
        try:
            if not self.classifier or not self.category_manager:
                raise RuntimeError("分类器或分类管理器未初始化")
                
            # 获取分类提示词
            prompt = self.category_manager.get_ai_prompt()
            
            # 进行分类
            result = await self.classifier.classify(data['content'], prompt)
            
            # 更新数据
            data['classification'] = result
            return data
            
        except Exception as e:
            logger.error(f"内容分类失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'data': data
            }
            
    async def _distribute_content(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """分发内容
        
        Args:
            data: 输入数据
            
        Returns:
            Dict[str, Any]: 分发结果
        """
        try:
            if not self.distributor:
                raise RuntimeError("分发器未初始化")
                
            return await self.distributor.distribute(data)
            
        except Exception as e:
            logger.error(f"内容分发失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'data': data
            }
            
    async def _store_content(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """存储内容
        
        Args:
            data: 输入数据
            
        Returns:
            Dict[str, Any]: 存储结果
        """
        try:
            if not self.storage:
                raise RuntimeError("存储未初始化")
                
            return await self.storage.store(data)
            
        except Exception as e:
            logger.error(f"内容存储失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'data': data
            }
            
    async def process_content(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """处理内容
        
        Args:
            content: 输入内容
            
        Returns:
            Dict[str, Any]: 处理结果
        """
        try:
            # 创建初始Observable
            stream = self.pipeline.process(content)
            
            # 订阅处理结果
            result = None
            def on_next(data):
                nonlocal result
                result = data
                
            def on_error(error):
                logger.error(f"处理错误: {str(error)}")
                
            def on_completed():
                logger.info("处理完成")
                
            # 执行处理
            stream.subscribe(
                on_next=on_next,
                on_error=on_error,
                on_completed=on_completed
            )
            
            return result or {
                'success': False,
                'error': '处理失败',
                'data': content
            }
            
        except Exception as e:
            logger.error(f"内容处理失败: {str(e)}")
            logger.debug(traceback.format_exc())
            return {
                'success': False,
                'error': str(e),
                'data': content
            }
            
    async def health_check(self) -> bool:
        """健康检查
        
        Returns:
            bool: 是否健康
        """
        try:
            # 检查各个组件
            components = [
                self.preprocessor,
                self.classifier,
                self.distributor,
                self.storage
            ]
            
            for component in components:
                if component and not await component.health_check():
                    return False
                    
            return True
            
        except Exception as e:
            logger.error(f"健康检查失败: {str(e)}")
            return False
            
    async def stop(self):
        """停止运行时"""
        try:
            # 停止各个组件
            components = [
                self.preprocessor,
                self.classifier,
                self.distributor,
                self.storage
            ]
            
            for component in components:
                if component:
                    await component.stop()
                    
            # 停止健康检查
            if self._health_check_task:
                self._health_check_task.cancel()
                try:
                    await self._health_check_task
                except asyncio.CancelledError:
                    pass
                self._health_check_task = None
                
            logger.info("运行时已停止")
            
        except Exception as e:
            logger.error(f"停止运行时失败: {str(e)}")
            logger.debug(traceback.format_exc())
            
    async def _health_check_loop(self):
        """健康检查循环"""
        while True:
            try:
                # 检查系统状态
                self._is_healthy = await self._check_health()
                
                # 等待下一次检查
                await asyncio.sleep(self.health_check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"健康检查失败: {str(e)}")
                self._is_healthy = False
                await asyncio.sleep(1)  # 避免过快重试
                
    async def _check_health(self) -> bool:
        """检查系统健康状态
        
        Returns:
            bool: 是否健康
        """
        try:
            # 检查系统资源
            if not self._check_resources():
                return False
                
            # 检查网络连接
            if not await self._check_network():
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"健康检查异常: {str(e)}")
            return False
            
    def _check_resources(self) -> bool:
        """检查系统资源
        
        Returns:
            bool: 资源是否充足
        """
        # TODO: 实现资源检查
        return True
        
    async def _check_network(self) -> bool:
        """检查网络连接
        
        Returns:
            bool: 网络是否正常
        """
        # TODO: 实现网络检查
        return True
        
    @property
    def is_healthy(self) -> bool:
        """获取健康状态
        
        Returns:
            bool: 是否健康
        """
        return self._is_healthy
        
    def get_stats(self) -> Dict[str, Any]:
        """获取运行时统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        return {
            'start_time': self.start_time.isoformat(),
            'uptime': (datetime.now() - self.start_time).total_seconds(),
            'is_healthy': self._is_healthy
        } 