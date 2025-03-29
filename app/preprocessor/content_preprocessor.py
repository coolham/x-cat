# -*- coding: utf-8 -*-
"""
内容预处理器
负责处理原始内容，包括URL提取、内容获取、指令处理等
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
from loguru import logger
from .url_extractor import URLExtractor
from .content_fetcher import ContentFetcher
from .command_processor import CommandProcessor
from app.core.processors import ContentPreprocessor as BaseContentPreprocessor
from .content_cleaner import ContentCleaner

class ContentPreprocessor(BaseContentPreprocessor):
    """
    内容预处理器：
    - 预处理器应该专注于基础功能：
        - URL 内容获取
        - 命令处理
        - 媒体内容识别
        - 基础文本清理
    """
    
    def __init__(
        self,
        config: Dict[str, Any],
        runtime: Any,
        proxy_url: Optional[str] = None,
        timeout: int = 30,
        max_content_length: int = 8000,
        max_url_count: int = 5,
        user_agent: Optional[str] = None,
        max_retries: int = 2
    ):
        """初始化内容预处理器
        
        Args:
            config: 配置字典
            runtime: 运行时环境
            proxy_url: 代理服务器URL (可选)
            timeout: 请求超时时间(秒)
            max_content_length: 提取内容的最大长度
            max_url_count: 每个消息最多提取的URL数量
            user_agent: 自定义User-Agent
            max_retries: 最大重试次数
        """
        super().__init__(config, runtime)
        
        # 保存配置
        self.proxy_url = proxy_url
        self.timeout = timeout
        self.max_content_length = max_content_length
        self.max_url_count = max_url_count
        self.user_agent = user_agent
        self.max_retries = max_retries
        
        # 初始化组件
        self.url_extractor = URLExtractor()
        self.content_fetcher = ContentFetcher(
            config=config,
            proxy_url=proxy_url,
            timeout=timeout,
            max_content_length=max_content_length,
            user_agent=user_agent,
            max_retries=max_retries
        )
        self.content_cleaner = ContentCleaner()
        self.command_processor = CommandProcessor()
        
        logger.info(f"内容预处理器初始化成功: max_url_count={max_url_count}, max_content_length={max_content_length}")
    
    async def preprocess(self, raw_content: Dict) -> Dict:
        """预处理内容
        
        Args:
            raw_content: 原始内容，包含以下字段：
                - text: 文本内容
                - source: 来源
                - metadata: 元数据（可选）
                
        Returns:
            Dict: 处理结果，包含以下字段：
                - success: 是否成功
                - content: 处理后的内容（成功时）
                - errors: 错误信息列表（失败时）
        """
        try:
            logger.info(f"开始预处理内容，来源: {raw_content.get('source', 'unknown')}")
            
            # 验证输入
            if not self._validate_input(raw_content):
                logger.error("输入内容格式无效")
                return {
                    'success': False,
                    'errors': ['输入内容格式无效']
                }
            
            text = raw_content['text']
            metadata = raw_content.get('metadata', {})
            
            logger.debug(f"内容长度: {len(text)} 字符")
            
            # 检查是否是命令
            if text.startswith('/'):
                logger.info("检测到命令，使用命令处理器处理")
                return self._handle_command(text, raw_content)
            
            # 检查是否是URL
            if self.url_extractor.is_valid_url(text):
                logger.info(f"检测到URL: {text}")
                return await self._handle_url(text, raw_content)
            
            # 检查是否有媒体内容
            if self._has_media(metadata):
                logger.info("检测到媒体内容")
                return self._handle_media(raw_content)
            
            # 处理普通文本
            logger.info("作为普通文本处理")
            return self._handle_text(text, raw_content)
            
        except Exception as e:
            logger.error(f"内容预处理失败: {str(e)}")
            return {
                'success': False,
                'errors': [str(e)]
            }
    
    def _validate_input(self, raw_content: Dict) -> bool:
        """验证输入内容
        
        Args:
            raw_content: 原始内容
            
        Returns:
            bool: 是否有效
        """
        if not isinstance(raw_content, dict):
            logger.error("输入内容不是字典类型")
            return False
        if 'text' not in raw_content or not isinstance(raw_content['text'], str):
            logger.error("输入内容缺少text字段或不是字符串类型")
            return False
        if 'source' not in raw_content or not isinstance(raw_content['source'], str):
            logger.error("输入内容缺少source字段或不是字符串类型")
            return False
        return True
    
    async def _handle_url(self, url: str, raw_content: Dict) -> Dict:
        """处理URL内容
        
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
                'text': result['content'],
                'type': 'article',
                'format': 'text',
                'source': result.get('source', url),
                'timestamp': datetime.now().isoformat(),
                'metadata': {
                    'url': url,
                    'original_text': raw_content['text'],
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
        """处理命令
        
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
                'text': result['content'],
                'type': 'command',
                'format': 'text',
                'source': raw_content['source'],
                'timestamp': datetime.now().isoformat(),
                'metadata': {
                    'command': text,
                    'original_text': raw_content['text'],
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
        """处理媒体内容
        
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
                'text': raw_content['text'],
                'type': 'media',
                'format': 'mixed',
                'source': raw_content['source'],
                'timestamp': datetime.now().isoformat(),
                'metadata': {
                    'photo': metadata.get('photo', []),
                    'video': metadata.get('video', []),
                    'document': metadata.get('document', []),
                    'original_text': raw_content['text'],
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
    
    def _handle_text(self, text: str, raw_content: Dict) -> Dict:
        """处理普通文本
        
        Args:
            text: 文本内容
            raw_content: 原始内容
            
        Returns:
            Dict: 处理结果
        """
        try:
            logger.info(f"处理普通文本，长度: {len(text)} 字符")
            
            # 构建内容格式
            content = {
                'text': text,
                'type': 'text',
                'format': 'text',
                'source': raw_content['source'],
                'timestamp': datetime.now().isoformat(),
                'metadata': {
                    'original_text': text,
                    **raw_content.get('metadata', {})
                }
            }
            
            logger.debug(f"文本处理完成: type={content['type']}, format={content['format']}")
            
            return {
                'success': True,
                'content': content,
                'errors': []
            }
            
        except Exception as e:
            logger.error(f"文本处理失败: {str(e)}")
            return {
                'success': False,
                'errors': [str(e)]
            }
    
    def _has_media(self, metadata: Dict) -> bool:
        """检查是否有媒体内容
        
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
    
    async def close(self):
        """关闭资源"""
        logger.info("开始关闭内容预处理器")
        await self.content_fetcher.close()
        logger.info("内容预处理器已关闭")
