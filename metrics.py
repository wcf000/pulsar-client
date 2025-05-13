"""
Prometheus metrics for Pulsar integration.
"""
from prometheus_client import Counter, Gauge, Histogram

pulsar_messages_sent = Counter(
    "pulsar_messages_sent", "Number of Pulsar messages sent", ["topic"]
)
pulsar_messages_received = Counter(
    "pulsar_messages_received", "Number of Pulsar messages received", ["topic"]
)
pulsar_errors = Counter(
    "pulsar_errors", "Number of Pulsar errors", ["type"]
)

PULSAR_MESSAGE_LATENCY = Histogram(
    "pulsar_message_latency_seconds", "Pulsar message processing latency", ["topic"]
)
PULSAR_QUEUE_SIZE = Gauge(
    "pulsar_queue_size", "Current size of Pulsar queues", ["topic"]
)
PULSAR_HEALTH = Gauge(
    "pulsar_health_status", "Pulsar health status (1=healthy, 0=unhealthy)"
)
# Add any other metric definitions here as needed
