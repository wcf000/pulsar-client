"""
Pulsar decorators for common operations.
"""
import functools
import logging
from collections.abc import Callable
from typing import Optional

from app.core.pulsar.config import PulsarConfig

from .client import PulsarClient
from .metrics import PULSAR_MESSAGE_LATENCY, pulsar_errors, pulsar_messages_sent

logger = logging.getLogger(__name__)
client = PulsarClient()  # Async client

def validate_topic_permissions(topic: str, role: str | None) -> None:
    """
    Secure validation for topic access permissions
    
    Args:
        topic: Pulsar topic path
        role: Service role (defaults to config role)
    
    Raises:
        PermissionError: If role lacks required permissions
        ValueError: For invalid topic format
    """
    if not topic or not isinstance(topic, str):
        raise ValueError("Topic must be a non-empty string")
        
    role = role or PulsarConfig.SECURITY.get('service_role')
    allowed_roles = PulsarConfig.SECURITY.get('topic_roles', {}).get(topic, [])
    
    if role not in allowed_roles:
        raise PermissionError(
            f"Role '{role}' not authorized for topic '{topic}'. "
            f"Allowed roles: {allowed_roles}"
        )

def pulsar_task(
    topic: str,
    dlq_topic: str | None = None,
    max_retries: int = 3,
    retry_delay: float = 5.0,
    client: PulsarClient | None = client
):
    """
    Decorator for creating Pulsar tasks from functions.
    
    Args:
        topic: Pulsar topic to publish to (must be non-empty string)
        max_retries: Maximum retry attempts (must be >= 0)
        retry_delay: Initial delay between retries in seconds (must be > 0)
        dlq_topic: Optional Dead Letter Queue topic (must be non-empty string if provided)
    """
    # Input validation
    if not isinstance(topic, str) or not topic.strip():
        raise ValueError("Topic must be a non-empty string")
    if not isinstance(max_retries, int) or max_retries < 0:
        raise ValueError("max_retries must be a non-negative integer")
    if not isinstance(retry_delay, (int, float)) or retry_delay <= 0:
        raise ValueError("retry_delay must be a positive number")
    if dlq_topic is not None and (not isinstance(dlq_topic, str) or not dlq_topic.strip()):
        raise ValueError("DLQ topic must be None or a non-empty string")

    validate_topic_permissions(topic, None)

    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            used_client = client or globals().get('client')
            attempt = 0
            last_exc = None
            while attempt <= max_retries:
                try:
                    result = await func(*args, **kwargs)
                    # Create and send task
                    task = {
                        "function": func.__name__,
                        "args": args,
                        "kwargs": kwargs,
                        "result": result,
                        "topic": topic  # ! Required for PulsarClient strict topic check
                    }
                    await used_client.send_message(topic, task)
                    pulsar_messages_sent.labels(topic=topic).inc()
                    return result
                except Exception as e:
                    attempt += 1
                    last_exc = e
                    pulsar_errors.labels(type=e.__class__.__name__).inc()
                    logger.error(f"Task failed on attempt {attempt}: {e}")
                    if attempt > max_retries:
                        if dlq_topic:
                            await used_client._send_to_dlq(topic, {"args": args, "kwargs": kwargs}, str(e))
                        raise
                    else:
                        import asyncio
                        await asyncio.sleep(retry_delay)
            # Defensive: should never reach here
            if last_exc:
                raise last_exc
        return wrapper
    return decorator


def pulsar_consumer(
    topic: str,
    subscription: str,
    filter_fn: Optional[Callable] = None,
    max_parallelism: int = 10,
    client: PulsarClient | None = None
):
    """
    Decorator for creating Pulsar consumers from functions.
    
    Args:
        topic: Topic to consume from (must be non-empty string)
        subscription: Subscription name (must be non-empty string)
        filter_fn: Optional filter function
        max_parallelism: Maximum concurrent processing tasks (must be > 0)
    """
    # Input validation
    if not isinstance(topic, str) or not topic.strip():
        raise ValueError("Topic must be a non-empty string")
    if not isinstance(subscription, str) or not subscription.strip():
        raise ValueError("Subscription must be a non-empty string")
    if not isinstance(max_parallelism, int) or max_parallelism <= 0:
        raise ValueError("max_parallelism must be a positive integer")

    validate_topic_permissions(topic, None)

    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            used_client = client or globals().get('client')
            with PULSAR_MESSAGE_LATENCY.labels(operation=func.__name__).time():
                return await used_client.batch_consume(
                    topic=topic,
                    subscription=subscription,
                    batch_size=1,
                    callback=func,
                    filter_fn=filter_fn,
                    max_parallelism=max_parallelism
                )
        return wrapper
    return decorator
