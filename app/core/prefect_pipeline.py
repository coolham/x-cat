from typing import Dict, Any, Optional
from loguru import logger
from prefect import task, flow
from prefect.exceptions import PrefectException
import os
from datetime import datetime
from prefect.task_runners import ConcurrentTaskRunner
import asyncio
import traceback
from pathlib import Path
import json

from app.storage.file_storage import FileStorage
from app.storage.feishu_raw_storage import FeishuRawStorage
from app.processors.content_preprocessor import ContentPreprocessor
from app.processors.content_extractor import ContentExtractor
from app.processors.content_assembler import ContentAssembler
from app.processors.content_classifier import ContentClassifier
from app.processors.content_distributor import ContentDistributor


class PrefectPipeline:
    """基于 Prefect 的数据处理管道"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化 Prefect 管道
        
        Args:
            config: 应用配置
        """
        self.config = config
        self.flow = None
        self.initialized = False
        
        # 获取项目目录
        project_dir = Path(__file__).parent.parent.parent
        prefect_dir = project_dir / "prefect_files"
        
        # 确保目录存在
        prefect_dir.mkdir(parents=True, exist_ok=True)
        
        # 设置 Prefect 环境变量，强制本地执行模式
        os.environ["PREFECT_API_URL"] = ""  # 空字符串表示本地模式
        os.environ["PREFECT_API_KEY"] = ""  # 不需要 API 密钥
        os.environ["PREFECT_PROFILES_PATH"] = str(prefect_dir / "profiles.toml")
        os.environ["PREFECT_LOCAL_STORAGE_PATH"] = str(prefect_dir / "storage")
        
        # 确保存储目录存在
        os.makedirs(os.environ["PREFECT_LOCAL_STORAGE_PATH"], exist_ok=True)
        
        # 初始化本地存储
        self.file_storage = FileStorage()
        
        # 初始化飞书存储
        self.feishu_storage = FeishuRawStorage(config)
        
        # 初始化预处理器 - 使用新的ContentPreprocessor
        self.content_preprocessor = ContentPreprocessor(config)
        self.content_extractor = ContentExtractor(config.get("extractor", {}))
        self.content_assembler = ContentAssembler(
            max_content_length=config.get("assembler", {}).get("max_content_length", 8000),
            max_total_length=config.get("assembler", {}).get("max_total_length", 15000),
            format_type=config.get("assembler", {}).get("format_type", "markdown")
        )
        self.content_classifier = ContentClassifier(config.get("classifier", {}))
        self.content_distributor = ContentDistributor(config.get("distributor", {}))
        
        # 禁用所有 API 相关功能
        os.environ["PREFECT_API_TLS_INSECURE_SKIP_VERIFY"] = "true"
        os.environ["PREFECT_API_RETRY_ATTEMPTS"] = "0"
        os.environ["PREFECT_API_RETRY_DELAY"] = "0"
        os.environ["PREFECT_API_RETRY_MAX_DELAY"] = "0"
        os.environ["PREFECT_API_RETRY_JITTER_FACTOR"] = "0"
        
        # 禁用日志服务器
        os.environ["PREFECT_LOGGING_SERVER_ENABLED"] = "false"
        os.environ["PREFECT_LOGGING_SERVER_LEVEL"] = "INFO"
        
        # 设置日志级别为 INFO
        os.environ["PREFECT_LOGGING_LEVEL"] = "INFO"
        
        # 禁用其他功能
        os.environ["PREFECT_SERVER_API_HOST"] = "127.0.0.1"
        os.environ["PREFECT_SERVER_API_PORT"] = "0"  # 使用随机端口
        os.environ["PREFECT_SERVER_API_ENABLED"] = "false"
        os.environ["PREFECT_SERVER_API_SSL_KEYFILE"] = ""
        os.environ["PREFECT_SERVER_API_SSL_CERTFILE"] = ""
        
        logger.info("Prefect 设置为本地执行模式")

    def initialize(self):
        """初始化管道"""
        if self.initialized:
            logger.warning("管道已初始化，跳过")
            return

        # 定义任务
        @task(name="extract_data", retries=3, retry_delay_seconds=5)
        def extract_data(raw_data: Dict[str, Any]) -> Dict[str, Any]:
            """提取数据"""
            logger.info("开始提取数据")
            try:
                # 模拟数据提取逻辑
                extracted_data = {"id": raw_data.get("id"), "content": raw_data.get("content")}
                logger.info(f"数据提取成功: {extracted_data}")
                return extracted_data
            except Exception as e:
                logger.error(f"数据提取出错: {str(e)}")
                raise PrefectException(f"数据提取出错: {str(e)}")

        @task(name="preprocess_data", retries=2)
        def preprocess_data(extracted_data: Dict[str, Any]) -> Dict[str, Any]:
            """预处理数据"""
            logger.info(f"开始预处理数据: {extracted_data}")
            try:
                # 使用内容预处理器处理数据
                preprocessed_data = self.content_preprocessor.process(extracted_data)
                logger.info(f"数据预处理成功: {preprocessed_data}")
                return preprocessed_data
            except Exception as e:
                logger.error(f"数据预处理出错: {str(e)}")
                raise PrefectException(f"数据预处理出错: {str(e)}")

        @task(name="extract_content", retries=2)
        def extract_content(preprocessed_data: Dict[str, Any]) -> Dict[str, Any]:
            """提取内容"""
            logger.info(f"开始提取内容: {preprocessed_data}")
            try:
                # 使用内容提取器提取内容
                extracted_content = self.content_extractor.process(preprocessed_data)
                logger.info(f"内容提取成功: {extracted_content}")
                return extracted_content
            except Exception as e:
                logger.error(f"内容提取出错: {str(e)}")
                raise PrefectException(f"内容提取出错: {str(e)}")

        @task(name="assemble_content", retries=2)
        def assemble_content(extracted_content: Dict[str, Any]) -> Dict[str, Any]:
            """组装内容"""
            logger.info(f"开始组装内容: {extracted_content}")
            try:
                # 使用内容组装器组装内容
                assembled_content = self.content_assembler.assemble(extracted_content)
                logger.info(f"内容组装成功: {assembled_content}")
                return assembled_content
            except Exception as e:
                logger.error(f"内容组装出错: {str(e)}")
                raise PrefectException(f"内容组装出错: {str(e)}")

        @task(name="classify_content", retries=2)
        def classify_content(assembled_content: Dict[str, Any]) -> Dict[str, Any]:
            """分类内容"""
            logger.info(f"开始分类内容: {assembled_content}")
            try:
                # 使用内容分类器分类内容
                classified_content = self.content_classifier.process(assembled_content)
                logger.info(f"内容分类成功: {classified_content}")
                return classified_content
            except Exception as e:
                logger.error(f"内容分类出错: {str(e)}")
                raise PrefectException(f"内容分类出错: {str(e)}")

        @task(name="distribute_content", retries=2)
        def distribute_content(classified_content: Dict[str, Any]) -> Dict[str, Any]:
            """分发内容"""
            logger.info(f"开始分发内容: {classified_content}")
            try:
                # 使用内容分发器分发内容
                distributed_content = self.content_distributor.process(classified_content)
                logger.info(f"内容分发成功: {distributed_content}")
                return distributed_content
            except Exception as e:
                logger.error(f"内容分发出错: {str(e)}")
                raise PrefectException(f"内容分发出错: {str(e)}")

        @task(name="process_data", retries=2)
        def process_data(extracted_data: Dict[str, Any]) -> Dict[str, Any]:
            """处理数据"""
            logger.info(f"开始处理数据: {extracted_data}")
            try:
                # 模拟数据处理逻辑
                processed_data = {**extracted_data, "processed": True}
                logger.info(f"数据处理成功: {processed_data}")
                return processed_data
            except Exception as e:
                logger.error(f"数据处理出错: {str(e)}")
                raise PrefectException(f"数据处理出错: {str(e)}")

        @task(name="store_local", retries=2)
        def store_local(processed_data: Dict[str, Any]) -> Dict[str, Any]:
            """将数据存储到本地文件"""
            return self.file_storage.store(processed_data)
            
        @task(name="store_feishu", retries=2)
        async def store_feishu(processed_data: Dict[str, Any]) -> Dict[str, Any]:
            """将数据存储到飞书文档"""
            # 初始化飞书存储
            if not self.feishu_storage._initialized:
                await self.feishu_storage.initialize()
            
            # 存储到飞书
            return await self.feishu_storage.store(processed_data)
            
        @task(name="store_feishu_bitable", retries=2)
        async def store_feishu_bitable(processed_data: Dict[str, Any]) -> Dict[str, Any]:
            """将数据存储到飞书多维表格"""
            # 初始化飞书存储
            if not self.feishu_storage._initialized:
                await self.feishu_storage.initialize()
            
            # 检查是否配置了多维表格
            if "feishu" not in self.config or "bitable" not in self.config["feishu"]:
                return {"bitable_storage": "not_configured"}
                
            bitable_config = self.config["feishu"]["bitable"]
            if "app_token" not in bitable_config or "table_id" not in bitable_config:
                return {"bitable_storage": "not_configured"}
            
            # 存储到飞书多维表格
            success = await self.feishu_storage.store_to_bitable(
                data=processed_data,
                app_token=bitable_config["app_token"],
                table_id=bitable_config["table_id"]
            )
            
            if success:
                return {"bitable_storage": "success"}
            else:
                return {"bitable_storage": "failed"}

        # 定义任务流
        @flow(
            name="data_pipeline",
            description="数据处理管道",
            validate_parameters=False,
            log_prints=True,
            retries=0,
            persist_result=False,
            task_runner=ConcurrentTaskRunner(),
            version="1.0.0"
        )
        def data_pipeline(raw_data: Dict[str, Any]) -> Dict[str, Any]:
            """
            数据处理管道
            
            Args:
                raw_data: 原始数据
                
            Returns:
                处理后的数据
            """
            logger.info(f"开始处理数据: {raw_data}")
            
            # 基本数据处理
            processed_data = {
                "id": raw_data.get("id", "unknown"),
                "content": raw_data.get("content", ""),
                "processed_at": datetime.now().isoformat(),
                "status": "processed",
                "source_type": raw_data.get("source_type", "unknown"),
                "content_type": raw_data.get("data_type", "TEXT")
            }
            
            # 预处理数据
            preprocessed_data = preprocess_data(processed_data)
            
            # 提取内容
            extracted_content = extract_content(preprocessed_data)
            
            # 组装内容
            assembled_content = assemble_content(extracted_content)
            
            # 分类内容
            classified_content = classify_content(assembled_content)
            
            # 分发内容
            distributed_content = distribute_content(classified_content)
            
            # 存储到本地
            local_storage_result = store_local(distributed_content)
            
            # 存储到飞书
            feishu_storage_result = asyncio.run(store_feishu(distributed_content))
            
            # 存储到飞书多维表格
            # feishu_bitable_result = asyncio.run(store_feishu_bitable(processed_data))
            
            # 合并结果
            result = {
                "processed_data": processed_data,
                "preprocessed_data": preprocessed_data,
                "extracted_content": extracted_content,
                "assembled_content": assembled_content,
                "classified_content": classified_content,
                "distributed_content": distributed_content,
                "local_storage_result": local_storage_result,
                "feishu_storage_result": feishu_storage_result,
                # "feishu_bitable_result": feishu_bitable_result
            }
            
            logger.info(f"data_pipeline : {result}")
            return result

        self.flow = data_pipeline
        self.initialized = True
        logger.info("Prefect 管道初始化完成")

    async def process(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理数据
        
        Args:
            raw_data: 原始数据，可以是字典或 ExtractedData 对象
            
        Returns:
            处理后的数据
        """
        if not self.initialized:
            logger.error("管道未初始化")
            return None
        
        try:
            logger.info(f"开始处理数据: {raw_data}")
            
            # 处理 ExtractedData 对象
            if hasattr(raw_data, '__dict__'):
                # 如果是 ExtractedData 对象，转换为字典
                data_dict = raw_data.__dict__
                logger.debug(f"将 ExtractedData 对象转换为字典: {data_dict}")
            elif isinstance(raw_data, dict):
                # 如果已经是字典，直接使用
                data_dict = raw_data
            else:
                logger.error(f"输入数据类型错误: {type(raw_data)}")
                return None
            
            # 使用 Prefect 流直接运行
            result = await asyncio.to_thread(self.flow, data_dict)
            
            logger.info(f"pipe process数据处理完成: {result}")
            return result
            
        except Exception as e:
            logger.error(f"数据处理失败: {str(e)}")
            logger.debug(f"异常详情: {traceback.format_exc()}")
            return None

    def run(self, raw_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        运行管道
        
        Args:
            raw_data: 原始数据
            
        Returns:
            处理后的数据
        """
        if not self.initialized:
            logger.error("管道未初始化")
            return None
        
        try:
            logger.info(f"运行管道处理数据: {raw_data}")
            
            # 在当前事件循环中运行协程
            loop = asyncio.get_event_loop()
            if loop.is_running():
                result = loop.run_until_complete(self.process(raw_data))
            else:
                result = asyncio.run(self.process(raw_data))
            
            logger.info(f"管道运行完成: {result}")
            return result
        except Exception as e:
            logger.error(f"管道运行失败: {str(e)}")
            logger.debug(f"异常详情: {traceback.format_exc()}")
            return None