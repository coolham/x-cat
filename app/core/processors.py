"""
内容处理器
提供内容处理的各个阶段实现
"""
from typing import Dict, Any, Optional
from loguru import logger

class BaseProcessor:
    """基础处理器"""
    
    def __init__(self, config: Dict[str, Any], runtime: Any):
        """初始化处理器
        
        Args:
            config: 配置字典
            runtime: 运行时环境
        """
        self.config = config
        self.runtime = runtime
        
    async def initialize(self) -> bool:
        """初始化处理器
        
        Returns:
            bool: 是否成功
        """
        try:
            return True
        except Exception as e:
            logger.error(f"{self.__class__.__name__} 初始化失败: {str(e)}")
            return False
            
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理数据
        
        Args:
            data: 输入数据
            
        Returns:
            Dict[str, Any]: 处理结果
        """
        raise NotImplementedError
        
    async def health_check(self) -> bool:
        """健康检查
        
        Returns:
            bool: 是否健康
        """
        return True
        
    async def stop(self):
        """停止处理器"""
        pass

class ContentExtractor(BaseProcessor):
    """内容提取器"""
    
    async def initialize(self) -> bool:
        """初始化提取器
        
        Returns:
            bool: 是否成功
        """
        try:
            # 检查运行时环境
            if not hasattr(self.runtime, 'extractors'):
                raise RuntimeError("运行时环境未正确初始化")
                
            # 检查必要的提取器
            required_extractors = ['telegram', 'url']
            for source_type in required_extractors:
                if source_type not in self.runtime.extractors:
                    raise RuntimeError(f"缺少必要的提取器: {source_type}")
                    
            return True
            
        except Exception as e:
            logger.error(f"内容提取器初始化失败: {str(e)}")
            return False
            
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理数据
        
        Args:
            data: 输入数据
            
        Returns:
            Dict[str, Any]: 处理结果
        """
        try:
            source_type = data.get('source_type')
            if source_type not in self.runtime.extractors:
                raise ValueError(f"不支持的源类型: {source_type}")
                
            extractor = self.runtime.extractors[source_type]
            return await extractor.extract(data)
            
        except Exception as e:
            logger.error(f"内容提取失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'data': data
            }

class ContentPreprocessor(BaseProcessor):
    """内容预处理器"""
    
    async def initialize(self) -> bool:
        """初始化预处理器
        
        Returns:
            bool: 是否成功
        """
        try:
            # 检查运行时环境
            if not hasattr(self.runtime, 'preprocessor'):
                raise RuntimeError("运行时环境未正确初始化")
                
            return True
            
        except Exception as e:
            logger.error(f"内容预处理器初始化失败: {str(e)}")
            return False
            
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理内容
        
        Args:
            data: 输入数据
            
        Returns:
            Dict[str, Any]: 处理结果
        """
        try:
            # 检查是否已经处理过
            if data.get('_processed', False):
                return data
                
            # 标记为已处理
            data['_processed'] = True
            
            # 获取内容
            content = data.get('content', '')
            if not content:
                return data
                
            # 提取URL
            urls = self.url_extractor.extract_urls(content)
            if urls:
                # 获取URL内容
                url_contents = await self.content_fetcher.fetch(urls)
                data['url_contents'] = url_contents
                
            # 清理内容
            cleaned_content = self.content_cleaner.clean(content)
            data['content'] = cleaned_content
            data['text'] = cleaned_content  # 同时提供text字段
            
            return data
            
        except Exception as e:
            logger.error(f"内容预处理失败: {str(e)}")
            return data

class ContentClassifier(BaseProcessor):
    """内容分类器"""
    
    async def initialize(self) -> bool:
        """初始化分类器
        
        Returns:
            bool: 是否成功
        """
        try:
            # 检查运行时环境
            if not hasattr(self.runtime, 'classifier') or not hasattr(self.runtime, 'category_manager'):
                raise RuntimeError("运行时环境未正确初始化")
                
            return True
            
        except Exception as e:
            logger.error(f"内容分类器初始化失败: {str(e)}")
            return False
            
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理数据
        
        Args:
            data: 输入数据
            
        Returns:
            Dict[str, Any]: 处理结果
        """
        try:
            if not self.runtime.classifier or not self.runtime.category_manager:
                raise RuntimeError("分类器或分类管理器未初始化")
                
            # 获取分类提示词
            prompt = self.runtime.category_manager.get_ai_prompt()
            
            # 进行分类
            result = await self.runtime.classifier.classify(data['content'], prompt)
            
            # 更新数据
            data['classification'] = result
            return data
            
        except Exception as e:
            logger.error(f"内容分类失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'data': data
            }

class ContentDistributor(BaseProcessor):
    """内容分发器"""
    
    async def initialize(self) -> bool:
        """初始化分发器
        
        Returns:
            bool: 是否成功
        """
        try:
            # 检查运行时环境
            if not hasattr(self.runtime, 'distributor'):
                raise RuntimeError("运行时环境未正确初始化")
                
            return True
            
        except Exception as e:
            logger.error(f"内容分发器初始化失败: {str(e)}")
            return False
            
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理数据
        
        Args:
            data: 输入数据
            
        Returns:
            Dict[str, Any]: 处理结果
        """
        try:
            if not self.runtime.distributor:
                raise RuntimeError("分发器未初始化")
                
            return await self.runtime.distributor.distribute(data)
            
        except Exception as e:
            logger.error(f"内容分发失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'data': data
            }

class ContentStorage(BaseProcessor):
    """内容存储器"""
    
    async def initialize(self) -> bool:
        """初始化存储器
        
        Returns:
            bool: 是否成功
        """
        try:
            # 检查运行时环境
            if not hasattr(self.runtime, 'storage'):
                raise RuntimeError("运行时环境未正确初始化")
                
            return True
            
        except Exception as e:
            logger.error(f"内容存储器初始化失败: {str(e)}")
            return False
            
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理数据
        
        Args:
            data: 输入数据
            
        Returns:
            Dict[str, Any]: 处理结果
        """
        try:
            if not self.runtime.storage:
                raise RuntimeError("存储器未初始化")
                
            return await self.runtime.storage.store(data)
            
        except Exception as e:
            logger.error(f"内容存储失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'data': data
            } 