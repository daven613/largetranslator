"""
Tests for the OpenAI translation module.
"""
import pytest
import os
from unittest.mock import AsyncMock, patch, MagicMock, call

@pytest.fixture(autouse=True)
def mock_env_api_key():
    """Fixture to mock OpenAI API key environment variable."""
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-api-key"}):
        yield

from backend.external_services.open_ai.translation import translate_text

@pytest.mark.asyncio
@patch('backend.external_services.open_ai.translation.get_client')
async def test_translate_text(mock_get_client):
    """Test the translate_text function."""
    # Setup mock OpenAI client and response
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "Texto traducido"
    # Use regular MagicMock since OpenAI client is synchronous
    mock_client.chat.completions.create = MagicMock(return_value=mock_response)
    
    # Execute the function
    result = await translate_text("Text to translate", "Spanish")
    
    # Verify the result
    assert result == "Texto traducido"
    
    # Verify the OpenAI API was called correctly
    mock_get_client.assert_called_once()
    mock_client.chat.completions.create.assert_called_once()
    
    # Check that the API was called with the correct arguments
    call_args = mock_client.chat.completions.create.call_args[1]
    assert call_args["model"] == "gpt-4"
    
    # Check that the messages include the right instructions
    messages = call_args["messages"]
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert "professional translator" in messages[0]["content"].lower()
    assert messages[1]["role"] == "user"
    assert "Text to translate" in messages[1]["content"]

@pytest.mark.asyncio
@patch('backend.external_services.open_ai.translation.get_client')
async def test_translate_text_with_custom_model(mock_get_client):
    """Test the translate_text function with a custom model."""
    # Setup mock OpenAI client and response
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "Texte traduit"
    # Use regular MagicMock since OpenAI client is synchronous
    mock_client.chat.completions.create = MagicMock(return_value=mock_response)
    
    # Execute the function with a custom model
    result = await translate_text("Text to translate", "French", model="gpt-3.5-turbo")
    
    # Verify the result
    assert result == "Texte traduit"
    
    # Verify the OpenAI API was called with the custom model
    call_args = mock_client.chat.completions.create.call_args[1]
    assert call_args["model"] == "gpt-3.5-turbo"

@pytest.mark.asyncio
@patch('backend.external_services.open_ai.translation.get_client')
@patch('backend.external_services.open_ai.translation.logger')
async def test_translate_text_error_handling(mock_logger, mock_get_client):
    """Test error handling in the translate_text function."""
    # Setup mock client to raise an exception
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    # Use regular MagicMock with side_effect for synchronous error
    mock_client.chat.completions.create = MagicMock(side_effect=Exception("API error"))
    
    # Execute the function
    with pytest.raises(Exception) as exc_info:
        await translate_text("Text to translate", "Spanish")
    
    # Verify the exception
    assert "API error" in str(exc_info.value)
    
    # Verify logging
    mock_logger.error.assert_called_once()

@pytest.mark.asyncio
@patch('backend.external_services.open_ai.translation.get_client')
async def test_translate_text_with_different_model(mock_get_client):
    """Test translate_text with a different model parameter."""
    # Setup mock OpenAI client and response
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    
    mock_completion = MagicMock()
    mock_choice = MagicMock()
    mock_message = MagicMock()
    
    mock_message.content = "Texto traducido"
    mock_choice.message = mock_message
    mock_completion.choices = [mock_choice]
    
    mock_completions = MagicMock()
    # Use regular MagicMock since OpenAI client is synchronous
    mock_completions.create = MagicMock(return_value=mock_completion)
    mock_client.chat.completions = mock_completions
    
    # Call function with different model
    custom_model = "gpt-3.5-turbo"
    result = await translate_text("Test text", "Spanish", custom_model)
    
    # Verify result
    assert result == "Texto traducido"
    
    # Verify the correct model was used
    call_args = mock_completions.create.call_args[1]
    assert call_args["model"] == custom_model

@pytest.mark.asyncio
@patch('backend.external_services.open_ai.translation.get_client')
async def test_translate_text_preserves_formatting(mock_get_client):
    """Test that translate_text preserves formatting instruction in prompt."""
    # Setup mock OpenAI client and response
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    
    mock_completion = MagicMock()
    mock_choice = MagicMock()
    mock_message = MagicMock()
    
    mock_message.content = "Texto\ntraducido\ncon formato"
    mock_choice.message = mock_message
    mock_completion.choices = [mock_choice]
    
    mock_completions = MagicMock()
    # Use regular MagicMock since OpenAI client is synchronous
    mock_completions.create = MagicMock(return_value=mock_completion)
    mock_client.chat.completions = mock_completions
    
    # Call function with multi-line text
    input_text = "Test\ntext\nwith formatting"
    result = await translate_text(input_text, "Spanish", "gpt-4")
    
    # Verify result
    assert result == "Texto\ntraducido\ncon formato"
    
    # Verify the prompt contains preservation instructions
    call_args = mock_completions.create.call_args[1]
    assert "Preserve formatting" in call_args["messages"][1]["content"] 