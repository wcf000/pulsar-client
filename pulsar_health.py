"""
Comprehensive health monitoring for Pulsar/Celery with Prometheus integration
"""

import asyncio
import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import JSONResponse
from prometheus_client import CONTENT_TYPE_LATEST, Gauge, generate_latest

from app.core.pulsar.pulsar_client import PulsarClient
from app.core.redis.rate_limit import service_rate_limit

router = APIRouter()
logger = logging.getLogger(__name__)

# Prometheus metrics
PULSAR_HEALTH = Gauge(
    "pulsar_health_status", "Pulsar health status (1=healthy, 0=unhealthy)"
)


class PulsarHealth:
    """
    Health checks for Pulsar including:
    - Connection health
    - Message throughput
    - Error rates
    """

    def __init__(self, client: PulsarClient = None):
        self.client = client or PulsarClient()
        self.last_check = datetime.min
        self.cached_status = None
        self.cache_ttl = timedelta(seconds=30)

    async def check_connection(self) -> bool:
        """Check if we can connect to Pulsar cluster."""
        try:
            # Simple request to verify connectivity
            async with self.client._client as session:
                response = await session.get(
                    f"{self.client._base_url}/admin/v2/clusters"
                )
                response.raise_for_status()
                return True
        except Exception as e:
            logger.error(f"Pulsar connection check failed: {e}")
            return False

    async def check_producer(self, topic: str = "health-check") -> bool:
        """Verify we can produce messages."""
        try:
            test_msg = {"timestamp": datetime.now().isoformat(), "type": "health-check"}
            await self.client.send_message(topic, test_msg)
            return True
        except Exception as e:
            logger.error(f"Pulsar producer check failed: {e}")
            return False

    async def check_consumer(self, topic: str = "health-check") -> bool:
        """Verify we can consume messages (using temporary subscription)."""
        sub_name = f"health-check-{datetime.now().timestamp()}"
        received = False

        try:
            # Send test message
            test_msg = {"timestamp": datetime.now().isoformat(), "type": "health-check"}
            await self.client.send_message(topic, test_msg)

            # Try to consume it
            async def callback(msg):
                nonlocal received
                if msg.get("type") == "health-check":
                    received = True

            # Short timeout for health check
            await asyncio.wait_for(
                self.client.consume_messages(topic, sub_name, callback), timeout=5.0
            )
            return received
        except asyncio.TimeoutError:
            return received
        except Exception as e:
            logger.error(f"Pulsar consumer check failed: {e}")
            return False
        finally:
            # Clean up temporary subscription
            try:
                async with self.client._client as session:
                    await session.delete(
                        f"{self.client._base_url}/admin/v2/persistent/{topic}/subscription/{sub_name}"
                    )
            except Exception:
                pass

    async def get_health_status(self) -> JSONResponse:
        """
        Comprehensive health check combining:
        - Connection
        - Producer
        - Consumer
        """
        if datetime.now() - self.last_check < self.cache_ttl and self.cached_status:
            return self.cached_status

        connection_ok = await self.check_connection()
        producer_ok = await self.check_producer()
        consumer_ok = await self.check_consumer()

        healthy = connection_ok and producer_ok and consumer_ok
        status_code = (
            200 if healthy else 503
        )

        response = JSONResponse(
            status_code=status_code,
            content={
                "healthy": healthy,
                "details": {
                    "connection": connection_ok,
                    "producer": producer_ok,
                    "consumer": consumer_ok,
                },
            },
        )

        self.last_check = datetime.now()
        self.cached_status = response
        return response


pulsar_health = PulsarHealth()


async def check_pulsar_health() -> dict:
    """
    Rate-limited Pulsar health check using service rate limiter
    """
    if not await service_rate_limit(
        key="pulsar_health", limit=2, window=3, endpoint="pulsar_health"
    ):
        raise HTTPException(
            status_code=429, detail="Pulsar health checks limited to 2 per 3 seconds"
        )

    return await pulsar_health.get_health_status()


@router.get("/health/pulsar")
async def pulsar_health():
    """Check Pulsar cluster health"""
    result = await check_pulsar_health()
    PULSAR_HEALTH.set(1)
    return result


@router.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
