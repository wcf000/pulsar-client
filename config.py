"""
Pulsar client configuration with production-ready settings.
"""

from app.core.config import settings


class PulsarConfig:
    """
    Configuration for Pulsar client with production settings.
    Gets values from environment variables via settings.
    """

    # Connection settings
    SERVICE_URL = (
        f"pulsar://{settings.PULSAR_ADVERTISED_ADDRESS}:{settings.PULSAR_BROKER_PORT}"
    )
    SERVICE_URLS = [
        f"pulsar://{settings.PULSAR_ADVERTISED_ADDRESS}:{settings.PULSAR_BROKER_PORT}"
    ]

    # Authentication
    AUTHENTICATION = {
        "tls": {
            "enabled": True,
            "cert_path": settings.PULSAR_TLS_CERT_PATH,
            "key_path": settings.PULSAR_TLS_KEY_PATH,
            "ca_path": settings.PULSAR_TLS_CA_PATH,
        },
        "token": settings.PULSAR_AUTH_TOKEN,
    }

    # Security
    SECURITY = {
        "tls_enabled": True,
        "cert_path": settings.PULSAR_TLS_CERT_PATH,
        "auth_type": "jwt",  # or 'oauth2'
        "jwt_token": settings.PULSAR_JWT_TOKEN,
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
