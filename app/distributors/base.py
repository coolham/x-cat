# -*- coding: utf-8 -*-
"""
分发器基类
定义内容分发的基本接口
"""
import asyncio
import time
from abc import ABC, abstractmethod
from typing import Dict, Optional
from loguru import logger

from .config import DistributorConfig
from .stats import DistributorStats
from .health import DistributorHealth
from .alert import DistributorAlert
from .cleanup import DistributorCleanup

class Distributor(ABC):
    """分发器基类"""
    
    def __init__(self):
        """初始化分发器"""
        self.name = self.__class__.__name__.lower()
        self.config = DistributorConfig()
        self.retry_config = self.config.get_retry_config(self.name)
        
        # 初始化统计、健康检查、监控告警和数据清理
        self.stats = DistributorStats()
        self.health = DistributorHealth()
        self.alert = DistributorAlert()
        self.cleanup = DistributorCleanup()
        
        # 启动数据清理任务
        asyncio.create_task(self._run_cleanup_task())
    
    async def _run_cleanup_task(self):
        """运行数据清理任务"""
        while True:
            try:
                # 执行数据清理
                self.cleanup.cleanup_all()
                
                # 等待下一次清理
                await asyncio.sleep(self.cleanup.config['cleanup_interval'])
                
            except Exception as e:
                logger.error(f"数据清理任务异常: {str(e)}")
                await asyncio.sleep(60)  # 发生错误时等待1分钟后重试
    
    @abstractmethod
    async def distribute(self, content: Dict) -> bool:
        """分发内容
        
        Args:
            content: 内容信息，包含以下字段：
                - id: 内容ID
                - text: 内容文本
                - source: 来源
                - metadata: 元数据
                - classification: 分类结果
                
        Returns:
            bool: 是否分发成功
        """
        pass
    
    async def distribute_with_retry(self, content: Dict) -> bool:
        """带重试机制的分发
        
        Args:
            content: 内容信息
            
        Returns:
            bool: 是否分发成功
        """
        max_attempts = self.retry_config['max_attempts']
        delay = self.retry_config['delay']
        
        start_time = time.time()
        retry_count = 0
        
        for attempt in range(max_attempts):
            try:
                success = await self.distribute(content)
                if success:
                    # 记录成功统计
                    response_time = (time.time() - start_time) * 1000
                    self.stats.record_distribution(
                        self.name,
                        success=True,
                        retry=retry_count > 0,
                        response_time=response_time
                    )
                    return True
                    
                if attempt < max_attempts - 1:
                    retry_count += 1
                    logger.warning(f"分发失败，{delay}秒后重试 ({attempt + 1}/{max_attempts})")
                    await asyncio.sleep(delay)
                    
            except Exception as e:
                if attempt < max_attempts - 1:
                    retry_count += 1
                    logger.error(f"分发异常，{delay}秒后重试 ({attempt + 1}/{max_attempts}): {str(e)}")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"分发失败，已达到最大重试次数: {str(e)}")
        
        # 记录失败统计
        response_time = (time.time() - start_time) * 1000
        self.stats.record_distribution(
            self.name,
            success=False,
            retry=retry_count > 0,
            response_time=response_time
        )
        
        return False
    
    def _format_content(self, content: Dict) -> Dict:
        """格式化内容
        
        Args:
            content: 原始内容信息
            
        Returns:
            Dict: 格式化后的内容
        """
        try:
            # 提取分类信息
            classification = content.get('classification', {})
            
            # 构建格式化内容
            formatted = {
                'id': content['id'],
                'text': content['text'],
                'source': content['source'],
                'metadata': content.get('metadata', {}),
                'classification': {
                    'primary': classification.get('primary_category', '其它'),
                    'secondary': classification.get('secondary_category', '待分类内容'),
                    'confidence': classification.get('confidence', 0.0),
                    'reasoning': classification.get('reasoning', '')
                },
                'timestamp': content.get('metadata', {}).get('date', '')
            }
            
            return formatted
            
        except Exception as e:
            logger.error(f"格式化内容失败: {str(e)}")
            return content
    
    def check_health(self) -> Dict:
        """检查分发器健康状态
        
        Returns:
            Dict: 健康状态信息
        """
        health_status = self.health.check_health(self.name)
        
        # 检查是否需要告警
        self.alert.check_and_alert(self.name, health_status)
        
        return health_status
    
    def get_stats(self) -> Dict:
        """获取分发器统计信息
        
        Returns:
            Dict: 统计信息
        """
        return self.stats.get_distributor_stats(self.name)
    
    def get_alerts(self) -> Dict:
        """获取分发器告警信息
        
        Returns:
            Dict: 告警信息
        """
        return self.alert.get_alerts(self.name)
    
    def update_cleanup_config(self, config: Dict):
        """更新数据清理配置
        
        Args:
            config: 新配置
        """
        self.cleanup.update_config(config) 