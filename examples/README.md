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