"""
Tests for the chunking CRUD module.
"""
import pytest
import uuid
from unittest.mock import AsyncMock, patch, MagicMock, call

from backend.db.crud.chunking import (
    create_chunk, create_chunks, get_chunk_by_id,
    get_chunks_by_document, get_chunks_by_chunk_set_id,
    create_chunk_set, get_chunk_set_by_id,
    get_chunk_sets_by_document, update_chunk_embedding
)
from backend.db import models

# Mock data
mock_chunk_id = uuid.uuid4()
mock_chunk_set_id = uuid.uuid4()
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
@patch('backend.db.crud.chunking.get_supabase_client')
async def test_create_chunk(mock_get_client, mock_supabase_client):
    """Test creating a chunk."""
    # Setup
    mock_get_client.return_value = mock_supabase_client
    
    # Mock successful chunk creation
    mock_chunk = {
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
    mock_supabase_client.table().insert().execute.return_value.data = [mock_chunk]
    
    # Execute
    chunk_create = models.ChunkCreate(
        chunk_set_id=mock_chunk_set_id,
        document_id=mock_document_id,
        content='Test content',
        sequence_number=1
    )
    result = await create_chunk(chunk_create)
    
    # Verify
    assert result.id == mock_chunk_id
    assert result.content == 'Test content'
    assert result.document_id == mock_document_id
    
    # Verify method calls
    mock_supabase_client.table.assert_called_with('chunks')

@pytest.mark.asyncio
@patch('backend.db.crud.chunking.get_supabase_client')
async def test_create_chunks(mock_get_client, mock_supabase_client):
    """Test creating multiple chunks at once."""
    # Setup
    mock_get_client.return_value = mock_supabase_client
    
    # Mock successful chunks creation
    mock_chunk1 = {
        'id': str(uuid.uuid4()),
        'chunk_set_id': str(mock_chunk_set_id),
        'document_id': str(mock_document_id),
        'content': 'Chunk 1',
        'sequence_number': 0,
        'metadata': {},
        'embedding': None,
        'created_at': '2023-01-01T00:00:00',
        'updated_at': '2023-01-01T00:00:00'
    }
    mock_chunk2 = {
        'id': str(uuid.uuid4()),
        'chunk_set_id': str(mock_chunk_set_id),
        'document_id': str(mock_document_id),
        'content': 'Chunk 2',
        'sequence_number': 1,
        'metadata': {},
        'embedding': None,
        'created_at': '2023-01-01T00:00:00',
        'updated_at': '2023-01-01T00:00:00'
    }
    mock_supabase_client.table().insert().execute.return_value.data = [mock_chunk1, mock_chunk2]
    
    # Execute
    chunks_create = [
        models.ChunkCreate(
            chunk_set_id=mock_chunk_set_id,
            document_id=mock_document_id,
            content='Chunk 1',
            sequence_number=0
        ),
        models.ChunkCreate(
            chunk_set_id=mock_chunk_set_id,
            document_id=mock_document_id,
            content='Chunk 2',
            sequence_number=1
        )
    ]
    results = await create_chunks(chunks_create)
    
    # Verify
    assert len(results) == 2
    assert results[0].content == 'Chunk 1'
    assert results[1].content == 'Chunk 2'
    
    # Verify method calls
    mock_supabase_client.table.assert_called_with('chunks')

@pytest.mark.asyncio
@patch('backend.db.crud.chunking.get_supabase_client')
async def test_get_chunk_by_id(mock_get_client, mock_supabase_client):
    """Test getting a chunk by ID."""
    # Setup
    mock_get_client.return_value = mock_supabase_client
    
    # Mock successful chunk retrieval
    mock_chunk = {
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
    mock_supabase_client.table().select().eq().execute.return_value.data = [mock_chunk]
    
    # Execute
    result = await get_chunk_by_id(mock_chunk_id)
    
    # Verify
    assert result.id == mock_chunk_id
    assert result.content == 'Test content'
    mock_supabase_client.table.assert_called_with('chunks')

@pytest.mark.asyncio
@patch('backend.db.crud.chunking.get_supabase_client')
async def test_create_chunk_set(mock_get_client, mock_supabase_client):
    """Test creating a chunk set."""
    # Setup
    mock_get_client.return_value = mock_supabase_client
    
    # Mock successful chunk set creation
    mock_chunk_set = {
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
    mock_supabase_client.table().insert().execute.return_value.data = [mock_chunk_set]
    
    # Execute
    chunk_set_create = models.ChunkSetCreate(
        document_id=mock_document_id,
        user_id=mock_user_id,
        name='Test Chunk Set',
        chunk_size=1000,
        chunk_overlap=200
    )
    result = await create_chunk_set(chunk_set_create)
    
    # Verify
    assert result.id == mock_chunk_set_id
    assert result.name == 'Test Chunk Set'
    assert result.document_id == mock_document_id
    
    # Verify method calls
    mock_supabase_client.table.assert_called_with('chunk_sets')

@pytest.mark.asyncio
@patch('backend.db.crud.chunking.get_supabase_client')
async def test_get_chunk_set_by_id(mock_get_client, mock_supabase_client):
    """Test getting a chunk set by ID."""
    # Setup
    mock_get_client.return_value = mock_supabase_client
    
    # Mock successful chunk set retrieval
    mock_chunk_set = {
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
    mock_supabase_client.table().select().eq().execute.return_value.data = [mock_chunk_set]
    
    # Execute
    result = await get_chunk_set_by_id(mock_chunk_set_id)
    
    # Verify
    assert result.id == mock_chunk_set_id
    assert result.name == 'Test Chunk Set'
    mock_supabase_client.table.assert_called_with('chunk_sets')

@pytest.mark.asyncio
@patch('backend.db.crud.chunking.get_supabase_client')
async def test_get_chunks_by_chunk_set_id(mock_get_client, mock_supabase_client):
    """Test getting chunks by chunk set ID."""
    # Setup
    mock_get_client.return_value = mock_supabase_client
    
    # Mock successful chunks retrieval
    mock_chunk1 = {
        'id': str(uuid.uuid4()),
        'chunk_set_id': str(mock_chunk_set_id),
        'document_id': str(mock_document_id),
        'content': 'Chunk 1',
        'sequence_number': 0,
        'metadata': {},
        'embedding': None,
        'created_at': '2023-01-01T00:00:00',
        'updated_at': '2023-01-01T00:00:00'
    }
    mock_chunk2 = {
        'id': str(uuid.uuid4()),
        'chunk_set_id': str(mock_chunk_set_id),
        'document_id': str(mock_document_id),
        'content': 'Chunk 2',
        'sequence_number': 1,
        'metadata': {},
        'embedding': None,
        'created_at': '2023-01-01T00:00:00',
        'updated_at': '2023-01-01T00:00:00'
    }
    mock_supabase_client.table().select().eq().order().execute.return_value.data = [mock_chunk1, mock_chunk2]
    
    # Execute
    results = await get_chunks_by_chunk_set_id(mock_chunk_set_id)
    
    # Verify
    assert len(results) == 2
    assert results[0].content == 'Chunk 1'
    assert results[1].content == 'Chunk 2'
    
    # Verify method calls
    mock_supabase_client.table.assert_called_with('chunks') 