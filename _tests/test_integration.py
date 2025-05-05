import asyncio
import time

import pytest

from app.core.pulsar.client import PulsarClient
from app.core.pulsar.config import PulsarConfig


@pytest.mark.integration
@pytest.mark.asyncio
async def test_real_pulsar_connection():
    """Verify we can connect to the configured Pulsar instance"""
    client = PulsarClient()
    try:
        # Test basic connectivity
        assert await client.health_check() is True
    finally:
        await client.close()

@pytest.mark.integration
@pytest.mark.asyncio
async def test_message_roundtrip():
    """Test sending and receiving a message"""
    test_topic = f"test-topic-{int(time.time())}"
    test_msg = {"test": "data"}
    
    client = PulsarClient()
    try:
        # Send message
        assert await client.send_message(test_topic, test_msg) is True
        
        # Receive message
        received = []
        
        async def processor(msg):
            received.append(msg)
            return True
            
        consumer = await client.create_consumer(
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
        await client.admin.delete_topic(test_topic)
        await client.close()
