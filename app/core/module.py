"""
核心模块定义
提供模块接口和辅助类
"""
import time
from enum import Enum, auto
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Set, Type, Callable
from dataclasses import dataclass, field


# 模块状态枚举
class ModuleState(Enum):
    """模块状态枚举类"""
    REGISTERED = auto()  # 已注册
    INITIALIZED = auto()  # 已初始化
    RUNNING = auto()     # 运行中
    PAUSED = auto()      # 已暂停
    STOPPING = auto()    # 正在停止
    STOPPED = auto()     # 已停止
    ERROR = auto()       # 错误状态


# 事件类
@dataclass
class Event:
    """事件数据类"""
    event_type: str
    source: str
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


# 模块接口
class Module(ABC):
    """
    模块接口基类
    所有功能模块必须实现此接口
    """
    
    def __init__(self, runtime: 'Runtime', module_id: str):
        """
        初始化模块
        
        Args:
            runtime: 运行时引用
            module_id: 模块唯一标识符
        """
        self.runtime = runtime
        self.module_id = module_id
        self.state = ModuleState.REGISTERED
        self.config = {}
        self.dependencies = set()
    
    @property
    def name(self) -> str:
        """模块名称"""
        return self.__class__.__name__
    
    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """
        初始化模块
        
        Args:
            config: 模块配置
            
        Returns:
            初始化是否成功
        """
        self.config = config
        self.state = ModuleState.INITIALIZED
        return True
    
    @abstractmethod
    async def start(self) -> bool:
        """
        启动模块
        
        Returns:
            启动是否成功
        """
        self.state = ModuleState.RUNNING
        return True
    
    @abstractmethod
    async def stop(self) -> bool:
        """
        停止模块
        
        Returns:
            停止是否成功
        """
        self.state = ModuleState.STOPPED
        return True
    
    async def pause(self) -> bool:
        """
        暂停模块
        
        Returns:
            暂停是否成功
        """
        if self.state == ModuleState.RUNNING:
            self.state = ModuleState.PAUSED
            return True
        return False
    
    async def resume(self) -> bool:
        """
        恢复模块
        
        Returns:
            恢复是否成功
        """
        if self.state == ModuleState.PAUSED:
            self.state = ModuleState.RUNNING
            return True
        return False
    
    async def health_check(self) -> bool:
        """
        健康检查
        
        Returns:
            模块是否健康
        """
        return self.state in [ModuleState.RUNNING, ModuleState.PAUSED]
    
    def add_dependency(self, module_id: str) -> None:
        """
        添加依赖模块
        
        Args:
            module_id: 依赖模块的ID
        """
        self.dependencies.add(module_id)
    
    def get_dependencies(self) -> Set[str]:
        """
        获取所有依赖模块的ID
        
        Returns:
            依赖模块ID集合
        """
        return self.dependencies 