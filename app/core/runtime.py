"""
X-Cat Runtime Module
核心运行时组件，负责管理模块生命周期和协调模块间通信
"""
import os
import time
import asyncio
import signal
import traceback
from typing import Dict, List, Any, Optional, Set, Type, Callable

from loguru import logger

from app.core import Module, ModuleState, Event


class Runtime:
    """
    系统运行时
    负责管理模块生命周期和协调模块间通信
    """
    
    def __init__(self):
        """初始化运行时"""
        self.modules: Dict[str, Module] = {}
        self.event_subscribers: Dict[str, List[Callable]] = {}
        self.running = False
        self.tasks = []
        
        # 初始化信号处理
        signal.signal(signal.SIGINT, self._handle_interrupt)
        signal.signal(signal.SIGTERM, self._handle_interrupt)
    
    def _handle_interrupt(self, sig, frame):
        """处理中断信号"""
        logger.info("Received interrupt signal, shutting down system...")
        self.running = False
        
    def register_module(self, module_class: Type[Module], module_id: str, **kwargs) -> Module:
        """
        注册模块
        
        Args:
            module_class: 模块类
            module_id: 模块ID
            **kwargs: 其他参数
            
        Returns:
            注册的模块实例
        """
        if module_id in self.modules:
            logger.warning(f"Module ID '{module_id}' already exists, will be replaced")
        
        module = module_class(self, module_id, **kwargs)
        self.modules[module_id] = module
        logger.info(f"Registered module: {module.name} (ID: {module_id})")
        return module
    
    def unregister_module(self, module_id: str) -> bool:
        """
        注销模块
        
        Args:
            module_id: 模块ID
            
        Returns:
            是否成功注销
        """
        if module_id not in self.modules:
            logger.warning(f"Module ID '{module_id}' does not exist, cannot unregister")
            return False
        
        module = self.modules[module_id]
        # 检查是否有其他模块依赖此模块
        for other_id, other_module in self.modules.items():
            if module_id in other_module.get_dependencies():
                logger.warning(f"Module '{other_id}' depends on '{module_id}', cannot unregister")
                return False
        
        del self.modules[module_id]
        logger.info(f"Unregistered module: {module.name} (ID: {module_id})")
        return True
    
    def get_module(self, module_id: str) -> Optional[Module]:
        """
        获取模块实例
        
        Args:
            module_id: 模块ID
            
        Returns:
            模块实例，不存在则返回None
        """
        return self.modules.get(module_id)
    
    async def initialize_modules(self, config: Dict[str, Any]) -> bool:
        """
        初始化所有模块
        
        Args:
            config: 全局配置
            
        Returns:
            是否所有模块都成功初始化
        """
        # 解析依赖关系，确定初始化顺序
        module_order = self._resolve_dependencies()
        
        # 按顺序初始化模块
        all_success = True
        for module_id in module_order:
            module = self.modules[module_id]
            
            # 跳过已经初始化的模块
            if module.state.name in ["INITIALIZED", "RUNNING", "PAUSED"]:
                logger.debug(f"跳过已初始化的模块: {module_id}")
                continue
                
            try:
                logger.debug(f"正在初始化模块: {module_id}")
                if await module.initialize(config):
                    logger.info(f"Module '{module_id}' initialized successfully")
                else:
                    logger.error(f"Module '{module_id}' initialization failed")
                    all_success = False
            except Exception as e:
                logger.error(f"Module '{module_id}' initialization error: {str(e)}")
                all_success = False
        
        return all_success
    
    async def start_modules(self) -> bool:
        """
        启动所有模块
        
        Returns:
            是否所有模块都成功启动
        """
        # 确定启动顺序，考虑依赖关系
        start_order = self._resolve_dependencies()
        if not start_order:
            logger.error("Circular dependency detected, cannot determine module start order")
            return False
        
        all_successful = True
        for module_id in start_order:
            module = self.modules[module_id]
            try:
                success = await module.start()
                if not success:
                    logger.error(f"Module '{module_id}' start failed")
                    all_successful = False
                else:
                    logger.info(f"Module '{module_id}' started successfully")
            except Exception as e:
                logger.error(f"Module '{module_id}' start error: {str(e)}")
                logger.debug(traceback.format_exc())
                all_successful = False
                module.state = ModuleState.ERROR
        
        return all_successful
    
    async def stop_modules(self) -> bool:
        """
        停止所有模块
        
        Returns:
            是否所有模块都成功停止
        """
        # 按依赖关系的反向顺序停止
        stop_order = list(reversed(self._resolve_dependencies()))
        
        all_successful = True
        for module_id in stop_order:
            module = self.modules[module_id]
            try:
                success = await module.stop()
                if not success:
                    logger.error(f"Module '{module_id}' stop failed")
                    all_successful = False
                else:
                    logger.info(f"Module '{module_id}' stopped successfully")
            except Exception as e:
                logger.error(f"Module '{module_id}' stop error: {str(e)}")
                logger.debug(traceback.format_exc())
                all_successful = False
                module.state = ModuleState.ERROR
        
        return all_successful
    
    def _resolve_dependencies(self) -> List[str]:
        """
        解析模块依赖关系，确定启动顺序
        
        Returns:
            模块ID列表，按启动顺序排序
        """
        # 拓扑排序算法
        visited = set()
        temp_visited = set()
        order = []
        
        def visit(node):
            if node in temp_visited:
                # 检测到循环依赖
                return False
            if node in visited:
                return True
            
            temp_visited.add(node)
            
            # 访问所有依赖
            module = self.modules[node]
            for dependency in module.get_dependencies():
                if dependency not in self.modules:
                    logger.warning(f"Module '{node}' depends on non-existent module '{dependency}'")
                    continue
                if not visit(dependency):
                    return False
            
            temp_visited.remove(node)
            visited.add(node)
            order.append(node)
            return True
        
        # 访问所有模块
        for module_id in self.modules:
            if module_id not in visited:
                if not visit(module_id):
                    return []  # 存在循环依赖
        
        return order
    
    async def publish_event(self, event: Event) -> None:
        """
        发布事件
        
        Args:
            event: 事件对象
        """
        event_type = event.event_type
        
        logger.debug(f"正在发布事件: 类型={event_type}, 来源={event.source}")
        
        if event_type not in self.event_subscribers or not self.event_subscribers[event_type]:
            logger.debug(f"没有订阅者处理事件: {event_type}")
            return
        
        subscriber_count = len(self.event_subscribers[event_type])
        logger.debug(f"找到 {subscriber_count} 个订阅者处理事件: {event_type}")
        
        # 异步执行所有回调函数
        tasks = []
        for callback in self.event_subscribers[event_type]:
            # 记录回调信息
            callback_info = getattr(callback, "__qualname__", str(callback))
            logger.debug(f"调用事件回调: {callback_info}")
            
            # 创建异步任务
            task = asyncio.create_task(self._safe_callback(callback, event))
            tasks.append(task)
        
        # 等待所有回调完成
        if tasks:
            try:
                await asyncio.gather(*tasks)
                logger.debug(f"所有事件回调已完成: {event_type}")
            except Exception as e:
                logger.error(f"事件回调过程中出错: {str(e)}")
    
    async def _safe_callback(self, callback, event):
        """安全地执行回调函数"""
        try:
            await callback(event)
        except Exception as e:
            import traceback
            callback_info = getattr(callback, "__qualname__", str(callback))
            logger.error(f"事件回调 '{callback_info}' 执行出错: {str(e)}")
            logger.debug(traceback.format_exc())
    
    def subscribe_event(self, event_type: str, callback: Callable) -> None:
        """
        订阅事件
        
        Args:
            event_type: 事件类型
            callback: 回调函数
        """
        if event_type not in self.event_subscribers:
            self.event_subscribers[event_type] = []
        self.event_subscribers[event_type].append(callback)
    
    def unsubscribe_event(self, event_type: str, callback: Callable) -> bool:
        """
        取消订阅事件
        
        Args:
            event_type: 事件类型
            callback: 回调函数
            
        Returns:
            是否成功取消订阅
        """
        if event_type not in self.event_subscribers:
            return False
        
        try:
            self.event_subscribers[event_type].remove(callback)
            return True
        except ValueError:
            return False
    
    async def run(self, config: Dict[str, Any]) -> int:
        """
        运行系统
        
        Args:
            config: 全局配置
            
        Returns:
            退出代码
        """
        logger.info("Initializing system...")
        if not await self.initialize_modules(config):
            logger.error("Some modules failed to initialize")
            return 1
        
        logger.info("Starting modules...")
        if not await self.start_modules():
            logger.error("Some modules failed to start")
            await self.stop_modules()
            return 1
        
        self.running = True
        logger.info("System is running")
        
        # 添加健康检查任务
        health_check_task = asyncio.create_task(self._health_check_loop())
        self.tasks.append(health_check_task)
        
        # 等待退出信号
        try:
            while self.running:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            logger.info("Received cancellation signal")
            self.running = False
        finally:
            logger.info("Stopping modules...")
            await self.stop_modules()
            
            # 取消所有任务
            for task in self.tasks:
                task.cancel()
            
            logger.info("System stopped")
        
        return 0
    
    async def _health_check_loop(self) -> None:
        """定期执行模块健康检查"""
        while self.running:
            for module_id, module in self.modules.items():
                try:
                    if module.state == ModuleState.RUNNING:
                        healthy = await module.health_check()
                        if not healthy:
                            logger.warning(f"Module '{module_id}' health check failed")
                            # 可以在这里添加自动重启逻辑
                except Exception as e:
                    logger.error(f"Module '{module_id}' health check error: {str(e)}")
            
            await asyncio.sleep(30)  # 每30秒检查一次 