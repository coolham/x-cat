"""
内容分类系统测试用例
"""
import pytest
import os
import sys
from typing import Dict, Any, List
from unittest.mock import patch, MagicMock, AsyncMock

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.category_system.content_categorizer import ContentCategorizer
from app.category_system.ai_categorizer import AICategorizer
from app.category_system.custom_categorizer import CustomCategorizer


@pytest.fixture
def test_config() -> Dict[str, Any]:
    """测试配置"""
    return {
        'ai': {
            'api_key': 'test_api_key',
            'provider': 'openai',
            'model': 'gpt-3.5-turbo',
            'max_tokens': 500,
            'temperature': 0.5,
            'system_prompt': '你是一个专业的内容分类助手，请对内容进行分类。'
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


class TestContentCategorizer:
    """测试内容分类系统"""
    
    def setup_method(self):
        """设置测试环境"""
        self.categorizer = ContentCategorizer()
    
    def test_init(self, test_config):
        """测试初始化"""
        self.categorizer.initialize(test_config)
        assert self.categorizer.ai_categorizer is not None
        assert self.categorizer.custom_categorizer is not None
    
    @pytest.mark.asyncio
    async def test_categorize_with_ai(self, test_config, test_content):
        """测试AI分类"""
        # 设置模拟
        with patch('app.category_system.content_categorizer.AICategorizer') as mock_ai:
            mock_instance = MagicMock()
            mock_instance.categorize = AsyncMock()
            mock_instance.categorize.return_value = {
                'success': True,
                'category': '技术',
                'subcategory': '编程',
                'confidence': 0.95,
                'keywords': ['python', '编程', '语法'],
                'summary': '这是一篇关于Python编程的文章',
                'source': 'ai'
            }
            mock_ai.return_value = mock_instance
            
            # 初始化分类系统
            self.categorizer.initialize(test_config)
            
            # 执行分类
            result = await self.categorizer.categorize(test_content)
            
            # 验证结果
            assert result['success'] is True
            assert result['category'] == '技术'
            assert result['subcategory'] == '编程'
            assert result['confidence'] == 0.95
            assert 'python' in result['keywords']
            assert result['source'] == 'ai'
    
    def test_categorize_with_custom(self, test_config, test_content):
        """测试自定义分类"""
        # 初始化分类系统
        self.categorizer.initialize(test_config)
        
        # 执行分类
        result = self.categorizer.categorize_sync(test_content)
        
        # 验证结果
        assert result['success'] is True
        assert result['category'] == '技术'
        assert result['subcategory'] == '编程'
        assert result['confidence'] == 1.0
        assert result['source'] == 'custom'
    
    @pytest.mark.asyncio
    async def test_categorize_fallback(self, test_config, test_content):
        """测试分类回退机制"""
        # 设置模拟
        with patch('app.category_system.content_categorizer.AICategorizer') as mock_ai:
            mock_instance = MagicMock()
            mock_instance.categorize = AsyncMock()
            mock_instance.categorize.return_value = {
                'success': False,
                'error': 'AI分类失败'
            }
            mock_ai.return_value = mock_instance
            
            # 初始化分类系统
            self.categorizer.initialize(test_config)
            
            # 执行分类
            result = await self.categorizer.categorize(test_content)
            
            # 验证结果
            assert result['success'] is True
            assert result['category'] == '技术'
            assert result['subcategory'] == '编程'
            assert result['source'] == 'custom'
    
    def test_invalid_config(self):
        """测试无效配置"""
        with pytest.raises(ValueError):
            self.categorizer.initialize({})


class TestAICategorizer:
    """测试AI分类系统"""
    
    def setup_method(self):
        """设置测试环境"""
        self.config = {
            'api_key': 'test_api_key',
            'provider': 'openai',
            'model': 'gpt-3.5-turbo',
            'max_tokens': 500,
            'temperature': 0.5,
            'system_prompt': '你是一个专业的内容分类助手，请对内容进行分类。'
        }
        with patch('app.category_system.ai_categorizer.AIClient'):
            self.categorizer = AICategorizer(self.config)
    
    @pytest.mark.asyncio
    async def test_categorize_success(self, test_content):
        """测试成功分类"""
        # 设置模拟
        with patch.object(self.categorizer, 'ai_client') as mock_client:
            mock_client.analyze = AsyncMock()
            mock_client.analyze.return_value = (True, {
                'content_type': '文章',
                'category': '技术',
                'subcategory': '编程',
                'sentiment': '中性',
                'keywords': ['python', '编程', '语法'],
                'summary': '这是一篇关于Python编程的文章',
                'language': 'zh'
            })
            
            # 执行分类
            result = await self.categorizer.categorize(test_content)
            
            # 验证结果
            assert result['success'] is True
            assert result['category'] == '技术'
            assert result['subcategory'] == '编程'
            assert result['confidence'] == 0.95
            assert 'python' in result['keywords']
            assert result['source'] == 'ai'
            
            # 验证AIClient.analyze被正确调用
            mock_client.analyze.assert_called_once_with(
                test_content,
                system_prompt=self.config['system_prompt']
            )
    
    @pytest.mark.asyncio
    async def test_categorize_failure(self, test_content):
        """测试分类失败"""
        # 设置模拟
        with patch.object(self.categorizer, 'ai_client') as mock_client:
            mock_client.analyze = AsyncMock()
            mock_client.analyze.return_value = (False, {'error': 'API调用失败'})
            
            # 执行分类
            result = await self.categorizer.categorize(test_content)
            
            # 验证结果
            assert result['success'] is False
            assert 'API调用失败' in result['error']
    
    def test_invalid_config(self):
        """测试无效配置"""
        with pytest.raises(ValueError):
            AICategorizer({})


class TestCustomCategorizer:
    """测试自定义分类系统"""
    
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
        self.categorizer = CustomCategorizer(self.config)
    
    @pytest.mark.asyncio
    async def test_categorize_match(self, test_content):
        """测试匹配分类"""
        # 执行分类
        result = await self.categorizer.categorize(test_content)
        
        # 验证结果
        assert result['success'] is True
        assert result['category'] == '技术'
        assert result['subcategory'] == '编程'
        assert result['confidence'] == 1.0
        assert result['source'] == 'custom'
        assert result['rule_name'] == '技术文章'
    
    @pytest.mark.asyncio
    async def test_categorize_no_match(self):
        """测试无匹配分类"""
        # 创建不匹配的内容
        content = {
            'content': '这是一篇不相关的文章。',
            'metadata': {'source': 'telegram'}
        }
        
        # 执行分类
        result = await self.categorizer.categorize(content)
        
        # 验证结果
        assert result['success'] is False
        assert '未找到匹配的分类规则' in result['error']
    
    def test_invalid_config(self):
        """测试无效配置"""
        with pytest.raises(ValueError):
            CustomCategorizer({})
    
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
            CustomCategorizer(invalid_config)


if __name__ == "__main__":
    async def run_tests():
        """直接运行测试函数"""
        print("===== 直接运行内容分类系统测试 =====")
        
        # 创建测试实例
        test = TestContentCategorizer()
        
        # 设置测试环境
        test.setup_method()
        
        try:
            # 运行所有测试方法
            print("\n----- 测试成功分类 -----")
            await test.test_categorize_with_ai()
            print("✓ 测试通过")
            
            print("\n----- 测试自定义分类 -----")
            test.test_categorize_with_custom()
            print("✓ 测试通过")
            
            print("\n----- 测试分类回退 -----")
            await test.test_categorize_fallback()
            print("✓ 测试通过")
            
            print("\n----- 测试无效配置 -----")
            test.test_invalid_config()
            print("✓ 测试通过")
            
            print("\n===== 所有测试通过 =====")
        except AssertionError as e:
            print(f"✗ 测试失败: {e}")
        except Exception as e:
            print(f"✗ 运行出错: {e}")
            import traceback
            traceback.print_exc()
    
    # 运行测试
    import asyncio
    asyncio.run(run_tests()) 