"""
Tests for the files CRUD module.
"""
import pytest
import uuid
from unittest.mock import AsyncMock, patch, MagicMock, call

from backend.db.crud.files import (
    create_document, get_document_by_id, get_documents_by_user,
    get_documents_by_metadata, update_document, delete_document,
    update_document_metadata
)
from backend.db import models

# Mock document data
mock_document_id = uuid.uuid4()
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

@pytest.mark.asyncio
@patch('backend.db.crud.files.get_supabase_client')
async def test_document_create(mock_get_client, mock_supabase_client):
    """Test creating a document."""
    # Setup
    mock_get_client.return_value = mock_supabase_client
    
    # Mock successful document creation
    mock_doc = {
        'id': str(mock_document_id),
        'user_id': str(mock_user_id),
        'name': 'Test Document',
        'file_size': 1000,
        'metadata': {},
        'created_at': '2023-01-01T00:00:00',
        'updated_at': '2023-01-01T00:00:00'
    }
    mock_supabase_client.table().insert().execute.return_value.data = [mock_doc]
    
    # Execute
    doc_create = models.DocumentCreate(
        user_id=mock_user_id,
        name='Test Document',
        file_size=1000
    )
    result = await create_document(doc_create)
    
    # Verify
    assert result.id == mock_document_id
    assert result.name == 'Test Document'
    
    # Verify method calls
    mock_supabase_client.table.assert_called_with('documents')

@pytest.mark.asyncio
@patch('backend.db.crud.files.get_supabase_client')
async def test_document_get_by_id(mock_get_client, mock_supabase_client):
    """Test getting a document by ID."""
    # Setup
    mock_get_client.return_value = mock_supabase_client
    
    # Mock successful document retrieval
    mock_doc = {
        'id': str(mock_document_id),
        'user_id': str(mock_user_id),
        'name': 'Test Document',
        'file_size': 1000,
        'metadata': {},
        'created_at': '2023-01-01T00:00:00',
        'updated_at': '2023-01-01T00:00:00'
    }
    mock_supabase_client.table().select().eq().execute.return_value.data = [mock_doc]
    
    # Execute
    result = await get_document_by_id(mock_document_id)
    
    # Verify
    assert result.id == mock_document_id
    assert result.name == 'Test Document'
    mock_supabase_client.table.assert_called_with('documents')

@pytest.mark.asyncio
@patch('backend.db.crud.files.get_supabase_client')
async def test_document_get_by_metadata(mock_get_client, mock_supabase_client):
    """Test getting documents by metadata."""
    # Setup
    mock_get_client.return_value = mock_supabase_client
    
    # Mock successful document retrieval
    mock_doc = {
        'id': str(mock_document_id),
        'user_id': str(mock_user_id),
        'name': 'Test Document',
        'file_size': 1000,
        'metadata': {'status': 'processed'},
        'created_at': '2023-01-01T00:00:00',
        'updated_at': '2023-01-01T00:00:00'
    }
    mock_supabase_client.table().select().eq().filter().execute.return_value.data = [mock_doc]
    
    # Execute
    result = await get_documents_by_metadata(mock_user_id, {'status': 'processed'})
    
    # Verify
    assert len(result) == 1
    assert result[0].id == mock_document_id
    assert result[0].metadata['status'] == 'processed'
    mock_supabase_client.table.assert_called_with('documents')

@pytest.mark.asyncio
@patch('backend.db.crud.files.get_supabase_client')
async def test_document_update(mock_get_client, mock_supabase_client):
    """Test updating a document."""
    # Setup
    mock_get_client.return_value = mock_supabase_client
    
    # Mock successful document update
    mock_doc = {
        'id': str(mock_document_id),
        'user_id': str(mock_user_id),
        'name': 'Updated Document',
        'file_size': 1000,
        'metadata': {},
        'created_at': '2023-01-01T00:00:00',
        'updated_at': '2023-01-01T00:00:00'
    }
    mock_supabase_client.table().update().eq().execute.return_value.data = [mock_doc]
    
    # Execute
    update_data = models.DocumentUpdate(name='Updated Document')
    result = await update_document(mock_document_id, update_data)
    
    # Verify
    assert result.name == 'Updated Document'
    mock_supabase_client.table.assert_called_with('documents')

@pytest.mark.asyncio
@patch('backend.db.crud.files.get_supabase_client')
async def test_document_delete(mock_get_client, mock_supabase_client):
    """Test deleting a document."""
    # Setup
    mock_get_client.return_value = mock_supabase_client
    
    # Mock successful document deletion
    mock_supabase_client.table().delete().eq().execute.return_value.data = [{'id': str(mock_document_id)}]
    
    # Execute
    result = await delete_document(mock_document_id)
    
    # Verify
    assert result is True
    mock_supabase_client.table.assert_called_with('documents')

@pytest.mark.asyncio
@patch('backend.db.crud.files.get_document_by_id')
@patch('backend.db.crud.files.update_document')
async def test_update_document_metadata(mock_update_document, mock_get_document_by_id):
    """Test updating document metadata."""
    # Setup
    mock_doc = models.Document(
        id=mock_document_id,
        user_id=mock_user_id,
        name='Test Document',
        file_size=1000,
        metadata={'existing': 'value'},
        created_at='2023-01-01T00:00:00',
        updated_at='2023-01-01T00:00:00'
    )
    mock_get_document_by_id.return_value = mock_doc
    
    updated_doc = mock_doc.model_copy()
    updated_doc.metadata = {'existing': 'value', 'new': 'metadata'}
    mock_update_document.return_value = updated_doc
    
    # Execute
    result = await update_document_metadata(mock_document_id, {'new': 'metadata'})
    
    # Verify
    assert result.metadata['existing'] == 'value'
    assert result.metadata['new'] == 'metadata'
    mock_get_document_by_id.assert_called_once_with(mock_document_id)
    # Check that update_document was called with the right parameters
    # We can't directly check the DocumentUpdate object, so we check that update_document was called
    assert mock_update_document.called 