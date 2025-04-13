"""
飞书存储模块测试
使用真实的飞书 API 进行测试
"""
import os
import json
import sys
import pytest
import asyncio
import logging
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime
from typing import Dict, Any
# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

from app.storage.feishu_raw_storage import FeishuRawStorage


@pytest.fixture
def real_config():
    """真实配置，从环境变量获取"""
    return {
        "feishu": {
            "app_id": os.environ.get("FEISHU_APP_ID"),
            "app_secret": os.environ.get("FEISHU_APP_SECRET"),
            "proxy_url": os.environ.get("FEISHU_PROXY_URL"),
            "folder_token": os.environ.get("FEISHU_FOLDER_TOKEN"),
            "bitable": {
                "enabled": True,
                "app_token": os.environ.get("FEISHU_BITABLE_APP_TOKEN", "ZP1BbR6fqaCpDosf3gXc9OZhnJb"),
                "table_id": os.environ.get("FEISHU_BITABLE_TABLE_ID", "tblHKTdD3z2gHGNP")
            }
        }
    }




@pytest.fixture
async def storage(real_config):
    """创建并初始化存储实例"""
    storage = FeishuRawStorage(real_config)
    await storage.initialize()
    yield storage
    # 测试结束后清理资源
    if storage.feishu_client:
        await storage.feishu_client.cleanup()




@pytest.mark.skipif(
    not os.environ.get("FEISHU_APP_ID") or not os.environ.get("FEISHU_APP_SECRET"),
    reason="飞书 API 凭证未设置，跳过测试"
)


@pytest.mark.asyncio
async def test_write_data_records(storage, real_config):
    """测试写入一套数据记录到飞书多维表格"""
    logger.info("开始测试写入数据记录到飞书多维表格")
    
    # 准备测试数据
    test_records = [
        {
            "content_type": "TEXT",
            "source_type": "twitter",
            "content": "测试类别1"
        },
        {
            "content_type": "TEXT",
            "source_type": "twitter",
            "content": "这是第二条测试内容，用于测试飞书多维表格存储功能。"
        },
    ]
    
    app_token = 'ZP1BbR6fqaCpDosf3gXc9OZhnJb'
    table_id = 'tblHKTdD3z2gHGNP'
    
    logger.info(f"使用多维表格配置: app_token={app_token}, table_id={table_id}")
    
    # 写入数据记录
    success_count = 0
    for i, record in enumerate(test_records):
        logger.info(f"正在写入第 {i+1} 条记录: {record}")
        result = await storage.store_to_feishu(
            app_token=app_token,
            table_id=table_id,
            data=record,
        )
        logger.info(f"写入结果: {result}")
        if result:
            success_count += 1
        
        # 验证结果
        logger.info(f"成功写入 {success_count}/{len(test_records)} 条记录")
        assert success_count == len(test_records), f"只有 {success_count}/{len(test_records)} 条记录写入成功"


if __name__ == "__main__":
    # 设置pytest的日志级别
    pytest.main([__file__, "-v", "--log-cli-level=INFO"])
