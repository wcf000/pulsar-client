# Pulsar Integration Usage Guide

This guide explains how to use the Pulsar integration in this codebase for distributed task processing, message publishing, and health monitoring. It covers the main modules: `client.py`, `config.py`, `decorators.py`, `health_check.py`, and `index.py`.

---

## 1. Configuration (`config.py`)

- All connection/auth settings are managed via `PulsarConfig`, which reads from `app.core.config.settings` (usually environment variables).
- Producer/consumer options, security (TLS/JWT), and role-based permissions are centrally defined.
- **Best Practice:** Always configure topics, authentication, and roles in `PulsarConfig` before using the client or decorators.

---

## 2. Pulsar Client (`client.py`)

- `PulsarClient` is an async HTTP client for Pulsar with production features:
  - Dead Letter Queue (DLQ) support
  - Message filtering
  - Retry and circuit breaker logic
  - Prometheus metrics for batches, retries, DLQ, processing time
- **Usage Example:**

```python
from app.core.pulsar.client import PulsarClient
client = PulsarClient()
await client.send_message("my-topic", {"msg": "hello"})
```

- **Best Practice:**
  - Use async/await for all client operations.
  - Monitor Prometheus metrics for batch size, retries, and DLQ events.
  - Handle exceptions (e.g., `CircuitBreakerError`).

---

## 3. Decorators (`decorators.py`)

- Use `@pulsar_task` to turn a function into an async Pulsar publisher with built-in retries and DLQ.
- Use `@pulsar_consumer` to process messages from a Pulsar topic, with optional filtering and parallelism.
- Use `validate_topic_permissions` to enforce role-based access on topics.

**Example:**
```python
from app.core.pulsar.decorators import pulsar_task, pulsar_consumer

@pulsar_task(topic="my-topic", max_retries=5, retry_delay=2.0)
async def publish_event(data):
    # ...

@pulsar_consumer(topic="my-topic", subscription="my-sub")
async def handle_event(message):
    # ...
```

- **Best Practice:**
  - Always validate topics and roles before publishing/consuming.
  - Set DLQ topics for critical pipelines.
  - Use filtering to avoid unnecessary processing.

---

## 4. Health Checks (`health_check.py`)

- Provides FastAPI endpoints and Prometheus metrics for Pulsar health:
  - Connection status
  - Producer checks
  - Error rates
- **Usage:**
  - Import and use `PulsarHealth` class or FastAPI router for health endpoints.
  - Metrics are exposed via `/metrics` for Prometheus scraping.

---

## 5. Index (`index.py`)

- Centralizes imports for client, decorators, and metrics for easy access.
- Exports:
  - `PulsarClient`, `pulsar_task`, `pulsar_consumer`, `validate_topic_permissions`, `batch_process_messages`
  - Prometheus metrics: `pulsar_messages_sent`, `pulsar_messages_received`, `pulsar_errors`, etc.
- **Usage:**
  - Import from `app.core.pulsar.index` for most Pulsar operations and metrics.

---

## 6. Monitoring & Metrics

- Prometheus metrics are provided for all major operations (sent/received, DLQ, retries, latency, queue size).
- **Best Practice:**
  - Set up Prometheus scraping on the `/metrics` endpoint.
  - Use Grafana dashboards to monitor Pulsar pipeline health.

---

## 7. Additional Best Practices

- Configure all roles and permissions in `PulsarConfig`.
- Use async patterns throughout for performance.
- Set DLQ topics for all critical consumers.
- Monitor metrics and logs for error spikes and retry storms.
- Use health checks in deployment pipelines.
- See `best_practices/` for advanced patterns, failover, and schema management.

---

For more advanced topics, troubleshooting, and production tips, see the `best_practices/` directory in this folder.
