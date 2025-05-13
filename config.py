"""
Pulsar client configuration with production-ready settings.
"""

from app.core.config import settings


import os
import sys

class PulsarConfig:
    """
    Configuration for Pulsar client with production settings.
    Gets values from environment variables via settings.
    """

    # Connection settings
    # * Use localhost:6650 for integration tests if env var is set or running under pytest
    _test_localhost = os.getenv("PULSAR_TEST_LOCALHOST") == "1" or "pytest" in sys.modules
    if _test_localhost:
        SERVICE_URL = "pulsar://127.0.0.1:6650"
        SERVICE_URLS = ["pulsar://127.0.0.1:6650"]
    else:
        SERVICE_URL = f"pulsar://{settings.pulsar.PULSAR_ADVERTISED_ADDRESS}:{settings.pulsar.PULSAR_BROKER_PORT}"
        SERVICE_URLS = [SERVICE_URL]

    # Authentication
    AUTHENTICATION = {
        "tls": {
            "enabled": False,
            "cert_path": settings.pulsar.PULSAR_TLS_CERT_PATH,
            "key_path": settings.pulsar.PULSAR_TLS_KEY_PATH,
            "ca_path": settings.pulsar.PULSAR_TLS_CA_PATH,
        },
        "token": settings.pulsar.PULSAR_AUTH_TOKEN,
    }

    # Security
    SECURITY = {
        "tls_enabled": False,
        "cert_path": settings.pulsar.PULSAR_TLS_CERT_PATH,
        "auth_type": "jwt",  # or 'oauth2'
        "jwt_token": settings.pulsar.PULSAR_JWT_TOKEN,
        "roles": [
            {"name": "admin", "permissions": ["produce", "consume", "manage"]},
            {"name": "service", "permissions": ["produce", "consume"]},
            {"name": "client", "permissions": ["consume"]},
        ],
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

    # Consumer settings
    CONSUMER = {
        "subscription_type": "Shared",  # or "Exclusive", "Failover", "Key_Shared"
        "ack_timeout_ms": 30000,
        "negative_ack_redelivery_delay_ms": 60000,
        "dead_letter_policy": {
            "max_redeliver_count": 3,
            "dead_letter_topic": "persistent://tenant/namespace/dlq-topic",
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
