# X-Cat Examples

This directory contains example scripts demonstrating how to use the X-Cat system.

## Setup

Before running any examples:

1. Copy the `.env.example` file from the root directory to a new `.env` file
2. Fill in the required configuration values in your `.env` file
3. Install the required dependencies: `pip install -r requirements.txt`

## Available Examples

### Telegram Monitor

The `telegram_monitor.py` script demonstrates how to monitor a Telegram channel for X posts.

**Usage:**

```bash
python examples/telegram_monitor.py
```

This script will:
- Connect to the Telegram Bot API using your credentials
- Monitor the specified channel for new messages
- Log any messages containing Twitter/X links
- Mark processed messages to avoid duplicate processing

**Configuration:**

Required environment variables:
- `TELEGRAM_API_KEY`: Your Telegram Bot API token
- `TELEGRAM_CHANNEL_ID`: ID of the channel to monitor

Optional environment variables:
- `LOG_LEVEL`: Logging level (default: INFO)
- `LOG_FILE`: Path to log file (if not set, logs only to console)

## Creating New Examples

If you develop a new example script:

1. Place it in this directory
2. Add documentation to this README
3. Ensure it follows the same pattern of loading configuration from environment variables
4. Add proper error handling and logging

## Testing Examples

The examples are designed to work with both real APIs and in mock mode:

- Set `MOCK_MODE=true` in your `.env` file to run with mock data
- Use real API credentials to connect to actual services

# 内容分析器示例

本目录包含 X-Cat 内容分析器的示例脚本，演示如何在独立环境中使用内容分析功能。

## 示例：内容分析

脚本 `analyze_content.py` 演示如何使用内容分析器分析文本或网页内容，并输出结构化分析结果。

### 使用方法

```bash
# 分析文本内容
python examples/analyze_content.py --text "这是一段需要分析的文本内容"

# 分析URL内容
python examples/analyze_content.py --url "https://example.com/article"

# 使用自定义配置文件
python examples/analyze_content.py --config my_config.json --text "分析内容"

# 将结果保存到文件
python examples/analyze_content.py --text "分析内容" --output result.txt
```

### 配置说明

脚本使用项目根目录下的 `config.json` 配置文件。如果该文件不存在，会尝试使用 `config.json.example` 作为备选。

配置文件中需要包含以下内容分析器配置：

```json
{
  "content_analyzer": {
    "api_key": "YOUR_API_KEY",
    "provider": "openrouter",
    "model": "anthropic/claude-3-opus-20240229",
    "proxy_url": "http://127.0.0.1:7890",
    "max_tokens": 2000,
    "temperature": 0.3,
    "max_content_length": 8000,
    "max_total_length": 15000,
    "max_urls": 5,
    "format_type": "markdown"
  }
}
```

### 输出结果示例

```
分析结果:
  内容类型: 文章
  分类: 技术
  子分类: AI
  情感: 中性
  语言: zh
  关键词: 内容分析, AI, 自然语言处理, 分类

摘要:
这是一篇关于AI内容分析技术的文章，主要介绍了如何使用自然语言处理技术对文本进行分类和摘要提取...
``` 