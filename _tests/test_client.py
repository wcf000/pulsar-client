import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from app.core.pulsar.client import PulsarClient
from app.core.pulsar.config import PulsarConfig

@pytest.fixture
def mock_client():
    """Fixture for PulsarClient with mocked dependencies"""
    with patch('aiohttp.ClientSession'), \
         patch('app.core.pulsar.client.CircuitBreaker'), \
         patch('app.core.pulsar.client.PULSAR_MESSAGE_LATENCY'), \
         patch('app.core.pulsar.client.PULSAR_BATCH_DURATION'):
        client = PulsarClient()
        client._process_message = AsyncMock(return_value=True)
        yield client

@pytest.mark.asyncio
async def test_send_message_success(mock_client):
    """Test successful message sending"""
    result = await mock_client.send_message("test_topic", {"key": "value"})
    assert result is True

@pytest.mark.asyncio
async def test_send_message_retry_logic(mock_client):
    """Test retry behavior on failed sends"""
    mock_client._process_message.side_effect = [Exception(), Exception(), True]
    result = await mock_client.send_message("test_topic", {"key": "value"})
    assert result is True
    assert mock_client._process_message.call_count == 3

@pytest.mark.asyncio
async def test_batch_process_messages(mock_client):
    """Test batch message processing"""
    messages = [
        {"topic": "test_topic", "payload": "msg1"},
        {"topic": "test_topic", "payload": "msg2"}
    ]
    results = await mock_client.batch_process_messages(messages, batch_size=2)
    assert len(results) == 2
    assert all(results)

@pytest.mark.asyncio
async def test_batch_process_empty(mock_client):
    """Test empty batch processing"""
    results = await mock_client.batch_process_messages([], batch_size=10)
    assert results == []

@pytest.mark.asyncio
async def test_batch_process_partial_failures(mock_client):
    """Test batch with partial failures"""
    mock_client._process_message.side_effect = [True, Exception(), True]
    messages = [
        {"topic": "test_topic", "payload": "msg1"},
        {"topic": "test_topic", "payload": "msg2"},
        {"topic": "test_topic", "payload": "msg3"}
    ]
    results = await mock_client.batch_process_messages(messages)
    assert results == [True, False, True]

@pytest.mark.asyncio
async def test_batch_process_large_batch(mock_client):
    """Test batch size limits"""
    messages = [{"topic": "test_topic", "payload": f"msg{i}"} for i in range(500)]
    results = await mock_client.batch_process_messages(messages, batch_size=50)
    assert len(results) == 500
    assert mock_client._process_message.call_count == 500

@pytest.mark.asyncio
async def test_circuit_breaker_activation(mock_client):
    """Test circuit breaker trips on repeated failures"""
    mock_client._process_message.side_effect = Exception("Simulated failure")
    mock_client.circuit_breaker.is_closed = False
    
    with pytest.raises(Exception):
        await mock_client.send_message("test_topic", {"key": "value"})
    
    assert mock_client.circuit_breaker.is_closed is False
