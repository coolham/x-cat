"""
网页内容获取模块
负责访问和下载网页内容，提取网页正文，清理和格式化内容
"""
import re
import asyncio
import aiohttp
from typing import Dict, Any, List, Tuple, Optional
import traceback
import time
from urllib.parse import urlparse
import os
import logging

from loguru import logger
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, Browser, Page, TimeoutError as PlaywrightTimeoutError


class ContentFetcher:
    """内容获取器"""
    
    def __init__(self, timeout: int = 5, max_content_length: int = 1000, use_cache: bool = False):
        """初始化内容获取器
        
        Args:
            timeout: 超时时间(秒)
            max_content_length: 最大内容长度
            use_cache: 是否使用缓存
        """
        self.logger = logging.getLogger(__name__)
        self.timeout = timeout
        self.max_content_length = max_content_length
        self.use_cache = use_cache
        
        # 初始化 aiohttp 获取器
        self.aiohttp_fetcher = AioHttpFetcher(timeout=timeout, max_content_length=max_content_length)
        
        # 初始化 Playwright 获取器
        self.playwright_fetcher = PlaywrightFetcher(timeout=timeout, max_content_length=max_content_length)
        
        # 初始化缓存管理器
        self.cache_manager = CacheManager()
        
        self.logger.info(f"初始化内容获取器: timeout={timeout}s, max_content_length={max_content_length}")
        if not use_cache:
            self.logger.info("缓存已禁用")
    
    async def _ensure_browser(self):
        """确保浏览器已启动"""
        if not hasattr(self, '_browser'):
            self._browser = await self.playwright_fetcher._ensure_playwright()
    
    async def _fetch_single_url(self, url: str) -> Dict[str, Any]:
        """获取单个URL的内容
        
        Args:
            url: URL地址
            
        Returns:
            Dict[str, Any]: 获取结果
        """
        # 检查缓存
        if self.use_cache:
            cached_content = await self.cache_manager.get(url)
            if cached_content:
                self.logger.info(f"使用缓存数据: {url}")
                return {
                    'success': True,
                    'content': cached_content,
                    'url': url
                }
        
        # 尝试使用 aiohttp 获取
        self.logger.debug(f"尝试使用 aiohttp 获取: {url}")
        try:
            content = await self.aiohttp_fetcher.fetch(url)
            if content:
                self.logger.info(f"使用 aiohttp 获取内容成功: {url}")
                if self.use_cache:
                    await self.cache_manager.set(url, content)
                return {
                    'success': True,
                    'content': content,
                    'url': url
                }
        except Exception as e:
            self.logger.warning(f"aiohttp 获取失败: {url} - {str(e)}")
        
        # 尝试使用 Playwright 获取
        self.logger.debug(f"尝试使用 Playwright 获取: {url}")
        try:
            await self._ensure_browser()
            content = await self.playwright_fetcher.fetch(url)
            if content:
                self.logger.info(f"使用 Playwright 获取内容成功: {url}")
                if self.use_cache:
                    await self.cache_manager.set(url, content)
                return {
                    'success': True,
                    'content': content,
                    'url': url
                }
        except Exception as e:
            self.logger.warning(f"Playwright 获取失败: {url} - {str(e)}")
        
        # 所有获取方式都失败
        self.logger.error(f"所有获取方式都失败: {url}")
        return {
            'success': False,
            'error': str(e),
            'url': url
        }
    
    async def fetch(self, urls: List[str]) -> List[Dict[str, Any]]:
        """获取多个URL的内容
        
        Args:
            urls: URL地址列表
            
        Returns:
            List[Dict[str, Any]]: 获取结果列表
        """
        self.logger.info(f"开始获取 {len(urls)} 个URL的内容，获取方式: {'aiohttp/Playwright'}")
        
        # 并发获取所有URL的内容
        tasks = [self._fetch_single_url(url) for url in urls]
        results = await asyncio.gather(*tasks)
        
        # 统计结果
        success_count = sum(1 for r in results if r['success'])
        self.logger.info(f"内容获取完成: 总数={len(urls)}, 成功={success_count}, 失败={len(urls)-success_count}")
        
        return results
    
    async def close(self):
        """关闭所有资源"""
        self.logger.info("开始关闭所有内容获取器")
        
        # 关闭 aiohttp 获取器
        await self.aiohttp_fetcher.close()
        
        # 关闭 Playwright 获取器
        await self.playwright_fetcher.close()
        
        # 关闭缓存管理器
        await self.cache_manager.close()
        
        self.logger.info("所有内容获取器已关闭")
    
    def _log_content_preview(self, content: str, url: str):
        """记录内容预览
        
        Args:
            content: 内容
            url: URL地址
        """
        preview = content[:100] + "..." if len(content) > 100 else content
        self.logger.debug(f"内容预览: {preview}")

    async def _extract_twitter(self, url: str) -> Dict[str, Any]:
        """
        使用Playwright提取Twitter/X内容
        
        Args:
            url: Twitter/X URL
            
        Returns:
            内容字典
        """
        page = None
        try:
            # 确保浏览器已初始化
            await self._ensure_browser()
            
            # 创建新页面
            page = await self._browser.new_page()
            
            # 设置超时
            page.set_default_timeout(self.timeout * 1000)
            
            try:
                # 访问URL
                await page.goto(url, wait_until="networkidle")
                
                # 等待推文内容加载
                await page.wait_for_selector('article[data-testid="tweet"]', timeout=10000)
                
                # 提取推文内容
                tweet = await page.query_selector('article[data-testid="tweet"]')
                if not tweet:
                    return {
                        "url": url,
                        "success": False,
                        "error": "未找到推文内容",
                        "content": "",
                        "title": url,
                        "type": "error"
                    }
                
                # 提取文本内容
                content = await tweet.evaluate('(el) => el.innerText')
                
                # 提取作者信息
                author = await page.query_selector('div[data-testid="User-Name"]')
                author_name = await author.evaluate('(el) => el.innerText') if author else "未知作者"
                
                # 提取时间戳
                time_element = await page.query_selector('time')
                timestamp = await time_element.get_attribute('datetime') if time_element else None
                
                # 裁剪内容长度
                if len(content) > self.max_content_length:
                    content = content[:self.max_content_length] + "..."
                
                return {
                    "url": url,
                    "success": True,
                    "content": content,
                    "title": f"推文 - {author_name}",
                    "type": "twitter",
                    "metadata": {
                        "author": author_name,
                        "timestamp": timestamp
                    }
                }
                
            except PlaywrightTimeoutError:
                return {
                    "url": url,
                    "success": False,
                    "error": "Navigation timeout",
                    "content": "",
                    "title": url,
                    "type": "error"
                }
            except Exception as e:
                error_msg = str(e)
                if "net::" in error_msg:
                    error_msg = error_msg.split("net::")[1]
                elif "JavaScript" in error_msg:
                    error_msg = "请开启JavaScript以访问内容"
                
                return {
                    "url": url,
                    "success": False,
                    "error": error_msg,
                    "content": "",
                    "title": url,
                    "type": "error"
                }
                
        finally:
            if page:
                try:
                    await page.close()
                except Exception as e:
                    logger.error(f"关闭页面失败: {str(e)}")
    
    async def _extract_medium(self, url: str) -> Dict[str, Any]:
        """
        提取Medium内容
        
        Args:
            url: Medium URL
            
        Returns:
            内容字典
        """
        # 调用通用处理，后续可以添加Medium特定处理逻辑
        result = await self._fetch_single_url(url)
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
        result = await self._fetch_single_url(url)
        result["type"] = "github"
        return result
    
    async def _ensure_session(self):
        """确保HTTP会话已初始化"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
    
    async def close(self):
        """关闭所有连接"""
        logger.info("开始关闭所有内容获取器")
        
        try:
            if self._session and not self._session.closed:
                await self._session.close()
                self._session = None
            
            if self._browser:
                try:
                    await self._browser.close()
                except Exception as e:
                    logger.error(f"关闭浏览器失败: {str(e)}")
                finally:
                    self._browser = None
            
            logger.info("所有内容获取器已关闭")
            
        except Exception as e:
            logger.error(f"关闭资源时发生错误: {str(e)}")
            # 不抛出异常，确保所有资源都尝试关闭 