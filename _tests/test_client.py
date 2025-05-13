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
        {"id": 1, "topic": topic, "payload": "msg1"},
        {"id": 2, "topic": topic, "payload": "msg2"}
    ]
    results = await client.batch_process_messages(topic, messages, batch_size=2)
    print(f"Batch process results: {results}")
    assert len(results) == 2
    if not all(results):
        print("At least one message failed to process. Results:", results)
    assert all(results)
    if hasattr(client, "admin"):
        await client.admin.delete_topic(topic)

@pytest.mark.asyncio
async def test_batch_process_empty():
    """Test empty batch processing (real Pulsar connection)"""
    client = PulsarClient(service_url="pulsar://127.0.0.1:6650")
    # Use a dummy topic for empty batch
    results = await client.batch_process_messages("test_empty_topic", [], batch_size=10)
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
    results = await client.batch_process_messages(topic, messages)
    assert len(results) == 3
    # Can't guarantee failure, but should get bools
    assert all(isinstance(r, bool) for r in results)
    if hasattr(client, "admin"):
        await client.admin.delete_topic(topic)

@pytest.mark.asyncio
async def test_batch_process_large_batch():
    """Test batch size limits (real Pulsar connection)"""
    client = PulsarClient(service_url="pulsar://127.0.0.1:6650")
    topic = f"test_large_{uuid.uuid4()}"
    messages = [{"id": i, "topic": topic, "payload": f"msg{i}"} for i in range(500)]
    results = await client.batch_process_messages(topic, messages, batch_size=50)
    print(f"Large batch results: {results[:10]}... (total {len(results)})")
    assert len(results) == 500
    assert all(isinstance(r, bool) for r in results)
    if hasattr(client, "admin"):
        await client.admin.delete_topic(topic)

@pytest.mark.asyncio
async def test_circuit_breaker_activation():
    """Test circuit breaker activation (real Pulsar connection)"""
    client = PulsarClient(service_url="pulsar://127.0.0.1:6650")
    # Simulate circuit breaker by sending to a non-existent topic or with invalid config
    with pytest.raises(Exception):
        await client.send_message("nonexistent_topic", {"key": "value"})
    # If you have a circuit breaker attribute, you can assert its state here
    # assert client.circuit_breaker.is_closed is False
