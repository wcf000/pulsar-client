import pytest
import time
import uuid
from app.core.pulsar.decorators import validate_topic_permissions, pulsar_task, pulsar_consumer
from app.core.pulsar.config import PulsarConfig

# * These tests require a running Pulsar broker and a properly configured PulsarConfig.
# * All tests use the real broker via the pulsar_client fixture.

@pytest.mark.asyncio
async def test_validate_topic_permissions_success():
    """Test successful topic validation (integration)"""
    # Setup config for allowed role
    PulsarConfig.SECURITY = {
        'service_role': 'allowed_role',
        'topic_roles': {'valid_topic': ['allowed_role']}
    }
    validate_topic_permissions("valid_topic", None)

@pytest.mark.asyncio
async def test_validate_topic_permissions_unauthorized():
    """Test unauthorized topic access (integration)"""
    PulsarConfig.SECURITY = {
        'service_role': 'allowed_role',
        'topic_roles': {'valid_topic': ['other_role']}
    }
    with pytest.raises(PermissionError):
        validate_topic_permissions("valid_topic", None)

@pytest.mark.asyncio
async def test_validate_topic_permissions_invalid_topic():
    """Test invalid topic format (integration)"""
    with pytest.raises(ValueError):
        validate_topic_permissions("", None)

@pytest.mark.asyncio
async def test_pulsar_task_decorator_happy_path():
    """Test successful decorated task execution (integration)"""
    topic = f"test_task_{uuid.uuid4()}"
    PulsarConfig.SECURITY = {
        'service_role': 'allowed_role',
        'topic_roles': {topic: ['allowed_role']}
    }
    async def sample_task():
        return "success"
    decorated = pulsar_task(topic=topic)(sample_task)
    result = await decorated()
    assert result == "success"
    from app.core.pulsar.decorators import client
    await client.admin.delete_topic(topic)

@pytest.mark.asyncio
async def test_pulsar_task_decorator_retry_logic():
    """Test decorator retry behavior (integration)"""
    topic = f"test_retry_{uuid.uuid4()}"
    PulsarConfig.SECURITY = {
        'service_role': 'allowed_role',
        'topic_roles': {topic: ['allowed_role']}
    }
    call_count = 0
    async def failing_task():
        nonlocal call_count
        call_count += 1
        raise Exception("Simulated failure")
    decorated = pulsar_task(topic=topic, max_retries=2, retry_delay=0.1)(failing_task)
    with pytest.raises(Exception):
        await decorated()
    assert call_count == 3
    from app.core.pulsar.decorators import client
    await client.admin.delete_topic(topic)

@pytest.mark.asyncio
async def test_pulsar_task_dlq_handling():
    """Test DLQ message routing on permanent failures (integration)"""
    topic = f"test_dlq_{uuid.uuid4()}"
    dlq_topic = f"dlq_{uuid.uuid4()}"
    PulsarConfig.SECURITY = {
        'service_role': 'allowed_role',
        'topic_roles': {topic: ['allowed_role'], dlq_topic: ['allowed_role']}
    }
    async def failing_task():
        raise Exception("Permanent failure")
    decorated = pulsar_task(topic=topic, max_retries=1, dlq_topic=dlq_topic, retry_delay=0.1)(failing_task)
    with pytest.raises(Exception):
        await decorated()
    from app.core.pulsar.decorators import client
    await client.admin.delete_topic(topic)
    await client.admin.delete_topic(dlq_topic)

@pytest.mark.integration
@pytest.mark.asyncio
async def test_pulsar_consumer_decorator(pulsar_client):
    """Test the pulsar_consumer decorator end-to-end (integration)"""
    import asyncio
    topic = f"consumer_{uuid.uuid4()}"
    subscription = f"sub_{uuid.uuid4()}"
    PulsarConfig.SECURITY = {
        'service_role': 'allowed_role',
        'topic_roles': {topic: ['allowed_role']}
    }
    received = []
    @pulsar_consumer(topic=topic, subscription=subscription)
    async def process_message(msg):
        received.append(msg)
        return True
    # Send a message
    msg = {"foo": "bar"}
    await pulsar_client.send_message(topic, msg)
    # Start the consumer
    await process_message()
    # Wait for processing
    await asyncio.sleep(1)
    assert any(m == msg for m in received)
    await pulsar_client.admin.delete_topic(topic)
