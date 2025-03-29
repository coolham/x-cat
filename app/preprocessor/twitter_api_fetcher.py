"""
Twitter API 内容获取器
使用 Twitter API v2 获取推文内容
"""
from typing import Dict, Any, List, Optional
from loguru import logger
import re
import aiohttp
import os
from urllib.parse import urlparse
import json
import asyncio
from datetime import datetime, timedelta

class TwitterAPIFetcher:
    """
    使用 Twitter API v2 获取推文内容
    """
    
    # 类级别的速率限制缓存
    _rate_limit_cache = {}
    _rate_limit_lock = asyncio.Lock()
    
    def __init__(
        self,
        api_key: str,
        api_secret: str,
        access_token: str,
        access_token_secret: str,
        bearer_token: str,
        max_content_length: int = 8000,
        proxy_url: Optional[str] = None,
        max_retries: int = 3,
        retry_delay: int = 5
    ):
        """
        初始化 Twitter API 获取器
        
        Args:
            api_key: Twitter API Key
            api_secret: Twitter API Secret
            access_token: Twitter Access Token
            access_token_secret: Twitter Access Token Secret
            bearer_token: Twitter Bearer Token
            max_content_length: 提取内容的最大长度
            proxy_url: 代理服务器URL (可选)
            max_retries: 最大重试次数
            retry_delay: 重试延迟（秒）
        """
        self.max_content_length = max_content_length
        self.proxy_url = proxy_url
        self.bearer_token = bearer_token
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.last_request_time = None
        self.request_count = 0
        self.rate_limit_reset = None
        
        logger.info(f"初始化 Twitter API 获取器: max_content_length={max_content_length}")
        if proxy_url:
            logger.info(f"使用代理: {proxy_url}")
        
        # 创建 aiohttp 会话
        self.session = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """获取或创建 aiohttp 会话"""
        if self.session is None or self.session.closed:
            # 创建连接器
            connector = aiohttp.TCPConnector(ssl=False)  # 禁用SSL验证
            
            # 创建会话
            self.session = aiohttp.ClientSession(
                connector=connector,
                headers={
                    'Authorization': f'Bearer {self.bearer_token.strip()}',  # 确保移除可能的空白字符
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
            )
            logger.debug("已初始化 aiohttp session")
            logger.debug(f"使用 Bearer Token: {self.bearer_token[:10]}...")  # 只显示前10个字符
        
        return self.session
    
    async def _handle_rate_limit(self, response: aiohttp.ClientResponse) -> bool:
        """
        处理速率限制
        
        Args:
            response: API响应
            
        Returns:
            bool: 是否需要重试
        """
        if response.status == 429:  # Too Many Requests
            # 获取速率限制重置时间
            reset_time = response.headers.get('x-rate-limit-reset')
            if reset_time:
                try:
                    reset_timestamp = int(reset_time)
                    async with self._rate_limit_lock:
                        # 更新全局速率限制缓存
                        self._rate_limit_cache['reset_time'] = reset_timestamp
                        self._rate_limit_cache['last_update'] = datetime.now().timestamp()
                    
                    self.rate_limit_reset = datetime.fromtimestamp(reset_timestamp)
                    wait_time = (self.rate_limit_reset - datetime.now()).total_seconds()
                    
                    if wait_time > 0:
                        logger.warning(f"触发速率限制，等待 {wait_time:.2f} 秒后重试")
                        logger.info(f"速率限制将在 {self.rate_limit_reset.strftime('%Y-%m-%d %H:%M:%S')} 重置")
                        await asyncio.sleep(wait_time)
                        return True
                except (ValueError, TypeError) as e:
                    logger.error(f"解析速率限制重置时间失败: {str(e)}")
            
            # 如果没有重置时间，使用默认延迟
            logger.warning(f"触发速率限制，等待 {self.retry_delay} 秒后重试")
            await asyncio.sleep(self.retry_delay)
            return True
        
        return False
    
    async def _check_rate_limit(self) -> bool:
        """
        检查是否处于速率限制状态
        
        Returns:
            bool: 是否需要等待
        """
        async with self._rate_limit_lock:
            if 'reset_time' in self._rate_limit_cache:
                reset_time = datetime.fromtimestamp(self._rate_limit_cache['reset_time'])
                wait_time = (reset_time - datetime.now()).total_seconds()
                if wait_time > 0:
                    logger.info(f"当前处于速率限制状态，需要等待 {wait_time:.2f} 秒")
                    logger.info(f"速率限制将在 {reset_time.strftime('%Y-%m-%d %H:%M:%S')} 重置")
                    await asyncio.sleep(wait_time)
                    return True
        return False
    
    async def _make_request(self, url: str, params: Dict[str, Any], proxy: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        发送API请求
        
        Args:
            url: API URL
            params: 请求参数
            proxy: 代理URL
            
        Returns:
            Dict[str, Any]: API响应数据
        """
        for attempt in range(self.max_retries):
            try:
                # 检查全局速率限制
                if await self._check_rate_limit():
                    continue
                
                # 检查是否需要等待
                if self.last_request_time:
                    wait_time = 1.0 - (datetime.now() - self.last_request_time).total_seconds()
                    if wait_time > 0:
                        await asyncio.sleep(wait_time)
                
                # 发送请求
                async with self.session.get(url, params=params, proxy=proxy) as response:
                    self.last_request_time = datetime.now()
                    
                    # 处理速率限制
                    if await self._handle_rate_limit(response):
                        continue
                    
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Twitter API 请求失败: {response.status} - {error_text}")
                        if attempt < self.max_retries - 1:
                            await asyncio.sleep(self.retry_delay)
                            continue
                        return None
                    
                    return await response.json()
                    
            except Exception as e:
                logger.error(f"请求出错: {str(e)}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                    continue
                return None
        
        return None
    
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
            
        # 提取推文ID
        tweet_ids = []
        for url in urls:
            tweet_id = self._extract_tweet_id(url)
            if tweet_id:
                tweet_ids.append(tweet_id)
        
        if not tweet_ids:
            return [{
                'success': False,
                'url': url,
                'error': '无效的推文URL'
            } for url in urls]
        
        try:
            logger.debug(f"开始获取推文内容: {tweet_ids}")
            
            # 获取会话
            session = await self._get_session()
            
            # 构建API URL
            api_url = f"https://api.twitter.com/2/tweets"
            params = {
                'ids': ','.join(tweet_ids),
                'tweet.fields': 'created_at,author_id,text,entities,attachments',
                'expansions': 'author_id,attachments.media_keys',
                'user.fields': 'name,username',
                'media.fields': 'type,url,preview_image_url'
            }
            
            # 设置代理
            proxy = None
            if self.proxy_url:
                proxy = self.proxy_url
                logger.debug(f"使用代理 {proxy} 获取推文")
            
            # 发送请求
            data = await self._make_request(api_url, params, proxy)
            if not data:
                return [{
                    'success': False,
                    'url': url,
                    'error': "API请求失败"
                } for url in urls]
            
            # 处理响应
            results = []
            for url in urls:
                tweet_id = self._extract_tweet_id(url)
                if not tweet_id:
                    results.append({
                        'success': False,
                        'url': url,
                        'error': '无效的推文URL'
                    })
                    continue
                
                # 查找对应的推文数据
                tweet_data = None
                if isinstance(data.get('data'), list):
                    for tweet in data['data']:
                        if tweet['id'] == tweet_id:
                            tweet_data = tweet
                            break
                elif isinstance(data.get('data'), dict):
                    if data['data']['id'] == tweet_id:
                        tweet_data = data['data']
                
                if not tweet_data:
                    results.append({
                        'success': False,
                        'url': url,
                        'error': '推文不存在或无法访问'
                    })
                    continue
                
                # 提取作者信息
                author = None
                if 'includes' in data and 'users' in data['includes']:
                    for user in data['includes']['users']:
                        if user['id'] == tweet_data['author_id']:
                            author = f"{user['name']} (@{user['username']})"
                            break
                
                # 构建结果
                result = {
                    'success': True,
                    'url': url,
                    'content': tweet_data['text'][:self.max_content_length],
                    'source': 'twitter_api',
                    'metadata': {
                        'author': author or f"User {tweet_data['author_id']}",
                        'created_at': tweet_data.get('created_at')
                    }
                }
                
                # 添加媒体信息
                if 'attachments' in tweet_data:
                    result['metadata']['media'] = []
                    if 'includes' in data and 'media' in data['includes']:
                        for media in data['includes']['media']:
                            if media['media_key'] in tweet_data['attachments'].get('media_keys', []):
                                result['metadata']['media'].append({
                                    'type': media['type'],
                                    'url': media.get('url') or media.get('preview_image_url')
                                })
                
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"获取推文内容失败: {str(e)}")
            return [{
                'success': False,
                'url': url,
                'error': str(e)
            } for url in urls]
    
    def _extract_tweet_id(self, url: str) -> Optional[str]:
        """
        从URL中提取推文ID
        
        Args:
            url: URL地址
            
        Returns:
            推文ID或None
        """
        # 匹配Twitter/X URL中的推文ID
        patterns = [
            r'twitter\.com/\w+/status/(\d+)',
            r'x\.com/\w+/status/(\d+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    async def close(self):
        """关闭 API 客户端"""
        if self.session and not self.session.closed:
            await self.session.close()
            logger.debug("已关闭 aiohttp session") 