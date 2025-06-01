#!/usr/bin/env python3
"""
Test script to verify that user authentication context is working properly with RLS.
This test will bypass file upload and directly test database operations.
"""
import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Add backend to Python path
backend_dir = Path(__file__).resolve().parent
sys.path.append(str(backend_dir))

from external_services.supabase.client import get_user_supabase_client
from external_services.supabase.auth_service import SupabaseAuthService

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
test_env_path = backend_dir / "test_end_to_end" / ".test_env"
env_path = backend_dir / ".env"

load_dotenv(dotenv_path=env_path)
load_dotenv(dotenv_path=test_env_path, override=True)

def test_auth_context():
    """Test that user authentication context works for database operations."""
    logger.info("=== Testing User Authentication Context ===")
    
    # Get test credentials
    test_email = os.getenv("SUPABASE_TEST_USER_EMAIL")
    test_password = os.getenv("SUPABASE_TEST_USER_PASSWORD")
    jwt_token = os.getenv("SUPABASE_TEST_JWT")
    
    if not all([test_email, test_password, jwt_token]):
        logger.error("Missing test credentials. Please ensure .test_env file exists with proper values.")
        return False
    
    logger.info(f"Testing with user: {test_email}")
    
    try:
        # Test 1: Sign in and get user info
        logger.info("Step 1: Authenticating user...")
        auth_response = SupabaseAuthService.sign_in(test_email, test_password)
        user = auth_response["user"]
        session = auth_response["session"]
        access_token = session.access_token
        user_id = user.id
        
        logger.info(f"Successfully authenticated user: {user_id}")
        
        # Test 2: Create user-specific client
        logger.info("Step 2: Creating user-specific Supabase client...")
        user_client = get_user_supabase_client(access_token)
        logger.info("Successfully created user-specific client")
        
        # Test 3: Try to insert a test document (this should work with proper RLS)
        logger.info("Step 3: Testing database insert with RLS...")
        test_doc_data = {
            "user_id": user_id,
            "name": "auth_test_document",
            "file_size": 100,
            "metadata": {"test": True}
        }
        
        try:
            # Try to insert into documents table
            result = user_client.table("documents").insert(test_doc_data).execute()
            if result.data:
                logger.info(f"✓ Successfully inserted document with RLS: {result.data[0]['id']}")
                document_id = result.data[0]['id']
                
                # Test 4: Try to select the document back (should work)
                logger.info("Step 4: Testing database select with RLS...")
                select_result = user_client.table("documents").select("*").eq("id", document_id).execute()
                if select_result.data:
                    logger.info(f"✓ Successfully selected document: {select_result.data[0]['name']}")
                else:
                    logger.error("✗ Failed to select document - RLS might be blocking access")
                    return False
                
                # Test 5: Clean up - delete the test document
                logger.info("Step 5: Cleaning up test document...")
                delete_result = user_client.table("documents").delete().eq("id", document_id).execute()
                logger.info("✓ Successfully cleaned up test document")
                
                return True
            else:
                logger.error("✗ Insert operation returned no data")
                return False
                
        except Exception as db_error:
            logger.error(f"✗ Database operation failed: {str(db_error)}")
            return False
    
    except Exception as e:
        logger.error(f"✗ Test failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_auth_context()
    if success:
        logger.info("=== ✓ All tests passed - User authentication context is working ===")
        sys.exit(0)
    else:
        logger.error("=== ✗ Tests failed - User authentication context is not working ===")
        sys.exit(1) 