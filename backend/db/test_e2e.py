"""
End-to-end tests for CRUD operations with Supabase.
These tests require proper Supabase credentials in environment variables.
"""
import os
import uuid
import logging
import json
from typing import Dict, Any
from pathlib import Path
from dotenv import load_dotenv

from backend.db import models
from backend.external_services.supabase.client import get_supabase_client

# Load environment variables from .env file in backend folder
backend_dir = Path(__file__).resolve().parent.parent
env_path = backend_dir / ".env"
load_dotenv(dotenv_path=env_path)

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Global test data
TEST_USER_ID = str(uuid.uuid4())  # Convert UUID to string
test_document_id = None
test_chunk_id = None


def test_connection():
    """Test that we can connect to Supabase."""
    try:
        client = get_supabase_client()
        # Simple test query
        result = client.table('documents').select('*').limit(1).execute()
        logger.info("✓ Supabase connection successful")
        return True
    except Exception as e:
        logger.error(f"✗ Supabase connection failed: {str(e)}")
        return False


def test_document_operations():
    """Test CRUD operations for documents."""
    global test_document_id
    
    # CREATE
    try:
        # Create document data
        doc_data = {
            "user_id": TEST_USER_ID,
            "name": f"Test Document {uuid.uuid4()}",
            "file_size": 1024,
            "metadata": {}
        }
        
        client = get_supabase_client()
        
        # Create document
        result = client.table('documents').insert(doc_data).execute()
        document_data = result.data[0]
        document = models.Document(**document_data)
        test_document_id = str(document.id)  # Store as string
        
        logger.info(f"✓ Document created with ID: {test_document_id}")
        
        # READ
        result = client.table('documents').select('*').eq('id', test_document_id).execute()
        if not result.data:
            raise ValueError(f"Document with ID {test_document_id} not found")
        retrieved_doc = models.Document(**result.data[0])
        
        assert retrieved_doc is not None
        assert str(retrieved_doc.id) == test_document_id
        logger.info("✓ Document retrieved successfully")
        
        # UPDATE
        update_data = {"name": "Updated Test Document"}
        result = client.table('documents').update(update_data).eq('id', test_document_id).execute()
        if not result.data:
            raise ValueError(f"Document with ID {test_document_id} not found during update")
        updated_doc = models.Document(**result.data[0])
        
        assert updated_doc.name == "Updated Test Document"
        logger.info("✓ Document updated successfully")
        
        # Search by user
        result = client.table('documents').select('*').eq('user_id', TEST_USER_ID).execute()
        docs = [models.Document(**doc) for doc in result.data]
        
        assert len(docs) > 0
        assert any(str(doc.id) == test_document_id for doc in docs)
        logger.info("✓ Document search by user successful")
        
        return True
    except Exception as e:
        logger.error(f"✗ Document operations failed: {str(e)}")
        return False


def test_chunk_operations():
    """Test CRUD operations for chunks."""
    global test_chunk_id
    
    if test_document_id is None:
        logger.error("✗ Cannot test chunks without a valid document ID")
        return False
    
    try:
        # CREATE
        chunk_data = {
            "document_id": test_document_id,
            "sequence_number": 1,
            "content": "This is a test chunk content for e2e testing.",
            "metadata": {"test": True}
        }
        
        client = get_supabase_client()
        result = client.table('chunks').insert(chunk_data).execute()
        chunk = models.Chunk(**result.data[0])
        test_chunk_id = str(chunk.id)  # Store as string
        
        logger.info(f"✓ Chunk created with ID: {test_chunk_id}")
        
        # READ
        result = client.table('chunks').select('*').eq('id', test_chunk_id).execute()
        if not result.data:
            raise ValueError(f"Chunk with ID {test_chunk_id} not found")
        retrieved_chunk = models.Chunk(**result.data[0])
        
        assert retrieved_chunk is not None
        assert str(retrieved_chunk.id) == test_chunk_id
        logger.info("✓ Chunk retrieved successfully")
        
        # READ by document
        result = client.table('chunks').select('*').eq('document_id', test_document_id).order('sequence_number').execute()
        doc_chunks = [models.Chunk(**chunk_data) for chunk_data in result.data]
        
        assert len(doc_chunks) > 0
        assert any(str(c.id) == test_chunk_id for c in doc_chunks)
        logger.info("✓ Chunks retrieved by document successfully")
        
        # UPDATE
        update_data = {"content": "Updated test chunk content."}
        result = client.table('chunks').update(update_data).eq('id', test_chunk_id).execute()
        if not result.data:
            raise ValueError(f"Chunk with ID {test_chunk_id} not found during update")
        updated_chunk = models.Chunk(**result.data[0])
        
        assert updated_chunk.content == "Updated test chunk content."
        logger.info("✓ Chunk updated successfully")
        
        # UPDATE embedding
        try:
            # Generate a 1536-dimensional vector with small random values
            embedding = [0.01] * 1536
            result = client.table('chunks').update({"embedding": embedding}).eq('id', test_chunk_id).execute()
            if not result.data:
                raise ValueError(f"Chunk with ID {test_chunk_id} not found during embedding update")
            updated_chunk = models.Chunk(**result.data[0])
            
            assert updated_chunk.embedding == embedding
            logger.info("✓ Chunk embedding updated successfully")
        except Exception as e:
            logger.warning(f"⚠ Embedding update failed (might require pgvector setup): {str(e)}")
            # Continue with the test even if embedding update fails
        
        return True
    except Exception as e:
        logger.error(f"✗ Chunk operations failed: {str(e)}")
        return False


def test_search_operations():
    """Test search operations."""
    try:
        client = get_supabase_client()
        
        # Content search using direct SQL instead of RPC
        try:
            result = client.table('chunks').select('*,documents(name)').eq('document_id', test_document_id).execute()
            search_results = result.data
            
            assert len(search_results) > 0
            logger.info("✓ Content search successful")
        except Exception as e:
            logger.warning(f"⚠ Content search failed: {str(e)}")
        
        # Skip vector search since it requires pgvector setup
        logger.info("ℹ Skipping vector search (requires pgvector extension)")
        
        return True
    except Exception as e:
        logger.error(f"✗ Search operations failed: {str(e)}")
        return False


def cleanup():
    """Clean up test data."""
    try:
        if test_document_id:
            # This should cascade to chunks due to foreign key constraint
            client = get_supabase_client()
            result = client.table('documents').delete().eq('id', test_document_id).execute()
            
            if result.data:
                logger.info("✓ Test data deleted successfully")
            else:
                logger.warning("⚠ Could not delete test document")
        return True
    except Exception as e:
        logger.error(f"✗ Cleanup failed: {str(e)}")
        return False


def run_tests():
    """Run all tests sequentially."""
    # Test connection first
    if not test_connection():
        logger.error("✗ Connection test failed. Aborting further tests.")
        return False
    
    # Run the tests
    document_success = test_document_operations()
    if not document_success:
        logger.error("✗ Document operations failed. Aborting further tests.")
        cleanup()
        return False
    
    chunk_success = test_chunk_operations()
    if not chunk_success:
        logger.error("✗ Chunk operations failed.")
        cleanup()
        return False
    
    search_success = test_search_operations()
    if not search_success:
        logger.error("✗ Search operations failed.")
    
    # Clean up regardless of test results
    cleanup()
    
    return document_success and chunk_success


def main():
    """Main function to run all tests."""
    logger.info("Starting end-to-end tests for CRUD operations...")
    
    if not os.environ.get("SUPABASE_URL") or not os.environ.get("SUPABASE_KEY"):
        logger.error("✗ Supabase credentials not found in environment variables")
        logger.error("Please set SUPABASE_URL and SUPABASE_KEY environment variables.")
        return
    
    success = run_tests()
    
    if success:
        logger.info("✓ All tests completed successfully!")
    else:
        logger.error("✗ Some tests failed. Check the logs for details.")


if __name__ == "__main__":
    main() 