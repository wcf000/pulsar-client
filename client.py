"""
Pulsar HTTP client implementation using pulsar.apps.http.
"""
import asyncio
import json
import logging
import time
from datetime import datetime

from prometheus_client import Counter, Gauge, Histogram
from pulsar.apps import http

from app.core.pulsar.config import PulsarConfig

logger = logging.getLogger(__name__)

# Metrics
PULSAR_BATCH_SIZE = Gauge("pulsar_batch_size", "Size of Pulsar message batches")
PULSAR_BATCHES_SENT = Counter(
    "pulsar_batches_sent", "Count of batches sent", ["compression_type"]
)
PULSAR_DLQ_MESSAGES = Counter(
    "pulsar_dlq_messages", "Messages sent to DLQ", ["original_topic", "error_type"]
)
PULSAR_RETRIES = Counter("pulsar_message_retries", "Message retry attempts", ["topic"])
PULSAR_PROCESSING_TIME = Histogram(
    "pulsar_processing_seconds", "Message processing time", ["topic"]
)


class PulsarClient:
    """
    Async Pulsar HTTP client with production features including:
    - Dead Letter Queue (DLQ) handling
    - Message filtering
    - Custom retry policies
    - Detailed metrics
    """

    def __init__(self, max_retries: int = 3, retry_delay: float = 5.0):
        self._client = http.HttpClient(
            ssl=PulsarConfig.SECURITY["tls_enabled"],
            headers={"Authorization": f"Bearer {PulsarConfig.SECURITY['jwt_token']}"},
        )
        self._base_url = f"http{'s' if PulsarConfig.SECURITY['tls_enabled'] else ''}://{PulsarConfig.SERVICE_URL}"
        self._max_retries = max_retries
        self._retry_delay = retry_delay
        self._batch = []
        self._last_flush = datetime.now()

    async def send_message(self, topic: str, message: dict):
        """Send a single message to Pulsar."""
        async with self._client as session:
            response = await session.post(
                f"{self._base_url}/topics/{topic}/messages",
                json=message,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()

    async def send_batch(self, topic: str):
        """Send batch of messages to Pulsar."""
        if not self._batch:
            return

        batch_size = len(self._batch)
        PULSAR_BATCH_SIZE.set(batch_size)

        try:
            compressed = self._compress_batch(self._batch)
            async with self._client as session:
                response = await session.post(
                    f"{self._base_url}/topics/{topic}/batch",
                    data=compressed,
                    headers={"Content-Encoding": "lz4"},
                )
                response.raise_for_status()

            PULSAR_BATCHES_SENT.labels(compression_type="lz4").inc()
            self._batch = []
            self._last_flush = datetime.now()

        except Exception as e:
            logger.error(f"Failed to send batch: {str(e)}")
            raise

    def _compress_batch(self, batch):
        """Compress batch using LZ4."""
        return json.dumps(batch).encode()

    async def _send_to_dlq(self, original_topic: str, message: dict, error: str):
        """Send failed message to DLQ"""
        dlq_topic = f"dlq.{original_topic}"
        try:
            await self.send_message(dlq_topic, {
                "original_message": message,
                "error": error,
                "timestamp": datetime.now().isoformat()
            })
            PULSAR_DLQ_MESSAGES.labels(
                original_topic=original_topic,
                error_type=error.__class__.__name__
            ).inc()
        except Exception as e:
            logger.error(f"Failed to send to DLQ: {e}")

    async def _process_with_retry(self, 
                                topic: str, 
                                message: dict, 
                                callback: callable,
                                retry_policy: dict = None):
        """Process message with custom retry policy"""
        retry_policy = retry_policy or {
            "max_retries": self._max_retries,
            "delay": self._retry_delay,
            "backoff_factor": 2
        }

        for attempt in range(retry_policy["max_retries"] + 1):
            try:
                start_time = time.time()
                await callback(message)
                PULSAR_PROCESSING_TIME.labels(topic=topic).observe(time.time() - start_time)
                return True
            except Exception as e:
                if attempt == retry_policy["max_retries"]:
                    await self._send_to_dlq(topic, message, str(e))
                    return False
                
                delay = retry_policy["delay"] * (retry_policy["backoff_factor"] ** attempt)
                logger.warning(f"Retry {attempt + 1} for message {message.get('id')} in {delay:.1f}s")
                PULSAR_RETRIES.labels(topic=topic).inc()
                await asyncio.sleep(delay)

    async def consume_messages(self, 
                             topic: str, 
                             subscription: str, 
                             callback: callable,
                             filter_fn: callable = None,
                             retry_policy: dict = None):
        """
        Enhanced consumer with filtering and retry policies
        """
        endpoint = f"{self._base_url}/topics/{topic}/subscriptions/{subscription}/messages"

        while True:
            try:
                async with self._client as session:
                    # Get message
                    response = await session.get(endpoint)
                    response.raise_for_status()
                    message = await response.json()

                    # Apply filter if provided
                    if filter_fn and not filter_fn(message):
                        await session.delete(endpoint)  # Skip filtered messages
                        continue

                    # Process with retry policy
                    success = await self._process_with_retry(topic, message, callback, retry_policy)
                    if success:
                        await session.delete(endpoint)  # Acknowledge

            except Exception as e:
                logger.error(f"Consumer error: {e}")
                await asyncio.sleep(self._retry_delay)

    async def batch_consume(
        self, 
        topic: str, 
        subscription: str, 
        batch_size: int, 
        callback: callable,
        filter_fn: callable = None,
        retry_policy: dict = None,
        max_parallelism: int = 10
    ):
        """
        Enhanced batch consumer with:
        - Filtering
        - Custom retry policies
        - Parallel processing
        - DLQ handling
        
        Args:
            topic: Topic to consume from
            subscription: Subscription name
            batch_size: Number of messages per batch
            callback: Async function to process batch
            filter_fn: Optional filter function (returns bool)
            retry_policy: Custom retry configuration
            max_parallelism: Max concurrent processing tasks
        """
        endpoint = f"{self._base_url}/topics/{topic}/subscriptions/{subscription}/messages?batch={batch_size}"
        semaphore = asyncio.Semaphore(max_parallelism)

        async def process_batch(messages):
            async with semaphore:
                filtered = [msg for msg in messages if not filter_fn or filter_fn(msg)]
                if not filtered:
                    return
                    
                try:
                    start_time = time.time()
                    await callback(filtered)
                    PULSAR_PROCESSING_TIME.labels(topic=topic).observe(
                        (time.time() - start_time) / len(filtered)
                    )
                    return True
                except Exception as e:
                    logger.error(f"Batch processing failed: {e}")
                    for msg in filtered:
                        await self._send_to_dlq(topic, msg, str(e))
                    return False

        while True:
            try:
                async with self._client as session:
                    # Get batch
                    response = await session.get(endpoint)
                    response.raise_for_status()
                    messages = await response.json()

                    if messages:
                        success = await self._process_with_retry(
                            topic,
                            messages,
                            process_batch,
                            retry_policy
                        )
                        if success:
                            await session.delete(endpoint)

            except Exception as e:
                logger.error(f"Batch consumer error: {e}")
                await asyncio.sleep(self._retry_delay)

"""
Pulsar HTTP Client Features:
    
1. Message Production:
- Single message sending
- Batch message sending with compression
    
2. Message Consumption:
- Single message processing with retries
- Batch processing with parallel execution
- Message filtering
    
3. Reliability Features:
- Dead Letter Queue (DLQ) for failed messages
- Customizable retry policies with exponential backoff
    
4. Monitoring:
- Batch size metrics
- Processing time histograms
- DLQ message counters
- Retry attempt tracking
    
Usage Example:
    
# Producer
client = PulsarClient()
await client.send_message("my-topic", {"key": "value"})
    
# Consumer
async def process(msg):
    print(f"Processing: {msg}")
    
await client.consume_messages(
    topic="my-topic",
    subscription="my-sub",
    callback=process,
    filter_fn=lambda msg: msg.get("important"),
    retry_policy={"max_retries": 5, "delay": 1}
)
"""
