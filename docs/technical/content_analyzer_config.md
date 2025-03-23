# 内容分析器模块配置指南

本文档提供了内容分析器模块的详细配置说明，帮助您根据自己的需求正确配置和优化内容分析器。

## 配置位置

内容分析器模块的配置位于系统主配置文件`config.json`中。您需要在此文件中添加`content_analyzer`部分，或直接在顶级配置中提供相关参数。

## 基本配置

以下是内容分析器模块的基本配置示例：

```json
{
  "content_analyzer": {
    "provider": "openrouter",
    "model": "openrouter:anthropic/claude-3-haiku",
    "api_key": "your_api_key_here",
    "max_tokens": 2000,
    "temperature": 0.7
  }
}
```

## 完整配置选项

下表列出了内容分析器模块支持的所有配置选项：

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| api_key | 字符串 | 是 | 无 | AI服务提供商的API密钥 |
| provider | 字符串 | 否 | "openai" | AI服务提供商，支持"openrouter"和"deepseek" |
| model | 字符串 | 否 | 视provider而定 | 使用的模型名称 |
| proxy_url | 字符串 | 否 | 无 | 代理服务器URL，格式为`http://host:port`或`socks5://host:port` |
| max_tokens | 整数 | 否 | 2000 | 最大生成token数，影响分析结果的长度和成本 |
| temperature | 浮点数 | 否 | 0.7 | 生成温度参数，控制创造性与确定性的平衡 |
| max_content_length | 整数 | 否 | 8000 | 每个网页内容的最大字符长度 |
| max_total_length | 整数 | 否 | 15000 | 组装后的最大总字符长度 |
| max_concurrency | 整数 | 否 | 3 | 并发处理URL的最大数量 |
| cache_dir | 字符串 | 否 | "./cache" | 缓存目录路径 |

## 服务提供商配置指南

### OpenRouter

OpenRouter是一个AI服务聚合平台，支持多种高质量模型。使用OpenRouter时，请注意以下配置要点：

1. **API密钥**：从[OpenRouter官网](https://openrouter.ai/)获取API密钥
2. **模型名称**：使用`openrouter:`前缀，例如`openrouter:anthropic/claude-3-haiku`

示例配置：

```json
{
  "content_analyzer": {
    "provider": "openrouter",
    "model": "openrouter:anthropic/claude-3-haiku",
    "api_key": "your_openrouter_api_key",
    "max_tokens": 2000,
    "temperature": 0.7
  }
}
```

推荐模型：
- `openrouter:anthropic/claude-3-haiku` - 性能好，成本适中
- `openrouter:openai/gpt-4o` - 高性能，成本较高
- `openrouter:anthropic/claude-3-opus` - 最高性能，成本高

### DeepSeek

DeepSeek提供中文优化的AI模型服务。使用DeepSeek时，请注意以下配置要点：

1. **API密钥**：从[DeepSeek官网](https://www.deepseek.com/)获取API密钥
2. **模型名称**：使用`deepseek:`前缀，例如`deepseek:deepseek-chat`

示例配置：

```json
{
  "content_analyzer": {
    "provider": "deepseek",
    "model": "deepseek:deepseek-chat",
    "api_key": "your_deepseek_api_key",
    "max_tokens": 2000,
    "temperature": 0.7
  }
}
```

## 代理配置

如果您需要通过代理服务器访问AI服务或网页内容，可以配置`proxy_url`参数：

```json
{
  "content_analyzer": {
    "provider": "openrouter",
    "model": "openrouter:anthropic/claude-3-haiku",
    "api_key": "your_api_key_here",
    "proxy_url": "http://127.0.0.1:7890"
  }
}
```

支持的代理格式：
- HTTP代理：`http://host:port`
- SOCKS5代理：`socks5://host:port`

代理设置会同时应用于AI服务调用和网页内容获取。

## 性能优化配置

为了优化内容分析器的性能和资源使用，您可以调整以下参数：

### 内容长度限制

```json
{
  "content_analyzer": {
    "max_content_length": 8000,
    "max_total_length": 15000
  }
}
```

- `max_content_length`控制每个单独网页内容的最大长度
- `max_total_length`控制组装后的总内容长度

较小的值可以减少AI处理成本，但可能影响分析质量；较大的值可以提高分析质量，但会增加成本。

### 并发控制

```json
{
  "content_analyzer": {
    "max_concurrency": 3
  }
}
```

`max_concurrency`控制同时处理的URL数量。较大的值可以提高处理速度，但会增加系统负载和网络带宽消耗。

## 分析参数调整

### 温度控制

```json
{
  "content_analyzer": {
    "temperature": 0.7
  }
}
```

`temperature`参数控制AI生成结果的随机性：
- 低温度(0.1-0.4)：结果更确定、一致，适合需要精确分类的场景
- 中温度(0.5-0.8)：平衡创造性和一致性，适合大多数分析场景
- 高温度(0.9-1.0)：结果更多样化，可能有创造性但不一定严格准确

### 生成长度控制

```json
{
  "content_analyzer": {
    "max_tokens": 2000
  }
}
```

`max_tokens`控制AI生成结果的最大长度。较大的值允许生成更详细的分析结果，但会增加API调用成本。

## 完整配置示例

以下是一个包含所有配置选项的完整示例：

```json
{
  "content_analyzer": {
    "provider": "openrouter",
    "model": "openrouter:anthropic/claude-3-haiku",
    "api_key": "your_api_key_here",
    "proxy_url": "http://127.0.0.1:7890",
    "max_tokens": 2000,
    "temperature": 0.7,
    "max_content_length": 8000,
    "max_total_length": 15000,
    "max_concurrency": 3,
    "cache_dir": "./data/cache"
  }
}
```

## 故障排除

### 常见问题和解决方案

1. **API密钥错误**：确保您的API密钥正确，并具有足够的余额

2. **模型格式错误**：确保使用正确的模型格式，包括提供商前缀
   - OpenRouter模型：`openrouter:provider/model`
   - DeepSeek模型：`deepseek:model`

3. **代理连接问题**：检查代理服务器是否正常运行，并且格式正确

4. **内容提取失败**：某些网站可能禁止爬虫，尝试调整`max_concurrency`或使用不同的代理

5. **分析结果不符合预期**：调整`temperature`参数或尝试不同的模型

如果问题仍然存在，请查看系统日志了解详细错误信息。 