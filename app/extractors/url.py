"""
URL内容提取器
负责从URL中提取内容
"""
import re
from typing import Dict, Any, List, Optional
from loguru import logger
import aiohttp
from bs4 import BeautifulSoup
from datetime import datetime
import traceback

from app.extractors.base import BaseExtractor

class URLExtractor(BaseExtractor):
    """URL内容提取器"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化URL提取器
        
        Args:
            config: 配置字典
        """
        super().__init__()
        self.config = config
        
        # 设置URL模式
        self.url_patterns = [
            r'https?://[^\s<>"]+|www\.[^\s<>"]+',  # 基本URL模式
            r'https?://t\.me/[^\s<>"]+',  # Telegram链接
            r'https?://twitter\.com/[^\s<>"]+',  # Twitter链接
            r'https?://weibo\.com/[^\s<>"]+',  # 微博链接
        ]
        
        # 设置允许的协议
        self.allowed_schemes = ['http', 'https']
        
        logger.info("URL提取器初始化成功")
        
    def get_source_type(self) -> str:
        """获取数据源类型
        
        Returns:
            str: 数据源类型
        """
        return 'url'
        
    def validate(self, data: Dict[str, Any]) -> bool:
        """验证输入数据
        
        Args:
            data: 输入数据
            
        Returns:
            bool: 是否验证通过
        """
        try:
            # 检查URL是否存在
            if 'url' not in data:
                logger.error("缺少URL字段")
                return False
                
            url = data['url']
            
            # 检查URL类型
            if not isinstance(url, str):
                logger.error("URL必须是字符串类型")
                return False
                
            # 检查URL格式
            if not any(re.match(pattern, url) for pattern in self.url_patterns):
                logger.error(f"URL格式无效: {url}")
                return False
                
            # 检查URL协议
            parsed = urlparse(url)
            if parsed.scheme not in self.allowed_schemes:
                logger.error(f"不支持的URL协议: {parsed.scheme}")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"URL验证失败: {str(e)}")
            logger.debug(traceback.format_exc())
            return False
            
    async def extract(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """提取URL内容
        
        Args:
            data: 输入数据
            
        Returns:
            Dict[str, Any]: 提取结果
        """
        try:
            # 验证输入
            if not self.validate(data):
                return {
                    'success': False,
                    'error': 'URL验证失败',
                    'data': data
                }
                
            url = data['url']
            
            # 获取URL内容
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        raise ValueError(f"获取URL内容失败: {response.status}")
                        
                    content = await response.text()
                    
            # 生成元数据
            metadata = {
                'url': url,
                'title': self._extract_title(content),
                'description': self._extract_description(content),
                'timestamp': datetime.now().isoformat(),
                'source_type': 'url'
            }
            
            return {
                'success': True,
                'content': content,
                'metadata': metadata
            }
            
        except Exception as e:
            logger.error(f"URL内容提取失败: {str(e)}")
            logger.debug(traceback.format_exc())
            return {
                'success': False,
                'error': str(e),
                'data': data
            }
            
    def _extract_title(self, content: str) -> str:
        """提取页面标题
        
        Args:
            content: 页面内容
            
        Returns:
            str: 页面标题
        """
        try:
            soup = BeautifulSoup(content, 'html.parser')
            title = soup.title.string if soup.title else ''
            return title.strip()
        except Exception as e:
            logger.warning(f"提取标题失败: {str(e)}")
            return ''
            
    def _extract_description(self, content: str) -> str:
        """提取页面描述
        
        Args:
            content: 页面内容
            
        Returns:
            str: 页面描述
        """
        try:
            soup = BeautifulSoup(content, 'html.parser')
            meta = soup.find('meta', attrs={'name': 'description'})
            description = meta['content'] if meta else ''
            return description.strip()
        except Exception as e:
            logger.warning(f"提取描述失败: {str(e)}")
            return ''
            
    def set_url_pattern(self, pattern: str):
        """设置URL匹配模式
        
        Args:
            pattern: 正则表达式模式
        """
        try:
            self.url_patterns = [pattern]
        except Exception as e:
            logger.error(f"设置URL模式失败: {str(e)}")
            
    def set_allowed_schemes(self, schemes: List[str]):
        """设置允许的URL协议
        
        Args:
            schemes: 协议列表
        """
        self.allowed_schemes = set(scheme.lower() for scheme in schemes)

    def extract_urls(self, text: str) -> List[str]:
        """从文本中提取URL
        
        Args:
            text: 输入文本
            
        Returns:
            List[str]: URL列表
        """
        try:
            # URL匹配模式
            url_pattern = r'https?://(?:www\.)?[^\s<>"]+|www\.[^\s<>"]+'
            
            # 查找所有URL
            urls = re.findall(url_pattern, text)
            
            # 清理URL
            cleaned_urls = []
            for url in urls:
                # 移除URL末尾的标点符号
                url = url.rstrip('.,;:!?')
                # 确保URL以http或https开头
                if not url.startswith(('http://', 'https://')):
                    url = 'https://' + url
                cleaned_urls.append(url)
                
            return cleaned_urls
            
        except Exception as e:
            logger.error(f"URL提取失败: {str(e)}")
            return [] 