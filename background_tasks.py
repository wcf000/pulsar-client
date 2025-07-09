"""
Background task execution for Pulsar operations that don't block HTTP responses.
"""
import asyncio
import logging
from typing import Dict, Any, Optional
from opentelemetry import trace

logger = logging.getLogger(__name__)

class BackgroundPulsarTask:
    """
    Execute Pulsar operations in true background without blocking HTTP responses.
    """
    
    @staticmethod
    def send_message_background(
        client, 
        topic: str, 
        message: Dict[str, Any], 
        span_name: Optional[str] = None
    ) -> None:
        """
        Schedule a Pulsar message to be sent in the background without blocking.
        
        Args:
            client: PulsarClient instance
            topic: Pulsar topic to send to
            message: Message data to send
            span_name: Optional span name for tracing
        """
        async def _background_send():
            """Internal coroutine that runs the actual send operation."""
            span_name_final = span_name or f"pulsar_background_send_{topic.split('/')[-1]}"
            
            with trace.get_tracer(__name__).start_as_current_span(span_name_final) as span:
                try:
                    span.set_attribute("pulsar.topic", topic)
                    span.set_attribute("pulsar.background", True)
                    span.set_attribute("pulsar.message_type", message.get("event_type", "unknown"))
                    
                    # Execute the actual send operation
                    if client and hasattr(client, 'send_message'):
                        success = await client.send_message(topic, message)
                        span.set_attribute("pulsar.success", success)
                        
                        if success:
                            logger.debug(f"✅ Background Pulsar message sent to {topic}")
                        else:
                            logger.warning(f"⚠️ Background Pulsar message failed for {topic}")
                    else:
                        logger.warning(f"⚠️ No Pulsar client available for background send to {topic}")
                        span.set_attribute("pulsar.success", False)
                        span.set_attribute("pulsar.error", "No client available")
                        
                except Exception as e:
                    span.set_attribute("pulsar.success", False)
                    span.set_attribute("pulsar.error", str(e))
                    span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                    logger.error(f"❌ Background Pulsar send failed for {topic}: {str(e)}")
        
        # Schedule the coroutine to run in the background without blocking
        try:
            # Use asyncio.create_task to run truly in background
            # This won't block the calling code
            asyncio.create_task(_background_send())
            logger.debug(f"🚀 Scheduled background Pulsar send for {topic}")
        except Exception as e:
            logger.error(f"❌ Failed to schedule background Pulsar task: {str(e)}")

    @staticmethod 
    def send_login_event_background(
        client,
        event_data: Dict[str, Any]
    ) -> None:
        """
        Send login event to Pulsar in background without blocking response.
        
        Args:
            client: PulsarClient instance
            event_data: Login event data
        """
        # Add metadata for tracking
        import uuid
        from datetime import datetime
        
        enriched_data = {
            **event_data,
            "event_id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "event_type": "login"
        }
        
        BackgroundPulsarTask.send_message_background(
            client=client,
            topic="persistent://public/default/auth-login",
            message=enriched_data,
            span_name="login_event_background"
        )
        
    @staticmethod
    def send_password_reset_event_background(
        client,
        event_data: Dict[str, Any]
    ) -> None:
        """
        Send password reset event to Pulsar in background without blocking response.
        
        Args:
            client: PulsarClient instance
            event_data: Password reset event data
        """
        # Add metadata for tracking
        import uuid
        from datetime import datetime
        
        enriched_data = {
            **event_data,
            "event_id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "event_type": "password_reset"
        }
        
        BackgroundPulsarTask.send_message_background(
            client=client,
            topic="persistent://public/default/auth-password-reset",
            message=enriched_data,
            span_name="password_reset_event_background"
        )