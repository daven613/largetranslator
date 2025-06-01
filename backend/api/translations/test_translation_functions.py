"""
Tests for the translation processing functions.
"""
import pytest
import uuid
import os
from unittest.mock import AsyncMock, patch, MagicMock, call
from datetime import datetime

from backend.db import models

# Mock data
mock_user_id = uuid.uuid4()
mock_chunk_set_id = uuid.uuid4()
mock_translation_id = uuid.uuid4()
mock_chunk_id = uuid.uuid4()
mock_document_id = uuid.uuid4()
mock_translated_chunk_id = uuid.uuid4()

# Fixtures
@pytest.fixture
def mock_translation():
    """Fixture to create a mock translation."""
    return models.Translation(
        id=mock_translation_id,
        chunk_set_id=mock_chunk_set_id,
        user_id=mock_user_id,
        target_language="Spanish",
        name="Test Translation",
        status="pending",
        completed_chunks=0,
        total_chunks=5,
        ai_model="gpt-4",
        metadata={},
        created_at="2023-01-01T00:00:00",
        updated_at="2023-01-01T00:00:00"
    )

@pytest.fixture
def mock_chunk():
    """Fixture to create a mock chunk."""
    return models.Chunk(
        id=mock_chunk_id,
        chunk_set_id=mock_chunk_set_id,
        document_id=mock_document_id,
        content="Test content",
        sequence_number=0,
        metadata={},
        embedding=None,
        created_at="2023-01-01T00:00:00",
        updated_at="2023-01-01T00:00:00"
    )

@pytest.fixture
def mock_translated_chunk():
    """Fixture to create a mock translated chunk."""
    return models.TranslatedChunk(
        id=mock_translated_chunk_id,
        translation_id=mock_translation_id,
        chunk_id=mock_chunk_id,
        translated_content="Contenido traducido",
        sequence_number=1,
        metadata={},
        created_at="2023-01-01T00:00:00",
        updated_at="2023-01-01T00:00:00"
    )

@pytest.fixture
def mock_chunk_set():
    """Fixture to create a mock chunk set."""
    return models.ChunkSet(
        id=mock_chunk_set_id,
        document_id=mock_document_id,
        name="Test Chunk Set",
        description="Test description",
        metadata={},
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

@pytest.fixture
def mock_translation_with_chunks(mock_translation_data, mock_translated_chunk_data):
    """Fixture to create a mock translation with translated chunks."""
    translation = models.Translation(**mock_translation_data)
    
    # We need to create a custom dict that includes translated_chunks
    translation_dict = {
        **mock_translation_data,
        "translated_chunks": [models.TranslatedChunk(**mock_translated_chunk_data)]
    }
    
    # Create TranslationWithChunks model
    return models.TranslationWithChunks(**translation_dict)

@pytest.fixture
def mock_translation_data():
    """Fixture to provide mock translation data."""
    return {
        "id": str(mock_translation_id),
        "chunk_set_id": str(mock_chunk_set_id),
        "user_id": str(mock_user_id),
        "target_language": "Spanish",
        "name": "Test Translation",
        "status": "pending",
        "completed_chunks": 0,
        "total_chunks": 5,
        "ai_model": "gpt-4",
        "metadata": {},
        "created_at": "2023-01-01T00:00:00",
        "updated_at": "2023-01-01T00:00:00"
    }

@pytest.fixture
def mock_translated_chunk_data():
    """Fixture to provide mock translated chunk data."""
    return {
        "id": str(mock_translated_chunk_id),
        "translation_id": str(mock_translation_id),
        "chunk_id": str(mock_chunk_id),
        "translated_content": "Contenido traducido",
        "sequence_number": 1,
        "metadata": {},
        "created_at": "2023-01-01T00:00:00",
        "updated_at": "2023-01-01T00:00:00"
    }

@pytest.fixture
def mock_document_data():
    """Fixture to provide mock document data."""
    return {
        "id": str(mock_document_id),
        "user_id": str(mock_user_id),
        "name": "Test Document.txt",  # Add file extension for test
        "file_path": "/path/to/document.txt",
        "file_type": "text/plain",
        "file_size": 1000,
        "content": "Test document content",
        "metadata": {},
        "created_at": "2023-01-01T00:00:00",
        "updated_at": "2023-01-01T00:00:00"
    }

@pytest.fixture
def mock_document():
    """Fixture to create a mock document."""
    return models.Document(
        id=mock_document_id,
        user_id=mock_user_id,
        name="Test Document.txt",
        file_path="/path/to/document.txt",
        file_type="text/plain",
        file_size=1000,
        content="Test document content",
        metadata={},
        created_at="2023-01-01T00:00:00",
        updated_at="2023-01-01T00:00:00"
    )

@pytest.mark.asyncio
@patch('backend.api.translations.router.get_translation_by_id', autospec=True)
@patch('backend.api.translations.router.get_chunk_by_id', autospec=True)
@patch('backend.api.translations.router.translate_text', autospec=True)
@patch('backend.api.translations.router.create_translated_chunk', autospec=True)
@patch('backend.api.translations.router.update_translation', autospec=True)
async def test_translate_chunk(
    mock_update_translation,
    mock_create_translated_chunk,
    mock_translate_text,
    mock_get_chunk,
    mock_get_translation,
    mock_translation_data,
    mock_chunk_data,
    mock_translated_chunk_data,
    mock_translation_id,
    mock_chunk_id
):
    """Test translating a single chunk."""
    # Import here to avoid import errors during collection
    from backend.api.translations.router import translate_chunk
    
    # Set up mocks
    mock_translation = models.Translation(**mock_translation_data)
    mock_chunk = models.Chunk(**mock_chunk_data)
    mock_translated_chunk = models.TranslatedChunk(**mock_translated_chunk_data)
    
    mock_get_translation.return_value = mock_translation
    mock_get_chunk.return_value = mock_chunk
    mock_translate_text.return_value = "Contenido traducido"
    mock_create_translated_chunk.return_value = mock_translated_chunk
    mock_update_translation.return_value = mock_translation
    
    # Call the function
    result = await translate_chunk(mock_chunk_id, mock_translation_id)
    
    # Verify the result
    assert result is not None
    
    # Verify the calls
    mock_get_translation.assert_called_once_with(mock_translation_id)
    mock_get_chunk.assert_called_once_with(mock_chunk_id)
    assert mock_translate_text.called
    assert mock_create_translated_chunk.called
    assert mock_update_translation.called

@pytest.mark.asyncio
@patch('backend.api.translations.router.get_translation_by_id', autospec=True)
@patch('backend.api.translations.router.get_chunks_by_chunk_set_id', autospec=True)
@patch('backend.api.translations.router.translate_chunk', autospec=True)
@patch('backend.api.translations.router.update_translation', autospec=True)
async def test_process_translation_job(
    mock_update_translation,
    mock_translate_chunk,
    mock_get_chunks,
    mock_get_translation,
    mock_translation_data,
    mock_chunk_data,
    mock_translation_id,
    mock_user_id
):
    """Test processing a complete translation job."""
    # Import here to avoid import errors during collection
    from backend.api.translations.router import process_translation_job
    
    # Set up mocks
    # Make sure translation user_id matches the mock_user_id to pass permission check
    translation_data = mock_translation_data.copy()
    translation_data['user_id'] = str(mock_user_id)
    mock_translation = models.Translation(**translation_data)
    mock_chunk = models.Chunk(**mock_chunk_data)
    
    mock_get_translation.return_value = mock_translation
    mock_get_chunks.return_value = [mock_chunk]
    mock_translate_chunk.return_value = True
    mock_update_translation.return_value = mock_translation
    
    # Call the function
    await process_translation_job(mock_translation_id, mock_user_id)
    
    # Verify the calls
    mock_get_translation.assert_called_once_with(mock_translation_id)
    mock_get_chunks.assert_called_once_with(mock_translation.chunk_set_id)
    mock_translate_chunk.assert_called_once()
    assert mock_update_translation.call_count >= 1

@pytest.mark.asyncio
@patch('backend.api.translations.router.get_translation_by_id', autospec=True)
@patch('backend.api.translations.router.get_chunk_by_id', autospec=True)
@patch('backend.api.translations.router.translate_text', autospec=True)
async def test_translate_chunk_translation_not_found(
    mock_translate_text,
    mock_get_chunk,
    mock_get_translation,
    mock_chunk_data,
    mock_translation_id,
    mock_chunk_id
):
    """Test translating a chunk when translation is not found."""
    # Import here to avoid import errors during collection
    from backend.api.translations.router import translate_chunk
    
    # Set up mocks
    mock_chunk = models.Chunk(**mock_chunk_data)
    
    mock_get_translation.return_value = None
    mock_get_chunk.return_value = mock_chunk
    
    # Call the function
    result = await translate_chunk(mock_chunk_id, mock_translation_id)
    
    # Verify the result
    assert result is None
    
    # Verify the calls
    mock_get_translation.assert_called_once_with(mock_translation_id)
    mock_get_chunk.assert_not_called()
    mock_translate_text.assert_not_called()

@pytest.mark.asyncio
@patch('backend.api.translations.router.get_translation_by_id', autospec=True)
@patch('backend.api.translations.router.get_chunk_by_id', autospec=True)
@patch('backend.api.translations.router.translate_text', autospec=True)
async def test_translate_chunk_chunk_not_found(
    mock_translate_text,
    mock_get_chunk,
    mock_get_translation,
    mock_translation_data,
    mock_translation_id,
    mock_chunk_id
):
    """Test translating a chunk when chunk is not found."""
    # Import here to avoid import errors during collection
    from backend.api.translations.router import translate_chunk
    
    # Set up mocks
    mock_translation = models.Translation(**mock_translation_data)
    
    mock_get_translation.return_value = mock_translation
    mock_get_chunk.return_value = None
    
    # Call the function
    result = await translate_chunk(mock_chunk_id, mock_translation_id)
    
    # Verify the result
    assert result is None
    
    # Verify the calls
    mock_get_translation.assert_called_once_with(mock_translation_id)
    mock_get_chunk.assert_called_once_with(mock_chunk_id)
    mock_translate_text.assert_not_called()

@pytest.mark.asyncio
@patch('backend.api.translations.router.get_translation_with_chunks', autospec=True)
@patch('backend.api.translations.router.get_chunk_set_by_id', autospec=True)
@patch('backend.api.translations.router.get_document_by_id', autospec=True)
@patch('backend.external_services.supabase.storage_service.SupabaseStorageService', autospec=True)
@patch('os.makedirs', autospec=True)
@patch('os.path.exists', autospec=True)
@patch('os.remove', autospec=True)
async def test_assemble_document(
    mock_remove,
    mock_path_exists,
    mock_makedirs,
    mock_storage_service,
    mock_get_document,
    mock_get_chunk_set,
    mock_get_translation_with_chunks,
    mock_translation_data,
    mock_chunk_set_data,
    mock_document_data,
    mock_translated_chunk_data
):
    """Test assembling a document from translated chunks."""
    # Import here to avoid import errors during collection
    from backend.api.translations.router import assemble_document
    
    # Set up mocks
    mock_storage_service_instance = mock_storage_service.return_value
    mock_storage_service_instance.upload_file.return_value = None
    
    # Create a translation with chunks
    translation_data = mock_translation_data.copy()
    translation_data['translated_chunks'] = [models.TranslatedChunk(**mock_translated_chunk_data)]
    translation_with_chunks = models.TranslationWithChunks(**translation_data)
    
    mock_chunk_set = models.ChunkSet(**mock_chunk_set_data)
    mock_document = models.Document(**mock_document_data)
    
    # Set up return values
    mock_get_translation_with_chunks.return_value = translation_with_chunks
    mock_get_chunk_set.return_value = mock_chunk_set
    mock_get_document.return_value = mock_document
    mock_path_exists.return_value = True
    
    # Call the function
    result = await assemble_document(mock_translation_with_chunks.id)
    
    # Assertions
    assert result is not None
    assert isinstance(result, str)
    assert "translations" in result
    
    # Verify mocks were called
    mock_get_translation_with_chunks.assert_called_once()
    mock_get_chunk_set.assert_called_once()
    mock_get_document.assert_called_once()
    mock_makedirs.assert_called_once()
    mock_storage_service_instance.upload_file.assert_called_once()
    mock_remove.assert_called_once()

@pytest.mark.asyncio
@patch('backend.api.translations.router.get_translation_with_chunks', autospec=True)
@patch('backend.api.translations.router.get_chunk_set_by_id', autospec=True)
@patch('backend.api.translations.router.get_document_by_id', autospec=True)
async def test_assemble_document_error_handling(
    mock_get_document,
    mock_get_chunk_set,
    mock_get_translation_with_chunks,
    mock_translation_id
):
    """Test error handling in assemble_document."""
    # Import here to avoid import errors during collection
    from backend.api.translations.router import assemble_document
    
    # Set up mock to raise exception
    mock_get_translation_with_chunks.return_value = None
    
    # Call the function and check for exception
    with pytest.raises(ValueError):
        await assemble_document(mock_translation_id)
    
    # Verify mocks were called
    mock_get_translation_with_chunks.assert_called_once_with(mock_translation_id)
    mock_get_chunk_set.assert_not_called()
    mock_get_document.assert_not_called() 