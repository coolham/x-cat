"""
Storage Module
存储模块，负责数据持久化
"""
import os
import json
import sqlite3
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from queue import Queue
import traceback
import time

from loguru import logger

from app.core.module import Module, ModuleState, Event


class StorageModule(Module):
    """
    存储模块
    处理数据的持久化存储
    """
    
    def __init__(self, runtime, module_id="storage"):
        """初始化存储模块"""
        super().__init__(runtime, module_id)
        self.db_path = None
        self.connection = None
        self.message_queue = []
        self.backup_dir = None
        self.processing_task = None
        self.max_backups = 10  # 最大备份数量
    
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """
        初始化存储模块
        
        Args:
            config: 配置字典
            
        Returns:
            初始化是否成功
        """
        try:
            # 获取存储模块配置
            if "storage" not in config:
                logger.warning("配置中没有storage字段，将使用默认配置")
                storage_config = {}
            else:
                storage_config = config["storage"]
            
            # 检查必需参数，支持直接在配置根目录下的参数
            db_path = storage_config.get("db_path")
            if not db_path:
                # 尝试从系统配置中获取数据目录，并构建默认db路径
                data_dir = config.get("system", {}).get("data_dir", "data")
                db_path = os.path.join(data_dir, "storage.db")
                logger.warning(f"未指定db_path，将使用默认路径: {db_path}")
            
            # 创建数据库目录（如果不存在）
            os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
            
            # 初始化数据库连接
            self.db_path = db_path
            self.connection = sqlite3.connect(db_path)
            self.connection.execute('PRAGMA journal_mode=WAL')
            
            # 创建表
            self._create_tables()
            
            # 备份配置
            self.backup_dir = storage_config.get("backup_dir")
            if self.backup_dir:
                os.makedirs(self.backup_dir, exist_ok=True)
            
            self.max_backups = storage_config.get("max_backups", 10)
            
            # 设置模块状态
            self.state = ModuleState.INITIALIZED
            logger.info(f"存储模块初始化成功，数据库路径: {db_path}")
            return True
        
        except Exception as e:
            logger.error(f"存储模块初始化失败: {str(e)}")
            logger.debug(traceback.format_exc())
            self.state = ModuleState.ERROR
            return False
    
    async def start(self) -> bool:
        """
        启动存储模块
        
        Returns:
            启动是否成功
        """
        if self.state != ModuleState.INITIALIZED:
            logger.error("存储模块未初始化")
            return False
        
        # 创建处理队列的异步任务
        self.processing_task = asyncio.create_task(self._processing_loop())
        
        # 注册消息事件处理
        self.runtime.subscribe_event("new_message", self._on_new_message)
        self.runtime.subscribe_event("message_analyzed", self._on_message_analyzed)
        
        self.state = ModuleState.RUNNING
        logger.info("存储模块已启动")
        return True
    
    async def stop(self) -> bool:
        """
        停止存储模块
        
        Returns:
            停止是否成功
        """
        if self.state != ModuleState.RUNNING:
            return True
        
        # 取消处理任务
        if self.processing_task:
            self.processing_task.cancel()
            try:
                await self.processing_task
            except asyncio.CancelledError:
                pass
        
        # 备份数据库
        if self.backup_dir:
            self._backup_database()
        
        # 关闭数据库连接
        if self.connection:
            self.connection.close()
            self.connection = None
                
        self.state = ModuleState.STOPPED
        logger.info("存储模块已停止")
        return True
    
    async def health_check(self) -> bool:
        """
        健康检查
        
        Returns:
            模块是否健康
        """
        # 检查数据库连接是否可用
        db_healthy = self.connection is not None
        
        # 检查处理任务是否正在运行
        task_healthy = self.processing_task is not None and not self.processing_task.done()
        
        # 检查消息队列大小
        queue_size = len(self.message_queue)
        queue_healthy = queue_size < 1000  # 队列过大可能表示处理不及时
        
        logger.debug(f"存储模块健康检查: 数据库={db_healthy}, 任务={task_healthy}, 队列={queue_healthy}(大小={queue_size})")
        
        return self.state == ModuleState.RUNNING and db_healthy and task_healthy and queue_healthy
    
    async def _on_new_message(self, event: Event) -> None:
        """处理新消息事件"""
        message_data = event.data
        message_id = message_data.get("message_id")
        
        if not message_id:
            return
            
        # 将消息添加到存储队列
        self.message_queue.append(("message", message_data))
    
    async def _on_message_analyzed(self, event: Event) -> None:
        """处理消息分析事件"""
        analysis_data = event.data
        if not analysis_data:
            return
            
        # 将分析结果添加到存储队列
        self.message_queue.append(("analysis", analysis_data))
    
    async def store_message(self, message_data: Dict[str, Any]) -> bool:
        """存储消息数据"""
        try:
            cursor = self.connection.cursor()
            
            # 提取消息数据
            message_id = message_data.get("message_id")
            sender_id = message_data.get("sender_id", "")
            sender_name = message_data.get("sender_name", "")
            chat_id = message_data.get("chat_id", "")
            chat_title = message_data.get("chat_title", "")
            message_type = message_data.get("message_type", "unknown")
            content = message_data.get("text", "")
            media_url = message_data.get("media_url", "")
            received_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 准备SQL - 使用与表结构匹配的列名
            sql = """
            INSERT OR REPLACE INTO messages 
            (message_id, sender_id, sender_name, chat_id, chat_title, 
            message_type, content, media_url, received_at, raw_data) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            # 执行SQL
            cursor.execute(sql, (
                message_id,
                sender_id,
                sender_name,
                chat_id,
                chat_title,
                message_type,
                content,
                media_url,
                received_at,
                json.dumps(message_data, ensure_ascii=False)
            ))
            
            # 提交事务
            self.connection.commit()
            
            logger.debug(f"消息已存储: {message_id}")
            return True
            
        except Exception as e:
            logger.error(f"存储消息时出错: {str(e)}")
            if self.connection:
                self.connection.rollback()
            return False
    
    async def store_analysis(self, analysis_data: Dict[str, Any]) -> bool:
        """
        存储分析数据
        
        Args:
            analysis_data: 分析数据字典，包含各种分析结果字段
            
        Returns:
            存储是否成功
        """
        try:
            cursor = self.connection.cursor()
            
            # 从分析数据中提取字段
            message_id = analysis_data.get("message_id", "")
            content_type = analysis_data.get("content_type", "未知")
            category = analysis_data.get("category", "未知")
            subcategory = analysis_data.get("subcategory", "未知")
            sentiment = analysis_data.get("sentiment", "中性")
            language = analysis_data.get("language", "未知")
            summary = analysis_data.get("summary", "")
            keywords = analysis_data.get("keywords", "[]")
            urls = analysis_data.get("urls", "[]")
            content_format = analysis_data.get("content_format", "未知")
            has_web_content = 1 if analysis_data.get("has_web_content", False) else 0
            
            # 确保关键词和URL是JSON字符串
            if isinstance(keywords, list):
                keywords = json.dumps(keywords, ensure_ascii=False)
            if isinstance(urls, list):
                urls = json.dumps(urls, ensure_ascii=False)
            
            # 准备SQL语句
            sql = """
            INSERT OR REPLACE INTO analysis
            (message_id, content_type, category, subcategory, sentiment, language, 
             summary, keywords, urls, content_format, has_web_content, raw_data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            # 执行SQL
            cursor.execute(sql, (
                message_id,
                content_type,
                category,
                subcategory,
                sentiment,
                language,
                summary,
                keywords,
                urls,
                content_format,
                has_web_content,
                json.dumps(analysis_data, ensure_ascii=False)
            ))
            
            # 提交事务
            self.connection.commit()
            
            logger.info(f"成功存储分析数据: {message_id}")
            return True
            
        except Exception as e:
            error_msg = f"保存分析数据时出错: {str(e)}"
            logger.error(error_msg)
            logger.debug(traceback.format_exc())
            
            # 回滚事务
            if self.connection:
                self.connection.rollback()
                
            return False
    
    def _create_tables(self) -> None:
        """创建必要的数据库表和索引"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 创建消息表
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id TEXT NOT NULL,
                sender_id TEXT,
                sender_name TEXT,
                chat_id TEXT,
                chat_title TEXT,
                message_type TEXT,
                content TEXT,
                media_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                received_at TIMESTAMP,
                raw_data TEXT
            )
            """)
            
            # 创建分析结果表（更新表结构，添加更多字段）
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id TEXT NOT NULL,
                content_type TEXT,
                category TEXT,
                subcategory TEXT,
                sentiment TEXT,
                language TEXT,
                summary TEXT,
                keywords TEXT,
                urls TEXT,
                content_format TEXT,
                has_web_content INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                raw_data TEXT,
                FOREIGN KEY (message_id) REFERENCES messages (message_id)
            )
            """)
            
            # 创建索引
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_message_id ON messages (message_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages (created_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_analysis_message_id ON analysis (message_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_analysis_category ON analysis (category)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_analysis_content_type ON analysis (content_type)")
            
            conn.commit()
    
    def _backup_database(self) -> None:
        """备份数据库"""
        if not self.backup_dir or not self.db_path:
            return
            
        try:
            # 生成备份文件名
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            backup_file = os.path.join(self.backup_dir, f"storage_{timestamp}.db")
            
            # 创建备份目录（如果不存在）
            os.makedirs(self.backup_dir, exist_ok=True)
            
            # 创建备份
            logger.info(f"正在备份数据库到 {backup_file}")
            # 使用sqlite3的备份API
            backup_conn = sqlite3.connect(backup_file)
            source_conn = sqlite3.connect(self.db_path)
            source_conn.backup(backup_conn)
            backup_conn.close()
            source_conn.close()
            
            logger.info(f"数据库备份成功: {backup_file}")
            
            # 清理旧备份
            self._cleanup_old_backups()
            
        except Exception as e:
            logger.error(f"备份数据库时出错: {e}")
    
    def _cleanup_old_backups(self) -> None:
        """清理旧的备份文件，只保留最近10个"""
        try:
            if not self.backup_dir or not os.path.exists(self.backup_dir):
                return
                
            # 获取所有备份文件
            backup_files = [
                os.path.join(self.backup_dir, f) 
                for f in os.listdir(self.backup_dir) 
                if f.startswith("storage_") and f.endswith(".db")
            ]
            
            # 按修改时间排序
            backup_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            
            # 删除旧文件
            for old_file in backup_files[self.max_backups:]:
                logger.debug(f"删除旧备份: {old_file}")
                os.remove(old_file)
                
        except Exception as e:
            logger.error(f"清理旧备份时出错: {e}")
    
    async def _processing_loop(self) -> None:
        """处理队列中的数据"""
        logger.info("存储处理循环已启动")
        
        while True:
            try:
                # 处理队列中的消息
                if self.message_queue:
                    # 获取下一个待处理的数据
                    data_type, data = self.message_queue.pop(0)
                    
                    # 根据数据类型进行处理
                    if data_type == "message":
                        await self.store_message(data)
                    elif data_type == "analysis":
                        await self.store_analysis(data)
                
                # 如果队列为空，休眠一段时间
                if not self.message_queue:
                    await asyncio.sleep(0.1)
                
            except asyncio.CancelledError:
                logger.info("存储处理循环被取消")
                break
            except Exception as e:
                logger.error(f"存储处理循环出错: {str(e)}")
                await asyncio.sleep(1)  # 出错后等待一段时间再继续 