"""
Content preprocessor module
"""
import os
import re
import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime
from loguru import logger
from prefect import task
from .base_processor import BaseProcessor
from app.preprocessor.preprocessor_config import PreprocessorConfig
from app.preprocessor.state import StateManager, ProcessingStatus
from app.preprocessor.url_extractor import URLExtractor
from app.preprocessor.content_fetcher import ContentFetcher
from app.preprocessor.command_processor import CommandProcessor
from app.preprocessor.content_cleaner import ContentCleaner

class ContentPreprocessor(BaseProcessor):
    """Content preprocessor that preprocesses content before analysis
    
    处理规则:
    1. 根据内容的类型做不同处理:
       - 对于 text 类型:
         - 判断里面是否有 URL，如果有 URL，调用 app/preprocessor/content_fetcher 来获取 URL 的内容，并和原来的文本内容组合到一起
         - 如果只是文本内容，不做其它处理
       - 对于 URL 类型:
         - 直接获取 URL 内容
       - 对于 command 类型:
         - 处理命令
       - 对于 media 类型:
         - 处理媒体内容
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化内容预处理器
        
        Args:
            config: 配置信息
        """
        super().__init__(config)
        
        # 从配置中获取预处理器相关的配置
        preprocessor_config = config.get("preprocessor", {}) if config else {}
        
        # 初始化配置
        self.config = PreprocessorConfig.from_dict(preprocessor_config)
        
        http_proxy = os.environ.get('HTTP_PROXY', '')
        https_proxy = os.environ.get('HTTPS_PROXY', '')
        logger.info(f"HTTP_PROXY={http_proxy}, HTTPS_PROXY={https_proxy}")

        # 初始化状态管理器
        self.state_manager = StateManager()
        
        # 基础配置
        self.clean_html = self.config.remove_html
        self.remove_extra_spaces = self.config.remove_extra_spaces
        self.normalize_whitespace = True  # 默认启用
        self.max_length = self.config.max_content_length
        
        # 初始化组件
        self.url_extractor = URLExtractor()
        self.content_fetcher = ContentFetcher(
            proxy_url=self.config.proxy_url,
            timeout=self.config.timeout,
            max_content_length=self.config.max_content_length,
            user_agent=self.config.user_agent,
            max_retries=self.config.max_retries
        )
        self.content_cleaner = ContentCleaner()
        self.command_processor = CommandProcessor()
        
        logger.info(f"内容预处理器初始化完成，配置: {self.config}")

    def initialize(self) -> bool:
        """Initialize the preprocessor
        
        Returns:
            bool: Whether initialization was successful
        """
        try:
            logger.info("Initializing content preprocessor")
            
            # 验证配置
            if not self.config.validate():
                return False
                
            # 初始化命令处理器
            if hasattr(self.command_processor, 'initialize'):
                asyncio.run(self.command_processor.initialize())
                
            self.state_manager.start_processing()
            super().initialize()
            return True
        except Exception as e:
            logger.error(f"Error initializing content preprocessor: {str(e)}")
            self.state_manager.update_progress("initialize", False, str(e))
            return False
        
    def cleanup(self) -> None:
        """Cleanup preprocessor resources"""
        logger.info("Cleaning up content preprocessor")
        self.state_manager.complete_processing(True)
        super().cleanup()
        
    @task
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理数据
        
        Args:
            data: 原始数据
            
        Returns:
            处理后的数据
        """
        try:
            self.state_manager.update_progress("process")
            logger.info(f"开始预处理数据: {data}")
            
            # 复制原始数据
            processed_data = data.copy()
            
            # 获取内容
            content = processed_data.get("content", "")
            if not content:
                logger.warning("数据中没有内容字段")
                self.state_manager.update_progress("process", False, "数据中没有内容字段")
                return processed_data
            
            # 确定内容类型
            content_type = self._determine_content_type(content, processed_data.get("metadata", {}))
            self.state_manager.update_progress(f"determine_type_{content_type}")
            
            # 根据内容类型处理
            if content_type == "url":
                result = asyncio.run(self._handle_url(content, processed_data))
                if result["success"]:
                    processed_data = result["content"]
                else:
                    logger.error(f"URL处理失败: {result['errors']}")
                    self.state_manager.update_progress("process_url", False, result["errors"][0])
            elif content_type == "command":
                result = self._handle_command(content, processed_data)
                if result["success"]:
                    processed_data = result["content"]
                else:
                    logger.error(f"命令处理失败: {result['errors']}")
                    self.state_manager.update_progress("process_command", False, result["errors"][0])
            elif content_type == "media":
                result = self._handle_media(processed_data)
                if result["success"]:
                    processed_data = result["content"]
                else:
                    logger.error(f"媒体处理失败: {result['errors']}")
                    self.state_manager.update_progress("process_media", False, result["errors"][0])
            else:
                # 处理普通文本
                processed_content = self._process_text(content)
                processed_data["content"] = processed_content
                self.state_manager.update_progress("process_text")
            
            # 添加预处理标记
            processed_data["preprocessed"] = True
            processed_data["preprocessing_info"] = {
                "clean_html": self.clean_html,
                "remove_extra_spaces": self.remove_extra_spaces,
                "normalize_whitespace": self.normalize_whitespace,
                "max_length": self.max_length,
                "original_length": len(content),
                "processed_length": len(processed_data.get("content", "")),
                "content_type": content_type,
                "status": self.state_manager.get_state().status.value,
                "progress": self.state_manager.get_progress()
            }
            
            logger.info(f"数据预处理完成: {processed_data}")
            return processed_data
            
        except Exception as e:
            logger.error(f"预处理失败: {str(e)}")
            self.state_manager.update_progress("process", False, str(e))
            return data
    
    def _process_text(self, text: str) -> str:
        """
        处理文本内容
        
        Args:
            text: 原始文本
            
        Returns:
            处理后的文本
        """
        # 检查文本中是否包含URL
        urls = self.url_extractor.extract_urls(text)
        
        if urls:
            logger.info(f"文本中包含 {len(urls)} 个URL，将获取URL内容并组合")
            # 获取URL内容
            url_contents = asyncio.run(self._fetch_url_contents(urls))
            
            # 组合原始文本和URL内容
            combined_text = text
            for i, url_content in enumerate(url_contents):
                if url_content["success"]:
                    combined_text += f"\n\n--- URL内容 ({urls[i]}) ---\n{url_content['content']}"
                else:
                    combined_text += f"\n\n--- URL获取失败 ({urls[i]}) ---\n{url_content['error']}"
            
            text = combined_text
        
        # 清理HTML标签
        if self.clean_html:
            text = self._clean_html(text)
        
        # 移除多余空格
        if self.remove_extra_spaces:
            text = self._remove_extra_spaces(text)
        
        # 规范化空白字符
        if self.normalize_whitespace:
            text = self._normalize_whitespace(text)
        
        # 截断过长的内容
        if len(text) > self.max_length:
            text = text[:self.max_length] + "..."
            logger.warning(f"内容已截断至 {self.max_length} 字符")
        
        return text
    
    async def _fetch_url_contents(self, urls: List[str]) -> List[Dict[str, Any]]:
        """
        获取URL内容
        
        Args:
            urls: URL列表
            
        Returns:
            URL内容列表
        """
        try:
            return await self.content_fetcher.fetch(urls)
        except Exception as e:
            logger.error(f"获取URL内容失败: {str(e)}")
            return [{"success": False, "error": str(e)} for _ in urls]
    
    def _determine_content_type(self, text: str, metadata: Dict) -> str:
        """
        确定内容类型
        
        Args:
            text: 文本内容
            metadata: 元数据
            
        Returns:
            str: 内容类型
        """
        if text.startswith(self.config.command_prefix):
            return "command"
        elif self.url_extractor.is_valid_url(text):
            return "url"
        elif self._has_media(metadata):
            return "media"
        else:
            return "text"
    
    async def _handle_url(self, url: str, raw_content: Dict) -> Dict:
        """
        处理URL内容
        
        Args:
            url: URL地址
            raw_content: 原始内容
            
        Returns:
            Dict: 处理结果
        """
        try:
            logger.info(f"开始获取URL内容: {url}")
            
            # 获取URL内容
            results = await self.content_fetcher.fetch([url])
            result = results[0]
            
            if not result['success']:
                logger.error(f"获取URL内容失败: {result['error']}")
                return {
                    'success': False,
                    'errors': [result['error']]
                }
            
            logger.info(f"成功获取URL内容，长度: {len(result['content'])} 字符")
            
            # 构建内容格式
            content = {
                'content': result['content'],
                'type': 'article',
                'format': 'text',
                'source': result.get('source', url),
                'timestamp': datetime.now().isoformat(),
                'metadata': {
                    'url': url,
                    'original_content': raw_content.get('content', ''),
                    **result.get('metadata', {}),
                    **raw_content.get('metadata', {})
                }
            }
            
            logger.debug(f"内容处理完成: type={content['type']}, format={content['format']}")
            
            return {
                'success': True,
                'content': content,
                'errors': [],
                'debug_info': {
                    'url': url,
                    'content_length': len(result['content'])
                }
            }
            
        except Exception as e:
            logger.error(f"URL内容处理失败: {str(e)}")
            return {
                'success': False,
                'errors': [str(e)]
            }
    
    def _handle_command(self, text: str, raw_content: Dict) -> Dict:
        """
        处理命令
        
        Args:
            text: 命令文本
            raw_content: 原始内容
            
        Returns:
            Dict: 处理结果
        """
        try:
            logger.info(f"开始处理命令: {text}")
            
            # 处理命令
            result = self.command_processor.process(text)
            
            if not result['success']:
                logger.error(f"命令处理失败: {result['error']}")
                return {
                    'success': False,
                    'errors': [result['error']]
                }
            
            logger.info("命令处理成功")
            
            # 构建内容格式
            content = {
                'content': result['content'],
                'type': 'command',
                'format': 'text',
                'source': raw_content.get('source', 'command'),
                'timestamp': datetime.now().isoformat(),
                'metadata': {
                    'command': text,
                    'original_content': raw_content.get('content', ''),
                    **raw_content.get('metadata', {})
                }
            }
            
            return {
                'success': True,
                'content': content,
                'errors': []
            }
            
        except Exception as e:
            logger.error(f"命令处理失败: {str(e)}")
            return {
                'success': False,
                'errors': [str(e)]
            }
    
    def _handle_media(self, raw_content: Dict) -> Dict:
        """
        处理媒体内容
        
        Args:
            raw_content: 原始内容
            
        Returns:
            Dict: 处理结果
        """
        try:
            metadata = raw_content.get('metadata', {})
            
            # 统计媒体数量
            photo_count = len(metadata.get('photo', []))
            video_count = len(metadata.get('video', []))
            document_count = len(metadata.get('document', []))
            
            logger.info(f"处理媒体内容: 图片={photo_count}, 视频={video_count}, 文档={document_count}")
            
            # 构建内容格式
            content = {
                'content': raw_content.get('content', ''),
                'type': 'media',
                'format': 'mixed',
                'source': raw_content.get('source', 'media'),
                'timestamp': datetime.now().isoformat(),
                'metadata': {
                    'photo': metadata.get('photo', []),
                    'video': metadata.get('video', []),
                    'document': metadata.get('document', []),
                    'original_content': raw_content.get('content', ''),
                    **metadata
                }
            }
            
            logger.debug(f"媒体内容处理完成: type={content['type']}, format={content['format']}")
            
            return {
                'success': True,
                'content': content,
                'errors': []
            }
            
        except Exception as e:
            logger.error(f"媒体内容处理失败: {str(e)}")
            return {
                'success': False,
                'errors': [str(e)]
            }
    
    def _has_media(self, metadata: Dict) -> bool:
        """
        检查是否有媒体内容
        
        Args:
            metadata: 元数据
            
        Returns:
            bool: 是否有媒体内容
        """
        has_media = bool(
            metadata.get('photo') or
            metadata.get('video') or
            metadata.get('document')
        )
        if has_media:
            logger.debug("检测到媒体内容")
        return has_media
    
    def _clean_html(self, text: str) -> str:
        """
        清理HTML标签
        
        Args:
            text: 原始文本
            
        Returns:
            清理后的文本
        """
        # 移除HTML标签
        text = re.sub(r'<[^>]+>', '', text)
        # 解码HTML实体
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&amp;', '&')
        text = text.replace('&quot;', '"')
        text = text.replace('&apos;', "'")
        return text
    
    def _remove_extra_spaces(self, text: str) -> str:
        """
        移除多余空格
        
        Args:
            text: 原始文本
            
        Returns:
            处理后的文本
        """
        # 移除连续的空格
        text = re.sub(r'\s+', ' ', text)
        return text
    
    def _normalize_whitespace(self, text: str) -> str:
        """
        规范化空白字符
        
        Args:
            text: 原始文本
            
        Returns:
            处理后的文本
        """
        # 将制表符替换为空格
        text = text.replace('\t', ' ')
        # 将换行符替换为空格
        text = text.replace('\n', ' ')
        # 移除连续的空格
        text = re.sub(r'\s+', ' ', text)
        return text 