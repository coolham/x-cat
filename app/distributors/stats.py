# -*- coding: utf-8 -*-
"""
分发统计
记录和统计分发情况
"""
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from loguru import logger

class DistributorStats:
    """分发统计"""
    
    def __init__(self):
        """初始化统计"""
        self.stats_dir = Path('data/stats')
        self.stats_dir.mkdir(parents=True, exist_ok=True)
        
        # 内存统计
        self.total_count = 0
        self.success_count = 0
        self.failure_count = 0
        self.retry_count = 0
        self.response_times = []
        
        # 加载历史统计
        self._load_stats()
    
    def _load_stats(self):
        """加载历史统计"""
        try:
            stats_file = self.stats_dir / 'distributor_stats.json'
            if stats_file.exists():
                with open(stats_file, 'r', encoding='utf-8') as f:
                    stats = json.load(f)
                    self.total_count = stats.get('total_count', 0)
                    self.success_count = stats.get('success_count', 0)
                    self.failure_count = stats.get('failure_count', 0)
                    self.retry_count = stats.get('retry_count', 0)
                    self.response_times = stats.get('response_times', [])
        except Exception as e:
            logger.error(f"加载统计信息失败: {str(e)}")
    
    def _save_stats(self):
        """保存统计信息"""
        try:
            stats = {
                'total_count': self.total_count,
                'success_count': self.success_count,
                'failure_count': self.failure_count,
                'retry_count': self.retry_count,
                'response_times': self.response_times,
                'last_updated': datetime.now().isoformat()
            }
            
            stats_file = self.stats_dir / 'distributor_stats.json'
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(stats, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"保存统计信息失败: {str(e)}")
    
    def record_distribution(self, 
                          distributor: str,
                          success: bool,
                          retry: bool = False,
                          response_time: Optional[float] = None):
        """记录分发情况
        
        Args:
            distributor: 分发器名称
            success: 是否成功
            retry: 是否重试
            response_time: 响应时间（毫秒）
        """
        try:
            # 更新计数
            self.total_count += 1
            if success:
                self.success_count += 1
            else:
                self.failure_count += 1
            if retry:
                self.retry_count += 1
            
            # 记录响应时间
            if response_time is not None:
                self.response_times.append(response_time)
            
            # 保存统计
            self._save_stats()
            
            # 记录日志
            status = "成功" if success else "失败"
            retry_info = "（重试）" if retry else ""
            logger.info(f"分发统计 - {distributor}: {status}{retry_info}")
            
        except Exception as e:
            logger.error(f"记录分发统计失败: {str(e)}")
    
    def get_stats(self) -> Dict:
        """获取统计信息
        
        Returns:
            Dict: 统计信息
        """
        try:
            # 计算成功率
            success_rate = (self.success_count / self.total_count * 100) if self.total_count > 0 else 0
            
            # 计算平均响应时间
            avg_response_time = sum(self.response_times) / len(self.response_times) if self.response_times else 0
            
            # 计算重试率
            retry_rate = (self.retry_count / self.total_count * 100) if self.total_count > 0 else 0
            
            return {
                'total_count': self.total_count,
                'success_count': self.success_count,
                'failure_count': self.failure_count,
                'retry_count': self.retry_count,
                'success_rate': round(success_rate, 2),
                'retry_rate': round(retry_rate, 2),
                'avg_response_time': round(avg_response_time, 2),
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取统计信息失败: {str(e)}")
            return {}
    
    def get_distributor_stats(self, distributor: str) -> Dict:
        """获取分发器统计信息
        
        Args:
            distributor: 分发器名称
            
        Returns:
            Dict: 分发器统计信息
        """
        try:
            stats_file = self.stats_dir / f'{distributor}_stats.json'
            if stats_file.exists():
                with open(stats_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
            
        except Exception as e:
            logger.error(f"获取分发器统计信息失败: {str(e)}")
            return {}
    
    def clear_stats(self):
        """清除统计信息"""
        try:
            self.total_count = 0
            self.success_count = 0
            self.failure_count = 0
            self.retry_count = 0
            self.response_times = []
            self._save_stats()
            logger.info("已清除统计信息")
            
        except Exception as e:
            logger.error(f"清除统计信息失败: {str(e)}") 