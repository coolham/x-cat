# 内容分析MCP服务测试指南

本目录包含内容分析MCP服务及其组件的测试用例。测试按照功能和依赖分为单元测试和集成测试。

## 测试结构

- `/unit`: 单元测试目录，包含各个独立组件的测试
  - `test_processors.py`: 测试预处理器、内容获取器和内容组装器
  - `test_content_analyzer.py`: 测试AI内容分析模块
  - `test_mcp_service.py`: 测试MCP服务层
  - `test_content_analyzer_module.py`: 测试内容分析器模块集成
  
- `/integration`: 集成测试目录，测试完整功能流程
  - `test_mcp_integration.py`: MCP服务架构集成测试

## 运行测试

### 环境准备

1. 确保已安装所有依赖：
   ```bash
   pip install -r requirements.txt
   ```

2. 对于集成测试，需要设置以下环境变量：
   ```bash
   # 用于AI服务的API密钥
   export TEST_API_KEY=your_api_key
   
   # 代理服务器URL（可选）
   export TEST_PROXY_URL=your_proxy_url
   ```

   Windows PowerShell:
   ```powershell
   $env:TEST_API_KEY="your_api_key"
   $env:TEST_PROXY_URL="your_proxy_url"
   ```

   也可以创建`.env.test`文件（基于`.env.test.example`），测试会自动加载该文件中的环境变量。

### 运行单元测试

```bash
# 运行所有单元测试
pytest tests/unit/

# 运行特定模块的测试
pytest tests/unit/test_processors.py
pytest tests/unit/test_content_analyzer.py
pytest tests/unit/test_mcp_service.py
pytest tests/unit/test_content_analyzer_module.py
```

### 运行集成测试

```bash
# 运行所有集成测试
pytest tests/integration/

# 运行特定集成测试
pytest tests/integration/test_mcp_integration.py
```

### 运行所有测试

```bash
# 运行所有测试
pytest

# 运行所有测试并生成报告
pytest --html=report.html
```

## 测试说明

### 单元测试

单元测试使用模拟（mock）隔离依赖，确保每个组件功能正常：

- **处理器测试**：测试预处理、内容获取和内容组装的核心功能
- **内容分析器测试**：测试AI分析功能，模拟AI客户端响应
- **MCP服务测试**：测试服务层如何整合各个组件
- **模块测试**：测试模块如何与系统框架集成

### 集成测试

集成测试验证完整功能流程，测试各组件协同工作：

- **MCP集成测试**：测试预处理、内容获取、组装和分析的端到端流程

集成测试通常需要实际API密钥，因为它们会调用真实的AI服务。

## 编写新测试

添加新测试时，请遵循以下原则：

1. 单元测试应该专注于单个功能点，并使用模拟隔离外部依赖
2. 集成测试应该测试真实的功能流程，但可以模拟耗时或不稳定的外部服务
3. 所有测试都应该有清晰的注释和描述
4. 测试类和方法应遵循命名约定：`Test{ComponentName}`和`test_{functionality}`

## 模拟数据

测试使用的模拟数据位于各个测试文件中。如果模拟数据变得复杂，可以考虑将它们移至单独的文件或目录。 