"""
系统协调器
负责协调各个模块的工作
"""
import logging
import time
from typing import Dict, Any, Optional

from app.adapters.base import DataSourceAdapter
from app.adapters.telegram import TelegramAdapter
from app.processors.base import ContentProcessor
from app.processors.twitter import TwitterLinkProcessor
from app.analyzers.base import ContentAnalyzer
from app.analyzers.gpt import GPTAnalyzer
from app.storage.base import StorageBackend
from app.storage.local import LocalStorage
from .config import ConfigLoader


class XCatSystem:
    """X帖子分类系统协调器"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化系统协调器
        
        Args:
            config_path: 配置文件路径，如果为None则使用默认路径
        """
        # 设置日志
        self.logger = logging.getLogger(__name__)
        
        # 加载配置
        self.config_loader = ConfigLoader(config_path)
        self.config = self.config_loader.get_config()
        
        # 初始化各个模块
        self.data_source = self._init_data_source()
        self.processor = self._init_processor()
        self.analyzer = self._init_analyzer()
        self.storage = self._init_storage()
        
        self.logger.info("X帖子分类系统初始化完成")
    
    def _init_data_source(self) -> DataSourceAdapter:
        """
        根据配置初始化数据源适配器
        
        Returns:
            数据源适配器实例
        """
        data_source_config = self.config.get('data_source', {})
        data_source_type = data_source_config.get('type', 'telegram')
        
        if data_source_type == 'telegram':
            api_key = data_source_config.get('api_key', '')
            channel_id = data_source_config.get('channel_id', '')
            processed_messages_file = data_source_config.get('processed_messages_file', 'data/processed_messages.txt')
            
            # Check if mock mode is enabled
            if data_source_config.get('mock_mode', False):
                self.logger.info("使用模拟模式初始化Telegram适配器")
                api_key = "mock_" + api_key
            
            return TelegramAdapter(api_key, channel_id, processed_messages_file)
        else:
            self.logger.warning(f"不支持的数据源类型: {data_source_type}，使用默认的Telegram适配器")
            return TelegramAdapter('', '')
    
    def _init_processor(self) -> ContentProcessor:
        """
        根据配置初始化内容处理器
        
        Returns:
            内容处理器实例
        """
        # 目前只支持Twitter链接处理器
        return TwitterLinkProcessor()
    
    def _init_analyzer(self) -> ContentAnalyzer:
        """
        根据配置初始化内容分析器
        
        Returns:
            内容分析器实例
        """
        analyzer_config = self.config.get('analyzer', {})
        analyzer_type = analyzer_config.get('type', 'gpt')
        
        if analyzer_type == 'gpt':
            api_key = analyzer_config.get('api_key', '')
            categories = analyzer_config.get('categories', [])
            return GPTAnalyzer(api_key, categories)
        else:
            self.logger.warning(f"不支持的分析器类型: {analyzer_type}，使用默认的GPT分析器")
            return GPTAnalyzer('', [])
    
    def _init_storage(self) -> StorageBackend:
        """
        根据配置初始化存储后端
        
        Returns:
            存储后端实例
        """
        storage_config = self.config.get('storage', {})
        storage_type = storage_config.get('type', 'local')
        
        if storage_type == 'local':
            db_path = storage_config.get('db_path', 'data/xcat.db')
            return LocalStorage(db_path)
        else:
            self.logger.warning(f"不支持的存储类型: {storage_type}，使用默认的本地存储")
            return LocalStorage('data/xcat.db')
    
    def run_once(self) -> int:
        """
        执行一次完整的处理流程
        
        Returns:
            成功处理的内容数量
        """
        try:
            # 1. 从数据源获取内容
            self.logger.info("正在从数据源获取内容")
            raw_contents = self.data_source.fetch_content()
            
            if not raw_contents:
                self.logger.info("没有新内容需要处理")
                return 0
            
            self.logger.info(f"获取到 {len(raw_contents)} 条新内容")
            
            processed_count = 0
            
            # 2. 逐条处理内容
            for raw_content in raw_contents:
                try:
                    # 3. 处理内容
                    processed_content = self.processor.process(raw_content)
                    
                    if not processed_content.get('processed', False):
                        self.logger.info(f"内容处理失败: {processed_content.get('error', '未知原因')}")
                        continue
                    
                    # 4. 分析分类
                    analyzed_content = self.analyzer.analyze(processed_content)
                    
                    if not analyzed_content.get('analyzed', False):
                        self.logger.info(f"内容分析失败: {analyzed_content.get('error', '未知原因')}")
                        continue
                    
                    # 5. 存储结果
                    success = self.storage.save(analyzed_content)
                    
                    if success:
                        # 6. 标记为已处理
                        self.data_source.mark_as_processed(raw_content.get('id', ''))
                        processed_count += 1
                    
                except Exception as e:
                    self.logger.error(f"处理内容时发生错误: {str(e)}")
            
            self.logger.info(f"成功处理 {processed_count} 条内容")
            return processed_count
        
        except Exception as e:
            self.logger.error(f"运行处理流程时发生错误: {str(e)}")
            return 0
    
    def run(self, interval: int = 60):
        """
        持续运行系统
        
        Args:
            interval: 轮询间隔(秒)
        """
        self.logger.info(f"系统开始运行，轮询间隔 {interval} 秒")
        
        try:
            while True:
                count = self.run_once()
                self.logger.info(f"本次运行处理了 {count} 条内容，等待 {interval} 秒后再次运行")
                time.sleep(interval)
        
        except KeyboardInterrupt:
            self.logger.info("接收到中断信号，系统停止运行")
        except Exception as e:
            self.logger.error(f"系统运行时发生错误: {str(e)}")
        
        self.logger.info("系统已停止运行") 