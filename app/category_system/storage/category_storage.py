# -*- coding: utf-8 -*-
"""
分类存储模块
负责存储分类结果和统计信息
"""
import os
import json
import time
from typing import Dict, List, Optional
from pathlib import Path
from loguru import logger

class CategoryStorage:
    """分类存储模块，负责存储分类结果和统计信息"""
    
    def __init__(self, storage_path: str = 'data/categories'):
        """初始化分类存储
        
        Args:
            storage_path: 存储目录路径
        """
        self.storage_path = Path(storage_path)
        self.results_path = self.storage_path / 'results.json'
        self.stats_path = self.storage_path / 'statistics.json'
        
        # 确保存储目录存在
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # 初始化数据
        self.results = self._load_results()
        self.statistics = self._load_statistics()
    
    def _load_results(self) -> Dict:
        """加载分类结果"""
        try:
            if self.results_path.exists():
                with open(self.results_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"加载分类结果失败: {str(e)}")
            return {}
    
    def _load_statistics(self) -> Dict:
        """加载统计信息"""
        try:
            if self.stats_path.exists():
                with open(self.stats_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {
                'category_usage': {},
                'classification_accuracy': {},
                'daily_stats': {}
            }
        except Exception as e:
            logger.error(f"加载统计信息失败: {str(e)}")
            return {
                'category_usage': {},
                'classification_accuracy': {},
                'daily_stats': {}
            }
    
    def _save_results(self) -> None:
        """保存分类结果"""
        try:
            with open(self.results_path, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存分类结果失败: {str(e)}")
            raise
    
    def _save_statistics(self) -> None:
        """保存统计信息"""
        try:
            with open(self.stats_path, 'w', encoding='utf-8') as f:
                json.dump(self.statistics, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存统计信息失败: {str(e)}")
            raise
    
    def store_classification(self, content_id: str, classification: Dict) -> bool:
        """存储分类结果
        
        Args:
            content_id: 内容ID
            classification: 分类结果
            
        Returns:
            bool: 是否存储成功
        """
        try:
            # 存储分类结果
            self.results[content_id] = {
                'classification': classification,
                'timestamp': int(time.time())
            }
            self._save_results()
            
            # 更新统计信息
            self._update_statistics(classification)
            
            return True
        except Exception as e:
            logger.error(f"存储分类结果失败: {str(e)}")
            return False
    
    def get_classification(self, content_id: str) -> Optional[Dict]:
        """获取分类结果
        
        Args:
            content_id: 内容ID
            
        Returns:
            Optional[Dict]: 分类结果，如果不存在则返回None
        """
        return self.results.get(content_id)
    
    def _update_statistics(self, classification: Dict) -> None:
        """更新统计信息
        
        Args:
            classification: 分类结果
        """
        try:
            # 更新分类使用次数
            primary_cat = classification['primary_category']
            if primary_cat not in self.statistics['category_usage']:
                self.statistics['category_usage'][primary_cat] = 0
            self.statistics['category_usage'][primary_cat] += 1
            
            # 更新每日统计
            today = time.strftime('%Y-%m-%d')
            if today not in self.statistics['daily_stats']:
                self.statistics['daily_stats'][today] = {
                    'total': 0,
                    'by_category': {}
                }
            
            daily = self.statistics['daily_stats'][today]
            daily['total'] += 1
            
            if primary_cat not in daily['by_category']:
                daily['by_category'][primary_cat] = 0
            daily['by_category'][primary_cat] += 1
            
            # 保存统计信息
            this._save_statistics()
            
        except Exception as e:
            logger.error(f"更新统计信息失败: {str(e)}")
    
    def get_statistics(self) -> Dict:
        """获取统计信息
        
        Returns:
            Dict: 统计信息
        """
        return self.statistics
    
    def get_category_usage(self) -> Dict[str, int]:
        """获取分类使用次数
        
        Returns:
            Dict[str, int]: 分类使用次数
        """
        return self.statistics['category_usage']
    
    def get_daily_stats(self, date: str = None) -> Dict:
        """获取每日统计信息
        
        Args:
            date: 日期，格式为YYYY-MM-DD，如果为None则返回最新日期
            
        Returns:
            Dict: 每日统计信息
        """
        if date is None:
            date = time.strftime('%Y-%m-%d')
        return self.statistics['daily_stats'].get(date, {})
    
    def clear_old_data(self, days: int = 30) -> None:
        """清理旧数据
        
        Args:
            days: 保留天数
        """
        try:
            # 清理旧的每日统计
            cutoff_date = time.strftime('%Y-%m-%d', 
                                      time.localtime(time.time() - days * 24 * 3600))
            self.statistics['daily_stats'] = {
                date: stats for date, stats in self.statistics['daily_stats'].items()
                if date >= cutoff_date
            }
            
            # 保存更新后的统计信息
            self._save_statistics()
            
        except Exception as e:
            logger.error(f"清理旧数据失败: {str(e)}")
