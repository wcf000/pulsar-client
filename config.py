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
    _test_localhost = os.getenv("PULSAR_TEST_LOCALHOST") == "1"
    print(_test_localhost)
    if _test_localhost:
        SERVICE_URL = "pulsar://127.0.0.1:6650"
        SERVICE_URLS = ["pulsar://127.0.0.1:6650"]
        print("🔧 Pulsar Config: Using localhost for testing")
    else:
        # Allow direct override from environment for StreamNative settings
        env_addr = os.getenv("PULSAR_ADVERTISED_ADDRESS")
        env_port = os.getenv("PULSAR_BROKER_PORT")
        env_token = os.getenv("PULSAR_AUTH_TOKEN")
        env_jwt = os.getenv("PULSAR_JWT_TOKEN")
        # Diagnostic: show raw environment values
        print(f"🔍 Env PULSAR_ADVERTISED_ADDRESS={env_addr}")
        print(f"🔍 Env PULSAR_BROKER_PORT={env_port}")
        print(f"🔍 Env PULSAR_AUTH_TOKEN length={(len(env_token) if env_token else 0)}")
        print(f"🔍 Env PULSAR_JWT_TOKEN length={(len(env_jwt) if env_jwt else 0)}")
        # Diagnostic: show settings values loaded via Pydantic
        print(f"🔍 SETTINGS PULSAR_ADVERTISED_ADDRESS={settings.pulsar.PULSAR_ADVERTISED_ADDRESS}")
        print(f"🔍 SETTINGS PULSAR_BROKER_PORT={settings.pulsar.PULSAR_BROKER_PORT}")
        print(f"🔍 SETTINGS PULSAR_AUTH_TOKEN length={len(settings.pulsar.PULSAR_AUTH_TOKEN or '')}")
        print(f"🔍 SETTINGS PULSAR_JWT_TOKEN length={len(settings.pulsar.PULSAR_JWT_TOKEN or '')}")
        # Fallback to settings if env vars are missing
        use_addr = env_addr or settings.pulsar.PULSAR_ADVERTISED_ADDRESS
        use_port = env_port or str(settings.pulsar.PULSAR_BROKER_PORT)
        SERVICE_URL = f"pulsar+ssl://{use_addr}:{use_port}"
        SERVICE_URLS = [SERVICE_URL]
        print(f"🔧 Pulsar Config: Using StreamNative cluster: {SERVICE_URL}")
        print(f"🔧 Pulsar Config: Advertised Address: {use_addr}")
        print(f"🔧 Pulsar Config: Broker Port: {use_port}")
        print("🔧 Pulsar Config: TLS Enabled: True")
        token_len = len(env_token) if env_token else len(settings.pulsar.PULSAR_AUTH_TOKEN or "")
        print(f"🔧 Pulsar Config: Auth Token Length: {token_len} chars")
        # Override authentication tokens from env
        AUTH_TOKEN = env_token or settings.pulsar.PULSAR_AUTH_TOKEN
        JWT_TOKEN = env_jwt or settings.pulsar.PULSAR_JWT_TOKEN

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
        "token": AUTH_TOKEN,  # TODO: STREAMNATIVE - Set your JWT token from StreamNative console
    }

    # Security
    # TODO: STREAMNATIVE - Update security settings for StreamNative cluster
    SECURITY = {
        "tls_enabled": True,  # TODO: STREAMNATIVE - Set to True for production
        "cert_path": settings.pulsar.PULSAR_TLS_CERT_PATH,
        "auth_type": "jwt",  # TODO: STREAMNATIVE - Keep as "jwt" for StreamNative
        "jwt_token": JWT_TOKEN,  # TODO: STREAMNATIVE - Set from StreamNative console
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
        "send_timeout_ms": 3000,  # Keep at 3 seconds (under 4s requirement)
        "block_if_queue_full": False,  # Don't block, fail fast
        "max_pending_messages": 100,  # Reduced from 1000
        "batching_enabled": True,
        "batching_max_messages": 100,  # Reduced from 1000
        "batching_max_publish_delay_ms": 5,  # Reduced from 10
    }

    # Polling interval for status checks
    POLL_INTERVAL: float = 1.0

    # Consumer settings
    CONSUMER = {
        "subscription_type": "Shared",  # or "Exclusive", "Failover", "Key_Shared"
        "ack_timeout_ms": 3000,  # Reduced from 5000 to 3 seconds (under 4s requirement)
        "negative_ack_redelivery_delay_ms": 3000,  # Reduced from 10000 to 3 seconds (under 4s requirement)
        "dead_letter_policy": {
            "max_redeliver_count": 2,  # Reduced from 3
            # TODO: STREAMNATIVE - Update DLQ topic with your tenant/namespace
            # Example: "persistent://your-tenant/your-namespace/dlq-topic"
            "dead_letter_topic": "persistent://public/default/user-dlq",
        },
        "receiver_queue_size": 100,  # Reduced from 1000
    }

    # Retry settings
    RETRY = {"max_retries": 2, "initial_backoff_ms": 50, "max_backoff_ms": 2000}  # Keep at 2s (under 4s requirement)

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
