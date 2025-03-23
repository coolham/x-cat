# X-Cat 信息聚合与分析系统

X-Cat是一个模块化的信息聚合与分析系统，设计用于收集、存储和分析来自各种来源的信息，特别是社交媒体和消息平台。系统可以自动获取、处理和分类信息，帮助用户从大量数据中获取有价值的见解。

## 系统架构

X-Cat采用模块化设计，主要包括以下组件：

1. **核心框架**：负责模块管理、配置和生命周期控制
2. **适配器**：连接各种信息源（如Telegram、RSS等）
3. **存储系统**：使用SQLite存储消息和分析结果
4. **分析器**：提供内容分析功能，包括AI驱动的分类和摘要
5. **处理器**：处理和转换原始数据

## 当前功能

- ✅ 从Telegram频道接收消息
- ✅ 存储消息到本地数据库
- ✅ 基础的消息分析和记录
- ✅ AI内容分析（使用OpenAI、OpenRouter或DeepSeek）
- ✅ 网页内容提取和处理
- ✅ 代理服务器支持

## 安装说明

### 系统要求

- Python 3.8+
- pip (Python包管理器)
- 可选：代理服务器（用于访问被限制的API）

### 安装步骤

1. 克隆仓库：
   ```
   git clone https://github.com/yourusername/x-cat.git
   cd x-cat
   ```

2. 安装依赖：
   ```
   pip install -r requirements.txt
   ```

3. 配置系统：
   - 复制`.env.example`为`.env`
   - 编辑`.env`文件，设置必要的配置（如Telegram令牌、API密钥等）

## 配置说明

### 基本配置

创建`.env`文件，包含以下配置项：

```
# 日志级别
LOG_LEVEL=INFO

# 数据存储
DATA_DIR=./data
SQLITE_DB=x-cat.db

# Telegram配置
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_SESSION_NAME=x_cat_session

# AI服务配置（至少配置一个）
OPENAI_API_KEY=your_openai_api_key
OPENROUTER_API_KEY=your_openrouter_api_key
DEEPSEEK_API_KEY=your_deepseek_api_key

# 代理服务器配置（可选）
HTTP_PROXY=http://127.0.0.1:7890
HTTPS_PROXY=http://127.0.0.1:7890
```

### AI提供商配置

系统支持多种AI服务提供商，您可以选择配置其中一个或多个：

1. **OpenAI API**：设置`OPENAI_API_KEY`环境变量
2. **OpenRouter**：设置`OPENROUTER_API_KEY`环境变量（可访问多种模型）
3. **DeepSeek**：设置`DEEPSEEK_API_KEY`环境变量

系统会按照优先级使用已配置的服务：OpenRouter > DeepSeek > OpenAI。

### 代理服务器配置

如果您需要通过代理服务器访问AI服务或其他网络资源，请设置以下环境变量：

```
HTTP_PROXY=http://your_proxy_server:port
HTTPS_PROXY=http://your_proxy_server:port
```

对于特定提供商的代理控制，可以设置：
```
OPENAI_USE_PROXY=true
OPENROUTER_USE_PROXY=true
DEEPSEEK_USE_PROXY=true
```

## 使用方法

### 启动系统

```
python main.py
```

### 测试AI功能

```
python tests/test_ai_client.py
```

### 添加到监控频道

将已创建的Telegram机器人添加到您想要监控的频道中，并确保它具有读取消息的权限。

## 开发计划

我们计划进一步扩展系统功能，包括：

1. 高级内容分析和聚类
2. 数据可视化界面
3. 更多信息源适配器
4. 用户定制分析规则

## 贡献指南

欢迎贡献代码、报告问题或提出新功能建议。请遵循以下步骤：

1. Fork仓库
2. 创建功能分支：`git checkout -b new-feature`
3. 提交更改：`git commit -am 'Add new feature'`
4. 推送到分支：`git push origin new-feature`
5. 创建Pull Request

## 许可证

[MIT License](LICENSE)