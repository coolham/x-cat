"""
飞书 Token 管理器
负责管理飞书 API 的访问令牌
"""
import os
import asyncio
import time
import aiohttp
from typing import Dict, Any, Optional
from loguru import logger


class FeishuTokenManager:
    """飞书 Token 管理器"""
    
    def __init__(self, app_id: Optional[str] = None, app_secret: Optional[str] = None, proxy_url: Optional[str] = None):
        """
        初始化飞书 Token 管理器
        
        Args:
            app_id: 飞书应用 ID
            app_secret: 飞书应用密钥
            proxy_url: 代理服务器 URL
        """
        self.app_id = app_id or os.getenv("FEISHU_APP_ID")
        self.app_secret = app_secret or os.getenv("FEISHU_APP_SECRET")
        self.proxy_url = proxy_url or os.getenv("FEISHU_PROXY_URL")
        self.token_type = os.getenv("FEISHU_TOKEN_TYPE", "tenant_access_token")
        
        self.tenant_access_token = None
        self.expires_at = 0
        self.session = None
    
    async def initialize(self) -> bool:
        """
        初始化 Token 管理器
        
        Returns:
            初始化是否成功
        """
        try:
            # 创建 aiohttp session
            self.session = aiohttp.ClientSession()
            
            # 获取访问令牌
            if not await self._refresh_token():
                return False
            
            logger.info("飞书 Token 管理器初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"飞书 Token 管理器初始化失败: {str(e)}")
            return False
    
    async def cleanup(self) -> None:
        """清理资源"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def _refresh_token(self) -> bool:
        """
        刷新访问令牌
        
        Returns:
            刷新是否成功
        """
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            # 构建请求
            url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
            data = {
                "app_id": self.app_id,
                "app_secret": self.app_secret
            }
            
            # 设置代理
            kwargs = {}
            if self.proxy_url:
                kwargs["proxy"] = self.proxy_url
            
            # 发送请求
            async with self.session.post(url, json=data, **kwargs) as response:
                result = await response.json()
                
                if result.get("code") == 0:
                    self.tenant_access_token = result.get("tenant_access_token")
                    self.expires_at = time.time() + result.get("expire") - 60  # 提前 60 秒刷新
                    logger.info("成功刷新飞书访问令牌")
                    return True
                else:
                    logger.error(f"刷新飞书访问令牌失败: {result.get('msg')}")
                    return False
                
        except Exception as e:
            logger.error(f"刷新飞书访问令牌时出错: {str(e)}")
            return False
    
    async def get_tenant_access_token(self) -> Optional[str]:
        """
        获取访问令牌
        
        Returns:
            访问令牌
        """
        # 检查令牌是否过期
        if not self.tenant_access_token or time.time() >= self.expires_at:
            if not await self._refresh_token():
                return None
        
        return self.tenant_access_token
    
    async def get_headers(self) -> Dict[str, str]:
        """
        获取请求头
        
        Returns:
            请求头
        """
        token = await self.get_token()
        if not token:
            return {}
        
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }


async def main():
    """主函数"""
    # 设置日志级别
    logger.remove()
    logger.add(lambda msg: print(msg), level="INFO")
    
    # 获取环境变量
    app_id = os.getenv("FEISHU_APP_ID")
    app_secret = os.getenv("FEISHU_APP_SECRET")
    
    if not app_id or not app_secret:
        logger.error("缺少必要的环境变量: FEISHU_APP_ID, FEISHU_APP_SECRET")
        return
    
    try:
        # 初始化 Token 管理器
        token_manager = FeishuTokenManager(app_id, app_secret)
        if not await token_manager.initialize():
            logger.error("Token 管理器初始化失败")
            return
        
        # 获取并打印 token
        tenant_access_token = await token_manager.get_tenant_access_token()
        if tenant_access_token:
            logger.info(f"获取到的 tenant_access_token: {tenant_access_token}")
            logger.info(f"token 过期时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(token_manager.expires_at))}")
        else:
            logger.error("获取 token 失败")
        
    except Exception as e:
        logger.error(f"运行出错: {str(e)}")
    finally:
        # 清理资源
        if 'token_manager' in locals():
            await token_manager.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
