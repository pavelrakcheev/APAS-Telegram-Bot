"""Shared fixtures for APAS tests."""

import os
import sys
import pytest

# Add project root to path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

# Set test environment variables before any imports
os.environ["TELEGRAM_BOT_TOKEN"] = "123456789:TEST_DUMMY_TOKEN"
os.environ["GROQ_API_KEY"] = "gsk_TEST_DUMMY_KEY"
os.environ["GEMINI_API_KEY"] = "TEST_GEMINI_KEY"
os.environ["YANDEX_API_KEY"] = "TEST_YANDEX_KEY"
os.environ["TELEGRAM_ID"] = "123456789"
os.environ["ADMIN_PASSWORD"] = "test_password"


@pytest.fixture
def mock_groq_response():
    """Mock Groq API response."""
    class MockMessage:
        def __init__(self, content="Test response"):
            self.content = content

    class MockChoice:
        def __init__(self):
            self.message = MockMessage()

    class MockResponse:
        def __init__(self):
            self.choices = [MockChoice()]

    return MockResponse()


@pytest.fixture
def mock_gemini_response():
    """Mock Gemini API response."""
    class MockText:
        def __init__(self):
            self.text = "Test Gemini response"

    return MockText()


@pytest.fixture
def mock_yandex_response():
    """Mock YandexGPT API response."""
    return {
        "result": {
            "alternatives": [
                {
                    "message": {
                        "text": "Test Yandex response"
                    }
                }
            ]
        }
    }


@pytest.fixture
def sample_model_config():
    """Sample model configuration for testing."""
    return {
        "name": "Test Model",
        "description": "Test model for unit tests",
        "provider": "test",
        "model_id": "test-model-1",
        "category": "test"
    }
