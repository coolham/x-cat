# -*- coding: utf-8 -*-
"""
分发器数据清理
清理过期的统计和健康状态数据
"""
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from loguru import logger

class DistributorCleanup:
    """分发器数据清理"""
    
    def __init__(self):
        """初始化数据清理"""
        self.data_dir = Path('data')
        self.config = {
            'stats_retention_days': 30,  # 统计数据保留天数
            'health_retention_days': 7,  # 健康状态保留天数
            'alert_retention_days': 14,  # 告警记录保留天数
            'cleanup_interval': 86400  # 清理间隔（秒）
        }
    
    def cleanup_stats(self) -> bool:
        """清理统计数据
        
        Returns:
            bool: 是否清理成功
        """
        try:
            stats_dir = self.data_dir / 'stats'
            if not stats_dir.exists():
                return True
            
            # 获取所有统计文件
            stats_files = list(stats_dir.glob('*.json'))
            
            # 计算过期时间
            cutoff_time = datetime.now() - timedelta(days=self.config['stats_retention_days'])
            
            # 清理过期文件
            for file in stats_files:
                try:
                    with open(file, 'r', encoding='utf-8') as f:
                        stats = json.load(f)
                    
                    # 检查最后更新时间
                    last_updated = datetime.fromisoformat(stats.get('last_updated', '2000-01-01'))
                    if last_updated < cutoff_time:
                        file.unlink()
                        logger.info(f"已删除过期统计文件: {file}")
                        
                except Exception as e:
                    logger.error(f"处理统计文件失败 ({file}): {str(e)}")
            
            return True
            
        except Exception as e:
            logger.error(f"清理统计数据失败: {str(e)}")
            return False
    
    def cleanup_health(self) -> bool:
        """清理健康状态数据
        
        Returns:
            bool: 是否清理成功
        """
        try:
            health_dir = self.data_dir / 'health'
            if not health_dir.exists():
                return True
            
            # 获取健康状态文件
            health_file = health_dir / 'distributor_health.json'
            if not health_file.exists():
                return True
            
            # 读取健康状态
            with open(health_file, 'r', encoding='utf-8') as f:
                health_data = json.load(f)
            
            # 计算过期时间
            cutoff_time = datetime.now() - timedelta(days=self.config['health_retention_days'])
            
            # 清理过期记录
            for distributor, status in list(health_data.items()):
                try:
                    timestamp = datetime.fromisoformat(status.get('timestamp', '2000-01-01'))
                    if timestamp < cutoff_time:
                        del health_data[distributor]
                        logger.info(f"已删除过期健康状态: {distributor}")
                        
                except Exception as e:
                    logger.error(f"处理健康状态失败 ({distributor}): {str(e)}")
            
            # 保存清理后的数据
            with open(health_file, 'w', encoding='utf-8') as f:
                json.dump(health_data, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            logger.error(f"清理健康状态数据失败: {str(e)}")
            return False
    
    def cleanup_alerts(self) -> bool:
        """清理告警记录
        
        Returns:
            bool: 是否清理成功
        """
        try:
            alert_dir = self.data_dir / 'alerts'
            if not alert_dir.exists():
                return True
            
            # 获取所有告警文件
            alert_files = list(alert_dir.glob('*.json'))
            
            # 计算过期时间
            cutoff_time = datetime.now() - timedelta(days=self.config['alert_retention_days'])
            
            # 清理过期文件
            for file in alert_files:
                try:
                    with open(file, 'r', encoding='utf-8') as f:
                        alerts = json.load(f)
                    
                    # 过滤过期告警
                    filtered_alerts = [
                        alert for alert in alerts
                        if datetime.fromisoformat(alert.get('timestamp', '2000-01-01')) >= cutoff_time
                    ]
                    
                    # 保存过滤后的告警
                    with open(file, 'w', encoding='utf-8') as f:
                        json.dump(filtered_alerts, f, ensure_ascii=False, indent=2)
                    
                    if len(filtered_alerts) < len(alerts):
                        logger.info(f"已清理过期告警: {file}")
                        
                except Exception as e:
                    logger.error(f"处理告警文件失败 ({file}): {str(e)}")
            
            return True
            
        except Exception as e:
            logger.error(f"清理告警记录失败: {str(e)}")
            return False
    
    def cleanup_all(self) -> bool:
        """清理所有数据
        
        Returns:
            bool: 是否清理成功
        """
        try:
            success = True
            
            # 清理统计数据
            if not this.cleanup_stats():
                success = False
            
            # 清理健康状态
            if not this.cleanup_health():
                success = False
            
            # 清理告警记录
            if not this.cleanup_alerts():
                success = False
            
            if success:
                logger.info("数据清理完成")
            else:
                logger.warning("数据清理部分失败")
            
            return success
            
        except Exception as e:
            logger.error(f"清理数据失败: {str(e)}")
            return False
    
    def update_config(self, config: Dict):
        """更新清理配置
        
        Args:
            config: 新配置
        """
        try:
            this.config.update(config)
            logger.info("已更新清理配置")
        except Exception as e:
            logger.error(f"更新清理配置失败: {str(e)}") 