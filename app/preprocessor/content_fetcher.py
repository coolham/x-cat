# -*- coding: utf-8 -*-
"""
内容获取器工厂类
负责根据URL类型选择合适的获取器
"""
from typing import Dict, Any, List, Optional, Tuple, Callable
from loguru import logger
from urllib.parse import urlparse, parse_qs, urlencode
import re
from .playwright_fetcher import PlaywrightFetcher
from .twitter_api_fetcher import TwitterAPIFetcher
from .aiohttp_fetcher import AiohttpFetcher
import asyncio
import os
from dotenv import load_dotenv

class ContentFetcher:
    """
    内容获取器工厂类
    根据URL类型选择合适的获取器
    
    处理规则:
    1. 对于图片、视频或文件链接，不获取内容，直接返回原始URL
    2. 对于Twitter等推文，使用Playwright机制获取内容
    3. 对于常规内容，使用网络请求获取，如果不能直接访问，使用代理服务器
    """
    
    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        proxy_url: Optional[str] = None,
        timeout: int = 30,
        max_content_length: int = 8000,
        user_agent: Optional[str] = None,
        max_retries: int = 2
    ):
        """
        初始化网页内容获取模块
        
        Args:
            config: 配置字典 (可选)
            proxy_url: 代理服务器URL (可选)
            timeout: 请求超时时间(秒)
            max_content_length: 提取内容的最大长度
            user_agent: 自定义User-Agent
            max_retries: 最大重试次数
        """
        # 优先使用传入的代理设置，如果没有则使用环境变量中的代理设置
        self.proxy_url = proxy_url or os.environ.get('HTTP_PROXY') or os.environ.get('HTTPS_PROXY')
        self.timeout = timeout
        self.max_content_length = max_content_length
        self.max_retries = max_retries
        
        # 默认User-Agent
        self.user_agent = user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        
        # HTTP会话
        self._session = None
        
        # 从配置中获取Twitter API配置
        twitter_api_config = (config or {}).get('twitter_api', {})
        if twitter_api_config:
            logger.info("初始化 Twitter API 获取器")
            self._twitter_api_fetcher = TwitterAPIFetcher(
                api_key=twitter_api_config.get('api_key'),
                api_secret=twitter_api_config.get('api_secret'),
                access_token=twitter_api_config.get('access_token'),
                access_token_secret=twitter_api_config.get('access_token_secret'),
                bearer_token=twitter_api_config.get('bearer_token'),
                max_content_length=max_content_length,
                proxy_url=self.proxy_url
            )
        else:
            logger.warning("Twitter API 配置不完整，将使用其他方式获取内容")
            self._twitter_api_fetcher = None
        
        # 初始化各个获取器
        self._aiohttp_fetcher = AiohttpFetcher(
            proxy_url=self.proxy_url,
            timeout=timeout,
            max_content_length=max_content_length,
            user_agent=user_agent
        )
        
        self._playwright_fetcher = PlaywrightFetcher(
            proxy_url=self.proxy_url,
            timeout=timeout,
            max_content_length=max_content_length,
            user_agent=user_agent
        )
        
        # Twitter/X URL 匹配模式
        self.twitter_url_patterns = [
            r'https?://(?:www\.)?twitter\.com/\w+/status/\d+',
            r'https?://(?:www\.)?x\.com/\w+/status/\d+'
        ]
        
        # 媒体文件扩展名
        self.media_extensions = [
            # 图片
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg', '.ico',
            # 视频
            '.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv', '.webm',
            # 音频
            '.mp3', '.wav', '.ogg', '.flac', '.aac',
            # 文档
            '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
            '.txt', '.rtf', '.csv', '.zip', '.rar', '.7z', '.tar', '.gz'
        ]
        
        logger.info(f"初始化内容获取器: timeout={timeout}s, max_content_length={max_content_length}")
        logger.info(f"使用代理设置: {self.proxy_url}")
    
    async def _extract_twitter(self, url: str) -> Dict[str, Any]:
        """
        提取Twitter/X内容
        
        Args:
            url: Twitter/X URL
            
        Returns:
            内容字典
        """
        # 调用通用处理，后续可以添加Twitter特定处理逻辑
        result = await self._fetch_generic(url)
        result["type"] = "twitter"
        return result
    
    async def _extract_medium(self, url: str) -> Dict[str, Any]:
        """
        提取Medium内容
        
        Args:
            url: Medium URL
            
        Returns:
            内容字典
        """
        # 调用通用处理，后续可以添加Medium特定处理逻辑
        result = await self._fetch_generic(url)
        result["type"] = "medium"
        return result
    
    async def _extract_github(self, url: str) -> Dict[str, Any]:
        """
        提取GitHub内容
        
        Args:
            url: GitHub URL
            
        Returns:
            内容字典
        """
        # 调用通用处理，后续可以添加GitHub特定处理逻辑
        result = await self._fetch_generic(url)
        result["type"] = "github"
        return result
    
    @property
    def site_handlers(self) -> Dict[str, Callable]:
        """获取站点处理器映射"""
        return {
            "twitter.com": self._extract_twitter,
            "x.com": self._extract_twitter,
            "medium.com": self._extract_medium,
            "github.com": self._extract_github
        }
    
    def _is_twitter_url(self, url: str) -> bool:
        """
        检查是否是Twitter/X URL
        
        Args:
            url: URL地址
            
        Returns:
            bool: 是否是Twitter/X URL
        """
        for pattern in self.twitter_url_patterns:
            if re.search(pattern, url):
                return True
        return False
    
    def _is_media_url(self, url: str) -> bool:
        """
        检查是否是媒体文件URL
        
        Args:
            url: URL地址
            
        Returns:
            bool: 是否是媒体文件URL
        """
        parsed = urlparse(url)
        path = parsed.path.lower()
        return any(path.endswith(ext) for ext in self.media_extensions)
    
    def _clean_twitter_url(self, url: str) -> str:
        """
        清理Twitter/X URL，移除不必要的参数
        
        Args:
            url: 原始URL
            
        Returns:
            str: 清理后的URL
        """
        parsed = urlparse(url)
        # 只保留路径部分
        clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        logger.debug(f"清理Twitter URL: {url} -> {clean_url}")
        return clean_url
    
    def _extract_tweet_id_from_url(self, url: str) -> Optional[str]:
        """
        从URL中提取推文ID
        
        Args:
            url: URL地址
            
        Returns:
            Optional[str]: 推文ID或None
        """
        # 检查是否是Twitter相关域名
        parsed = urlparse(url)
        if parsed.netloc not in ["twitter.com", "www.twitter.com", "x.com", "www.x.com", "m.twitter.com", "m.x.com"]:
            logger.debug(f"URL域名不属于Twitter: {url}")
            return None

        # 清理URL，移除查询参数和片段
        clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        
        # 使用正则表达式提取推文ID
        match = re.search(r'/status/(\d+)', clean_url)
        if match:
            tweet_id = match.group(1)
            logger.debug(f"从URL提取推文ID: {clean_url} -> {tweet_id}")
            return tweet_id
        
        logger.debug(f"未能从URL提取推文ID: {clean_url}")
        return None
    
    def _log_content_preview(self, content: str, source: str, url: str):
        """
        记录内容预览
        
        Args:
            content: 获取的内容
            source: 内容来源（获取方式）
            url: URL地址
        """
        preview = content[:64] + "..." if len(content) > 64 else content
        logger.info(f"使用 {source} 获取内容成功: {url}")
        logger.info(f"内容预览: {preview}")
    
    async def _fetch_single_url(self, url: str) -> Dict[str, Any]:
        """
        获取单个URL的内容，按优先级尝试不同的获取方式
        
        Args:
            url: URL地址
            
        Returns:
            Dict[str, Any]: 获取结果
        """
        # 检查是否是媒体文件URL
        if self._is_media_url(url):
            logger.info(f"检测到媒体文件URL，直接返回: {url}")
            return {
                'success': True,
                'url': url,
                'content': url,
                'type': 'media',
                'title': url,
                'metadata': {'is_media': True, 'original_url': url}
            }
        
        # 1. 首先尝试使用 Twitter API
        if self._twitter_api_fetcher and self._is_twitter_url(url):
            clean_url = self._clean_twitter_url(url)
            tweet_id = self._extract_tweet_id_from_url(clean_url)
            if tweet_id:
                logger.debug(f"尝试使用 Twitter API 获取: {url}")
                result = await self._twitter_api_fetcher.fetch([clean_url])
                if result and result[0]['success']:
                    self._log_content_preview(result[0]['content'], "Twitter API", url)
                    return result[0]
                logger.warning(f"Twitter API 获取失败: {url} - {result[0].get('error', '未知错误')}")
        
        # 2. 如果是Twitter URL，使用Playwright
        if self._is_twitter_url(url):
            logger.debug(f"尝试使用 Playwright 获取Twitter内容: {url}")
            result = await self._playwright_fetcher.fetch([url])
            if result and result[0]['success']:
                self._log_content_preview(result[0]['content'], "Playwright", url)
                return result[0]
            logger.warning(f"Playwright 获取Twitter内容失败: {url} - {result[0].get('error', '未知错误')}")
        
        # 3. 尝试使用 aiohttp
        logger.debug(f"尝试使用 aiohttp 获取: {url}")
        result = await self._aiohttp_fetcher.fetch([url])
        if result and result[0]['success']:
            self._log_content_preview(result[0]['content'], "aiohttp", url)
            return result[0]
        logger.warning(f"aiohttp 获取失败: {url} - {result[0].get('error', '未知错误')}")
        
        # 4. 最后尝试使用 Playwright
        logger.debug(f"尝试使用 Playwright 获取: {url}")
        result = await self._playwright_fetcher.fetch([url])
        if result and result[0]['success']:
            self._log_content_preview(result[0]['content'], "Playwright", url)
            return result[0]
        logger.error(f"所有获取方式都失败: {url}")
        return result[0] if result else {'success': False, 'error': '所有获取方式都失败'}
    
    async def fetch(self, urls: List[str]) -> List[Dict[str, Any]]:
        """
        获取多个URL的内容
        
        Args:
            urls: URL列表
            
        Returns:
            内容列表，每个元素是一个字典
        """
        if not urls:
            logger.warning("没有提供URL")
            return []
        
        # 确定获取方式
        fetch_methods = []
        for url in urls:
            if self._is_media_url(url):
                fetch_methods.append("媒体文件(直接返回)")
            elif self._twitter_api_fetcher and self._is_twitter_url(url):
                fetch_methods.append("Twitter API")
            elif self._is_twitter_url(url):
                fetch_methods.append("Playwright (Twitter)")
            else:
                fetch_methods.append("aiohttp/Playwright")
        
        logger.info(f"开始获取 {len(urls)} 个URL的内容，获取方式: {', '.join(fetch_methods)}")
        
        # 并行获取所有URL的内容
        tasks = [self._fetch_single_url(url) for url in urls]
        results = await asyncio.gather(*tasks)
        
        # 统计结果
        success_count = sum(1 for r in results if r['success'])
        logger.info(f"内容获取完成: 总数={len(results)}, 成功={success_count}, 失败={len(results)-success_count}")
        
        return results
    
    async def close(self):
        """关闭所有获取器"""
        logger.info("开始关闭所有内容获取器")
        await self._aiohttp_fetcher.close()
        await self._playwright_fetcher.close()
        if self._twitter_api_fetcher:
            await self._twitter_api_fetcher.close()
        logger.info("所有内容获取器已关闭")

    async def _fetch_generic(self, url: str) -> Dict[str, Any]:
        """
        获取通用URL内容
        
        Args:
            url: URL地址
            
        Returns:
            Dict[str, Any]: 获取结果
        """
        # 首先尝试使用 aiohttp
        logger.debug(f"尝试使用 aiohttp 获取通用内容: {url}")
        result = await self._aiohttp_fetcher.fetch([url])
        if result and result[0]['success']:
            self._log_content_preview(result[0]['content'], "aiohttp", url)
            return result[0]
        
        # 如果 aiohttp 失败，尝试使用 Playwright
        logger.debug(f"尝试使用 Playwright 获取通用内容: {url}")
        result = await self._playwright_fetcher.fetch([url])
        if result and result[0]['success']:
            self._log_content_preview(result[0]['content'], "Playwright", url)
            return result[0]
        
        # 如果都失败，返回错误
        logger.error(f"获取通用内容失败: {url}")
        return {
            'success': False,
            'url': url,
            'error': '获取内容失败',
            'content': '',
            'type': 'error'
        }