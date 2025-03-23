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

from loguru import logger
from bs4 import BeautifulSoup


class ContentFetcher:
    """
    网页内容获取模块
    负责从URL获取网页内容，提取正文，处理不同类型的网页
    
    职责:
    1. 访问和下载网页内容
    2. 提取网页正文
    3. 清理和格式化内容
    4. 处理各种网页类型和格式
    """
    
    def __init__(
        self,
        proxy_url: Optional[str] = None,
        timeout: int = 30,
        max_content_length: int = 8000,
        user_agent: Optional[str] = None,
        max_retries: int = 2
    ):
        """
        初始化网页内容获取模块
        
        Args:
            proxy_url: 代理服务器URL (可选)
            timeout: 请求超时时间(秒)
            max_content_length: 提取内容的最大长度
            user_agent: 自定义User-Agent
            max_retries: 最大重试次数
        """
        self.proxy_url = proxy_url
        self.timeout = timeout
        self.max_content_length = max_content_length
        self.max_retries = max_retries
        
        # 默认User-Agent
        self.user_agent = user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        
        # HTTP会话
        self._session = None
        
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
            
        # 确保会话已初始化
        await self._ensure_session()
        
        # 并行获取内容
        tasks = [self._fetch_single_url(url) for url in urls]
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
    
    async def _fetch_single_url(self, url: str) -> Dict[str, Any]:
        """
        获取单个URL的内容
        
        Args:
            url: URL
            
        Returns:
            内容字典
        """
        # 解析域名
        domain = urlparse(url).netloc
        
        # 尝试站点特定处理
        if any(site in domain for site in self.site_handlers):
            for site, handler in self.site_handlers.items():
                if site in domain:
                    return await handler(url)
        
        # 通用处理
        return await self._fetch_generic(url)
    
    async def _fetch_generic(self, url: str) -> Dict[str, Any]:
        """
        通用网页内容获取处理
        
        Args:
            url: URL
            
        Returns:
            内容字典
        """
        retries = 0
        while retries <= self.max_retries:
            try:
                async with self._session.get(
                    url,
                    proxy=self.proxy_url,
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                    headers={"User-Agent": self.user_agent}
                ) as response:
                    if response.status != 200:
                        raise Exception(f"HTTP错误: {response.status}")
                    
                    # 检查内容类型
                    content_type = response.headers.get("Content-Type", "")
                    if "text/html" not in content_type and "application/xhtml+xml" not in content_type:
                        return {
                            "url": url,
                            "success": True,
                            "content": f"[非HTML内容: {content_type}]",
                            "title": url,
                            "type": "non_html"
                        }
                    
                    # 获取HTML内容
                    html = await response.text()
                    
                    # 解析HTML
                    soup = BeautifulSoup(html, "html.parser")
                    
                    # 提取标题
                    title = soup.title.text.strip() if soup.title else url
                    
                    # 提取正文
                    content = self._extract_main_content(soup)
                    
                    # 裁剪内容长度
                    if len(content) > self.max_content_length:
                        content = content[:self.max_content_length] + "..."
                    
                    return {
                        "url": url,
                        "success": True,
                        "content": content,
                        "title": title,
                        "type": "html"
                    }
                    
            except Exception as e:
                retries += 1
                if retries > self.max_retries:
                    return {
                        "url": url,
                        "success": False,
                        "error": f"获取失败: {str(e)}",
                        "content": "",
                        "title": url,
                        "type": "error"
                    }
                # 重试前等待
                await asyncio.sleep(1)
    
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
        
        return text
    
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
    
    async def _ensure_session(self):
        """确保HTTP会话已初始化"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
    
    async def close(self):
        """关闭HTTP会话"""
        if self._session and not self._session.closed:
            await self._session.close() 