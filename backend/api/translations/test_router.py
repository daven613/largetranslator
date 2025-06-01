"""
Tests for the translations API router.
"""
import pytest
import uuid
import os
from unittest.mock import AsyncMock, patch, MagicMock, call
from datetime import datetime

from fastapi import FastAPI, status
from fastapi.testclient import TestClient
from fastapi.responses import JSONResponse

from backend.api.main import app
from backend.api.translations import router
from backend.api.translations.schemas import TranslationCreateRequest
from backend.db import models
from backend.api import dependencies

# Create test client
client = TestClient(app)

# Mock data
mock_user_id = uuid.uuid4()
mock_chunk_set_id = uuid.uuid4()
mock_translation_id = uuid.uuid4()
mock_chunk_id = uuid.uuid4()
mock_document_id = uuid.uuid4()

# Mock user for dependency override
mock_user = {"id": str(mock_user_id), "email": "test@example.com"}

# Override the authentication dependency
@pytest.fixture(autouse=True)
def setup_auth_override():
    """Override auth dependency for all tests"""
    app.dependency_overrides[dependencies.get_current_user] = lambda: mock_user
    yield
    app.dependency_overrides.clear()

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
        created_at="2023-01-01T00:00:00",
        updated_at="2023-01-01T00:00:00"
    )

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
def mock_chunk_data():
    """Fixture to provide mock chunk data."""
    return {
        "id": str(mock_chunk_id),
        "chunk_set_id": str(mock_chunk_set_id),
        "document_id": str(mock_document_id),
        "content": "Test content",
        "sequence_number": 0,
        "metadata": {},
        "embedding": None,
        "created_at": "2023-01-01T00:00:00",
        "updated_at": "2023-01-01T00:00:00"
    }

@pytest.fixture
def mock_translated_chunk():
    """Fixture to create a mock translated chunk."""
    return models.TranslatedChunk(
        id=uuid.uuid4(),
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
        chunk_size=1000,
        total_chunks=5,
        created_at="2023-01-01T00:00:00",
        updated_at="2023-01-01T00:00:00"
    )

@pytest.fixture
def mock_chunk_set_data():
    """Fixture to provide mock chunk set data."""
    return {
        "id": str(mock_chunk_set_id),
        "document_id": str(mock_document_id),
        "user_id": str(mock_user_id),
        "name": "Test Chunk Set",
        "chunk_size": 1000,
        "chunk_overlap": 200,
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
        "name": "Test Document",
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
        name="Test Document",
        file_path="/path/to/document.txt",
        file_size=1000,
        metadata={},
        created_at="2023-01-01T00:00:00",
        updated_at="2023-01-01T00:00:00"
    )

@pytest.mark.asyncio
@patch('backend.api.translations.router.get_chunk_set_by_id')
@patch('backend.api.translations.router.get_document_by_id')
@patch('backend.api.translations.router.get_chunks_by_chunk_set_id')
@patch('backend.api.translations.router.create_translation')
@patch('backend.api.translations.router.process_translation_job')
async def test_create_translation(
    mock_process_job,
    mock_create_translation,
    mock_get_chunks_by_chunk_set_id,
    mock_get_document_by_id,
    mock_get_chunk_set_by_id,
    mock_chunk_set,
    mock_document,
    mock_translation,
    mock_chunk,
    mock_chunk_set_id
):
    """Test creating a translation."""
    # Setup mocks
    mock_get_chunk_set_by_id.return_value = mock_chunk_set
    mock_get_document_by_id.return_value = mock_document
    mock_get_chunks_by_chunk_set_id.return_value = [mock_chunk]
    mock_create_translation.return_value = mock_translation
    mock_process_job.return_value = None
    
    # Test data
    test_data = {
        "chunk_set_id": str(mock_chunk_set_id),
        "prompt": "Translate this text to Spanish"
    }
    
    # Send request
    response = client.post("/api/translations/", json=test_data)
    
    # Assertions
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["id"] == str(mock_translation_id)
    assert response.json()["target_language"] == "Spanish"
    
    # Verify mocks were called correctly
    mock_get_chunk_set_by_id.assert_called_once_with(mock_chunk_set_id)
    mock_get_document_by_id.assert_called_once_with(mock_chunk_set.document_id)
    mock_create_translation.assert_called_once()

@pytest.mark.asyncio
@patch('backend.api.translations.router.get_translations_by_user')
async def test_get_translations(
    mock_get_translations_by_user,
    mock_translation
):
    """Test getting all translations for a user."""
    # Setup mock
    mock_get_translations_by_user.return_value = [mock_translation]
    
    # Send request
    response = client.get("/api/translations/")
    
    # Assertions
    assert response.status_code == status.HTTP_200_OK
    assert "translations" in response.json()
    assert len(response.json()["translations"]) == 1
    assert response.json()["translations"][0]["id"] == str(mock_translation_id)
    
    # Verify mock was called correctly
    mock_get_translations_by_user.assert_called_once_with(mock_user_id)

@pytest.mark.asyncio
@patch('backend.api.translations.router.get_translation_by_id')
async def test_get_translation(
    mock_get_translation_by_id,
    mock_translation
):
    """Test getting a specific translation."""
    # Setup mock
    mock_get_translation_by_id.return_value = mock_translation
    
    # Send request - use the ID from the mock_translation
    response = client.get(f"/api/translations/{mock_translation.id}")
    
    # Assertions
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["id"] == str(mock_translation.id)
    assert response.json()["target_language"] == "Spanish"
    
    # Verify mock was called correctly
    mock_get_translation_by_id.assert_called_once_with(mock_translation.id)

@pytest.mark.asyncio
@patch('backend.api.translations.router.get_translation_by_id')
@patch('backend.api.translations.router.delete_translation')
async def test_delete_translation(
    mock_delete_translation,
    mock_get_translation_by_id,
    mock_translation,
    mock_translation_id
):
    """Test deleting a translation."""
    # Setup mock
    mock_get_translation_by_id.return_value = mock_translation
    mock_delete_translation.return_value = True
    
    # Send request
    response = client.delete(f"/api/translations/{mock_translation_id}")
    
    # Assertions
    assert response.status_code == status.HTTP_204_NO_CONTENT
    
    # Verify mock was called correctly
    mock_get_translation_by_id.assert_called_once_with(mock_translation_id)
    mock_delete_translation.assert_called_once_with(mock_translation_id)

@pytest.mark.asyncio
@patch('backend.api.translations.router.translate_chunk')
@patch('backend.api.translations.router.get_chunks_by_chunk_set_id')
@patch('backend.api.translations.router.get_translation_by_id')
async def test_start_translation(
    mock_get_translation_by_id,
    mock_get_chunks_by_chunk_set_id,
    mock_translate_chunk,
    mock_translation,
    mock_chunk,
    mock_translation_id
):
    """Test starting a translation process."""
    # Setup mocks
    mock_get_translation_by_id.return_value = mock_translation
    mock_get_chunks_by_chunk_set_id.return_value = [mock_chunk]
    mock_translate_chunk.return_value = True
    
    # Send request
    response = client.post(f"/api/translations/{mock_translation_id}/start")
    
    # Assertions
    assert response.status_code == status.HTTP_202_ACCEPTED
    
    # Verify mocks were called correctly
    mock_get_translation_by_id.assert_called_once_with(mock_translation_id)
    mock_get_chunks_by_chunk_set_id.assert_called_once_with(mock_translation.chunk_set_id)

@pytest.mark.asyncio
@patch('backend.api.translations.router.get_translation_by_id')
async def test_get_translation_status(
    mock_get_translation_by_id,
    mock_translation
):
    """Test getting the status of a translation."""
    # Setup mock
    mock_get_translation_by_id.return_value = mock_translation
    
    # Send request
    response = client.get(f"/api/translations/{mock_translation.id}/status")
    
    # Assertions
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["id"] == str(mock_translation.id)
    assert response.json()["status"] == "pending"
    assert "progress" in response.json()
    
    # Verify mock was called correctly
    mock_get_translation_by_id.assert_called_once_with(mock_translation.id)

@pytest.mark.asyncio
@patch('backend.api.translations.router.get_translation_by_id')
@patch('os.path.exists')
@patch('backend.external_services.supabase.storage_service.SupabaseStorageService')
@patch('fastapi.responses.FileResponse')
async def test_download_translated_document(
    mock_file_response,
    mock_storage_service,
    mock_path_exists,
    mock_get_translation_by_id,
    mock_translation
):
    """Test downloading a translated document."""
    # Setup mocks - create a completed translation with output path
    modified_translation = mock_translation.copy()
    modified_translation.status = "completed"
    modified_translation.output_file_path = "translations/123/test_file.txt"
    mock_get_translation_by_id.return_value = modified_translation
    
    # Mock storage service
    mock_storage_service_instance = mock_storage_service.return_value
    mock_storage_service_instance.download_file.return_value = None
    
    # Mock file response
    mock_path_exists.return_value = True
    mock_file_response.return_value = JSONResponse(content={"filename": "test_file.txt"})
    
    # Patch the FileResponse class
    with patch('backend.api.translations.router.FileResponse', return_value=mock_file_response.return_value):
        # Send request
        response = client.get(f"/api/translations/{mock_translation.id}/download")
        
        # Assertions
        assert response.status_code == status.HTTP_200_OK
        
        # Verify mocks were called correctly
        mock_get_translation_by_id.assert_called_once_with(mock_translation.id)
        mock_storage_service_instance.download_file.assert_called_once()

@pytest.mark.asyncio
@patch('backend.api.translations.router.get_translation_by_id')
@patch('backend.api.translations.router.update_translation')
@patch('backend.api.translations.router.get_chunks_by_chunk_set_id')
@patch('backend.api.translations.router.translate_chunk')
async def test_regenerate_translation(
    mock_translate_chunk,
    mock_get_chunks_by_chunk_set_id,
    mock_update_translation,
    mock_get_translation_by_id,
    mock_translation,
    mock_chunk
):
    """Test regenerating a translation."""
    # Setup mocks
    mock_get_translation_by_id.return_value = mock_translation
    mock_update_translation.return_value = mock_translation
    mock_get_chunks_by_chunk_set_id.return_value = [mock_chunk]
    mock_translate_chunk.return_value = True
    
    # Test data
    test_data = {
        "chunk_ids": [str(mock_chunk.id)]
    }
    
    # Send request
    response = client.post(f"/api/translations/{mock_translation.id}/regenerate", json=test_data)
    
    # Assertions
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["id"] == str(mock_translation.id)
    
    # Verify mocks were called correctly
    # The router calls get_translation_by_id and update_translation multiple times
    assert mock_get_translation_by_id.call_count >= 1
    assert mock_update_translation.call_count >= 1
    assert mock_translate_chunk.call_count >= 1 