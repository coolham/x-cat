"""
Pytest configuration file for X-Cat tests
"""
import os
import sys
import pytest
from dotenv import load_dotenv
import logging

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)


def pytest_configure(config):
    """Configure pytest environment"""
    # Try to load test env file if exists
    if os.path.exists('tests/.env.test'):
        load_dotenv('tests/.env.test')
    else:
        # Set default test environment variables
        os.environ['MOCK_MODE'] = 'True'
        os.environ['TELEGRAM_API_KEY'] = 'test_api_key'
        os.environ['TELEGRAM_CHANNEL_ID'] = 'test_channel_id'
    
    # Configure logging for tests
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def pytest_addoption(parser):
    """Add custom command line options"""
    parser.addoption(
        "--integration", 
        action="store_true", 
        default=False, 
        help="run integration tests that require real API connections"
    )


def pytest_collection_modifyitems(config, items):
    """Modify collected test items"""
    if not config.getoption("--integration"):
        skip_integration = pytest.mark.skip(reason="need --integration option to run")
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip_integration)


@pytest.fixture
def mock_environment():
    """Set up a clean mock environment for tests"""
    # Save original environment values
    original_env = {}
    for key in ['MOCK_MODE', 'TELEGRAM_API_KEY', 'TELEGRAM_CHANNEL_ID']:
        original_env[key] = os.environ.get(key)
    
    # Set test values
    os.environ['MOCK_MODE'] = 'True'
    os.environ['TELEGRAM_API_KEY'] = 'mock_test_key'
    os.environ['TELEGRAM_CHANNEL_ID'] = 'test_channel'
    
    yield
    
    # Restore original values
    for key, value in original_env.items():
        if value is not None:
            os.environ[key] = value
        elif key in os.environ:
            del os.environ[key] 