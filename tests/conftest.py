import pytest
import sys
from loguru import logger


# Configure loguru for tests
logger.remove()  # Remove default handler
logger.add(sys.stdout, level="DEBUG")


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment for each test"""
    # Ensure clean state for each test
    yield
    # Cleanup after each test if needed
