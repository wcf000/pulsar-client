"""
Pulsar integration for distributed task processing with enhanced utilities.
"""

import logging
from uuid import uuid4

from prometheus_client import Counter, Gauge, Histogram

from .client import (
    PulsarClient,
    batch_process_messages
)
from .decorators import (
    pulsar_task,
    pulsar_consumer,
    validate_topic_permissions
)

__all__ = [
    'PulsarClient',
    'pulsar_task',
    'pulsar_consumer',
    'batch_process_messages',
    'validate_topic_permissions'
]

logger = logging.getLogger(__name__)

# Initialize the Pulsar client
client = PulsarClient()

# Prometheus metrics
pulsar_messages_sent = Counter(
    "pulsar_messages_sent", "Number of Pulsar messages sent", ["topic"]
)

pulsar_messages_received = Counter(
    "pulsar_messages_received", "Number of Pulsar messages received", ["topic"]
)

pulsar_errors = Counter("pulsar_errors", "Number of Pulsar errors", ["type"])

PULSAR_MESSAGE_LATENCY = Histogram(
    "pulsar_message_latency_seconds", "Pulsar message processing latency", ["operation"]
)

PULSAR_QUEUE_SIZE = Gauge(
    "pulsar_queue_size", "Current size of Pulsar queues", ["topic"]
)

# Task state constants
PENDING = "PENDING"
PROGRESS = "PROGRESS"
COMPLETED = "COMPLETED"
FAILED = "FAILED"


# Expose client methods as module-level functions for backward compatibility
get_client = client.get_client
shutdown_client = client.shutdown
create_producer = client.create_producer
create_consumer = client.create_consumer
send_message = client.send_message
receive_messages = client.receive_messages
create_pulsar_task = client.create_pulsar_task
get_task_status = client.get_task_status
wait_for_task_completion = client.wait_for_task_completion
track_batch_tasks = client.track_batch_tasks
configure_task_retries = client.configure_task_retries
get_queue_stats = client.get_queue_stats
log_task_event = client.log_task_event

# Expose decorators
pulsar_task = pulsar_task
pulsar_consumer = pulsar_consumer
