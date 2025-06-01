"""
Tests for the auth CRUD module.
"""
import pytest
import uuid
from unittest.mock import AsyncMock, patch, MagicMock, call

from backend.db.crud.auth import get_user_by_id

# Mock data
mock_user_id = uuid.uuid4()

@pytest.fixture
def mock_supabase_client():
    """Fixture for mocking Supabase client."""
    client_mock = MagicMock()
    
    # Create fresh mocks for each test
    table_mock = MagicMock()
    client_mock.table.return_value = table_mock
    
    # Mock the chain of calls
    select_mock = MagicMock()
    
    table_mock.select.return_value = select_mock
    
    eq_mock = MagicMock()
    execute_mock = MagicMock()
    
    select_mock.eq.return_value = eq_mock
    eq_mock.execute.return_value = execute_mock
    
    execute_mock.data = []
    
    return client_mock

@pytest.mark.asyncio
@patch('backend.db.crud.auth.get_supabase_client')
async def test_get_user_by_id(mock_get_client, mock_supabase_client):
    """Test getting a user by ID."""
    # Setup
    mock_get_client.return_value = mock_supabase_client
    
    # Mock successful user retrieval
    mock_user = {
        'id': str(mock_user_id),
        'email': 'test@example.com',
        'role': 'authenticated',
        'created_at': '2023-01-01T00:00:00'
    }
    mock_supabase_client.table().select().eq().execute.return_value.data = [mock_user]
    
    # Execute
    result = await get_user_by_id(mock_user_id)
    
    # Verify
    assert result['id'] == str(mock_user_id)
    assert result['email'] == 'test@example.com'
    
    # Verify method calls
    mock_supabase_client.table.assert_called_with('auth.users') 