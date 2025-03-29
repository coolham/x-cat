"""
流水线处理器
负责协调各个处理阶段
"""
from typing import Dict, List, Any, Callable, Optional
from loguru import logger
from datetime import datetime
from app.cache.cache_manager import CacheManager

class PipelineStage:
    """流水线阶段"""
    
    def __init__(self, name: str, processor: Callable):
        """初始化流水线阶段
        
        Args:
            name: 阶段名称
            processor: 处理器函数
        """
        self.name = name
        self.processor = processor
        self.last_process_time = None
        self.process_count = 0
        self.error_count = 0
        self.next_stage = None
        
    async def process(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """处理数据
        
        Args:
            data: 输入数据
            
        Returns:
            处理后的数据，如果返回None则终止流水线
        """
        try:
            logger.debug(f"开始处理阶段: {self.name}")
            start_time = datetime.now()
            
            result = await self.processor(data)
            
            if result is None:
                return None
            
            # 更新统计信息
            self.last_process_time = datetime.now()
            self.process_count += 1
            process_duration = (self.last_process_time - start_time).total_seconds()
            
            logger.debug(f"完成处理阶段: {self.name}, 耗时: {process_duration:.2f}秒")
            
            if self.next_stage:
                return await self.next_stage.process(result)
            return result
            
        except Exception as e:
            self.error_count += 1
            logger.error(f"处理阶段 {self.name} 出错: {str(e)}")
            return None
            
    def get_stats(self) -> Dict[str, Any]:
        """获取阶段统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        return {
            'name': self.name,
            'process_count': self.process_count,
            'error_count': self.error_count,
            'last_process_time': self.last_process_time.isoformat() if self.last_process_time else None,
            'success_rate': (self.process_count - self.error_count) / self.process_count if self.process_count > 0 else 0
        }

class Pipeline:
    """流水线处理器"""
    
    def __init__(self):
        """初始化流水线"""
        self.first_stage = None
        self.running = False
        self.cache_manager = CacheManager("cache")
        
    def add_stage(self, name: str, processor: Callable) -> None:
        """添加处理阶段
        
        Args:
            name: 阶段名称
            processor: 处理器函数
        """
        stage = PipelineStage(name, processor)
        
        if not self.first_stage:
            self.first_stage = stage
        else:
            current = self.first_stage
            while current.next_stage:
                current = current.next_stage
            current.next_stage = stage
        
    async def process(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """处理数据
        
        Args:
            data: 输入数据
            
        Returns:
            处理后的数据
        """
        if not self.first_stage:
            logger.warning("流水线为空")
            return data
            
        # 检查缓存
        if "url" in data:
            cached_data = self.cache_manager.load(data["url"])
            if cached_data:
                logger.info(f"使用缓存数据: {data['url']}")
                return cached_data
        
        # 处理数据
        result = await self.first_stage.process(data)
        
        # 保存到缓存
        if result and "url" in result:
            self.cache_manager.save(result["url"], result)
            logger.info(f"数据已缓存: {result['url']}")
        
        return result
            
    def get_stats(self) -> Dict[str, Any]:
        """获取流水线统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        return {
            'stage_count': self.get_stage_count(),
            'stages': [stage.get_stats() for stage in self.get_stages()]
        }

    def get_stage_count(self) -> int:
        """获取流水线阶段数量
        
        Returns:
            int: 阶段数量
        """
        count = 0
        current = self.first_stage
        while current:
            count += 1
            current = current.next_stage
        return count

    def get_stages(self) -> List[PipelineStage]:
        """获取流水线所有阶段
        
        Returns:
            List[PipelineStage]: 阶段列表
        """
        stages = []
        current = self.first_stage
        while current:
            stages.append(current)
            current = current.next_stage
        return stages 