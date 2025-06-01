#!/usr/bin/env python3

"""
Debug script to test storage operations directly
"""
import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Add backend to Python path
backend_dir = Path(__file__).resolve().parent
sys.path.append(str(backend_dir))

from external_services.supabase.storage_service import SupabaseStorageService
from external_services.supabase.auth_service import SupabaseAuthService

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
test_env_path = backend_dir / "test_end_to_end" / ".test_env"
env_path = backend_dir / ".env"

load_dotenv(env_path)
load_dotenv(test_env_path, override=True)

def main():
    print("=== Storage Debug Test ===")
    
    try:
        # Authenticate user
        auth_service = SupabaseAuthService()
        user_data = auth_service.sign_in("daven613us@gmail.com", "12341234")
        access_token = user_data["session"].access_token
        user_id = user_data["user"].id
        
        print(f"Authenticated user: {user_id}")
        print(f"Access token (first 50 chars): {access_token[:50]}...")
        
        # Test file details
        test_content = b"This is a test file for storage debugging."
        test_filename = "debug_test.txt"
        
        print(f"\n=== Testing Storage Upload ===")
        print(f"User ID: {user_id}")
        print(f"Filename: {test_filename}")
        print(f"Content length: {len(test_content)}")
        
        # Try to upload file with detailed error logging
        try:
            result = SupabaseStorageService.upload_file(
                user_id=str(user_id),
                file_name=test_filename,
                file_content=test_content,
                content_type="text/plain",
                user_token=access_token
            )
            print(f"✓ Upload successful: {result}")
            
            # Try to list files
            print(f"\n=== Testing File List ===")
            files = SupabaseStorageService.list_files(str(user_id))
            print(f"Files found: {files}")
            
            # Try to delete the test file
            print(f"\n=== Testing File Deletion ===")
            delete_result = SupabaseStorageService.delete_file(str(user_id), test_filename)
            print(f"✓ Delete successful: {delete_result}")
            
        except Exception as storage_error:
            print(f"✗ Storage error: {storage_error}")
            print(f"Error type: {type(storage_error)}")
            
            # Try to get more details about the error
            if hasattr(storage_error, 'response'):
                print(f"Response status: {storage_error.response.status_code}")
                print(f"Response content: {storage_error.response.text}")
            
    except Exception as e:
        print(f"Authentication or general error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 