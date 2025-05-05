# Pulsar Production Implementation Guide

## Decorator Usage Examples

### Producer Decorator
```python
@pulsar_task(
    topic="user_updates",
    max_retries=3,
    retry_delay=5.0,
    dlq_topic="user_updates_dlq"
)
async def update_user(user_id: int, data: dict):
    """
    Example producer that validates inputs before processing
    """
    if not isinstance(user_id, int) or user_id <= 0:
        raise ValueError("user_id must be positive integer")
    
    # Business logic here
    return {"status": "success", "user_id": user_id}
```

### Consumer Decorator
```python
@pulsar_consumer(
    topic="user_updates",
    subscription="user_service",
    max_parallelism=5
)
async def process_user_update(message: dict):
    """
    Example consumer with automatic metrics and error handling
    """
    user_id = message.get('user_id')
    if not user_id:
        raise ValueError("Missing user_id in message")
    
    # Process update
    print(f"Processing update for user {user_id}")
```

### Error Handling
Both decorators automatically:
- Track success/failure metrics
- Handle retries according to configuration
- Send failed messages to DLQ when configured
- Log all errors with context

### Circuit Breaker Implementation

The Pulsar client uses the `circuitbreaker` library to prevent cascading failures:

### Configuration
```python
# Default settings (can be overridden):
CB_FAILURE_THRESHOLD = 5  # Consecutive failures before opening circuit
CB_RECOVERY_TIMEOUT = 30  # Seconds in open state before half-open
CB_EXPECTED_EXCEPTION = (ConnectionError, TimeoutError)  # Triggers circuit
```

### Behavior
1. **Closed State**: Normal operation
2. **Open State**: Fails fast after threshold reached
3. **Half-Open**: Allows one test request after timeout
4. **Metrics**: All state changes are logged and metered

### Monitoring
Key metrics to watch:
- `circuit_breaker_state` (0=closed, 1=half-open, 2=open)
- `circuit_breaker_failures` (count of consecutive failures)

### Performance Tips
1. Use appropriate `max_parallelism` for consumers
2. Set reasonable `retry_delay` to avoid tight loops
3. Monitor Prometheus metrics for:
   - `pulsar_messages_sent`
   - `pulsar_errors`
   - `pulsar_message_latency_seconds`
