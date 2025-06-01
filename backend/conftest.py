"""
Global pytest fixtures and configuration.
"""
import pytest
import os
import uuid
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime
from typing import Dict, Any

from backend.external_services.supabase.test_utils import patch_supabase_client

# Common test IDs
@pytest.fixture(scope="session")
def mock_user_id():
    """Fixture for a mock user ID"""
    return uuid.uuid4()

@pytest.fixture(scope="session")
def mock_document_id():
    """Fixture for a mock document ID"""
    return uuid.uuid4()

@pytest.fixture(scope="session")
def mock_chunk_set_id():
    """Fixture for a mock chunk set ID"""
    return uuid.uuid4()

@pytest.fixture(scope="session")
def mock_chunk_id():
    """Fixture for a mock chunk ID"""
    return uuid.uuid4()

@pytest.fixture(scope="session")
def mock_translation_id():
    """Fixture for a mock translation ID"""
    return uuid.uuid4()

@pytest.fixture
def mock_user(mock_user_id):
    """Fixture for a mock user"""
    return {"id": str(mock_user_id), "email": "test@example.com"}

# Mocked models
@pytest.fixture
def mock_document_data(mock_document_id, mock_user_id):
    """Fixture for mock document data"""
    return {
        'id': str(mock_document_id),
        'user_id': str(mock_user_id),
        'name': 'Test Document',
        'file_size': 1000,
        'metadata': {},
        'created_at': '2023-01-01T00:00:00',
        'updated_at': '2023-01-01T00:00:00'
    }

@pytest.fixture
def mock_chunk_data(mock_chunk_id, mock_chunk_set_id, mock_document_id):
    """Fixture for mock chunk data"""
    return {
        'id': str(mock_chunk_id),
        'chunk_set_id': str(mock_chunk_set_id),
        'document_id': str(mock_document_id),
        'content': 'Test content',
        'sequence_number': 1,
        'metadata': {},
        'embedding': None,
        'created_at': '2023-01-01T00:00:00',
        'updated_at': '2023-01-01T00:00:00'
    }

@pytest.fixture
def mock_chunk_set_data(mock_chunk_set_id, mock_document_id, mock_user_id):
    """Fixture for mock chunk set data"""
    return {
        'id': str(mock_chunk_set_id),
        'document_id': str(mock_document_id),
        'user_id': str(mock_user_id),
        'name': 'Test Chunk Set',
        'chunk_size': 1000,
        'chunk_overlap': 200,
        'metadata': {},
        'created_at': '2023-01-01T00:00:00',
        'updated_at': '2023-01-01T00:00:00'
    }

@pytest.fixture
def mock_translation_data(mock_translation_id, mock_chunk_set_id, mock_user_id):
    """Fixture for mock translation data"""
    return {
        'id': str(mock_translation_id),
        'chunk_set_id': str(mock_chunk_set_id),
        'user_id': str(mock_user_id),
        'target_language': 'Spanish',
        'name': 'Test Translation',
        'status': 'pending',
        'completed_chunks': 0,
        'total_chunks': 5,
        'ai_model': 'gpt-4.1-nano',
        'metadata': {},
        'output_file_path': None,
        'created_at': '2023-01-01T00:00:00',
        'updated_at': '2023-01-01T00:00:00'
    }

@pytest.fixture
def mock_translated_chunk_data(mock_translation_id, mock_chunk_id):
    """Fixture for mock translated chunk data"""
    return {
        'id': str(uuid.uuid4()),
        'translation_id': str(mock_translation_id),
        'chunk_id': str(mock_chunk_id),
        'translated_content': 'Contenido traducido',
        'sequence_number': 1,
        'metadata': {},
        'created_at': '2023-01-01T00:00:00',
        'updated_at': '2023-01-01T00:00:00'
    }

@pytest.fixture
def mock_all_data(
    mock_document_data,
    mock_chunk_set_data,
    mock_chunk_data,
    mock_translation_data,
    mock_translated_chunk_data,
    mock_user
):
    """Fixture with all mock data for tables"""
    return {
        'documents': [mock_document_data],
        'chunk_sets': [mock_chunk_set_data],
        'chunks': [mock_chunk_data],
        'translations': [mock_translation_data],
        'translated_chunks': [mock_translated_chunk_data],
        'auth.users': [mock_user]
    }

@pytest.fixture(scope="function", autouse=True)
def setup_supabase_env(mock_all_data):
    """Set up Supabase environment for tests with mock data"""
    mock_client = patch_supabase_client(mock_all_data)
    yield mock_client

# Common mock setup for Supabase client
@pytest.fixture
def mock_supabase_client():
    """Fixture for mocking Supabase client."""
    client_mock = MagicMock()
    
    # Create fresh mocks for each test
    table_mock = MagicMock()
    client_mock.table.return_value = table_mock
    
    # Mock the chain of calls
    select_mock = MagicMock()
    insert_mock = MagicMock()
    update_mock = MagicMock()
    delete_mock = MagicMock()
    
    table_mock.select.return_value = select_mock
    table_mock.insert.return_value = insert_mock
    table_mock.update.return_value = update_mock
    table_mock.delete.return_value = delete_mock
    
    eq_mock = MagicMock()
    filter_mock = MagicMock()
    order_mock = MagicMock()
    execute_mock = MagicMock()
    
    # Set up mocks for method chains
    for mock_obj in [select_mock, insert_mock, update_mock, delete_mock]:
        mock_obj.eq.return_value = eq_mock
        mock_obj.filter.return_value = filter_mock
        mock_obj.order.return_value = order_mock
        mock_obj.execute.return_value = execute_mock
    
    eq_mock.eq.return_value = eq_mock
    eq_mock.filter.return_value = filter_mock
    eq_mock.order.return_value = order_mock
    eq_mock.execute.return_value = execute_mock
    
    filter_mock.eq.return_value = eq_mock
    filter_mock.filter.return_value = filter_mock
    filter_mock.order.return_value = order_mock
    filter_mock.execute.return_value = execute_mock
    
    order_mock.eq.return_value = eq_mock
    order_mock.filter.return_value = filter_mock
    order_mock.order.return_value = order_mock
    order_mock.execute.return_value = execute_mock
    
    execute_mock.data = []
    
    return client_mock 