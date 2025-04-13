# X-Cat 系统 architecture document

## 1. System Overview

X-Cat is a content automatic classification and storage system that adopts a pipeline-based processing architecture. The system can receive content from multiple data sources (such as Telegram, Feishu, etc.), classify it through AI analysis, and distribute the content to different storage targets (such as local storage, Notion, Feishu, etc.).

This document details the overall architecture of the system, including component relationships, data flows, and key design information.

## 2. Component Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        External Systems/Modules                          │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                               Runtime                                   │
│                      (System Runtime Environment/Core Controller)        │
└───────────────┬───────────────┬───────────────┬───────────────┬─────────┘
                │               │               │               │
                ▼               ▼               ▼               ▼
┌───────────────┴───────┐ ┌─────┴───────┐ ┌─────┴───────┐ ┌─────┴───────┐
│      Adapters        │ │  Extractors │ │  Processors │ │  Analyzers  │
│    (Adapters)        │ │  (Extractors)│ │  (Processors)│ │  (Analyzers) │
└───────────────┬───────┘ └─────┬───────┘ └─────┬───────┘ └─────┬───────┘
                │               │               │               │
                ▼               ▼               ▼               ▼
┌───────────────┴───────┐ ┌─────┴───────┐ ┌─────┴───────┐ ┌─────┴───────┐
│   TelegramAdapter     │ │  Telegram   │ │  Content    │ │  Content    │
│   FeishuAdapter       │ │  Extractor  │ │  Preprocessor│ │  Analyzer   │
│   (Other Adapters...) │ │  URLExtractor│ │  Classifier │ │  AI         │
└───────────────┬───────┘ └─────┬───────┘ └─────┬───────┘ └─────┬───────┘
                │               │               │               │
                ▼               ▼               ▼               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                               Pipeline                                   │
│                      (Pipeline/Process Flow Coordinator)                 │
└───────────────┬───────────────┬───────────────┬───────────────┬─────────┘
                │               │               │               │
                ▼               ▼               ▼               ▼
┌───────────────┴───────┐ ┌─────┴───────┐ ┌─────┴───────┐ ┌─────┴───────┐
│      Distributors     │ │   Storage   │ │  Category  │ │  Integrations│
│    (Distributors)     │ │  (Storage)  │ │  System    │ │  (Integrations)│
└───────────────┬───────┘ └─────┬───────┘ └─────┬───────┘ └─────┬───────┘
                │               │               │               │
                ▼               ▼               ▼               ▼
┌───────────────┴───────┐ ┌─────┴───────┐ ┌─────┴───────┐ ┌─────┴───────┐
│   LocalDistributor    │ │  Local      │ │  Category  │ │  Feishu     │
│   NotionDistributor   │ │  Storage    │ │  Manager   │ │  API        │
│   (Other Distributors)│ │  (Other Storage)│ │  AIClassifier│ │  Token     │
└───────────────────────┘ └─────────────┘ └─────────────┘ └─────────────┘
```

## 3. Data Flow Diagram

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  External   │────▶│   Adapter   │────▶│  Extractor  │
│   Message   │     │             │     │             │
└─────────────┘     └─────────────┘     └─────────────┘
                                                │
                                                ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Storage    │◀────│ Distributor │◀────│ Classifier  │
│  Target     │     │             │     │             │
└─────────────┘     └─────────────┘     └─────────────┘
                                                │
                                                ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Category   │────▶│ Preprocessor│────▶│  Analyzer   │
│  System     │     │             │     │             │
└─────────────┘     └─────────────┘     └─────────────┘
```

### 3.1 Detailed Data Flow

1. **Message Reception**:
   - External systems (such as Telegram, Feishu) send messages
   - Adapters receive messages and convert them to standard format

2. **Content Extraction**:
   - Extractors extract text content from messages
   - Identify and extract URL links
   - Get webpage content from URL

3. **Content Preprocessing**:
   - Clean and format content
   - Control content length
   - Assemble original message and webpage content

4. **Content Analysis**:
   - Use AI service to analyze content
   - Identify content type, sentiment, keywords, etc.
   - Generate content summary

5. **Content Classification**:
   - Classify content based on category system
   - Assign main category and subcategories
   - Record classification confidence and reason

6. **Content Distribution**:
   - Select distribution target based on classification result
   - Format content to fit different targets
   - Send content to target system

7. **Content Storage**:
   - Save content to local storage
   - Record metadata and classification information
   - Build index for retrieval

## 4. Core Component Design

### 4.1 Runtime (System Runtime Environment)

Runtime is the core component of the system, responsible for managing the lifecycle of all other components and coordinating communication between them.

**Main Functions**:
- Initialize and manage all components
- Build processing pipeline
- Handle system signals (such as SIGINT, SIGTERM)
- Provide health check and statistics information
- Coordinate communication between components

**Key Methods**:
- `initialize()`: Initialize all components
- `process_content()`: Process content
- `health_check()`: Check system health status
- `stop()`: Stop system

### 4.2 Pipeline (Pipeline)

Pipeline is responsible for coordinating various processing stages to ensure data flows in the correct order.

**Main Functions**:
- Manage processing stages
- Control data flow
- Provide caching mechanism
- Collect statistics information

**Key Classes**:
- `Pipeline`: Pipeline main class
- `PipelineStage`: Pipeline stage class

**Key Methods**:
- `add_stage()`: Add processing stage
- `process()`: Process data
- `get_stats()`: Get statistics information

### 4.3 Adapters (Adapters)

Adapters are responsible for receiving messages from different sources and converting them to standard format used by the system.

**Main Adapters**:
- `TelegramAdapter`: Receive messages from Telegram
- `FeishuAdapter`: Receive messages from Feishu

**Key Functions**:
- Message reception and verification
- Format conversion
- Error handling

### 4.4 Extractors (Extractors)

Extractors are responsible for extracting content from messages, including text and URL.

**Main Extractors**:
- `TelegramExtractor`: Extract content from Telegram messages
- `URLExtractor`: Extract URL from text

**Key Functions**:
- Content extraction
- URL identification and verification
- Webpage content retrieval

### 4.5 Preprocessors (Preprocessors)

Preprocessors are responsible for preliminary processing of extracted content to prepare for subsequent analysis.

**Main Preprocessors**:
- `ContentPreprocessor`: Content preprocessor

**Key Functions**:
- Content cleaning and formatting
- Length control
- Content assembly

### 4.6 Analyzers (Analyzers)

Analyzers are responsible for deep analysis of content to extract useful information.

**Main Analyzers**:
- `ContentAnalyzer`: Content analyzer

**Key Functions**:
- Content type identification
- Sentiment analysis
- Keyword extraction
- Summary generation

### 4.7 Category System (Category System)

Category system is responsible for classifying content, which is one of the core functions of the system.

**Main Components**:
- `CategoryManager`: Category manager
- `AIClassifier`: AI classifier

**Key Functions**:
- Load and manage category definitions
- Provide category query interface
- Support category updates
- Generate AI prompt words

### 4.8 Distributors (Distributors)

Distributors are responsible for distributing processed content to different targets.

**Main Distributors**:
- `LocalDistributor`: Local distributor
- `NotionDistributor`: Notion distributor

**Key Functions**:
- Content distribution
- Retry mechanism
- Error handling
- Statistics recording

### 4.9 Storage (Storage)

Storage component is responsible for saving processed content.

**Main Storage**:
- `LocalStorage`: Local storage

**Key Functions**:
- Content saving
- Metadata management
- Index building

### 4.10 Integrations (Integrations)

Integration component is responsible for interacting with external systems.

**Main Integrations**:
- `FeishuAPI`: Feishu API integration
- `FeishuTokenManager`: Feishu Token manager

**Key Functions**:
- API call encapsulation
- Token management
- Error handling

## 5. Key Design Information

### 5.1 Pipeline Design

X-Cat system adopts a pipeline-based processing architecture with the following characteristics:

- **Chain Processing**: Data flows from one stage to the next, forming a processing chain
- **Stage Independence**: Each stage processes data independently without relying on the internal state of other stages
- **Error Isolation**: An error in one stage does not affect other stages
- **Statistics Collection**: Each stage collects its own statistics information
- **Caching Mechanism**: Support caching processing results to avoid repeated processing

### 5.2 Category System Design

Category system is one of the core functions of X-Cat with the following characteristics:

- **Dual Format Configuration**: Support Markdown and structured format category definitions
- **Automatic Updates**: Detect category definition changes and automatically update
- **Multi-language Support**: Support Chinese and English category
- **AI Classification**: Use AI service for content classification
- **Classification Feedback**: Support classification suggestions and feedback mechanism

### 5.3 Feishu Integration Design

Feishu integration is an important extension of the system with the following characteristics:

- **Token Management**: Automatically manage Feishu API access tokens
- **API Encapsulation**: Encapsulate Feishu API calls to provide simple interfaces
- **Table Operations**: Support creation, reading, updating, and deleting multi-dimensional tables
- **Robot Operations**: Support sending text messages, interactive messages, and reply messages

### 5.4 Error Handling Design

System adopts comprehensive error handling mechanism:

- **Retry Mechanism**: Key operations support automatic retries
- **Degradation Strategy**: System can downgrade operation when a component fails
- **Error Logging**: Detailed error log recording
- **Health Check**: Regularly check system health status

### 5.5 Extensibility Design

System design has good extensibility:

- **Plugin Architecture**: Support adding new adapters, extractors, processors, distributors, and storage
- **Standard Interface**: Components communicate through standard interfaces
- **Configuration Driven**: Control component behavior through configuration
- **Event Driven**: Support event-based communication

## 6. System Configuration

System configures through `config.json` file, mainly including the following parts:

```json
{
  "system": {
    "proxy_url": "http://127.0.0.1:7890",
    "health_check_interval": 60
  },
  "telegram_adapter": {
    "api_id": "your_api_id",
    "api_hash": "your_api_hash",
    "bot_token": "your_bot_token"
  },
  "url_extractor": {
    "max_url_count": 5,
    "timeout": 30
  },
  "preprocessor": {
    "max_content_length": 8000,
    "max_total_length": 15000
  },
  "content_analyzer": {
    "provider": "openrouter",
    "model": "openrouter:anthropic/claude-3-haiku",
    "api_key": "your_api_key",
    "max_tokens": 2000,
    "temperature": 0.7
  },
  "distributor": {
    "retry_count": 3,
    "retry_delay": 5
  },
  "storage": {
    "path": "./data/storage"
  },
  "feishu": {
    "app_id": "your_app_id",
    "app_secret": "your_app_secret",
    "token_type": "tenant_access_token"
  }
}
```

## 7. Deployment and Maintenance

### 7.1 Deployment Steps

1. Prepare configuration file
2. Install dependencies
3. Initialize system
4. Start service
5. Verify functionality

### 7.2 Maintenance Tasks

- Regularly check configuration
- Monitor system status
- Clean expired data
- Backup important information

### 7.3 Fault Handling

- Check logs
- Verify configuration
- Restart service
- Restore backup

## 8. Future Extension

### 8.1 Planned Features

- Support more data sources (such as WeChat, DingTalk)
- Support more storage targets (such as Yuque, Confluence)
- Enhance AI analysis capabilities
- Provide Web management interface

### 8.2 Technical Improvements

- Optimize performance
- Enhance extensibility
- Improve error handling
- Enhance security

## 9. Module Operation Relationship Analysis

### 9.1 Extractors and Processors Operation Relationship

Extractors and Processors modules in X-Cat system are different processing stages in pipeline processing architecture, and their relationship is **passive call** rather than active running service.

#### Data Flow

1. **Data Source → Adapter → Pipeline → Extractor → Preprocessor → Classifier → Distributor → Storage**

2. **Specific Process**：
   - External system (such as Telegram) sends messages
   - Adapter (such as TelegramAdapter) receives messages and converts them to standard format
   - Adapter passes messages to pipeline (Pipeline)
   - Pipeline sequentially calls various processing stages, including extractors, preprocessors, etc.
   - Each stage processes the result and passes it to the next stage

#### Extractors Module

1. **Function Positioning**：
   - Extractors are the first processing stage in the pipeline
   - Responsible for extracting content from original messages, including text and URL
   - Not active running, but called by pipeline

2. **Main Components**：
   - `BaseExtractor`: Extractor base class, define interface
   - `TelegramExtractor`: Extract content from Telegram messages
   - `URLExtractor`: Extract URL from text

3. **Working Mode**：
   - Create various extractor instances in Runtime initialization
   - Pipeline calls `_extract_content` method, which selects corresponding extractor based on message source_type
   - Extractor executes `extract` method to process message, returning extraction result

#### Processors Module

1. **Function Positioning**：
   - Processors are subsequent processing stages in the pipeline
   - Responsible for further processing of extracted content, such as preprocessing, classification, etc.
   - Not active running, but called by pipeline

2. **Main Components**：
   - `ContentProcessor`: Processor base class, define interface
   - `PreProcessor`: Preprocess content
   - `ContentFetcher`: Get webpage content from URL
   - `ContentAssembler`: Assemble original message and webpage content

3. **Working Mode**：
   - Create various processor instances in Runtime initialization
   - Pipeline sequentially calls various processing stages, such as `_preprocess_content`, `_classify_content`, etc.
   - Each processor executes corresponding processing logic, returning processing result

#### Key Code Analysis

1. **Pipeline Construction** (In Runtime initialization):
   ```python
   # 7. Build pipeline
   self.pipeline.add_stage("Extract", self._extract_content)
   self.pipeline.add_stage("Preprocess", self._preprocess_content)
   self.pipeline.add_stage("Classify", self._classify_content)
   self.pipeline.add_stage("Distribute", self._distribute_content)
   self.pipeline.add_stage("Store", self._store_content)
   ```

2. **Extractor Call** (In `_extract_content` method):
   ```python
   source_type = data.get('source_type')
   if source_type in self.extractors:
       extractor = self.extractors[source_type]
       result = await extractor.extract(data)
       return result
   ```

3. **Preprocessor Call** (In `_preprocess_content` method):
   ```python
   if not self.preprocessor:
       raise RuntimeError("Preprocessor not initialized")
   return await self.preprocessor.process(data)
   ```

4. **Message Processing Flow** (In main.py):
   ```python
   # Process message
   result = await pipeline.process(processed_message)
   ```

#### Conclusion

1. **Not Active Running Service**:
   - Extractors and Processors are not active running services
   - They are processing stages called sequentially by pipeline

2. **Data Flow**:
   - Data from external system → adapter → pipeline → extractor → preprocessor → classifier → distributor → storage
   - Each stage processes the result and passes it to the next stage

3. **Trigger Mechanism**:
   - System starts, adapter (such as TelegramAdapter) starts polling or listening
   - When new messages are received, adapter passes messages to pipeline
   - Pipeline sequentially calls various processing stages, including extractors and preprocessors

4. **Summary**:
   - Extractors are not active running services, but processing stages called by pipeline
   - They receive messages from adapter, process them, and pass them to the next processing stage
   - Entire system is event-driven, triggered by external messages 

## 3. Configuration Management System

The X-Cat system uses a hierarchical configuration management approach that separates sensitive information from general configuration settings. This design ensures security, flexibility, and maintainability.

### 3.1 Configuration Structure

The configuration system consists of three main components:

1. **Environment Variables (.env)**
   - Contains sensitive information such as API keys, tokens, and secrets
   - Uses the `XCAT_` prefix to distinguish system variables
   - Example: `XCAT_TELEGRAM_API_KEY`, `XCAT_OPENAI_API_KEY`

2. **Base Configuration (config/base.yaml)**
   - Contains default system settings
   - Defines the structure for all configuration options
   - Includes system-wide settings like logging, data directories, etc.

3. **Module Configurations (config/*.yaml)**
   - Contains module-specific settings
   - Each module has its own configuration file
   - Examples: `telegram.yaml`, `content_analyzer.yaml`, `storage.yaml`

### 3.2 Configuration Loading Process

The configuration loading process follows these steps:

1. Load environment variables from `.env` file
2. Load base configuration from `config/base.yaml`
3. Load all module configurations from `config/*.yaml` files
4. Merge configurations in the following order:
   - Start with base configuration
   - Apply module configurations
   - Override with environment variables

### 3.3 Configuration Manager

The `ConfigManager` class in `app/core/config_manager.py` handles all configuration operations:

```python
class ConfigManager:
    def __init__(self, config_dir: str = "config", env_file: str = ".env"):
        self.config_dir = config_dir
        self.env_file = env_file
        self.config = {}
        self.secrets = {}
        
    def load(self) -> Dict[str, Any]:
        # Load environment variables
        self._load_env()
        
        # Load base configuration
        self._load_base_config()
        
        # Load module configurations
        self._load_module_configs()
        
        # Merge configurations
        return self._merge_configs()
```

### 3.4 Configuration Priority

Configuration values are applied in the following order (highest to lowest priority):

1. Environment variables (highest priority)
2. Module-specific configuration files
3. Base configuration (lowest priority)

This allows for flexible configuration management:
- Sensitive information is kept secure in environment variables
- Default settings are provided in the base configuration
- Module-specific settings can override defaults
- Environment variables can override any setting when needed

### 3.5 Example Configuration Structure

```
project_root/
├── .env                    # Environment variables (secrets)
├── .env.example            # Example environment file
├── config/
│   ├── base.yaml           # Base configuration
│   ├── telegram.yaml       # Telegram module configuration
│   ├── content_analyzer.yaml # Content analyzer configuration
│   └── storage.yaml        # Storage module configuration
```

### 3.6 Security Considerations

- Sensitive information is never stored in version-controlled files
- API keys and tokens are only stored in `.env` file (added to .gitignore)
- Configuration files use YAML format for better readability and structure
- Environment variables use a consistent naming convention with `XCAT_` prefix 