import asyncio
from datetime import timedelta

import pytest

from app.core.pulsar.client import PulsarClient


@pytest.mark.asyncio
async def test_wait_for_task_completion_success(monkeypatch):
    client = PulsarClient()
    # Simulate get_task_status side effects: 2 pending then completed
    statuses = [
        {"state": client.PENDING},
        {"state": client.PROGRESS},
        {"state": client.COMPLETED},
    ]
    calls = []
    async def fake_get(task_id):
        calls.append(1)
        return statuses[len(calls) - 1]
    monkeypatch.setattr(client, 'get_task_status', fake_get)

    received = []
    async def progress_cb(status):
        received.append(status)

    result = await client.wait_for_task_completion(
        task_id="abc", timeout=5, poll_interval=0.01, progress_callback=progress_cb
    )
    assert result == statuses[-1]
    assert received == statuses

@pytest.mark.asyncio
async def test_wait_for_task_completion_timeout(monkeypatch):
    client = PulsarClient()
    # Always return PENDING
    async def always_pending(task_id):
        return {"state": client.PENDING}
    monkeypatch.setattr(client, 'get_task_status', always_pending)

    with pytest.raises(asyncio.TimeoutError):
        await client.wait_for_task_completion(
            task_id="xyz", timeout=0.05, poll_interval=0.01
        )

@pytest.mark.asyncio
async def test_progress_callback_exception(monkeypatch):
    client = PulsarClient()
    # Return completed immediately
    async def complete(task_id):
        return {"state": client.COMPLETED}
    monkeypatch.setattr(client, 'get_task_status', complete)

    called = False
    def bad_cb(status):
        nonlocal called
        called = True
        raise ValueError("oops")

    result = await client.wait_for_task_completion(
        task_id="123", timeout=1, poll_interval=0.01, progress_callback=bad_cb
    )
    assert result["state"] == client.COMPLETED
    assert called
