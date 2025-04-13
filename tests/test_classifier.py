"""
内容分类器测试用例
"""
import pytest
from typing import Dict, Any, List
from unittest.mock import patch, MagicMock, AsyncMock

from app.classifiers.content_classifier import ContentClassifier
from app.classifiers.ai_classifier import AIClassifier
from app.classifiers.custom_classifier import CustomClassifier


@pytest.fixture
def test_config() -> Dict[str, Any]:
    """测试配置"""
    return {
        'ai': {
            'api_key': 'test_api_key',
            'provider': 'test_provider',
            'model': 'test_model',
            'max_tokens': 500,
            'temperature': 0.5
        },
        'custom': {
            'rules': [
                {
                    'name': '技术文章',
                    'patterns': ['python', 'java', '编程'],
                    'category': '技术',
                    'subcategory': '编程'
                },
                {
                    'name': '新闻',
                    'patterns': ['新闻', '报道', '突发'],
                    'category': '新闻',
                    'subcategory': '综合'
                }
            ]
        }
    }


@pytest.fixture
def test_content() -> Dict[str, Any]:
    """测试内容"""
    return {
        'content': '这是一篇关于Python编程的文章，介绍了Python的基础语法和高级特性。',
        'metadata': {
            'source': 'telegram',
            'message_id': '123456',
            'date': '2024-01-01T12:00:00'
        },
        'urls': ['https://example.com/python-article'],
        'content_format': 'text_with_url',
        'has_web_content': True
    }


class TestContentClassifier:
    """测试内容分类器"""
    
    def setup_method(self):
        """设置测试环境"""
        self.classifier = ContentClassifier()
    
    def test_init(self, test_config):
        """测试初始化"""
        self.classifier.initialize(test_config)
        assert self.classifier.ai_classifier is not None
        assert self.classifier.custom_classifier is not None
    
    @pytest.mark.asyncio
    async def test_classify_with_ai(self, test_config, test_content):
        """测试AI分类"""
        # 设置模拟
        with patch('app.classifiers.ai_classifier.AIClassifier') as mock_ai:
            mock_instance = MagicMock()
            mock_instance.classify = AsyncMock()
            mock_instance.classify.return_value = {
                'success': True,
                'category': '技术',
                'subcategory': '编程',
                'confidence': 0.95,
                'keywords': ['python', '编程', '语法'],
                'summary': '这是一篇关于Python编程的文章'
            }
            mock_ai.return_value = mock_instance
            
            # 初始化分类器
            self.classifier.initialize(test_config)
            
            # 执行分类
            result = await self.classifier.classify(test_content)
            
            # 验证结果
            assert result['success'] is True
            assert result['category'] == '技术'
            assert result['subcategory'] == '编程'
            assert result['confidence'] == 0.95
            assert 'python' in result['keywords']
            assert result['source'] == 'ai'
    
    def test_classify_with_custom(self, test_config, test_content):
        """测试自定义分类"""
        # 初始化分类器
        self.classifier.initialize(test_config)
        
        # 执行分类
        result = self.classifier.classify_sync(test_content)
        
        # 验证结果
        assert result['success'] is True
        assert result['category'] == '技术'
        assert result['subcategory'] == '编程'
        assert result['confidence'] == 1.0
        assert result['source'] == 'custom'
    
    @pytest.mark.asyncio
    async def test_classify_fallback(self, test_config, test_content):
        """测试分类回退机制"""
        # 设置模拟
        with patch('app.classifiers.ai_classifier.AIClassifier') as mock_ai:
            mock_instance = MagicMock()
            mock_instance.classify = AsyncMock()
            mock_instance.classify.return_value = {
                'success': False,
                'error': 'AI分类失败'
            }
            mock_ai.return_value = mock_instance
            
            # 初始化分类器
            self.classifier.initialize(test_config)
            
            # 执行分类
            result = await self.classifier.classify(test_content)
            
            # 验证结果
            assert result['success'] is True
            assert result['category'] == '技术'
            assert result['subcategory'] == '编程'
            assert result['source'] == 'custom'
    
    def test_invalid_config(self):
        """测试无效配置"""
        with pytest.raises(ValueError):
            self.classifier.initialize({})


class TestAIClassifier:
    """测试AI分类器"""
    
    def setup_method(self):
        """设置测试环境"""
        self.config = {
            'api_key': 'test_api_key',
            'provider': 'test_provider',
            'model': 'test_model',
            'max_tokens': 500,
            'temperature': 0.5
        }
        self.classifier = AIClassifier(self.config)
    
    @pytest.mark.asyncio
    async def test_classify_success(self, test_content):
        """测试成功分类"""
        # 设置模拟
        with patch('app.classifiers.ai_classifier.AIClient') as mock_client:
            mock_instance = MagicMock()
            mock_instance.analyze = AsyncMock()
            mock_instance.analyze.return_value = (True, {
                'content_type': '文章',
                'category': '技术',
                'subcategory': '编程',
                'sentiment': '中性',
                'keywords': ['python', '编程', '语法'],
                'summary': '这是一篇关于Python编程的文章',
                'language': 'zh'
            })
            mock_client.return_value = mock_instance
            
            # 执行分类
            result = await self.classifier.classify(test_content)
            
            # 验证结果
            assert result['success'] is True
            assert result['category'] == '技术'
            assert result['subcategory'] == '编程'
            assert result['confidence'] == 0.95
            assert 'python' in result['keywords']
            assert result['source'] == 'ai'
    
    @pytest.mark.asyncio
    async def test_classify_failure(self, test_content):
        """测试分类失败"""
        # 设置模拟
        with patch('app.classifiers.ai_classifier.AIClient') as mock_client:
            mock_instance = MagicMock()
            mock_instance.analyze = AsyncMock()
            mock_instance.analyze.return_value = (False, {'error': 'API调用失败'})
            mock_client.return_value = mock_instance
            
            # 执行分类
            result = await self.classifier.classify(test_content)
            
            # 验证结果
            assert result['success'] is False
            assert 'API调用失败' in result['error']
    
    def test_invalid_config(self):
        """测试无效配置"""
        with pytest.raises(ValueError):
            AIClassifier({})


class TestCustomClassifier:
    """测试自定义分类器"""
    
    def setup_method(self):
        """设置测试环境"""
        self.config = {
            'rules': [
                {
                    'name': '技术文章',
                    'patterns': ['python', 'java', '编程'],
                    'category': '技术',
                    'subcategory': '编程'
                },
                {
                    'name': '新闻',
                    'patterns': ['新闻', '报道', '突发'],
                    'category': '新闻',
                    'subcategory': '综合'
                }
            ]
        }
        self.classifier = CustomClassifier(self.config)
    
    def test_classify_match(self, test_content):
        """测试匹配分类"""
        # 执行分类
        result = self.classifier.classify(test_content)
        
        # 验证结果
        assert result['success'] is True
        assert result['category'] == '技术'
        assert result['subcategory'] == '编程'
        assert result['confidence'] == 1.0
        assert result['source'] == 'custom'
        assert result['rule_name'] == '技术文章'
    
    def test_classify_no_match(self):
        """测试无匹配分类"""
        # 创建不匹配的内容
        content = {
            'content': '这是一篇不相关的文章。',
            'metadata': {'source': 'telegram'}
        }
        
        # 执行分类
        result = self.classifier.classify(content)
        
        # 验证结果
        assert result['success'] is False
        assert '未找到匹配的分类规则' in result['error']
    
    def test_invalid_config(self):
        """测试无效配置"""
        with pytest.raises(ValueError):
            CustomClassifier({})
    
    def test_invalid_rule(self):
        """测试无效规则"""
        invalid_config = {
            'rules': [
                {
                    'name': '无效规则',
                    # 缺少必要字段
                }
            ]
        }
        
        with pytest.raises(ValueError):
            CustomClassifier(invalid_config) 