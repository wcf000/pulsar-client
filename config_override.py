"""
Override default Pulsar configuration settings.
This file is imported early in the app startup to modify configuration before clients are initialized.
"""

from app.core.pulsar.config import PulsarConfig

# Define a default service role
DEFAULT_ROLE = 'service'

# Update security configuration to allow the service role to access all topics
PulsarConfig.SECURITY.update({
    'service_role': DEFAULT_ROLE,
    'topic_roles': {
        # Wildcard entry for development - allows any topic
        '*': [DEFAULT_ROLE],
        
        # Auth topics
        'persistent://public/default/auth-login': [DEFAULT_ROLE],
        'persistent://public/default/auth-password-reset': [DEFAULT_ROLE],
        'persistent://public/default/auth-suspicious-activity': [DEFAULT_ROLE],
        'persistent://public/default/auth-dlq': [DEFAULT_ROLE],
        
        # User topics
        'persistent://public/default/user-created': [DEFAULT_ROLE],
        'persistent://public/default/user-updated': [DEFAULT_ROLE],
        'persistent://public/default/user-deleted': [DEFAULT_ROLE],
        'persistent://public/default/user-dlq': [DEFAULT_ROLE],
        
        # Item topics
        'persistent://public/default/item-created': [DEFAULT_ROLE],
        'persistent://public/default/item-updated': [DEFAULT_ROLE],
        'persistent://public/default/item-deleted': [DEFAULT_ROLE],
        
        # Messaging topics
        'persistent://public/default/notifications': [DEFAULT_ROLE],
        'persistent://public/default/user-activity': [DEFAULT_ROLE],
        'persistent://public/default/system-alerts': [DEFAULT_ROLE],
        'persistent://public/default/dead-letter-queue': [DEFAULT_ROLE],
    }
})

print("Pulsar security configuration overridden with default permissions")