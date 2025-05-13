"""
Pulsar integration for distributed task processing with enhanced utilities.
"""

import logging
from uuid import uuid4

from .client import PulsarClient
from .decorators import pulsar_consumer, pulsar_task, validate_topic_permissions

__all__ = [
    'PulsarClient',
    'pulsar_task',
    'pulsar_consumer',
    'validate_topic_permissions'
]

logger = logging.getLogger(__name__)

# Initialize the Pulsar client
client = PulsarClient()

# Task state constants
PENDING = "PENDING"
PROGRESS = "PROGRESS"
COMPLETED = "COMPLETED"
FAILED = "FAILED"


# Expose only implemented PulsarClient methods for production use
shutdown_client = client.close
send_message = client.send_message
send_batch = client.send_batch
consume_messages = client.consume_messages
batch_consume = client.batch_consume
batch_process_messages = client.batch_process_messages
wait_for_task_completion = client.wait_for_task_completion

# Expose decorators
pulsar_task = pulsar_task
pulsar_consumer = pulsar_consumer
