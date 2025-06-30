# Makes this directory a Python package, enabling submodule patching and imports.

# Import configuration overrides FIRST before any other pulsar modules
from app.core.pulsar.config_override import *

# Now import other modules
import app.core.pulsar.index

# Provide direct access to commonly used decorators and classes
from app.core.pulsar.client import PulsarClient
from app.core.pulsar.decorators import pulsar_task

# Export commonly used items
__all__ = ['PulsarClient', 'pulsar_task']
