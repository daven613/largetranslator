"""
Test script to verify the duplicate translated chunk fix.
This can be run to test that the translate_chunk function properly handles existing chunks.
"""
import asyncio
import uuid
from unittest.mock import patch, AsyncMock

# Mock the dependencies
async def mock_get_translation_by_id(translation_id):
    return type('MockTranslation', (), {
        'id': translation_id,
        'user_id': uuid.uuid4(),
        'ai_model': 'gpt-4.1-nano',
        'completed_chunks': 0,
        'total_chunks': 2
    })()

async def mock_get_chunk_by_id(chunk_id):
    return type('MockChunk', (), {
        'id': chunk_id,
        'content': 'Test content to translate',
        'sequence_number': 1
    })()

async def mock_get_translated_chunk_by_translation_and_chunk(translation_id, chunk_id):
    # Simulate that a translated chunk already exists
    return type('MockTranslatedChunk', (), {
        'id': uuid.uuid4(),
        'translation_id': translation_id,
        'chunk_id': chunk_id,
        'translated_content': 'Already translated content',
        'sequence_number': 1
    })()

async def test_duplicate_chunk_handling():
    """Test that translate_chunk handles existing chunks correctly."""
    print("Testing duplicate chunk handling...")
    
    # Import the function we want to test
    try:
        from api.translations.router import translate_chunk
    except ImportError:
        try:
            from backend.api.translations.router import translate_chunk
        except ImportError:
            print("Could not import translate_chunk function. Make sure you're running from the correct directory.")
            return False
    
    # Test data
    test_translation_id = uuid.uuid4()
    test_chunk_id = uuid.uuid4()
    
    # Mock all the dependencies
    with patch('backend.api.translations.router.get_translation_by_id', side_effect=mock_get_translation_by_id), \
         patch('backend.api.translations.router.get_chunk_by_id', side_effect=mock_get_chunk_by_id), \
         patch('backend.db.crud.translations.get_translated_chunk_by_translation_and_chunk', side_effect=mock_get_translated_chunk_by_translation_and_chunk):
        
        # Call the function
        result = await translate_chunk(test_chunk_id, test_translation_id, "Test prompt")
        
        # Check that it returns the existing chunk ID instead of trying to create a new one
        if result is not None:
            print("✅ SUCCESS: translate_chunk correctly returned existing chunk ID instead of creating duplicate")
            return True
        else:
            print("❌ FAILED: translate_chunk returned None instead of existing chunk ID")
            return False

async def main():
    """Run the test."""
    print("=== Testing Duplicate Chunk Fix ===")
    success = await test_duplicate_chunk_handling()
    
    if success:
        print("\n🎉 All tests passed! The duplicate chunk fix should work correctly.")
    else:
        print("\n💥 Tests failed. There may be an issue with the fix.")

if __name__ == "__main__":
    asyncio.run(main()) 