# X-Cat 测试文件

本目录包含X-Cat项目的各种测试文件。

## 测试分类

### 单元测试

- `unit/` - 包含各个模块的单元测试

### 集成测试

- `integration/` - 包含集成测试

### 功能测试

- `test_telegram.py` - 测试Telegram适配器功能
- `test_telegram_v20.py` - 使用python-telegram-bot v20版本的功能测试
- `test_telegram_receive.py` - 专门测试Telegram消息接收功能
- `test_ai_client.py` - 测试AI客户端和内容提取功能

## 如何运行测试

### 单个测试文件

```bash
python tests/test_ai_client.py
```

### 使用pytest运行所有测试

```bash
pytest tests/
```

## 测试配置

测试需要适当的环境变量配置，请复制 `.env.test.example` 为 `.env.test` 并填写相应配置。

- 对于AI功能测试，需要配置 `OPENAI_API_KEY` 或 `OPENROUTER_API_KEY`
- 对于Telegram功能测试，需要配置 `TELEGRAM_BOT_TOKEN` 和 `TELEGRAM_CHAT_ID`
- 如果需要测试代理功能，需要配置 `HTTP_PROXY` 和 `HTTPS_PROXY`

注意：某些测试会在缺少配置时自动跳过，详情请查看各测试文件内的说明。 