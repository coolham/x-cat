"""
本地存储实现
使用SQLite数据库存储内容
"""
import os
import json
import sqlite3
import logging
from typing import Dict, Any, List, Optional

from .base import StorageBackend


class LocalStorage(StorageBackend):
    """本地SQLite存储实现"""
    
    def __init__(self, db_path: str):
        """
        初始化本地存储
        
        Args:
            db_path: SQLite数据库文件路径
        """
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        
        # 确保目录存在
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        
        # 初始化数据库
        self._init_db()
    
    def _init_db(self):
        """初始化数据库表结构"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 创建内容表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS contents (
                id TEXT PRIMARY KEY,
                original_message_id TEXT,
                twitter_link TEXT,
                original_text TEXT,
                category TEXT,
                summary TEXT,
                timestamp TEXT,
                extra_data TEXT
            )
            ''')
            
            conn.commit()
            conn.close()
            self.logger.info(f"数据库初始化成功: {self.db_path}")
        except Exception as e:
            self.logger.error(f"数据库初始化失败: {str(e)}")
    
    def save(self, analyzed_content: Dict[str, Any]) -> bool:
        """
        保存分析后的内容到SQLite数据库
        
        Args:
            analyzed_content: 分析后的内容
            
        Returns:
            是否成功保存
        """
        try:
            # 提取需要的字段
            content_id = analyzed_content.get('twitter_link', '')
            if not content_id:
                self.logger.error("无法保存内容: 缺少唯一标识符")
                return False
            
            # 准备数据
            original_message_id = analyzed_content.get('original_message_id', '')
            twitter_link = analyzed_content.get('twitter_link', '')
            original_text = analyzed_content.get('original_text', '')
            category = analyzed_content.get('category', '未分类')
            summary = analyzed_content.get('summary', '')
            timestamp = analyzed_content.get('timestamp', '')
            
            # 将其他字段保存为JSON
            extra_fields = {k: v for k, v in analyzed_content.items() 
                          if k not in ['original_message_id', 'twitter_link', 
                                      'original_text', 'category', 'summary', 'timestamp']}
            extra_data = json.dumps(extra_fields)
            
            # 保存到数据库
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            INSERT OR REPLACE INTO contents 
            (id, original_message_id, twitter_link, original_text, category, summary, timestamp, extra_data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (content_id, original_message_id, twitter_link, original_text, 
                  category, summary, timestamp, extra_data))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"内容保存成功: {content_id}")
            return True
        except Exception as e:
            self.logger.error(f"保存内容失败: {str(e)}")
            return False
    
    def get_by_id(self, content_id: str) -> Dict[str, Any]:
        """
        通过ID获取内容
        
        Args:
            content_id: 内容ID
            
        Returns:
            获取的内容，如果不存在则返回空字典
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM contents WHERE id = ?', (content_id,))
            row = cursor.fetchone()
            
            if not row:
                return {}
            
            # 将行转换为字典
            result = dict(row)
            
            # 解析额外数据
            if 'extra_data' in result and result['extra_data']:
                extra_data = json.loads(result['extra_data'])
                result.update(extra_data)
                del result['extra_data']
            
            conn.close()
            return result
        except Exception as e:
            self.logger.error(f"获取内容失败: {str(e)}")
            return {}
    
    def get_by_category(self, category: str) -> List[Dict[str, Any]]:
        """
        获取特定类别的所有内容
        
        Args:
            category: 内容类别
            
        Returns:
            内容列表
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM contents WHERE category = ?', (category,))
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                # 将行转换为字典
                result = dict(row)
                
                # 解析额外数据
                if 'extra_data' in result and result['extra_data']:
                    extra_data = json.loads(result['extra_data'])
                    result.update(extra_data)
                    del result['extra_data']
                
                results.append(result)
            
            conn.close()
            return results
        except Exception as e:
            self.logger.error(f"获取类别内容失败: {str(e)}")
            return [] 