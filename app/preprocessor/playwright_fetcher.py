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
import re

class PlaywrightFetcher:
    """使用 Playwright 的内容获取器"""
    
    def __init__(
        self,
        proxy_url: Optional[str] = None,
        timeout: int = 30,
        max_content_length: int = 8000,
        user_agent: Optional[str] = None
    ):
        """
        初始化 Playwright 内容获取器
        
        Args:
            proxy_url: 代理服务器URL (可选)
            timeout: 请求超时时间(秒)
            max_content_length: 提取内容的最大长度
            user_agent: 自定义User-Agent
        """
        self.proxy_url = proxy_url
        self.timeout = timeout
        self.max_content_length = max_content_length
        
        # 默认User-Agent
        self.user_agent = user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        
        # Playwright实例
        self._playwright = None
        self._browser = None
        
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
        
        contents = []
        try:
            # 创建共享浏览器上下文
            logger.info("创建共享浏览器上下文")
            context = await self._browser.new_context(
                proxy={
                    "server": self.proxy_url,
                    "username": None,
                    "password": None
                } if self.proxy_url else None,
                viewport={'width': 1920, 'height': 1080}
            )
            
            async def process_url(url: str) -> Dict[str, Any]:
                page = None
                try:
                    # 验证URL是否有效
                    if not url or not url.strip():
                        raise ValueError("URL 为空或无效")
                    
                    # 创建新页面
                    logger.info(f"为 {url} 创建新页面")
                    page = await context.new_page()
                    
                    if not page:
                        raise RuntimeError("页面创建失败")
                    
                    # 设置超时（同步方法，无需 await）
                    page.set_default_timeout(self.timeout * 1000)
                    
                    # 导航到URL
                    logger.info(f"开始导航到: {url}")
                    response = await page.goto(
                        url,
                        timeout=self.timeout * 1000,
                        wait_until="networkidle"
                    )
                    
                    if not response:
                        raise RuntimeError("页面导航失败")
                        
                    logger.info(f"页面加载状态: {response.status}")
                    
                    # 等待页面完全加载
                    await page.wait_for_load_state("domcontentloaded")
                    await page.wait_for_load_state("networkidle")
                    
                    # 获取页面内容
                    content = await page.content()
                    if not content:
                        raise RuntimeError("页面内容为空")
                        
                    # 解析HTML
                    soup = BeautifulSoup(content, "html.parser")
                    
                    # 提取标题
                    title = soup.title.text.strip() if soup.title else url
                    logger.info(f"提取到页面标题: {title}")
                    
                    # 提取正文
                    text_content = self._extract_main_content(soup)
                    logger.info(f"提取到正文内容，长度: {len(text_content)} 字符")
                    
                    return {
                        "url": url,
                        "success": True,
                        "content": text_content,
                        "title": title,
                        "type": "html"
                    }
                    
                except ValueError as ve:
                    logger.error(f"无效的URL: {url} - {str(ve)}")
                    return {
                        "url": url,
                        "success": False,
                        "error": "无效的URL",
                        "content": "",
                        "title": "",
                        "type": "error"
                    }
                except TimeoutError:
                    logger.error(f"访问URL超时: {url}")
                    return {
                        "url": url,
                        "success": False,
                        "error": "请求超时",
                        "content": "",
                        "title": "",
                        "type": "error"
                    }
                except Exception as e:
                    logger.error(f"处理URL失败: {url} - {str(e)}")
                    return {
                        "url": url,
                        "success": False,
                        "error": f"获取失败: {str(e)}",
                        "content": "",
                        "title": "",
                        "type": "error"
                    }
                finally:
                    # 确保正确关闭页面
                    if page:
                        try:
                            await page.close()
                            logger.info("页面已关闭")
                        except Exception as e:
                            logger.error(f"关闭页面时出错: {str(e)}")
            
            # 并发处理所有URL
            tasks = [process_url(url) for url in urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 处理结果
            for i, result in enumerate(results):
                if isinstance(result, Exception):
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
            
        except Exception as e:
            logger.error(f"处理过程中发生错误: {str(e)}")
        finally:
            # 关闭共享上下文
            if context:
                try:
                    await context.close()
                    logger.info("共享浏览器上下文已关闭")
                except Exception as e:
                    logger.error(f"关闭浏览器上下文时出错: {str(e)}")
        
        return contents
    
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
                logger.info("正在启动 Playwright...")
                self._playwright = await async_playwright().start()
                if not self._playwright:
                    raise RuntimeError("Playwright 启动失败")
                logger.info("Playwright 已启动")
                
            if not self._browser:
                logger.info("正在启动浏览器...")
                browser_options = {
                    "headless": True,
                    "slow_mo": 100,  # 添加延迟，使操作更慢
                    "args": [
                        "--start-maximized",  # 最大化窗口
                        "--disable-gpu",  # 禁用 GPU 加速
                        "--no-sandbox",  # 禁用沙箱
                        "--disable-dev-shm-usage"  # 禁用共享内存
                    ]
                }
                if self.proxy_url:
                    browser_options["proxy"] = {"server": self.proxy_url}
                    logger.info(f"使用代理: {self.proxy_url}")
                    
                self._browser = await self._playwright.chromium.launch(**browser_options)
                if not self._browser:
                    raise RuntimeError("无法启动浏览器")
                logger.info("浏览器已启动")
                
        except Exception as e:
            logger.error(f"初始化 Playwright 失败: {str(e)}")
            # 清理资源
            try:
                if self._browser:
                    await self._browser.close()
                if self._playwright:
                    await self._playwright.stop()
            except Exception as cleanup_error:
                logger.error(f"清理资源失败: {str(cleanup_error)}")
            self._browser = None
            self._playwright = None
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