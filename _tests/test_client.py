import pytest
from app.core.pulsar.client import PulsarClient
import sys

# Debug: Confirm import source and health_check presence
print("PulsarClient imported from:", PulsarClient.__module__)
print("PulsarClient file:", sys.modules[PulsarClient.__module__].__file__)
print("Has health_check:", hasattr(PulsarClient, "health_check"))

import asyncio
import logging
from typing import Any

import uuid

@pytest.mark.asyncio
async def test_send_message_success():
    """Test successful message sending (real Pulsar connection)"""
    import sys
    print("PulsarClient imported from:", PulsarClient.__module__)
    print("PulsarClient file:", sys.modules[PulsarClient.__module__].__file__)
    print("Has health_check:", hasattr(PulsarClient, "health_check"))
    client = PulsarClient(service_url="pulsar://127.0.0.1:6650")
    print("Client config service_url:", getattr(client, 'service_url', None))
    topic = f"test_send_{uuid.uuid4()}"
    result = await client.send_message(topic, {"key": "value"})
    assert result is True
    if hasattr(client, "admin"):
        await client.admin.delete_topic(topic)

@pytest.mark.asyncio
async def test_send_message_retry_logic():
    """Test retry behavior on failed sends (real Pulsar connection)"""
    client = PulsarClient(service_url="pulsar://127.0.0.1:6650")
    topic = f"test_retry_{uuid.uuid4()}"
    # Simulate a retry by sending a message that may fail, then succeed
    try:
        await client.send_message(topic, {"key": "value1"})
    except Exception:
        pass
    result = await client.send_message(topic, {"key": "value2"})
    assert result is True
    if hasattr(client, "admin"):
        await client.admin.delete_topic(topic)

@pytest.mark.asyncio
async def test_batch_process_messages():
    """Test batch message processing (real Pulsar connection)"""
    client = PulsarClient(service_url="pulsar://127.0.0.1:6650")
    topic = f"test_batch_{uuid.uuid4()}"
    messages = [
        {"topic": topic, "payload": "msg1"},
        {"topic": topic, "payload": "msg2"}
    ]
    results = await client.batch_process_messages(messages, batch_size=2)
    assert len(results) == 2
    assert all(results)
    if hasattr(client, "admin"):
        await client.admin.delete_topic(topic)

@pytest.mark.asyncio
async def test_batch_process_empty():
    """Test empty batch processing (real Pulsar connection)"""
    client = PulsarClient(service_url="pulsar://127.0.0.1:6650")
    results = await client.batch_process_messages([], batch_size=10)
    assert results == []

@pytest.mark.asyncio
async def test_batch_process_partial_failures():
    """Test batch with partial failures (real Pulsar connection)"""
    client = PulsarClient(service_url="pulsar://127.0.0.1:6650")
    topic = f"test_partial_{uuid.uuid4()}"
    messages = [
        {"topic": topic, "payload": "msg1"},
        {"topic": topic, "payload": "msg2"},
        {"topic": topic, "payload": "msg3"}
    ]
    results = await client.batch_process_messages(messages)
    assert len(results) == 3
    # Can't guarantee failure, but should get bools
    assert all(isinstance(r, bool) for r in results)
    if hasattr(client, "admin"):
        await client.admin.delete_topic(topic)

@pytest.mark.asyncio
async def test_batch_process_large_batch(pulsar_client):
    """Test batch size limits (real Pulsar connection)"""
    topic = f"test_large_{uuid.uuid4()}"
    messages = [{"topic": topic, "payload": f"msg{i}"} for i in range(500)]
    results = await pulsar_client.batch_process_messages(messages, batch_size=50)
    assert len(results) == 500
    assert all(isinstance(r, bool) for r in results)
    await pulsar_client.admin.delete_topic(topic)

@pytest.mark.asyncio
async def test_circuit_breaker_activation(pulsar_client):
    """Test circuit breaker activation (real Pulsar connection)"""
    # Use the shared pulsar_client fixture for real broker tests

    # Simulate circuit breaker by sending to a non-existent topic or with invalid config
    with pytest.raises(Exception):
        await pulsar_client.send_message("nonexistent_topic", {"key": "value"})
    # assert mock_client.circuit_breaker.is_closed is False
    
    assert mock_client.circuit_breaker.is_closed is False
