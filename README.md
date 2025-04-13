# X-Cat

X-Cat 是一个基于 Prefect 的数据处理管道系统，用于自动提取、处理和存储来自 Telegram 的消息内容。

## 功能特点

- 基于 Prefect 的数据处理管道
- 支持 Telegram 消息自动提取
- 数据预处理和分类
- 多目标数据分发（本地存储、飞书文档、飞书多维表格等）
- 完善的错误处理和重试机制
- 详细的日志记录

## 系统要求

- Python 3.8+
- 依赖包：见 `requirements.txt`

## 安装

1. 克隆仓库：

```bash
git clone https://github.com/yourusername/x-cat.git
cd x-cat
```

2. 安装依赖：

```bash
pip install -r requirements.txt
```

3. 配置环境变量：

```bash
cp .env.example .env
# 编辑 .env 文件，填入你的 API 密钥和其他配置
```

## 配置

1. 编辑 `config/config.yaml` 文件，根据需要调整配置项
2. 确保 `.env` 文件中包含所有必要的环境变量

## 使用方法

### 基本用法

```bash
python -m app.main
```

### 命令行参数

- `-c, --config`: 配置文件目录路径（默认：`config`）
- `-e, --env`: 环境变量文件路径（默认：`.env`）
- `-l, --log-level`: 日志级别（可选：DEBUG, INFO, WARNING, ERROR, CRITICAL）
- `-f, --log-file`: 日志文件路径
- `-d, --data-dir`: 数据目录路径

示例：

```bash
python -m app.main -c custom_config -e custom.env -l DEBUG -f logs/debug.log
```

## 项目结构

```
x-cat/
├── app/
│   ├── adapters/         # 适配器（Telegram等）
│   ├── core/             # 核心组件
│   ├── models/           # 数据模型
│   ├── processors/       # 处理器
│   ├── storage/          # 存储适配器
│   └── utils/            # 工具函数
├── config/               # 配置文件
├── data/                 # 数据目录
├── logs/                 # 日志目录
├── .env.example          # 环境变量模板
├── .gitignore            # Git忽略文件
├── README.md             # 项目说明
└── requirements.txt      # 依赖列表
```

## 开发指南

### 添加新的处理器

1. 在 `app/processors/` 目录下创建新的处理器类
2. 在 `config/config.yaml` 中添加相应的配置项
3. 在 `app/core/prefect_pipeline.py` 中注册新的处理器

### 添加新的存储目标

1. 在 `app/storage/` 目录下创建新的存储适配器
2. 在 `config/config.yaml` 中添加相应的配置项
3. 在 `app/core/prefect_pipeline.py` 中注册新的存储适配器

## 飞书多维表格存储

X-Cat 支持将数据存储到飞书多维表格，便于数据管理和查询。要启用此功能，请按照以下步骤配置：

1. 在飞书开放平台创建多维表格，并获取 `app_token` 和 `table_id`
2. 在 `.env` 文件中添加以下环境变量：
   ```
   FEISHU_BITABLE_APP_TOKEN=your_feishu_bitable_app_token_here
   FEISHU_BITABLE_TABLE_ID=your_feishu_bitable_table_id_here
   ```
3. 确保 `config/config.yaml` 文件中的飞书配置包含多维表格配置：
   ```yaml
   feishu:
     enabled: true
     app_id: "${FEISHU_APP_ID}"
     app_secret: "${FEISHU_APP_SECRET}"
     bitable:
       enabled: true
       app_token: "${FEISHU_BITABLE_APP_TOKEN}"
       table_id: "${FEISHU_BITABLE_TABLE_ID}"
   ```

多维表格中的字段包括：
- 原始内容：提取的原始内容
- 数据类型：内容类型（文本、图片等）
- 来源：数据来源（Telegram、微信等）
- 时间戳：数据提取时间
- ID：数据唯一标识符

## 许可证

MIT

## 贡献

欢迎提交 Issue 和 Pull Request！