"""
Decorators for Pulsar client operations to add metrics collection.
"""
import functools
import time
from typing import Any, Callable, TypeVar, cast

from app.core.pulsar.metrics import (
    pulsar_messages_sent,
    PULSAR_PRODUCER_LAG,
    PULSAR_PRODUCER_LATENCY
)

# Type variable for function return type
T = TypeVar('T')

def track_producer_metrics(topic: str):
    """
    Decorator to track Pulsar producer metrics including:
    - Message count by topic
    - Producer latency
    - Producer lag (time between message creation and sending)
    
    Args:
        topic: The Pulsar topic the message is being sent to
        
    Usage:
        @track_producer_metrics('my-topic')
        async def send_message(message):
            # Your send implementation
            return result
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper_async(*args: Any, **kwargs: Any) -> T:
            # Record metrics
            message = kwargs.get('message', None)
            if not message and len(args) > 1:
                message = args[1]  # Assume second arg is message in most Pulsar client implementations
                
            # Get timestamp if available, or use current time
            message_creation_time = time.time()
            if message and isinstance(message, dict) and 'timestamp' in message:
                message_creation_time = message.get('timestamp', time.time())
                
            # Track start time for latency
            start_time = time.time()
            
            try:
                # Call the original function
                result = await func(*args, **kwargs)
                
                # On success, update metrics
                pulsar_messages_sent.labels(topic).inc()
                
                # Calculate and record latency
                latency = time.time() - start_time
                PULSAR_PRODUCER_LATENCY.labels(topic).observe(latency)
                
                # Calculate and record lag (time from message creation to sending)
                lag = time.time() - message_creation_time
                PULSAR_PRODUCER_LAG.labels(topic).set(lag)
                
                return result
            except Exception:
                # Don't need to track errors here as they're tracked in the client
                raise
                
        # If it's not async, create a sync wrapper
        @functools.wraps(func)
        def wrapper_sync(*args: Any, **kwargs: Any) -> T:
            # Record metrics
            message = kwargs.get('message', None)
            if not message and len(args) > 1:
                message = args[1]  # Assume second arg is message
                
            # Get timestamp if available, or use current time
            message_creation_time = time.time()
            if message and isinstance(message, dict) and 'timestamp' in message:
                message_creation_time = message.get('timestamp', time.time())
                
            # Track start time for latency
            start_time = time.time()
            
            try:
                # Call the original function
                result = func(*args, **kwargs)
                
                # On success, update metrics
                pulsar_messages_sent.labels(topic).inc()
                
                # Calculate and record latency
                latency = time.time() - start_time
                PULSAR_PRODUCER_LATENCY.labels(topic).observe(latency)
                
                # Calculate and record lag
                lag = time.time() - message_creation_time
                PULSAR_PRODUCER_LAG.labels(topic).set(lag)
                
                return result
            except Exception:
                # Don't need to track errors here as they're tracked in the client
                raise
        
        # Use the appropriate wrapper based on whether the function is async or not
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return cast(Callable[..., T], wrapper_async)
        else:
            return wrapper_sync
            
    return decorator
