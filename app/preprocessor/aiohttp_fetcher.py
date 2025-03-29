"""
Aiohttp内容获取器
用于获取标准网页内容
"""
from typing import Dict, Any, List, Optional
from loguru import logger
import aiohttp
import asyncio
from bs4 import BeautifulSoup
import re

class AiohttpFetcher:
    """
    使用aiohttp获取网页内容
    """
    
    def __init__(
        self,
        proxy_url: Optional[str] = None,
        timeout: int = 30,
        max_content_length: int = 8000,
        user_agent: Optional[str] = None,
        max_retries: int = 3
    ):
        """
        初始化aiohttp获取器
        
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
        self.user_agent = user_agent or 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        self.max_retries = max_retries
        self._session = None
        
        logger.info(f"初始化 aiohttp 获取器: timeout={timeout}s, max_content_length={max_content_length}")
        if proxy_url:
            logger.info(f"使用代理: {proxy_url}")
    
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
            
        # 确保session已初始化
        await self._ensure_session()
        
        # 并发获取内容
        tasks = [self._fetch_single(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理结果
        processed_results = []
        for url, result in zip(urls, results):
            if isinstance(result, Exception):
                processed_results.append({
                    'success': False,
                    'url': url,
                    'error': str(result)
                })
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def _fetch_single(self, url: str) -> Dict[str, Any]:
        """
        获取单个URL的内容
        
        Args:
            url: URL地址
            
        Returns:
            内容字典
        """
        for attempt in range(self.max_retries):
            try:
                # 设置代理
                proxy = None
                if self.proxy_url:
                    proxy = self.proxy_url
                    logger.debug(f"使用代理 {proxy} 获取: {url}")
                
                async with self._session.get(url, proxy=proxy, timeout=self.timeout) as response:
                    if response.status != 200:
                        return {
                            'success': False,
                            'url': url,
                            'error': f'HTTP {response.status}'
                        }
                    
                    # 检查内容类型
                    content_type = response.headers.get('content-type', '').lower()
                    if 'text/html' not in content_type:
                        return {
                            'success': False,
                            'url': url,
                            'error': f'不支持的内容类型: {content_type}'
                        }
                    
                    # 获取内容
                    html = await response.text()
                    
                    # 提取主要内容
                    content = self._extract_main_content(html)
                    
                    return {
                        'success': True,
                        'url': url,
                        'content': content[:self.max_content_length],
                        'source': 'aiohttp'
                    }
                    
            except asyncio.TimeoutError:
                if attempt == self.max_retries - 1:
                    return {
                        'success': False,
                        'url': url,
                        'error': '请求超时'
                    }
            except Exception as e:
                if attempt == self.max_retries - 1:
                    return {
                        'success': False,
                        'url': url,
                        'error': str(e)
                    }
            
            # 重试前等待
            await asyncio.sleep(1)
    
    def _extract_main_content(self, html: str) -> str:
        """
        从HTML中提取主要内容
        
        Args:
            html: HTML内容
            
        Returns:
            提取的文本内容
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        # 移除脚本和样式元素
        for script in soup(['script', 'style']):
            script.decompose()
        
        # 获取文本
        text = soup.get_text()
        
        # 清理文本
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text
    
    async def _ensure_session(self):
        """确保aiohttp session已初始化"""
        if self._session is None:
            connector = aiohttp.TCPConnector(ssl=False)
            self._session = aiohttp.ClientSession(
                connector=connector,
                headers={'User-Agent': self.user_agent}
            )
            logger.debug("已初始化 aiohttp session")
    
    async def close(self):
        """关闭aiohttp session"""
        if self._session:
            await self._session.close()
            self._session = None
            logger.debug("已关闭 aiohttp session") 