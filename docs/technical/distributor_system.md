# 分发器系统设计文档

## 系统架构

### 核心组件

app/distributors/
├── base.py              # 分发器基类
├── config.py            # 配置管理
├── stats.py             # 统计功能
├── health.py            # 健康检查
├── alert.py             # 监控告警
├── cleanup.py           # 数据清理
├── local.py             # 本地分发器
└── notion.py            # Notion分发器

### 组件关系图

┌─────────────────┐      ┌───────────────────┐
│  分类系统/模块   │─────▶│    Distributor    │
└─────────────────┘      └─────────┬─────────┘
                                   │
                ┌──────────────────┼──────────────────┐
                ▼                  ▼                  ▼
       ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
       │  LocalStorage   │ │  NotionStorage  │ │  OtherStorage   │
       └─────────────────┘ └─────────────────┘ └─────────────────┘

## 模块详细设计

### 1. 分发器基类 (Distributor)

#### 1.1 核心功能
- 定义分发接口
- 提供重试机制
- 内容格式化
- 统计记录
- 健康检查
- 监控告警
- 数据清理

#### 1.2 主要方法
- `distribute()`: 分发内容（抽象方法）
- `distribute_with_retry()`: 带重试机制的分发
- `_format_content()`: 格式化内容
- `check_health()`: 检查健康状态
- `get_stats()`: 获取统计信息
- `get_alerts()`: 获取告警信息

#### 1.3 配置管理
- 重试配置
- 健康检查配置
- 告警配置
- 清理配置

### 2. 统计功能 (DistributorStats)

#### 2.1 统计指标
- 成功/失败次数
- 重试次数
- 响应时间
- 成功率
- 平均响应时间

#### 2.2 主要方法
- `record_distribution()`: 记录分发结果
- `get_distributor_stats()`: 获取统计信息
- `get_all_stats()`: 获取所有统计信息
- `clear_stats()`: 清理统计数据

### 3. 健康检查 (DistributorHealth)

#### 3.1 检查指标
- 分发成功率
- 响应时间
- 错误率
- 重试率

#### 3.2 主要方法
- `check_health()`: 检查健康状态
- `get_health_status()`: 获取健康状态
- `get_all_health()`: 获取所有健康状态
- `clear_health()`: 清理健康状态

### 4. 监控告警 (DistributorAlert)

#### 4.1 告警指标
- 失败率阈值
- 响应时间阈值
- 重试次数阈值

#### 4.2 主要方法
- `check_and_alert()`: 检查并发送告警
- `get_alerts()`: 获取告警信息
- `clear_alerts()`: 清理告警记录
- `update_alert_config()`: 更新告警配置

### 5. 数据清理 (DistributorCleanup)

#### 5.1 清理内容
- 统计数据（30天）
- 健康状态（7天）
- 告警记录（14天）

#### 5.2 主要方法
- `cleanup_stats()`: 清理统计数据
- `cleanup_health()`: 清理健康状态
- `cleanup_alerts()`: 清理告警记录
- `cleanup_all()`: 清理所有数据
- `update_config()`: 更新清理配置

## 使用示例

### 1. 初始化分发器
```python
# 创建本地分发器
local_distributor = LocalDistributor()

# 创建Notion分发器
notion_distributor = NotionDistributor()
```

### 2. 分发内容
```python
# 准备内容
content = {
    'id': 'content_001',
    'text': '测试内容',
    'source': 'test',
    'metadata': {
        'date': '2024-03-24T10:00:00'
    },
    'classification': {
        'primary_category': '测试分类',
        'secondary_category': '测试子分类',
        'confidence': 0.9,
        'reasoning': '测试分类理由'
    }
}

# 分发内容
success = await local_distributor.distribute_with_retry(content)
```

### 3. 获取统计信息
```python
# 获取统计信息
stats = local_distributor.get_stats()
print(f"成功率: {stats['success_rate']}")
print(f"平均响应时间: {stats['avg_response_time']}ms")
```

### 4. 检查健康状态
```python
# 检查健康状态
health = local_distributor.check_health()
print(f"状态: {health['status']}")
print(f"成功率: {health['success_rate']}")
```

### 5. 获取告警信息
```python
# 获取告警信息
alerts = local_distributor.get_alerts()
for alert in alerts:
    print(f"告警时间: {alert['timestamp']}")
    print(f"告警信息: {alert['message']}")
```

## 注意事项

1. 错误处理
   - 网络错误重试
   - 异常情况恢复
   - 错误日志记录

2. 性能优化
   - 异步处理
   - 批量操作
   - 缓存机制

3. 数据管理
   - 定期清理
   - 数据备份
   - 状态恢复

4. 监控告警
   - 阈值设置
   - 告警级别
   - 通知方式

## 测试与验证

### 1. 单元测试
```python
def test_distribute_success():
    """测试成功分发"""
    distributor = LocalDistributor()
    content = create_test_content()
    
    success = await distributor.distribute_with_retry(content)
    assert success
    assert distributor.distribute_count == 1

def test_distribute_retry():
    """测试分发重试"""
    distributor = LocalDistributor()
    distributor.success_rate = 0.5
    
    success = await distributor.distribute_with_retry(content)
    assert success
    assert distributor.distribute_count > 1
```

### 2. 集成测试
```python
def test_distribution_with_category():
    """测试带分类的分发"""
    distributor = LocalDistributor()
    category_manager = CategoryManager()
    
    # 获取分类信息
    primary_categories = category_manager.get_primary_categories()
    assert len(primary_categories) > 0
    
    # 分发内容
    success = await distributor.distribute_with_retry(content)
    assert success
    
    # 检查分类信息
    formatted_content = distributor._format_content(content)
    assert formatted_content['classification']['primary'] == content['classification']['primary_category']
```

## 部署与维护

### 1. 部署步骤
1. 准备配置文件
2. 初始化分发器
3. 配置存储目标
4. 启动监控服务
5. 验证系统功能

### 2. 维护任务
- 定期检查配置
- 监控系统状态
- 清理过期数据
- 备份重要信息

### 3. 故障处理
- 网络异常处理
- 存储异常处理
- 系统恢复流程
- 数据修复方法 