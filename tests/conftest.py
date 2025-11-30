import pytest
import sys
from loguru import logger


# Configure loguru for tests
logger.remove()  # Remove default handler
logger.add(sys.stdout, level="DEBUG")


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment for each test"""
    import os

    # Ensure clean state for each test
    yield

    # Cleanup test config file if it exists
    test_config_file = "push_to_talk_config_test.json"
    if os.path.exists(test_config_file):
        try:
            os.remove(test_config_file)
        except Exception:
            pass  # Ignore cleanup errors
