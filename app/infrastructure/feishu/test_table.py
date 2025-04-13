"""
飞书表格测试脚本
用于测试飞书表格相关功能
"""
import os
import sys
import json
import asyncio
from typing import Tuple, Optional
from loguru import logger
from dotenv import load_dotenv

# 添加项目根目录到 Python 路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
sys.path.append(project_root)

# 加载 .env 文件
env_path = os.path.join(project_root, '.env')
load_dotenv(env_path)

# 打印环境变量，用于调试
logger.info(f"FEISHU_APP_ID: {os.getenv('FEISHU_APP_ID')}")
logger.info(f"FEISHU_APP_SECRET: {'已设置' if os.getenv('FEISHU_APP_SECRET') else '未设置'}")

from app.infrastructure.feishu.client import FeishuClient


def get_feishu_config() -> Tuple[Optional[str], Optional[str], Optional[str], list]:
    """
    获取飞书配置
    
    Returns:
        Tuple[app_id, app_secret, app_token, missing_vars]
    """
    app_id = os.getenv("FEISHU_APP_ID")
    app_secret = os.getenv("FEISHU_APP_SECRET")
    app_token = 'ZP1BbR6fqaCpDosf3gXc9OZhnJb'  # 硬编码的 app_token
    
    # 检查必要的环境变量
    missing_vars = []
    if not app_id:
        missing_vars.append("FEISHU_APP_ID")
    if not app_secret:
        missing_vars.append("FEISHU_APP_SECRET")
    
    return app_id, app_secret, app_token, missing_vars


async def test_list_tables():
    """测试列出数据表功能"""
    try:
        # 获取飞书配置
        app_id, app_secret, app_token, missing_vars = get_feishu_config()
        
        if missing_vars:
            logger.error(f"缺少必要的环境变量: {', '.join(missing_vars)}")
            return
        
        # 初始化飞书客户端
        client = FeishuClient(app_id, app_secret)
        if not await client.initialize():
            logger.error("飞书客户端初始化失败")
            return
        
        # 列出数据表
        result = await client.list_tables(app_token)
        if not result:
            logger.error("列出数据表失败")
            return
        
        # 打印表格列表
        if result["items"]:
            logger.info(f"共找到 {len(result['items'])} 个数据表:")
            for i, table_info in enumerate(result["items"]):
                logger.info(f"{i+1}. {table_info['name']} (ID: {table_info['table_id']})")
        else:
            logger.info("未找到任何数据表")
        
    except Exception as e:
        logger.error(f"测试列出数据表时出错: {str(e)}")
    finally:
        # 清理资源
        if 'client' in locals():
            await client.cleanup()


async def test_create_table():
    """测试创建数据表功能"""
    try:
        # 获取飞书配置
        app_id, app_secret, app_token, missing_vars = get_feishu_config()
        
        if missing_vars:
            logger.error(f"缺少必要的环境变量: {', '.join(missing_vars)}")
            return
        
        # 初始化飞书客户端
        client = FeishuClient(app_id, app_secret)
        if not await client.initialize():
            logger.error("飞书客户端初始化失败")
            return
        
        # 创建数据表
        table_name = "测试数据表"
        fields = [
            {"name": "标题", "type": "text"},
            {"name": "内容", "type": "text"},
            {"name": "时间", "type": "dateTime"},
            {"name": "状态", "type": "select", "property": {"options": [{"name": "待处理"}, {"name": "处理中"}, {"name": "已完成"}]}}
        ]
        
        table_id = await client.create_table(app_token, table_name, fields)
        if not table_id:
            logger.error("创建数据表失败")
            return
        
        logger.info(f"成功创建数据表: {table_name} (ID: {table_id})")
        
        # 更新数据表名称
        new_table_name = "更新后的数据表"
        if not await client.update_table(app_token, table_id, new_table_name):
            logger.error("更新数据表失败")
            return
        
        logger.info(f"成功更新数据表名称: {new_table_name}")
        
        # 添加记录
        record_fields = {
            "标题": "测试记录",
            "内容": "这是一条测试记录",
            "时间": "2023-04-01 12:00:00",
            "状态": "待处理"
        }
        
        record_id = await client.add_record(app_token, table_id, record_fields)
        if not record_id:
            logger.error("添加记录失败")
            return
        
        logger.info(f"成功添加记录: {record_id}")
        
        # 获取记录
        record = await client.get_record(app_token, table_id, record_id)
        if not record:
            logger.error("获取记录失败")
            return
        
        logger.info(f"成功获取记录: {json.dumps(record, ensure_ascii=False, indent=2)}")
        
        # 更新记录
        update_fields = {
            "状态": "处理中"
        }
        
        if not await client.update_record(app_token, table_id, record_id, update_fields):
            logger.error("更新记录失败")
            return
        
        logger.info(f"成功更新记录: {record_id}")
        
        # 获取记录列表
        records = await client.list_records(app_token, table_id)
        if not records:
            logger.error("获取记录列表失败")
            return
        
        logger.info(f"成功获取记录列表，共 {len(records['items'])} 条记录")
        
        # 删除记录
        if not await client.delete_record(app_token, table_id, record_id):
            logger.error("删除记录失败")
            return
        
        logger.info(f"成功删除记录: {record_id}")
        
    except Exception as e:
        logger.error(f"测试创建数据表时出错: {str(e)}")
    finally:
        # 清理资源
        if 'client' in locals():
            await client.cleanup()


async def main():
    """主函数"""
    # 设置日志级别
    logger.remove()
    logger.add(lambda msg: print(msg), level="INFO")
    
    # 运行测试
    logger.info("开始测试列出数据表功能...")
    await test_list_tables()
    
    logger.info("\n开始测试创建数据表功能...")
    await test_create_table()


if __name__ == "__main__":
    asyncio.run(main()) 