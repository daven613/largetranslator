#!/usr/bin/env python3
"""
Debug script to test actual storage upload operation.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
backend_dir = Path(__file__).resolve().parent
env_path = backend_dir / ".env"
test_env_path = backend_dir / "test_end_to_end" / ".test_env"

load_dotenv(env_path)
if test_env_path.exists():
    load_dotenv(test_env_path, override=True)

# Import after loading env vars
from external_services.supabase.auth_service import SupabaseAuthService
from external_services.supabase.storage_service import SupabaseStorageService

def test_storage_upload():
    """Test actual storage upload operation."""
    
    # Use existing user credentials
    test_email = "daven613us@gmail.com"
    test_password = "12341234"
    
    print("🔐 Step 1: Authenticating user...")
    auth_service = SupabaseAuthService()
    
    try:
        # Sign in with existing user
        auth_result = auth_service.sign_in(test_email, test_password)
        user = auth_result["user"]
        access_token = auth_result["session"].access_token
        
        print(f"✅ Authentication successful!")
        print(f"   User ID: {user.id}")
        
        # Test storage upload
        print(f"\n📤 Step 2: Testing storage upload...")
        
        test_content = b"This is a test file for storage upload debugging."
        file_name = "debug_test_file.txt"
        
        print(f"   Attempting to upload: {file_name}")
        print(f"   Expected path: {user.id}/{file_name}")
        print(f"   User token provided: Yes")
        
        result = SupabaseStorageService.upload_file(
            user_id=str(user.id),
            file_name=file_name,
            file_content=test_content,
            content_type="text/plain",
            user_token=access_token
        )
        
        print(f"✅ Storage upload successful!")
        print(f"   File ID: {result.get('file_id')}")
        print(f"   File URL: {result.get('url')}")
        
    except Exception as e:
        print(f"❌ Storage upload failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_storage_upload() 