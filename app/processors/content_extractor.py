"""
Content extractor module
"""
from typing import Any, Dict, List, Optional
from loguru import logger
from prefect import task
from .base_processor import BaseProcessor
import re
import json

class ContentExtractor(BaseProcessor):
    """Content extractor that extracts content from messages"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the extractor
        
        Args:
            config: Extractor configuration
        """
        super().__init__(config or {})
        self.extract_keywords = self.config.get("extract_keywords", True)
        self.extract_entities = self.config.get("extract_entities", True)
        self.extract_summary = self.config.get("extract_summary", True)
        self.keyword_count = self.config.get("keyword_count", 10)
        logger.info(f"内容提取器初始化完成，配置: {self.config}")
        
    def initialize(self) -> bool:
        """Initialize the extractor
        
        Returns:
            bool: Whether initialization was successful
        """
        try:
            logger.info("Initializing content extractor")
            super().initialize()
            return True
        except Exception as e:
            logger.error(f"Error initializing content extractor: {str(e)}")
            return False
        
    def cleanup(self) -> None:
        """Cleanup extractor resources"""
        logger.info("Cleaning up content extractor")
        super().cleanup()
        
    @task
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract content from message
        
        Args:
            data: 预处理后的数据
            
        Returns:
            提取后的数据
        """
        logger.info(f"开始提取内容: {data}")
        
        if not self._initialized:
            self.initialize()
            
        try:
            # 复制原始数据
            extracted_data = data.copy()
            
            # 获取内容
            content = extracted_data.get("content", "")
            if not content:
                logger.warning("数据中没有内容字段")
                return extracted_data
            
            # 提取关键词
            if self.extract_keywords:
                keywords = self._extract_keywords(content)
                extracted_data["keywords"] = keywords
            
            # 提取实体
            if self.extract_entities:
                entities = self._extract_entities(content)
                extracted_data["entities"] = entities
            
            # 提取摘要
            if self.extract_summary:
                summary = self._extract_summary(content)
                extracted_data["summary"] = summary
            
            # 添加提取标记
            extracted_data["extracted"] = True
            extracted_data["extraction_info"] = {
                "extract_keywords": self.extract_keywords,
                "extract_entities": self.extract_entities,
                "extract_summary": self.extract_summary,
                "keyword_count": self.keyword_count
            }
            
            logger.debug(f"Content extracted: {extracted_data}")
            return extracted_data
            
        except Exception as e:
            logger.error(f"Error extracting content: {str(e)}")
            raise
    
    def _extract_keywords(self, text: str) -> List[str]:
        """
        提取关键词
        
        Args:
            text: 文本内容
            
        Returns:
            关键词列表
        """
        # 简单的关键词提取算法
        # 1. 分词
        words = re.findall(r'\w+', text)
        
        # 2. 统计词频
        word_freq = {}
        for word in words:
            if len(word) > 1:  # 忽略单字符
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # 3. 按词频排序
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        
        # 4. 返回前N个关键词
        return [word for word, _ in sorted_words[:self.keyword_count]]
    
    def _extract_entities(self, text: str) -> Dict[str, List[str]]:
        """
        提取实体
        
        Args:
            text: 文本内容
            
        Returns:
            实体字典
        """
        # 简单的实体提取算法
        entities = {
            "person": [],
            "location": [],
            "organization": [],
            "date": [],
            "number": []
        }
        
        # 提取日期
        date_pattern = r'\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日]?'
        entities["date"] = re.findall(date_pattern, text)
        
        # 提取数字
        number_pattern = r'\d+(?:\.\d+)?'
        entities["number"] = re.findall(number_pattern, text)
        
        # 提取人名（简单规则）
        person_pattern = r'[赵钱孙李周吴郑王冯陈褚卫蒋沈韩杨朱秦尤许何吕施张孔曹严华金魏陶姜戚谢邹喻水云苏潘葛奚范彭郎鲁韦昌马苗凤花方俞任袁柳鲍史唐费岑薛雷贺倪汤滕殷罗毕郝邬安常乐于时傅卞齐康伍余元卜顾孟平' \
                         r'[一-龥]{1,2}'
        entities["person"] = re.findall(person_pattern, text)
        
        # 提取地名（简单规则）
        location_pattern = r'[北京上海广州深圳天津重庆武汉成都杭州南京西安长沙济南青岛大连沈阳哈尔滨长春福州厦门宁波合肥南昌贵阳昆明兰州西宁银川乌鲁木齐拉萨]' \
                          r'[市省区县]?'
        entities["location"] = re.findall(location_pattern, text)
        
        # 提取组织名（简单规则）
        org_pattern = r'[公司企业集团银行医院学校政府]'
        org_matches = re.findall(org_pattern, text)
        entities["organization"] = [f"{org}公司" for org in org_matches]
        
        return entities
    
    def _extract_summary(self, text: str) -> str:
        """
        提取摘要
        
        Args:
            text: 文本内容
            
        Returns:
            摘要
        """
        # 简单的摘要提取算法
        # 1. 分段
        paragraphs = text.split('\n')
        
        # 2. 选择第一段作为摘要
        if paragraphs:
            summary = paragraphs[0]
            # 截断过长的摘要
            if len(summary) > 200:
                summary = summary[:200] + "..."
            return summary
        
        return "" 