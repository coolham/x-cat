# -*- coding: utf-8 -*-
"""
分发器健康检查
监控分发器状态
"""
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from loguru import logger

from .stats import DistributorStats

class DistributorHealth:
    """分发器健康检查"""
    
    def __init__(self):
        """初始化健康检查"""
        self.health_dir = Path('data/health')
        self.health_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化统计
        self.stats = DistributorStats()
        
        # 健康检查配置
        self.config = {
            'max_failure_rate': 0.1,  # 最大失败率
            'max_response_time': 5000,  # 最大响应时间（毫秒）
            'min_success_rate': 0.9,  # 最小成功率
            'check_interval': 300  # 检查间隔（秒）
        }
        
        # 加载历史健康状态
        self._load_health()
    
    def _load_health(self):
        """加载历史健康状态"""
        try:
            health_file = self.health_dir / 'distributor_health.json'
            if health_file.exists():
                with open(health_file, 'r', encoding='utf-8') as f:
                    self.health_status = json.load(f)
            else:
                self.health_status = {}
        except Exception as e:
            logger.error(f"加载健康状态失败: {str(e)}")
            self.health_status = {}
    
    def _save_health(self):
        """保存健康状态"""
        try:
            health_file = self.health_dir / 'distributor_health.json'
            with open(health_file, 'w', encoding='utf-8') as f:
                json.dump(self.health_status, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存健康状态失败: {str(e)}")
    
    def check_health(self, distributor: str) -> Dict:
        """检查分发器健康状态
        
        Args:
            distributor: 分发器名称
            
        Returns:
            Dict: 健康状态信息
        """
        try:
            # 获取统计信息
            stats = self.stats.get_stats()
            
            # 计算健康指标
            health = {
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'metrics': {
                    'success_rate': stats.get('success_rate', 0),
                    'retry_rate': stats.get('retry_rate', 0),
                    'avg_response_time': stats.get('avg_response_time', 0),
                    'total_count': stats.get('total_count', 0),
                    'failure_count': stats.get('failure_count', 0)
                },
                'issues': []
            }
            
            # 检查失败率
            if stats.get('total_count', 0) > 0:
                failure_rate = stats['failure_count'] / stats['total_count']
                if failure_rate > self.config['max_failure_rate']:
                    health['status'] = 'warning'
                    health['issues'].append(f"失败率过高: {failure_rate:.2%}")
            
            # 检查响应时间
            if stats.get('avg_response_time', 0) > self.config['max_response_time']:
                health['status'] = 'warning'
                health['issues'].append(f"响应时间过长: {stats['avg_response_time']}ms")
            
            # 检查成功率
            if stats.get('success_rate', 0) < self.config['min_success_rate']:
                health['status'] = 'warning'
                health['issues'].append(f"成功率过低: {stats['success_rate']:.2%}")
            
            # 更新健康状态
            self.health_status[distributor] = health
            self._save_health()
            
            # 记录日志
            if health['status'] == 'healthy':
                logger.info(f"分发器健康检查 - {distributor}: 正常")
            else:
                logger.warning(f"分发器健康检查 - {distributor}: 警告 - {', '.join(health['issues'])}")
            
            return health
            
        except Exception as e:
            logger.error(f"检查分发器健康状态失败: {str(e)}")
            return {
                'status': 'error',
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }
    
    def get_health_status(self, distributor: str) -> Dict:
        """获取分发器健康状态
        
        Args:
            distributor: 分发器名称
            
        Returns:
            Dict: 健康状态信息
        """
        return self.health_status.get(distributor, {})
    
    def get_all_health_status(self) -> Dict:
        """获取所有分发器健康状态
        
        Returns:
            Dict: 所有分发器健康状态
        """
        return self.health_status
    
    def update_config(self, config: Dict):
        """更新健康检查配置
        
        Args:
            config: 新配置
        """
        try:
            self.config.update(config)
            logger.info("已更新健康检查配置")
        except Exception as e:
            logger.error(f"更新健康检查配置失败: {str(e)}")
    
    def clear_health_status(self):
        """清除健康状态"""
        try:
            self.health_status = {}
            self._save_health()
            logger.info("已清除健康状态")
        except Exception as e:
            logger.error(f"清除健康状态失败: {str(e)}") 