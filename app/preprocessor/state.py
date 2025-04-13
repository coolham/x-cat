"""
预处理状态管理
"""
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
from loguru import logger

class ProcessingStatus(Enum):
    """处理状态枚举"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class ProcessingState:
    """处理状态类"""
    status: ProcessingStatus
    current_task: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error_count: int = 0
    processed_count: int = 0
    total_count: int = 0
    errors: list = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        """初始化默认值"""
        if self.errors is None:
            self.errors = []
        if self.metadata is None:
            self.metadata = {}
        if self.start_time is None:
            self.start_time = datetime.now()

class StateManager:
    """状态管理器"""
    
    def __init__(self):
        """初始化状态管理器"""
        self._state = ProcessingState(status=ProcessingStatus.PENDING)
        logger.info("预处理状态管理器初始化成功")
    
    def get_state(self) -> ProcessingState:
        """获取当前状态
        
        Returns:
            ProcessingState: 当前状态
        """
        return self._state
    
    def start_processing(self, total_count: int = 0) -> None:
        """开始处理
        
        Args:
            total_count: 总处理数量
        """
        self._state = ProcessingState(
            status=ProcessingStatus.PROCESSING,
            start_time=datetime.now(),
            total_count=total_count
        )
        logger.info(f"开始处理，总数量: {total_count}")
    
    def update_progress(self, task: str, success: bool = True, error: Optional[str] = None) -> None:
        """更新进度
        
        Args:
            task: 当前任务
            success: 是否成功
            error: 错误信息
        """
        self._state.current_task = task
        if success:
            self._state.processed_count += 1
        else:
            self._state.error_count += 1
            if error:
                self._state.errors.append({
                    'task': task,
                    'time': datetime.now().isoformat(),
                    'error': error
                })
        
        logger.debug(f"进度更新: {self._state.processed_count}/{self._state.total_count}, 错误: {self._state.error_count}")
    
    def complete_processing(self, success: bool = True) -> None:
        """完成处理
        
        Args:
            success: 是否成功
        """
        self._state.end_time = datetime.now()
        self._state.status = ProcessingStatus.COMPLETED if success else ProcessingStatus.FAILED
        
        duration = (self._state.end_time - self._state.start_time).total_seconds()
        logger.info(f"处理完成: 状态={self._state.status.value}, 耗时={duration}秒, "
                   f"处理={self._state.processed_count}, 错误={self._state.error_count}")
    
    def cancel_processing(self) -> None:
        """取消处理"""
        self._state.status = ProcessingStatus.CANCELLED
        self._state.end_time = datetime.now()
        logger.info("处理已取消")
    
    def get_progress(self) -> Dict[str, Any]:
        """获取进度信息
        
        Returns:
            Dict[str, Any]: 进度信息
        """
        progress = {
            'status': self._state.status.value,
            'current_task': self._state.current_task,
            'processed': self._state.processed_count,
            'total': self._state.total_count,
            'errors': self._state.error_count,
            'error_details': self._state.errors
        }
        
        if self._state.start_time:
            progress['start_time'] = self._state.start_time.isoformat()
        if self._state.end_time:
            progress['end_time'] = self._state.end_time.isoformat()
            duration = (self._state.end_time - self._state.start_time).total_seconds()
            progress['duration'] = duration
        
        return progress
    
    def add_metadata(self, key: str, value: Any) -> None:
        """添加元数据
        
        Args:
            key: 键
            value: 值
        """
        self._state.metadata[key] = value
        logger.debug(f"添加元数据: {key}={value}")
    
    def get_metadata(self, key: str) -> Optional[Any]:
        """获取元数据
        
        Args:
            key: 键
            
        Returns:
            Optional[Any]: 值
        """
        return self._state.metadata.get(key)
    
    def clear_metadata(self) -> None:
        """清除元数据"""
        self._state.metadata.clear()
        logger.debug("清除元数据") 