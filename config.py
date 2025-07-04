"""
Pulsar client configuration with production-ready settings.
"""

from app.core.config import settings
import logging

# Set up logger for debugging Pulsar connections
logger = logging.getLogger(__name__)


import os
import sys

class PulsarConfig:
    """
    Configuration for Pulsar client with production settings.
    Gets values from environment variables via settings.
    """

    # Connection settings
    # * Use localhost:6650 for integration tests if env var is set or running under pytest
    # TODO: STREAMNATIVE - Update SERVICE_URL to use StreamNative cluster endpoint
    # Example: "pulsar+ssl://your-cluster.streamnative.cloud:6651"
    _test_localhost = os.getenv("PULSAR_TEST_LOCALHOST") == "1" or "pytest" in sys.modules
    if _test_localhost:
        SERVICE_URL = "pulsar://127.0.0.1:6650"
        SERVICE_URLS = ["pulsar://127.0.0.1:6650"]
        print("🔧 Pulsar Config: Using localhost for testing")
    else:
        # TODO: STREAMNATIVE - Replace with your StreamNative cluster URL
        # SERVICE_URL = "pulsar+ssl://your-cluster.streamnative.cloud:6651"
        SERVICE_URL = f"pulsar+ssl://{settings.pulsar.PULSAR_ADVERTISED_ADDRESS}:{settings.pulsar.PULSAR_BROKER_PORT}"
        SERVICE_URLS = [SERVICE_URL]
        print(f"🔧 Pulsar Config: Using StreamNative cluster: {SERVICE_URL}")
        print(f"🔧 Pulsar Config: Advertised Address: {settings.pulsar.PULSAR_ADVERTISED_ADDRESS}")
        print(f"🔧 Pulsar Config: Broker Port: {settings.pulsar.PULSAR_BROKER_PORT}")
        print("🔧 Pulsar Config: TLS Enabled: True")
        print(f"🔧 Pulsar Config: Auth Token Length: {len(settings.pulsar.PULSAR_AUTH_TOKEN) if settings.pulsar.PULSAR_AUTH_TOKEN else 0} chars")

    # Authentication
    # TODO: STREAMNATIVE - Enable TLS and configure authentication for StreamNative
    # StreamNative requires TLS and token-based authentication
    AUTHENTICATION = {
        "tls": {
            "enabled": True,  # TODO: STREAMNATIVE - Set to True for production
            "cert_path": settings.pulsar.PULSAR_TLS_CERT_PATH,
            "key_path": settings.pulsar.PULSAR_TLS_KEY_PATH,
            "ca_path": settings.pulsar.PULSAR_TLS_CA_PATH,
        },
        "token": settings.pulsar.PULSAR_AUTH_TOKEN,  # TODO: STREAMNATIVE - Set your JWT token from StreamNative console
    }

    # Security
    # TODO: STREAMNATIVE - Update security settings for StreamNative cluster
    SECURITY = {
        "tls_enabled": True,  # TODO: STREAMNATIVE - Set to True for production
        "cert_path": settings.pulsar.PULSAR_TLS_CERT_PATH,
        "auth_type": "jwt",  # TODO: STREAMNATIVE - Keep as "jwt" for StreamNative
        "jwt_token": settings.pulsar.PULSAR_JWT_TOKEN,  # TODO: STREAMNATIVE - Set from StreamNative console
        "roles": [
            {"name": "admin", "permissions": ["produce", "consume", "manage"]},
            {"name": "service", "permissions": ["produce", "consume"]},
            {"name": "client", "permissions": ["consume"]},
        ],
        # TODO: STREAMNATIVE - Add topic permissions configuration
        # StreamNative uses tenant/namespace/topic structure
        "service_role": "notes-app",  # Default role for this application
        "topic_roles": {
            # TODO: STREAMNATIVE - Update with your tenant/namespace structure
            # Example: "persistent://your-tenant/your-namespace/topic-name": ["service"]
            "*": ["service", "admin"],  # Wildcard for development
        }
    }

    # Producer settings
    PRODUCER = {
        "send_timeout_ms": 30000,
        "block_if_queue_full": True,
        "max_pending_messages": 1000,
        "batching_enabled": True,
        "batching_max_messages": 1000,
        "batching_max_publish_delay_ms": 10,
    }

    # Polling interval for status checks
    POLL_INTERVAL: float = 1.0

    # Consumer settings
    CONSUMER = {
        "subscription_type": "Shared",  # or "Exclusive", "Failover", "Key_Shared"
        "ack_timeout_ms": 30000,
        "negative_ack_redelivery_delay_ms": 60000,
        "dead_letter_policy": {
            "max_redeliver_count": 3,
            # TODO: STREAMNATIVE - Update DLQ topic with your tenant/namespace
            # Example: "persistent://your-tenant/your-namespace/dlq-topic"
            "dead_letter_topic": "persistent://public/default/user-dlq",
        },
        "receiver_queue_size": 1000,
    }

    # Retry settings
    RETRY = {"max_retries": 5, "initial_backoff_ms": 100, "max_backoff_ms": 10000}

    # Monitoring
    MONITORING = {"stats_interval_seconds": 60}

    # Cache metrics settings
    CACHE_METRICS = {
        "enabled": True,
        "interval_seconds": 60,
        "metrics": [
            {"name": "cache_hits", "type": "counter", "help": "Total cache hits"},
            {"name": "cache_misses", "type": "counter", "help": "Total cache misses"},
            {"name": "cache_size", "type": "gauge", "help": "Current cache size in bytes"},
            {"name": "cache_evictions", "type": "counter", "help": "Total cache evictions"},
            {"name": "cache_latency", "type": "histogram", "help": "Cache operation latency"}
        ]
    }
