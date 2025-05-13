from unittest.mock import AsyncMock, patch

import pytest

from app.core.pulsar.client import PulsarClient


@pytest.mark.asyncio

async def test_message_metrics_tracking():
    """Test Prometheus metrics collection"""
    with patch("app.core.pulsar.client.PULSAR_MESSAGE_LATENCY") as mock_metrics:
        client = PulsarClient()
        # Patch the underlying _client to prevent real Pulsar network calls
        with patch.object(client, "_client") as mock_client:
            mock_producer = mock_client.create_producer.return_value
            mock_producer.send.return_value = None
            mock_producer.close.return_value = None
            await client.send_message("test_topic", {"key": "value", "topic": "test_topic"})

        # * Check that .labels() and .observe() were called for metrics
        assert mock_metrics.labels.called
        assert mock_metrics.labels().observe.called


@pytest.mark.asyncio

async def test_batch_metrics_tracking():
    """Test batch processing metrics"""
    with (
        patch("app.core.pulsar.client.PULSAR_BATCH_DURATION") as mock_duration,
        patch("app.core.pulsar.client.PULSAR_BATCH_SUCCESS") as mock_success,
        patch(
            "app.core.pulsar.client.PulsarClient._process_message",
            new_callable=AsyncMock,
        ) as mock_process,
    ):
        mock_duration.labels.return_value = mock_duration
        mock_success.labels.return_value = mock_success
        mock_process.return_value = True
        client = PulsarClient()
        messages = [{"key": str(i), "topic": "test_topic"} for i in range(10)]
        await client.batch_process_messages("test_topic", messages)

        assert mock_duration.observe.called
        # * Check that .inc was called (optionally check call args)
        assert mock_success.inc.called
        # Optionally: assert mock_success.inc.call_args == ((10,),)
