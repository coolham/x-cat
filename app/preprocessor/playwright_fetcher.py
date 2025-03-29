"""
使用 Playwright 的内容获取器
负责从需要 JavaScript 渲染的网站获取内容
"""
import asyncio
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup
from loguru import logger
from urllib.parse import urlparse
from playwright.async_api import async_playwright, TimeoutError
from app.cache.cache_manager import CacheManager
import re

class PlaywrightFetcher:
    """使用 Playwright 的内容获取器"""
    
    def __init__(
        self,
        proxy_url: Optional[str] = None,
        timeout: int = 30,
        max_content_length: int = 8000,
        user_agent: Optional[str] = None,
        cache_dir: str = "cache"
    ):
        """
        初始化 Playwright 内容获取器
        
        Args:
            proxy_url: 代理服务器URL (可选)
            timeout: 请求超时时间(秒)
            max_content_length: 提取内容的最大长度
            user_agent: 自定义User-Agent
            cache_dir: 缓存目录路径
        """
        self.proxy_url = proxy_url
        self.timeout = timeout
        self.max_content_length = max_content_length
        
        # 默认User-Agent
        self.user_agent = user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        
        # Playwright实例
        self._playwright = None
        self._browser = None
        
        # 缓存管理器
        self.cache_manager = CacheManager(cache_dir)
        
        # 站点特定处理器
        self.site_handlers = {
            "twitter.com": self._extract_twitter,
            "x.com": self._extract_twitter,
            "medium.com": self._extract_medium,
            "github.com": self._extract_github
        }
    
    async def fetch(self, urls: List[str]) -> List[Dict[str, Any]]:
        """
        获取多个URL的内容
        
        Args:
            urls: URL列表
            
        Returns:
            内容列表，每个元素是一个字典
        """
        if not urls:
            return []
            
        # 确保 Playwright 已初始化
        await self._ensure_playwright()
        
        # 并行获取内容
        tasks = [self._fetch_single(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        contents = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # 处理异常
                logger.error(f"获取URL内容失败: {urls[i]} - {str(result)}")
                contents.append({
                    "url": urls[i],
                    "success": False,
                    "error": f"获取失败: {str(result)}",
                    "content": "",
                    "title": "",
                    "type": "error"
                })
            else:
                contents.append(result)
        
        return contents
    
    async def _fetch_single(self, url: str) -> Dict[str, Any]:
        """
        获取单个URL的内容
        
        Args:
            url: URL
            
        Returns:
            内容字典
        """
        # 检查缓存
        cached_data = self.cache_manager.load(url)
        if cached_data:
            logger.info(f"使用缓存数据: {url}")
            return cached_data
        
        context = None
        page = None
        
        try:
            # 确保浏览器已初始化
            if not self._browser:
                await self._ensure_playwright()
            
            # 创建上下文
            context = await self._browser.new_context(
                proxy={
                    "server": self.proxy_url,
                    "username": None,
                    "password": None
                } if self.proxy_url else None,
                viewport={'width': 1920, 'height': 1080}
            )
            
            # 创建页面
            page = await context.new_page()
            
            # 访问URL
            try:
                # 设置页面超时
                await page.set_default_timeout(self.timeout * 1000)
                await page.goto(url, timeout=self.timeout * 1000)
            except TimeoutError:
                result = {
                    "url": url,
                    "success": False,
                    "error": "请求超时",
                    "content": "",
                    "title": "",
                    "type": "error"
                }
                self.cache_manager.save(url, result)
                return result
            
            # 等待内容加载
            try:
                await page.wait_for_load_state('networkidle', timeout=self.timeout * 1000)
            except TimeoutError:
                result = {
                    "url": url,
                    "success": False,
                    "error": "等待页面加载超时",
                    "content": "",
                    "title": "",
                    "type": "error"
                }
                self.cache_manager.save(url, result)
                return result
            
            # 获取页面内容
            content = await page.content()
            
            # 检查是否需要JavaScript
            if "JavaScript is required to view this content" in content:
                result = {
                    "url": url,
                    "success": False,
                    "error": "JavaScript is required to view this content",
                    "content": "",
                    "title": "",
                    "type": "error"
                }
                self.cache_manager.save(url, result)
                return result
            
            # 解析HTML
            soup = BeautifulSoup(content, "html.parser")
            
            # 提取标题
            title = soup.title.text.strip() if soup.title else url
            
            # 提取正文
            content = self._extract_main_content(soup)
            
            result = {
                "url": url,
                "success": True,
                "content": content,
                "title": title,
                "type": "html"
            }
            
            # 保存到缓存
            self.cache_manager.save(url, result)
            return result
            
        except Exception as e:
            logger.error(f"Playwright获取内容失败: {url} - {str(e)}")
            result = {
                "url": url,
                "success": False,
                "error": f"获取失败: {str(e)}",
                "content": "",
                "title": "",
                "type": "error"
            }
            self.cache_manager.save(url, result)
            return result
        finally:
            # 清理资源
            try:
                if page:
                    await page.close()
                if context:
                    await context.close()
            except Exception as e:
                logger.error(f"清理资源失败: {str(e)}")
    
    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """
        提取HTML主要内容
        
        Args:
            soup: BeautifulSoup对象
            
        Returns:
            提取的主要内容
        """
        # 移除脚本、样式等元素
        for script in soup(["script", "style", "header", "footer", "nav", "aside"]):
            script.decompose()
        
        # 尝试查找主内容
        main_content = None
        
        # 尝试找到主要内容容器
        for container in [
            soup.find("main"),
            soup.find("article"),
            soup.find(id=re.compile("^(content|main|article)")),
            soup.find(class_=re.compile("^(content|main|article)"))
        ]:
            if container:
                main_content = container
                break
        
        # 如果找不到主内容容器，使用body
        if not main_content:
            main_content = soup.body if soup.body else soup
        
        # 获取文本
        text = main_content.get_text(separator="\n")
        
        # 清理文本
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        text = "\n".join(lines)
        
        # 确保内容长度不超过限制
        if len(text) > self.max_content_length:
            text = text[:self.max_content_length - 3] + "..."
        
        return text
    
    async def _extract_twitter(self, url: str) -> Dict[str, Any]:
        """
        提取Twitter/X内容
        
        Args:
            url: Twitter/X URL
            
        Returns:
            内容字典
        """
        return await self._fetch_single(url)
    
    async def _extract_medium(self, url: str) -> Dict[str, Any]:
        """
        提取Medium内容
        
        Args:
            url: Medium URL
            
        Returns:
            内容字典
        """
        return await self._fetch_single(url)
    
    async def _extract_github(self, url: str) -> Dict[str, Any]:
        """
        提取GitHub内容
        
        Args:
            url: GitHub URL
            
        Returns:
            内容字典
        """
        return await self._fetch_single(url)
    
    async def _ensure_playwright(self):
        """确保 Playwright 已初始化"""
        try:
            if not self._playwright:
                self._playwright = await async_playwright().start()
                logger.info("Playwright 已启动")
            if not self._browser:
                self._browser = await self._playwright.chromium.launch(
                    headless=True,
                    proxy={"server": self.proxy_url} if self.proxy_url else None
                )
                logger.info("浏览器已启动")
        except Exception as e:
            logger.error(f"初始化 Playwright 失败: {str(e)}")
            raise RuntimeError("Playwright 初始化失败") from e
    
    async def close(self):
        """关闭 Playwright"""
        try:
            if self._browser:
                await self._browser.close()
            if self._playwright:
                await self._playwright.stop()
        except Exception as e:
            logger.error(f"关闭 Playwright 失败: {str(e)}")
        finally:
            self._browser = None
            self._playwright = None