"""
Prometheus metrics for Pulsar integration.
Uses standardized metrics for monitoring Pulsar performance and health.
"""
from prometheus_client import Counter, Gauge, Histogram

from app.core.prometheus.metrics import get_metric_registry

# Message counters
pulsar_messages_sent = Counter(
    "pulsar_messages_sent", 
    "Number of Pulsar messages sent", 
    ["topic"],
    registry=get_metric_registry()
)
pulsar_messages_received = Counter(
    "pulsar_messages_received", 
    "Number of Pulsar messages received", 
    ["topic"],
    registry=get_metric_registry()
)
pulsar_errors = Counter(
    "pulsar_errors", 
    "Number of Pulsar errors", 
    ["type"],
    registry=get_metric_registry()
)

# Latency and performance metrics
PULSAR_MESSAGE_LATENCY = Histogram(
    "pulsar_message_latency_seconds", 
    "Pulsar message processing latency", 
    ["topic"],
    registry=get_metric_registry()
)
PULSAR_PRODUCER_LATENCY = Histogram(
    "pulsar_producer_latency_seconds", 
    "Time taken to produce a message to Pulsar", 
    ["topic"],
    registry=get_metric_registry()
)

# Queue metrics
PULSAR_QUEUE_SIZE = Gauge(
    "pulsar_queue_size", 
    "Current size of Pulsar queues", 
    ["topic"],
    registry=get_metric_registry()
)

# Health metrics
PULSAR_HEALTH = Gauge(
    "pulsar_health_status", 
    "Pulsar health status (1=healthy, 0=unhealthy)",
    registry=get_metric_registry()
)

# Producer lag metrics
PULSAR_PRODUCER_LAG = Gauge(
    "pulsar_producer_lag_seconds",
    "Pulsar producer lag (time between message creation and sending)",
    ["topic"],
    registry=get_metric_registry()
)

# Consumer lag metrics - moved from metrics.py
PULSAR_CONSUMER_LAG = Gauge(
    "pulsar_consumer_lag_seconds",
    "Pulsar consumer lag (time between message publish and processing)",
    ["topic", "subscription"],
    registry=get_metric_registry()
)

# Backlog metrics
PULSAR_SUBSCRIPTION_BACKLOG = Gauge(
    "pulsar_subscription_backlog_messages",
    "Number of messages in backlog for a Pulsar subscription",
    ["topic", "subscription"],
    registry=get_metric_registry()
)
