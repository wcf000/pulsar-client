import pytest
from pulsar import Client

@pytest.mark.asyncio
async def test_minimal_pulsar_connection():
    # Try to connect to the broker and close immediately
    url = "pulsar://127.0.0.1:6650"
    try:
        client = Client(url)
        print(f"Connected to Pulsar at {url}")
        client.close()
    except Exception as e:
        pytest.fail(f"Could not connect to Pulsar at {url}: {e}")
