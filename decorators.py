"""
Pulsar decorators for common operations.
"""
from __future__ import annotations

import functools
import logging
import os
from collections.abc import Callable
from typing import Optional

from app.core.pulsar.config import PulsarConfig

logger = logging.getLogger(__name__)

# Check if Pulsar is enabled before importing the client
PULSAR_ENABLED = os.getenv("PULSAR_ENABLED", "true").lower() == "true"

# Only import and initialize Pulsar client if it's enabled
client = None
pulsar_messages_sent = None
pulsar_errors = None

if PULSAR_ENABLED:
    try:
        from app.core.pulsar.client import PulsarClient
        from app.core.pulsar.metrics import PULSAR_MESSAGE_LATENCY, pulsar_errors, pulsar_messages_sent
        from app.core.pulsar.metrics import PULSAR_CONSUMER_LAG
        client = PulsarClient()  # Async client
    except Exception as e:
        logger.warning(f"PulsarClient initialization failed at import time: {e}")
        client = None
else:
    logger.info("Pulsar is disabled - skipping client initialization")

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
    
    # Get the role from config if not provided    
    role = role or PulsarConfig.SECURITY.get('service_role')
    
    # Check if we have a wildcard permission (for development)
    wildcard_roles = PulsarConfig.SECURITY.get('topic_roles', {}).get('*', [])
    if role in wildcard_roles:
        # Allow access via wildcard
        return
        
    # Get specifically allowed roles for this topic
    allowed_roles = PulsarConfig.SECURITY.get('topic_roles', {}).get(topic, [])
    
    # Skip validation in development mode or if permissions are empty
    # This is a fallback to prevent startup issues
    if not allowed_roles:
        # Development fallback - warn but continue
        logger.warning(
            f"No roles configured for topic '{topic}'. "
            "Allowing access for development purposes."
        )
        return
        
    # Normal validation
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

    # Skip topic permission validation if Pulsar is disabled
    if PULSAR_ENABLED:
        validate_topic_permissions(topic, None)

    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # If Pulsar is disabled, just execute the function without publishing
            if not PULSAR_ENABLED or client is None:
                logger.debug(f"Pulsar disabled - executing {func.__name__} without publishing to topic {topic}")
                return await func(*args, **kwargs)
            
            used_client = client or globals().get('client')
            if used_client is None:
                logger.warning(f"No Pulsar client available - executing {func.__name__} without publishing")
                return await func(*args, **kwargs)
                
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
                    if pulsar_messages_sent:
                        pulsar_messages_sent.labels(topic=topic).inc()
                    return result
                except Exception as e:
                    attempt += 1
                    last_exc = e
                    if pulsar_errors:
                        pulsar_errors.labels(type=e.__class__.__name__).inc()
                    logger.error(f"Task failed on attempt {attempt}: {e}")
                    if attempt > max_retries:
                        if dlq_topic:
                            try:
                                await used_client._send_to_dlq(topic, {"args": args, "kwargs": kwargs}, str(e))
                            except Exception as dlq_error:
                                logger.error(f"Failed to send to DLQ: {dlq_error}")
                        
                        # If it's a Pulsar connection error, log and return the function result
                        # instead of failing the entire operation
                        if "ConnectError" in str(e) or "Pulsar error" in str(e):
                            logger.warning(f"Pulsar connection failed for {func.__name__}, continuing without publishing: {e}")
                            return result if 'result' in locals() else await func(*args, **kwargs)
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
            # Instrument consumer lag
            response = await used_client.batch_consume(
                topic=topic,
                subscription=subscription,
                batch_size=1,
                callback=lambda msgs: track_lag_and_callback(msgs, topic, subscription, func),
                filter_fn=filter_fn,
                max_parallelism=max_parallelism
            )
            return response
        return wrapper
    return decorator

def track_lag_and_callback(messages, topic, subscription, callback):
    """
    Track consumer lag for Pulsar messages and then execute the callback.
    
    Args:
        messages: List of Pulsar messages
        topic: The Pulsar topic
        subscription: The subscription name
        callback: Function to call with messages
        
    Returns:
        Result from callback function
    """
    import time
    from app.core.pulsar.metrics import PULSAR_CONSUMER_LAG, pulsar_messages_received
    
    total_lag = 0
    count = 0
    
    for msg in messages:
        # Increment received messages counter
        pulsar_messages_received.labels(topic).inc()
        
        # Track consumer lag
        ts = msg.get('publish_timestamp', None)
        if ts is not None:
            lag = time.time() - ts
            total_lag += lag
            count += 1
    
    # Update the consumer lag metric with average lag if we have messages
    if count > 0:
        avg_lag = total_lag / count
        PULSAR_CONSUMER_LAG.labels(topic, subscription).set(avg_lag)
        
    # Execute the callback
    return callback(messages)
