import asyncio
import time

import pytest

import pytest
import pytest_asyncio
import time
from app.core.pulsar.client import PulsarClient
from app.core.pulsar.config import PulsarConfig

@pytest_asyncio.fixture
async def pulsar_client():
    client = PulsarClient(service_url="pulsar://127.0.0.1:6650")
    yield client
    await client.close()

@pytest.mark.integration
@pytest.mark.asyncio
async def test_real_pulsar_connection(pulsar_client):
    """Verify we can connect to the configured Pulsar instance"""
    assert await pulsar_client.health_check() is True


@pytest.mark.integration
@pytest.mark.asyncio
async def test_message_roundtrip(pulsar_client):
    """Test sending and receiving a message"""
    test_topic = f"test-topic-{int(time.time())}"
    test_msg = {"test": "data", "topic": test_topic}
    
    # Use the shared pulsar_client fixture for real broker tests

    try:
        # Send message
        assert await pulsar_client.send_message(test_topic, test_msg) is True
        
        # Receive message
        received = []
        
        async def processor(msg):
            received.append(msg)
            return True
            
        consumer = await pulsar_client.create_consumer(
            topic=test_topic,
            subscription="test-sub",
            processor=processor
        )
        
        # Wait for processing
        await asyncio.sleep(PulsarConfig.POLL_INTERVAL * 2)
        
        assert len(received) == 1
        assert received[0] == test_msg
    finally:
        # Cleanup
        await pulsar_client.admin.delete_topic(test_topic)
