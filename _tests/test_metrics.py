from unittest.mock import AsyncMock, patch

import pytest

from app.core.pulsar.client import PulsarClient


@pytest.mark.asyncio

async def test_message_metrics_tracking():
    """Test Prometheus metrics collection"""
    with (
        patch("app.core.pulsar.client.PULSAR_MESSAGE_LATENCY") as mock_metrics,
        patch(
            "app.core.pulsar.client.PulsarClient._process_message",
            new_callable=AsyncMock,
        ) as mock_process,
    ):
        mock_process.return_value = True
        client = PulsarClient()
        await client.send_message("test_topic", {"key": "value"})

        assert mock_metrics.labels.called
        assert mock_metrics.observe.called


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
        mock_process.return_value = True
        client = PulsarClient()
        messages = [{"topic": "test_topic"} for _ in range(10)]
        await client.batch_process_messages(messages)

        assert mock_duration.observe.called
        assert mock_success.inc.called_with(10)
