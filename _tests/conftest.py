import pytest
from unittest.mock import patch

@pytest.fixture(autouse=True)
def mock_pulsar_config():
    """Mock PulsarConfig for all tests"""
    with patch('app.core.pulsar.config.PulsarConfig') as mock_config:
        mock_config.SECURITY = {
            'service_role': 'test_role',
            'topic_roles': {
                'allowed_topic': ['test_role']
            }
        }
        mock_config.RETRY = {
            'max_retries': 3,
            'delay': 1.0
        }
        yield mock_config
