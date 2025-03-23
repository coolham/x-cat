"""
内容提取器模块
负责从URL中提取网页内容
"""
import re
import asyncio
from typing import Dict, Any, List, Optional, Tuple, Union
import traceback

import httpx
from loguru import logger
from bs4 import BeautifulSoup

class ContentExtractor:
    """
    内容提取器
    负责从URL中提取网页内容、清理和格式化
    
    属性:
        proxy_url: 代理服务器URL
        timeout: 请求超时时间
        user_agent: 请求头User-Agent
        max_content_length: 最大内容长度
    """
    
    def __init__(
        self, 
        proxy_url: Optional[str] = None,
        timeout: float = 30.0,
        user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        max_content_length: int = 100000
    ):
        """
        初始化内容提取器
        
        Args:
            proxy_url: 代理服务器URL (可选)
            timeout: 请求超时时间，默认30秒
            user_agent: 请求头User-Agent
            max_content_length: 最大内容长度，防止提取过大内容
        """
        self.proxy_url = proxy_url
        self.timeout = timeout
        self.user_agent = user_agent
        self.max_content_length = max_content_length
        
        # 创建HTTP客户端
        proxies = {"http://": proxy_url, "https://": proxy_url} if proxy_url else None
        self.client = httpx.AsyncClient(
            proxies=proxies, 
            timeout=timeout,
            follow_redirects=True
        )
        
        logger.debug(f"内容提取器初始化成功: proxy={proxy_url is not None}")
    
    async def extract_from_url(self, url: str) -> Tuple[bool, Dict[str, Any]]:
        """
        从URL提取内容
        
        Args:
            url: 目标URL
            
        Returns:
            (成功标志, 提取结果或错误信息)
            提取结果包含：
            - title: 网页标题
            - content: 正文内容
            - url: 最终URL（考虑重定向）
            - metadata: 元数据字典
        """
        try:
            # 准备请求头
            headers = {
                "User-Agent": self.user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"
            }
            
            # 发送请求
            logger.debug(f"正在请求URL: {url}")
            response = await self.client.get(url, headers=headers)
            
            # 检查状态码
            if response.status_code != 200:
                error_msg = f"请求失败: HTTP {response.status_code}"
                logger.error(error_msg)
                return False, {"error": error_msg, "url": url}
            
            # 限制内容长度
            content = response.text[:self.max_content_length]
            
            # 解析HTML
            result = self._parse_html(content, response.url)
            result["url"] = str(response.url)  # 使用最终URL（考虑重定向）
            
            return True, result
            
        except httpx.TimeoutException:
            error_msg = f"请求超时: {url}"
            logger.error(error_msg)
            return False, {"error": error_msg, "url": url}
            
        except httpx.RequestError as e:
            error_msg = f"请求错误: {str(e)}"
            logger.error(error_msg)
            return False, {"error": error_msg, "url": url}
            
        except Exception as e:
            error_msg = f"提取内容时出错: {str(e)}"
            logger.error(error_msg)
            logger.debug(traceback.format_exc())
            return False, {"error": error_msg, "url": url}
    
    def _parse_html(self, html_content: str, url: str) -> Dict[str, Any]:
        """
        解析HTML内容
        
        Args:
            html_content: HTML内容
            url: 页面URL
            
        Returns:
            解析结果字典
        """
        result = {
            "title": "",
            "content": "",
            "url": str(url),
            "metadata": {}
        }
        
        try:
            # 使用BeautifulSoup解析
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 提取标题
            if soup.title:
                result["title"] = soup.title.string.strip() if soup.title.string else ""
            
            # 提取元数据
            meta_tags = {
                "description": "",
                "keywords": "",
                "author": "",
                "og:title": "",
                "og:description": "",
                "og:image": "",
                "twitter:title": "",
                "twitter:description": "",
                "twitter:image": ""
            }
            
            for meta in soup.find_all("meta"):
                name = meta.get("name", "").lower()
                property = meta.get("property", "").lower()
                content = meta.get("content", "")
                
                if name in meta_tags:
                    meta_tags[name] = content
                elif property in meta_tags:
                    meta_tags[property] = content
            
            result["metadata"] = meta_tags
            
            # 提取正文内容
            # 首先尝试找到主要内容区域
            main_content = None
            
            # 检查常见的内容容器
            for container in ["article", "main", ".post-content", ".article-content", "#content", ".content"]:
                if container.startswith(".") or container.startswith("#"):
                    elements = soup.select(container)
                else:
                    elements = soup.find_all(container)
                
                if elements:
                    main_content = elements[0]
                    break
            
            # 如果没有找到明确的内容容器，则使用body
            if not main_content:
                main_content = soup.body
            
            # 提取文本内容
            if main_content:
                # 移除脚本、样式等非内容元素
                for element in main_content.find_all(["script", "style", "iframe", "nav", "footer", "header"]):
                    element.decompose()
                
                # 获取所有段落
                paragraphs = main_content.find_all("p")
                if paragraphs:
                    content = "\n\n".join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
                    result["content"] = content
                else:
                    # 如果没有找到段落，则使用所有文本
                    result["content"] = main_content.get_text(" ", strip=True)
            
            # 简单的内容清理
            result["content"] = re.sub(r'\s+', ' ', result["content"]).strip()
            
            return result
            
        except Exception as e:
            logger.error(f"解析HTML时出错: {str(e)}")
            logger.debug(traceback.format_exc())
            result["content"] = "解析HTML时出错"
            return result
    
    def extract_urls_from_text(self, text: str) -> List[str]:
        """
        从文本中提取URL
        
        Args:
            text: 输入文本
            
        Returns:
            URL列表
        """
        # URL正则表达式模式
        url_pattern = r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+(?:/[^\s]*)?'
        
        # 查找所有匹配
        urls = re.findall(url_pattern, text)
        
        # 去重
        unique_urls = list(set(urls))
        
        return unique_urls
    
    async def close(self):
        """关闭HTTP客户端"""
        await self.client.aclose() 