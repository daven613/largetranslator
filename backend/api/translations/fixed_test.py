"""
Simplified test for translations API.
"""
import pytest
import uuid
from unittest.mock import patch, MagicMock

from fastapi import status
from fastapi.testclient import TestClient

from backend.api.main import app
from backend.db import models
from backend.api import dependencies

# Create test client
client = TestClient(app)

# Mock data
mock_user_id = uuid.uuid4()
mock_chunk_set_id = uuid.uuid4()
mock_translation_id = uuid.uuid4()

# Test user for dependency override
test_user = {"id": str(mock_user_id), "email": "test@example.com"}

@pytest.fixture(autouse=True)
def setup_auth_override():
    """Override auth dependency for all tests"""
    app.dependency_overrides[dependencies.get_current_user] = lambda: test_user
    yield
    app.dependency_overrides.clear()

@pytest.fixture
def mock_translation_data():
    """Mock translation data fixture"""
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

@pytest.mark.asyncio
@patch('backend.api.translations.router.get_translations_by_user')
async def test_get_translations(mock_get_translations, mock_translation_data):
    """Test getting all translations for a user."""
    # Create a translation model from the data
    mock_translation = models.Translation(**mock_translation_data)
    
    # Setup the mock to return a list with our translation
    mock_get_translations.return_value = [mock_translation]
    
    # Send request to the endpoint
    response = client.get("/api/translations/")
    
    # Check the response
    assert response.status_code == status.HTTP_200_OK
    assert "translations" in response.json()
    assert len(response.json()["translations"]) == 1
    
    # Verify the mock was called correctly
    mock_get_translations.assert_called_once_with(mock_user_id) 