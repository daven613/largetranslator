"""
Tests for the translations CRUD module.
"""
import pytest
import uuid
from unittest.mock import AsyncMock, patch, MagicMock, call

from backend.db.crud.translations import (
    create_translation, get_translation_by_id, get_translations_by_user,
    update_translation, delete_translation, create_translated_chunk,
    get_translated_chunks_by_translation, get_translation_with_chunks
)
from backend.db import models

# Mock data
mock_translation_id = uuid.uuid4()
mock_chunk_set_id = uuid.uuid4()
mock_user_id = uuid.uuid4()
mock_chunk_id = uuid.uuid4()
mock_translated_chunk_id = uuid.uuid4()

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
@patch('backend.db.crud.translations.get_supabase_client')
async def test_create_translation(mock_get_client, mock_supabase_client):
    """Test creating a translation."""
    # Setup
    mock_get_client.return_value = mock_supabase_client
    
    # Mock successful translation creation
    mock_translation = {
        'id': str(mock_translation_id),
        'chunk_set_id': str(mock_chunk_set_id),
        'user_id': str(mock_user_id),
        'target_language': 'Spanish',
        'name': 'Test Translation',
        'status': 'pending',
        'completed_chunks': 0,
        'total_chunks': 5,
        'ai_model': 'gpt-4',
        'metadata': {},
        'created_at': '2023-01-01T00:00:00',
        'updated_at': '2023-01-01T00:00:00'
    }
    mock_supabase_client.table().insert().execute.return_value.data = [mock_translation]
    
    # Execute
    translation_create = models.TranslationCreate(
        chunk_set_id=mock_chunk_set_id,
        user_id=mock_user_id,
        target_language='Spanish',
        name='Test Translation',
        total_chunks=5
    )
    result = await create_translation(translation_create)
    
    # Verify
    assert result.id == mock_translation_id
    assert result.target_language == 'Spanish'
    assert result.status == 'pending'
    
    # Verify method calls
    mock_supabase_client.table.assert_called_with('translations')

@pytest.mark.asyncio
@patch('backend.db.crud.translations.get_supabase_client')
async def test_get_translation_by_id(mock_get_client, mock_supabase_client):
    """Test getting a translation by ID."""
    # Setup
    mock_get_client.return_value = mock_supabase_client
    
    # Mock successful translation retrieval
    mock_translation = {
        'id': str(mock_translation_id),
        'chunk_set_id': str(mock_chunk_set_id),
        'user_id': str(mock_user_id),
        'target_language': 'Spanish',
        'name': 'Test Translation',
        'status': 'pending',
        'completed_chunks': 0,
        'total_chunks': 5,
        'ai_model': 'gpt-4',
        'metadata': {},
        'created_at': '2023-01-01T00:00:00',
        'updated_at': '2023-01-01T00:00:00'
    }
    mock_supabase_client.table().select().eq().execute.return_value.data = [mock_translation]
    
    # Execute
    result = await get_translation_by_id(mock_translation_id)
    
    # Verify
    assert result.id == mock_translation_id
    assert result.target_language == 'Spanish'
    mock_supabase_client.table.assert_called_with('translations')

@pytest.mark.asyncio
@patch('backend.db.crud.translations.get_supabase_client')
async def test_get_translations_by_user(mock_get_client, mock_supabase_client):
    """Test getting translations by user ID."""
    # Setup
    mock_get_client.return_value = mock_supabase_client
    
    # Mock successful translations retrieval
    mock_translation1 = {
        'id': str(uuid.uuid4()),
        'chunk_set_id': str(mock_chunk_set_id),
        'user_id': str(mock_user_id),
        'target_language': 'Spanish',
        'name': 'Translation 1',
        'status': 'pending',
        'completed_chunks': 0,
        'total_chunks': 5,
        'ai_model': 'gpt-4',
        'metadata': {},
        'created_at': '2023-01-01T00:00:00',
        'updated_at': '2023-01-01T00:00:00'
    }
    mock_translation2 = {
        'id': str(uuid.uuid4()),
        'chunk_set_id': str(mock_chunk_set_id),
        'user_id': str(mock_user_id),
        'target_language': 'French',
        'name': 'Translation 2',
        'status': 'completed',
        'completed_chunks': 5,
        'total_chunks': 5,
        'ai_model': 'gpt-4',
        'metadata': {},
        'created_at': '2023-01-01T00:00:00',
        'updated_at': '2023-01-01T00:00:00'
    }
    mock_supabase_client.table().select().eq().execute.return_value.data = [mock_translation1, mock_translation2]
    
    # Execute
    results = await get_translations_by_user(mock_user_id)
    
    # Verify
    assert len(results) == 2
    assert results[0].target_language == 'Spanish'
    assert results[1].target_language == 'French'
    
    # Verify method calls
    mock_supabase_client.table.assert_called_with('translations')

@pytest.mark.asyncio
@patch('backend.db.crud.translations.get_supabase_client')
async def test_update_translation(mock_get_client, mock_supabase_client):
    """Test updating a translation."""
    # Setup
    mock_get_client.return_value = mock_supabase_client
    
    # Mock successful translation update
    mock_translation = {
        'id': str(mock_translation_id),
        'chunk_set_id': str(mock_chunk_set_id),
        'user_id': str(mock_user_id),
        'target_language': 'Spanish',
        'name': 'Updated Translation',
        'status': 'completed',
        'completed_chunks': 5,
        'total_chunks': 5,
        'ai_model': 'gpt-4',
        'metadata': {},
        'created_at': '2023-01-01T00:00:00',
        'updated_at': '2023-01-01T00:00:00'
    }
    mock_supabase_client.table().update().eq().execute.return_value.data = [mock_translation]
    
    # Execute
    update_data = models.TranslationUpdate(
        name='Updated Translation',
        status='completed'
    )
    result = await update_translation(mock_translation_id, update_data)
    
    # Verify
    assert result.name == 'Updated Translation'
    assert result.status == 'completed'
    
    # Verify method calls
    mock_supabase_client.table.assert_called_with('translations')

@pytest.mark.asyncio
@patch('backend.db.crud.translations.get_supabase_client')
async def test_delete_translation(mock_get_client, mock_supabase_client):
    """Test deleting a translation."""
    # Setup
    mock_get_client.return_value = mock_supabase_client
    
    # Mock successful translation deletion
    mock_supabase_client.table().delete().eq().execute.return_value.data = [{'id': str(mock_translation_id)}]
    
    # Execute
    result = await delete_translation(mock_translation_id)
    
    # Verify
    assert result is True
    
    # Verify method calls
    mock_supabase_client.table.assert_called_with('translations')

@pytest.mark.asyncio
@patch('backend.db.crud.translations.get_supabase_client')
async def test_create_translated_chunk(mock_get_client, mock_supabase_client):
    """Test creating a translated chunk."""
    # Setup
    mock_get_client.return_value = mock_supabase_client
    
    # Mock successful translated chunk creation
    mock_translated_chunk = {
        'id': str(mock_translated_chunk_id),
        'translation_id': str(mock_translation_id),
        'chunk_id': str(mock_chunk_id),
        'translated_content': 'Contenido traducido',
        'sequence_number': 1,
        'metadata': {},
        'created_at': '2023-01-01T00:00:00',
        'updated_at': '2023-01-01T00:00:00'
    }
    mock_supabase_client.table().insert().execute.return_value.data = [mock_translated_chunk]
    
    # Execute
    chunk_create = models.TranslatedChunkCreate(
        translation_id=mock_translation_id,
        chunk_id=mock_chunk_id,
        translated_content='Contenido traducido',
        sequence_number=1
    )
    result = await create_translated_chunk(chunk_create)
    
    # Verify
    assert result.id == mock_translated_chunk_id
    assert result.translated_content == 'Contenido traducido'
    
    # Verify method calls
    mock_supabase_client.table.assert_called_with('translated_chunks')

@pytest.mark.asyncio
@patch('backend.db.crud.translations.get_supabase_client')
async def test_get_translated_chunks_by_translation(mock_get_client, mock_supabase_client):
    """Test getting translated chunks by translation ID."""
    # Setup
    mock_get_client.return_value = mock_supabase_client
    
    # Mock successful translated chunks retrieval
    mock_translated_chunk1 = {
        'id': str(uuid.uuid4()),
        'translation_id': str(mock_translation_id),
        'chunk_id': str(uuid.uuid4()),
        'translated_content': 'Chunk 1 traducido',
        'sequence_number': 0,
        'metadata': {},
        'created_at': '2023-01-01T00:00:00',
        'updated_at': '2023-01-01T00:00:00'
    }
    mock_translated_chunk2 = {
        'id': str(uuid.uuid4()),
        'translation_id': str(mock_translation_id),
        'chunk_id': str(uuid.uuid4()),
        'translated_content': 'Chunk 2 traducido',
        'sequence_number': 1,
        'metadata': {},
        'created_at': '2023-01-01T00:00:00',
        'updated_at': '2023-01-01T00:00:00'
    }
    mock_supabase_client.table().select().eq().order().execute.return_value.data = [
        mock_translated_chunk1, mock_translated_chunk2
    ]
    
    # Execute
    results = await get_translated_chunks_by_translation(mock_translation_id)
    
    # Verify
    assert len(results) == 2
    assert results[0].translated_content == 'Chunk 1 traducido'
    assert results[1].translated_content == 'Chunk 2 traducido'
    
    # Verify method calls
    mock_supabase_client.table.assert_called_with('translated_chunks')

@pytest.mark.asyncio
@patch('backend.db.crud.translations.get_translation_by_id')
@patch('backend.db.crud.translations.get_translated_chunks_by_translation')
async def test_get_translation_with_chunks(
    mock_get_translated_chunks,
    mock_get_translation
):
    """Test getting a translation with its translated chunks."""
    # Setup
    # Mock translation
    mock_translation_obj = models.Translation(
        id=mock_translation_id,
        chunk_set_id=mock_chunk_set_id,
        user_id=mock_user_id,
        target_language='Spanish',
        name='Test Translation',
        status='completed',
        completed_chunks=5,
        total_chunks=5,
        ai_model='gpt-4',
        metadata={},
        created_at='2023-01-01T00:00:00',
        updated_at='2023-01-01T00:00:00'
    )
    mock_get_translation.return_value = mock_translation_obj
    
    # Mock translated chunks
    mock_chunks = [
        models.TranslatedChunk(
            id=uuid.uuid4(),
            translation_id=mock_translation_id,
            chunk_id=uuid.uuid4(),
            translated_content='Contenido 1',
            sequence_number=0,
            metadata={},
            created_at='2023-01-01T00:00:00',
            updated_at='2023-01-01T00:00:00'
        ),
        models.TranslatedChunk(
            id=uuid.uuid4(),
            translation_id=mock_translation_id,
            chunk_id=uuid.uuid4(),
            translated_content='Contenido 2',
            sequence_number=1,
            metadata={},
            created_at='2023-01-01T00:00:00',
            updated_at='2023-01-01T00:00:00'
        )
    ]
    mock_get_translated_chunks.return_value = mock_chunks
    
    # Execute
    result = await get_translation_with_chunks(mock_translation_id)
    
    # Verify
    assert result.id == mock_translation_id
    assert result.name == 'Test Translation'
    assert len(result.translated_chunks) == 2
    assert result.translated_chunks[0].translated_content == 'Contenido 1'
    assert result.translated_chunks[1].translated_content == 'Contenido 2'
    
    # Verify calls
    mock_get_translation.assert_called_once_with(mock_translation_id)
    mock_get_translated_chunks.assert_called_once_with(mock_translation_id) 