import pytest
import logging
import sys


# Configure logging for tests
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment for each test"""
    # Ensure clean state for each test
    yield
    # Cleanup after each test if needed
