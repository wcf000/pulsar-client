import asyncio
import time

import pytest

from app.core.pulsar.client import PulsarClient
from app.core.pulsar.config import PulsarConfig

# Helper: try both localhost and 127.0.0.1 for Pulsar broker (Windows+Docker workaround)



@pytest.mark.integration
@pytest.mark.asyncio

async def test_real_pulsar_connection():
    """Verify we can connect to the configured Pulsar instance"""
    # Use the shared pulsar_client fixture for real broker tests

    try:
        # Test basic connectivity
        assert await PulsarClient.health_check() is True
    finally:
        await PulsarClient.close()

@pytest.mark.integration
@pytest.mark.asyncio

async def test_circuit_breaker_activation(pulsar_client):
    """Test circuit breaker activation (real Pulsar connection)"""
    # Use the shared pulsar_client fixture for real broker tests

    # Simulate circuit breaker by sending to a non-existent topic or with invalid config
    with pytest.raises(Exception):
        await pulsar_client.send_message("nonexistent_topic", {"key": "value"})
    # todo: Add assertion for circuit breaker state if/when available on the real client

@pytest.mark.integration
@pytest.mark.asyncio

async def test_message_roundtrip(pulsar_client):
    """Test sending and receiving a message"""
    test_topic = f"test-topic-{int(time.time())}"
    test_msg = {"test": "data"}
    
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
        await PulsarClient.admin.delete_topic(test_topic)
        await PulsarClient.close()
