# 分类系统设计文档

## 系统架构

### 核心组件

app/
├── preprocessor/           # 预处理模块
│   ├── content_preprocessor.py  # 内容预处理器
│   ├── url_extractor.py        # URL提取器
│   └── content_fetcher.py      # 内容获取器
├── category_system/        # 分类系统
│   ├── models/            # 数据模型
│   ├── storage/           # 数据存储
│   └── ai/                # AI分类
└── services/              # 服务层
    └── mcp_service.py     # MCP服务

app/category_system/
├── models/                # 数据模型
│   ├── category.py        # 分类实体模型
│   ├── category_version.py # 分类版本模型
│   ├── category_manager.py # 分类管理器
│   └── category_converter.py # 分类定义转换器
├── storage/               # 数据存储
│   └── category_storage.py # 分类存储接口
├── ai/                    # AI分类
│   ├── classifier.py      # AI分类器
│   └── prompts.py         # 分类提示模板
└── category_analyzer.py   # 分类分析器

### 配置文件
config/
├── category_definitions.md    # Markdown格式分类定义（用于人工编辑）
└── category_definitions.yaml  # 结构化分类定义（用于程序处理）

### 组件关系图

┌─────────────────┐      ┌───────────────────┐
│  外部系统/模块   │─────▶│  CategoryManager  │
└─────────────────┘      └─────────┬─────────┘
                                   │
                ┌──────────────────┼──────────────────┐
                ▼                  ▼                  ▼
       ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
       │   AIClassifier  │ │ CategoryStorage │ │CategoryAnalyzer │
       └────────┬────────┘ └────────┬────────┘ └────────┬────────┘
                │                   │                   │
                ▼                   ▼                   │
       ┌─────────────────┐ ┌─────────────────┐         │
       │ MCP服务(AI接口) │ │   数据库存储    │◀────────┘
       └─────────────────┘ └─────────────────┘

## 模块详细设计

### 1. 分类定义管理

#### 1.1 分类定义格式

1. Markdown格式 (category_definitions.md)
```markdown
# 内容分类系统

## 1. 人工智能 (ai)
- 大语言模型 (llm)
- 计算机视觉 (vision)
...
```

2. 结构化格式 (category_definitions.yaml)
```yaml
version: '1.0'
last_updated: '2024-03-24'
content_hash: 'md5_hash_of_markdown_content'
categories:
  ai:
    id: 'cat_ai'
    name: '人工智能'
    description: '人工智能相关技术、应用和发展'
    order: 1
    subcategories:
      llm:
        id: 'subcat_ai_llm'
        name: '大语言模型'
        description: '大型语言模型技术与应用'
...
```

#### 1.2 分类定义转换器 (CategoryConverter)

功能：
- 在Markdown和结构化格式之间转换分类定义
- 生成AI分类提示词
- 支持多语言（中文/英文）
- 计算内容哈希值用于变更检测

主要方法：
- `markdown_to_structured()`: 将Markdown格式转换为结构化格式
- `structured_to_markdown()`: 将结构化格式转换为Markdown格式
- `create_ai_prompt()`: 创建AI分类提示词
- `calculate_hash()`: 计算内容哈希值

#### 1.3 自动更新机制

1. 变更检测
   - 使用MD5哈希值检测Markdown文件变更
   - 定期检查分类定义文件
   - 支持手动触发更新

2. 更新流程
   - 检测到变更时自动转换格式
   - 更新内部状态和缓存
   - 保存新的结构化配置
   - 记录更新日志

3. 错误处理
   - 配置文件备份
   - 更新失败回滚
   - 异常情况恢复

4. 使用示例
```python
# 初始化分类管理器
category_manager = CategoryManager()

# 检查并更新分类定义
if category_manager.check_and_update():
    print("分类系统已更新")
else:
    print("分类系统无需更新")
```

### 2. 分类管理器 (CategoryManager)

#### 2.1 核心功能
- 加载和管理分类定义
- 提供分类查询接口
- 支持分类更新
- 维护分类版本
- 生成AI提示词

#### 2.2 主要方法
- `get_primary_categories()`: 获取一级分类列表
- `get_secondary_categories()`: 获取二级分类列表
- `get_category_by_id()`: 根据ID获取分类信息
- `get_category_path()`: 获取分类完整路径
- `update_category()`: 更新分类信息
- `get_ai_prompt()`: 获取AI分类提示词

#### 2.3 配置管理
- 支持双格式配置文件
- 自动同步两种格式
- 配置文件备份和恢复
- 版本控制和更新记录

### 3. AI分类器 (AIClassifier)

#### 3.1 功能特点
- 使用预定义分类体系
- 支持多语言分类
- 提供分类置信度
- 返回分类理由

#### 3.2 分类流程
1. 加载分类定义
2. 生成分类提示词
3. 调用AI服务
4. 解析分类结果
5. 存储分类结果

#### 3.3 分类结果格式
```json
{
  "primary_category": "选择的一级分类名称",
  "secondary_category": "选择的二级分类名称（如果适用）",
  "confidence": 0.0-1.0,
  "reasoning": "分类理由（50字以内）"
}
```

### 4. 分类存储 (CategoryStorage)

#### 4.1 存储内容
- 分类定义
- 分类使用统计
- 分类结果
- 分类建议

#### 4.2 主要功能
- 保存分类结果
- 更新分类统计
- 记录分类建议
- 提供分类查询

### 5. 分类分析器 (CategoryAnalyzer)

#### 5.1 功能
- 定期分析分类使用情况
- 识别低频分类
- 收集和分析分类建议
- 基于使用情况优化分类体系

#### 5.2 优化策略
- 识别使用频率低的分类
- 分析分类重叠和冗余
- 提供分类优化建议

## 使用示例

### 1. 初始化分类管理器
```python
category_manager = CategoryManager()
```

### 2. 获取分类信息
```python
# 获取一级分类
primary_cats = category_manager.get_primary_categories()

# 获取二级分类
secondary_cats = category_manager.get_secondary_categories('cat_ai')

# 获取分类路径
path = category_manager.get_category_path('subcat_ai_llm')
```

### 3. 更新分类
```python
category_manager.update_category('cat_ai', {
    'name': '人工智能',
    'description': '人工智能相关技术、应用和发展'
})
```

### 4. 获取AI提示词
```python
# 中文提示词
zh_prompt = category_manager.get_ai_prompt(language='zh')

# 英文提示词
en_prompt = category_manager.get_ai_prompt(language='en')
```

## 注意事项

1. 分类维护
   - 使用Markdown格式编辑分类
   - 保持分类ID的唯一性
   - 定期检查和优化分类体系

2. 性能优化
   - 分类数据缓存
   - 按需加载分类定义
   - 优化AI提示词长度

3. 错误处理
   - 配置文件备份
   - 分类结果验证
   - 异常情况恢复

4. 多语言支持
   - 分类名称使用中文
   - 分类ID使用英文
   - 支持中英文提示词

## 系统监控与统计

### 1. 分类使用统计

#### 1.1 统计指标
- 分类使用频率
- 分类准确率
- 分类覆盖范围
- 分类重叠度
- 分类建议采纳率

#### 1.2 统计方法
```python
class CategoryStatistics:
    def __init__(self):
        self.usage_count = {}  # 分类使用次数
        self.accuracy = {}     # 分类准确率
        self.coverage = {}     # 分类覆盖范围
        self.overlap = {}      # 分类重叠度
        
    def update_usage(self, category_id: str):
        """更新分类使用次数"""
        self.usage_count[category_id] = self.usage_count.get(category_id, 0) + 1
        
    def calculate_accuracy(self, category_id: str, correct: bool):
        """计算分类准确率"""
        if category_id not in self.accuracy:
            self.accuracy[category_id] = {'correct': 0, 'total': 0}
        stats = self.accuracy[category_id]
        stats['total'] += 1
        if correct:
            stats['correct'] += 1
```

### 2. 系统监控

#### 2.1 监控指标
- 分类响应时间
- 系统资源使用
- 错误率统计
- 更新频率统计

#### 2.2 监控方法
```python
class SystemMonitor:
    def __init__(self):
        self.response_times = []
        self.error_count = 0
        self.update_count = 0
        
    def record_response_time(self, time_ms: float):
        """记录响应时间"""
        self.response_times.append(time_ms)
        
    def record_error(self):
        """记录错误"""
        self.error_count += 1
        
    def record_update(self):
        """记录更新"""
        self.update_count += 1
```

## 分类反馈机制

### 1. 分类建议

#### 1.1 建议来源
- 用户反馈
- AI分类结果
- 系统分析
- 专家建议

#### 1.2 建议处理
```python
class CategorySuggestion:
    def __init__(self):
        self.suggestions = []
        self.feedback = {}
        
    def add_suggestion(self, 
                      category_id: str,
                      suggestion_type: str,
                      content: str,
                      source: str):
        """添加分类建议"""
        self.suggestions.append({
            'category_id': category_id,
            'type': suggestion_type,
            'content': content,
            'source': source,
            'timestamp': time.time(),
            'status': 'pending'
        })
        
    def process_suggestion(self, suggestion_id: str, action: str):
        """处理分类建议"""
        for suggestion in self.suggestions:
            if suggestion['id'] == suggestion_id:
                suggestion['status'] = action
                suggestion['processed_at'] = time.time()
                break
```

### 2. 反馈收集

#### 2.1 反馈类型
- 分类准确性反馈
- 分类覆盖范围反馈
- 分类结构建议
- 使用体验反馈

#### 2.2 反馈处理
```python
class FeedbackCollector:
    def __init__(self):
        self.feedback = {}
        
    def collect_feedback(self,
                        category_id: str,
                        feedback_type: str,
                        content: str,
                        user_id: str):
        """收集反馈"""
        if category_id not in self.feedback:
            self.feedback[category_id] = []
        self.feedback[category_id].append({
            'type': feedback_type,
            'content': content,
            'user_id': user_id,
            'timestamp': time.time()
        })
```

## 性能优化

### 1. 缓存策略

#### 1.1 缓存内容
- 分类定义
- 统计结果
- 常用查询结果
- AI提示词

#### 1.2 缓存实现
```python
class CategoryCache:
    def __init__(self):
        self.cache = {}
        self.ttl = 3600  # 缓存过期时间（秒）
        
    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        if key in self.cache:
            data, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                return data
        return None
        
    def set(self, key: str, value: Any):
        """设置缓存"""
        self.cache[key] = (value, time.time())
```

### 2. 查询优化

#### 2.1 优化策略
- 索引优化
- 查询缓存
- 批量处理
- 异步处理

#### 2.2 实现方法
```python
class QueryOptimizer:
    def __init__(self):
        self.index = {}
        self.query_cache = {}
        
    def build_index(self, categories: Dict):
        """构建索引"""
        for cat_id, cat in categories.items():
            # 构建名称索引
            self.index[cat['name']] = cat_id
            # 构建描述索引
            for word in cat['description'].split():
                if word not in self.index:
                    self.index[word] = []
                self.index[word].append(cat_id)
```

## 测试与验证

### 1. 单元测试

#### 1.1 测试内容
- 分类定义转换
- 分类查询功能
- 分类更新功能
- 统计功能

#### 1.2 测试用例
```python
def test_category_converter():
    """测试分类转换器"""
    converter = CategoryConverter()
    
    # 测试Markdown到结构化转换
    markdown = "# 内容分类系统\n## 1. 测试分类 (test)"
    structured = converter.markdown_to_structured(markdown)
    assert structured['categories']['test']['name'] == '测试分类'
    
    # 测试结构化到Markdown转换
    markdown = converter.structured_to_markdown(structured)
    assert '## 1. 测试分类' in markdown

def test_category_manager():
    """测试分类管理器"""
    manager = CategoryManager()
    
    # 测试获取分类
    categories = manager.get_primary_categories()
    assert len(categories) > 0
    
    # 测试更新分类
    success = manager.update_category('cat_test', {'name': '新测试分类'})
    assert success
```

### 2. 集成测试

#### 2.1 测试场景
- 分类系统初始化
- 分类定义更新
- 分类查询流程
- 统计功能集成

#### 2.2 测试方法
```python
def test_category_system_integration():
    """测试分类系统集成"""
    # 初始化系统
    manager = CategoryManager()
    statistics = CategoryStatistics()
    monitor = SystemMonitor()
    
    # 测试分类流程
    start_time = time.time()
    categories = manager.get_primary_categories()
    monitor.record_response_time((time.time() - start_time) * 1000)
    
    # 测试统计功能
    statistics.update_usage('cat_test')
    statistics.calculate_accuracy('cat_test', True)
    
    # 验证结果
    assert len(categories) > 0
    assert monitor.response_times[-1] < 100  # 响应时间小于100ms
```

## 部署与维护

### 1. 部署策略

#### 1.1 部署步骤
1. 准备配置文件
2. 初始化分类系统
3. 加载分类定义
4. 启动监控服务
5. 验证系统功能

#### 1.2 部署检查
```python
def deploy_category_system():
    """部署分类系统"""
    try:
        # 检查配置文件
        if not Path('config/category_definitions.md').exists():
            raise FileNotFoundError("分类定义文件不存在")
            
        # 初始化系统
        manager = CategoryManager()
        statistics = CategoryStatistics()
        monitor = SystemMonitor()
        
        # 验证功能
        categories = manager.get_primary_categories()
        if not categories:
            raise ValueError("分类加载失败")
            
        logger.info("分类系统部署成功")
        return True
        
    except Exception as e:
        logger.error(f"分类系统部署失败: {str(e)}")
        return False
```

### 2. 维护计划

#### 2.1 日常维护
- 定期检查分类定义
- 更新统计信息
- 清理缓存数据
- 备份配置文件

#### 2.2 维护任务
```python
def maintain_category_system():
    """维护分类系统"""
    try:
        # 检查分类定义
        manager = CategoryManager()
        if manager.check_and_update():
            logger.info("分类定义已更新")
            
        # 更新统计信息
        statistics = CategoryStatistics()
        statistics.update_statistics()
        
        # 清理缓存
        cache = CategoryCache()
        cache.cleanup()
        
        # 备份配置
        manager._save_categories()
        
        logger.info("分类系统维护完成")
        return True
        
    except Exception as e:
        logger.error(f"分类系统维护失败: {str(e)}")
        return False
```

## API接口设计

### 1. RESTful API

#### 1.1 分类管理接口
```python
class CategoryAPI:
    def __init__(self):
        self.manager = CategoryManager()
        
    def get_categories(self, language: str = 'zh') -> Dict:
        """获取分类列表"""
        return {
            'primary_categories': self.manager.get_primary_categories(language),
            'secondary_categories': self.manager.get_secondary_categories(language)
        }
        
    def get_category(self, category_id: str, language: str = 'zh') -> Dict:
        """获取单个分类信息"""
        return self.manager.get_category_by_id(category_id, language)
        
    def get_category_path(self, category_id: str, language: str = 'zh') -> Dict:
        """获取分类路径"""
        return self.manager.get_category_path(category_id, language)
        
    def update_category(self, category_id: str, data: Dict) -> bool:
        """更新分类信息"""
        return self.manager.update_category(category_id, data)
```

#### 1.2 分类操作接口
```python
class CategoryOperationAPI:
    def __init__(self):
        self.manager = CategoryManager()
        self.classifier = AIClassifier()
        
    def classify_content(self, content: str, language: str = 'zh') -> Dict:
        """AI分类内容"""
        return self.classifier.classify(content, language)
        
    def get_ai_prompt(self, language: str = 'zh') -> str:
        """获取AI分类提示词"""
        return self.manager.get_ai_prompt(language)
```

### 2. 接口规范

#### 2.1 请求格式
```json
{
  "language": "zh",  // 可选，默认"zh"
  "category_id": "cat_ai",  // 分类ID
  "data": {  // 更新数据
    "name": "新名称",
    "description": "新描述"
  }
}
```

#### 2.2 响应格式
```json
{
  "success": true,
  "data": {
    // 响应数据
  },
  "message": "操作成功",
  "error": null
}
```

## 国际化支持

### 1. 语言配置

#### 1.1 语言定义
```python
class LanguageConfig:
    SUPPORTED_LANGUAGES = {
        'zh': '中文',
        'en': 'English'
    }
    
    DEFAULT_LANGUAGE = 'zh'
    
    @classmethod
    def is_supported(cls, language: str) -> bool:
        """检查语言是否支持"""
        return language in cls.SUPPORTED_LANGUAGES
```

#### 1.2 翻译管理
```python
class TranslationManager:
    def __init__(self):
        self.translations = {}
        
    def load_translations(self, language: str):
        """加载语言翻译"""
        # TODO: 实现翻译加载逻辑
        pass
        
    def get_translation(self, key: str, language: str) -> str:
        """获取翻译文本"""
        # TODO: 实现翻译获取逻辑
        return key
```

### 2. 多语言内容

#### 2.1 分类定义格式
```yaml
categories:
  ai:
    id: 'cat_ai'
    name:
      zh: '人工智能'
      en: 'Artificial Intelligence'
    description:
      zh: '人工智能相关技术、应用和发展'
      en: 'AI technologies, applications and development'
```

#### 2.2 使用示例
```python
# 获取中文分类
zh_categories = category_manager.get_primary_categories('zh')

# 获取英文分类
en_categories = category_manager.get_primary_categories('en')

# 获取多语言分类
category = category_manager.get_category_by_id('cat_ai', 'en')
```

## 数据迁移接口（预留）

### 1. 迁移接口
```python
class CategoryMigration:
    def __init__(self):
        self.manager = CategoryManager()
        
    def migrate(self, source_version: str, target_version: str) -> bool:
        """迁移分类数据"""
        # TODO: 实现数据迁移逻辑
        return True
        
    def backup(self) -> bool:
        """备份分类数据"""
        # TODO: 实现数据备份逻辑
        return True
        
    def restore(self, backup_id: str) -> bool:
        """恢复分类数据"""
        # TODO: 实现数据恢复逻辑
        return True
```

## 安全机制接口（预留）

### 1. 安全接口
```python
class CategorySecurity:
    def __init__(self):
        self.manager = CategoryManager()
        
    def validate_access(self, user_id: str, operation: str) -> bool:
        """验证访问权限"""
        # TODO: 实现权限验证逻辑
        return True
        
    def audit_log(self, user_id: str, operation: str, details: Dict):
        """记录审计日志"""
        # TODO: 实现审计日志逻辑
        pass
```

## 预处理模块设计

### 1. 内容预处理器 (ContentPreprocessor)

#### 1.1 功能特点
- URL提取和验证
- 并发内容获取
- 内容组装和格式化
- 错误处理和重试机制
- 资源管理和清理

#### 1.2 配置参数
```python
{
    'max_url_count': 5,        # 最大URL数量
    'max_content_length': 8000, # 内容长度限制
    'proxy_url': None,         # 代理服务器
    'timeout': 30              # 超时时间
}
```

#### 1.3 处理流程
1. 输入验证
   - 检查必要字段
   - 验证数据类型
   - 清理无效数据

2. URL处理
   - 提取URL
   - 验证URL有效性
   - 限制URL数量

3. 内容获取
   - 并发请求
   - 超时控制
   - 错误处理

4. 内容组装
   - 合并原始内容
   - 添加URL内容
   - 格式化输出

### 2. URL提取器 (URLExtractor)

#### 2.1 功能特点
- 正则表达式匹配
- URL验证
- 去重处理

#### 2.2 实现细节
```python
class URLExtractor:
    def __init__(self):
        self.url_pattern = re.compile(
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        )
```

### 3. 内容获取器 (ContentFetcher)

#### 3.1 功能特点
- 异步HTTP请求
- HTML解析
- 内容提取
- 长度限制

#### 3.2 实现细节
```python
class ContentFetcher:
    async def fetch_all(self, urls: List[str]) -> List[Dict]:
        # 并发获取内容
        tasks = [self._fetch_single(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
```

### 4. 测试用例

#### 4.1 单元测试
```python
def test_url_extractor():
    """测试URL提取器"""
    extractor = URLExtractor()
    
    # 测试基本URL提取
    content = "访问 https://example.com 和 http://test.com"
    urls = extractor.extract(content)
    assert len(urls) == 2
    assert "https://example.com" in urls
    
    # 测试无效URL
    content = "无效URL: http://"
    urls = extractor.extract(content)
    assert len(urls) == 0

def test_content_fetcher():
    """测试内容获取器"""
    fetcher = ContentFetcher()
    
    # 测试成功获取
    result = await fetcher._fetch_single("https://example.com")
    assert result['success']
    assert 'content' in result
    
    # 测试超时处理
    result = await fetcher._fetch_single("http://slow-site.com")
    assert not result['success']
    assert 'timeout' in result['error'].lower()

def test_content_preprocessor():
    """测试内容预处理器"""
    preprocessor = ContentPreprocessor()
    
    # 测试基本处理
    content = {
        'text': '查看 https://example.com',
        'source': 'telegram',
        'metadata': {'user_id': '123'}
    }
    result = await preprocessor.preprocess(content)
    assert result['success']
    assert 'content' in result
    assert 'urls' in result
    
    # 测试错误处理
    invalid_content = {'text': 'test'}
    result = await preprocessor.preprocess(invalid_content)
    assert not result['success']
    assert 'errors' in result
```

#### 4.2 集成测试
```python
async def test_preprocessing_pipeline():
    """测试预处理流水线"""
    preprocessor = ContentPreprocessor()
    
    # 测试完整流程
    content = {
        'text': '''
        查看以下链接：
        https://example.com/article1
        https://example.com/article2
        ''',
        'source': 'telegram',
        'metadata': {'user_id': '123'}
    }
    
    result = await preprocessor.preprocess(content)
    
    # 验证结果
    assert result['success']
    assert len(result['urls']) <= 5  # 检查URL数量限制
    assert 'content' in result
    assert 'errors' in result
    
    # 验证内容格式
    content_parts = result['content'].split('\n\n')
    assert len(content_parts) >= 1  # 至少包含原始内容
    
    # 验证错误处理
    if result['errors']:
        assert all(isinstance(error, str) for error in result['errors'])
```

### 5. 性能优化

#### 5.1 缓存策略
- URL内容缓存
- 提取结果缓存
- 缓存过期机制

#### 5.2 并发控制
- 限制并发请求数
- 请求超时控制
- 错误重试机制

#### 5.3 资源管理
- 会话复用
- 内存使用控制
- 资源及时释放

### 6. 错误处理

#### 6.1 错误类型
- 输入验证错误
- URL提取错误
- 网络请求错误
- 内容解析错误

#### 6.2 错误恢复
- 部分失败处理
- 重试机制
- 降级策略

### 7. 监控指标

#### 7.1 性能指标
- 处理时间
- URL提取数量
- 内容获取成功率
- 资源使用情况

#### 7.2 质量指标
- 错误率统计
- 内容完整性
- 格式正确性

## 内容提取模块设计

### 1. 模块结构

```
app/
├── extractors/              # 内容提取模块
│   ├── base.py             # 基础提取器接口
│   ├── telegram.py         # Telegram提取器
│   ├── wechat.py          # 微信提取器（预留）
│   └── web.py             # 网页提取器
```

### 2. 基础提取器接口 (BaseExtractor)

#### 2.1 核心功能
- 定义统一的提取器接口
- 提供通用的URL提取功能
- 管理元数据生成
- 错误处理和验证

#### 2.2 主要方法
```python
class BaseExtractor(ABC):
    def get_source_type(self) -> str:
        """获取数据源类型"""
        pass
    
    async def extract(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """提取内容"""
        pass
    
    async def validate(self, raw_data: Dict[str, Any]) -> bool:
        """验证原始数据"""
        pass
```

### 3. Telegram提取器 (TelegramExtractor)

#### 3.1 功能特点
- 提取消息文本内容
- 识别和提取URL
- 收集消息元数据
- 处理特殊消息类型
- 错误处理和验证

#### 3.2 元数据字段
```python
{
    'message_id': int,          # 消息ID
    'chat_id': int,            # 聊天ID
    'chat_type': str,          # 聊天类型
    'from_user': Dict,         # 发送者信息
    'reply_to_message': Dict,  # 回复消息信息
    'entities': List,          # 消息实体
    'media_type': str,         # 媒体类型
    'source_type': str,        # 数据源类型
    'extracted_at': str,       # 提取时间
    'raw_data': Dict          # 原始数据
}
```

#### 3.3 处理流程
1. 验证消息格式
   - 检查必要字段
   - 验证数据类型
   - 处理缺失字段

2. 提取内容
   - 获取文本内容
   - 提取URL
   - 收集元数据

3. 错误处理
   - 格式验证错误
   - 字段缺失处理
   - 异常捕获和报告

### 4. 测试用例

#### 4.1 单元测试
```python
@pytest.mark.asyncio
async def test_telegram_extractor():
    """测试Telegram提取器"""
    extractor = TelegramExtractor()
    
    # 测试有效消息
    valid_message = {
        'message_id': 123,
        'text': '查看 https://example.com',
        'chat': {'id': 456, 'type': 'private'},
        'from': {'id': 789, 'username': 'test_user'},
        'date': int(datetime.now().timestamp())
    }
    
    result = await extractor.extract(valid_message)
    assert result['success']
    assert result['content'] == '查看 https://example.com'
    assert len(result['urls']) == 1
```

#### 4.2 测试场景
- 基本消息提取
- URL提取和验证
- 元数据收集
- 错误处理
- 特殊消息类型
- 异常情况处理

### 5. 性能优化

#### 5.1 优化策略
- 异步处理
- 缓存机制
- 批量处理
- 资源管理

#### 5.2 监控指标
- 处理时间
- 成功率
- 错误率
- 资源使用

### 6. 错误处理

#### 6.1 错误类型
- 格式错误
- 字段缺失
- 类型错误
- 处理异常

#### 6.2 错误恢复
- 部分失败处理
- 降级策略
- 重试机制

### 7. 扩展性

#### 7.1 新数据源支持
- 实现BaseExtractor接口
- 添加数据源特定逻辑
- 注册新提取器

#### 7.2 功能扩展
- 自定义元数据
- 特殊内容处理
- 过滤规则
- 转换规则
