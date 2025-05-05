import pytest
from unittest.mock import patch, AsyncMock
from app.core.pulsar.decorators import validate_topic_permissions
from app.core.pulsar.config import PulsarConfig

@pytest.mark.asyncio
async def test_validate_topic_permissions_success():
    """Test successful topic validation"""
    with patch.object(PulsarConfig.SECURITY, 'get') as mock_get:
        mock_get.side_effect = lambda k: {
            'service_role': 'allowed_role',
            'topic_roles': {'valid_topic': ['allowed_role']}
        }.get(k)
        validate_topic_permissions("valid_topic")

@pytest.mark.asyncio
async def test_validate_topic_permissions_unauthorized():
    """Test unauthorized topic access"""
    with patch.object(PulsarConfig.SECURITY, 'get') as mock_get:
        mock_get.side_effect = lambda k: {
            'service_role': 'allowed_role',
            'topic_roles': {'valid_topic': ['other_role']}
        }.get(k)
        with pytest.raises(PermissionError):
            validate_topic_permissions("valid_topic")

@pytest.mark.asyncio
async def test_validate_topic_permissions_invalid_topic():
    """Test invalid topic format"""
    with pytest.raises(ValueError):
        validate_topic_permissions("")

@pytest.mark.asyncio
async def test_pulsar_task_decorator_happy_path():
    """Test successful decorated task execution"""
    from app.core.pulsar.decorators import pulsar_task
    
    @pulsar_task(topic="test_topic")
    async def sample_task():
        return "success"
        
    with patch('app.core.pulsar.decorators.client.send_message', new_callable=AsyncMock) as mock_send:
        mock_send.return_value = True
        result = await sample_task()
        assert result == "success"
        assert mock_send.called

@pytest.mark.asyncio
async def test_pulsar_task_decorator_retry_logic():
    """Test decorator retry behavior"""
    from app.core.pulsar.decorators import pulsar_task
    
    call_count = 0
    
    @pulsar_task(topic="test_topic", max_retries=3)
    async def failing_task():
        nonlocal call_count
        call_count += 1
        raise Exception("Simulated failure")
        
    with patch('app.core.pulsar.decorators.client.send_message', new_callable=AsyncMock), \
         patch('asyncio.sleep', new_callable=AsyncMock):
        with pytest.raises(Exception):
            await failing_task()
        assert call_count == 3

@pytest.mark.asyncio
async def test_pulsar_task_dlq_handling():
    """Test DLQ message routing on permanent failures"""
    from app.core.pulsar.decorators import pulsar_task
    
    @pulsar_task(topic="test_topic", max_retries=1, dlq_topic="dlq_topic")
    async def failing_task():
        raise Exception("Permanent failure")
        
    with patch('app.core.pulsar.decorators.client.send_message', new_callable=AsyncMock) as mock_send, \
         patch('asyncio.sleep', new_callable=AsyncMock):
        mock_send.side_effect = [Exception(), True]  # Fail first, succeed DLQ
        
        with pytest.raises(Exception):
            await failing_task()
            
        # Verify DLQ message was sent
        assert mock_send.call_count == 2
        assert mock_send.call_args_list[1][0][0] == "dlq_topic"
