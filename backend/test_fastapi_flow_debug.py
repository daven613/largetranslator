#!/usr/bin/env python3
"""
Debug script to exactly mimic the FastAPI flow without FastAPI.
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

def test_fastapi_flow():
    """Test the exact flow that FastAPI uses."""
    
    # Use existing user credentials
    test_email = "daven613us@gmail.com"
    test_password = "12341234"
    
    print("🔐 Step 1: Authenticating user (like FastAPI auth dependency)...")
    auth_service = SupabaseAuthService()
    
    try:
        # Sign in with existing user (simulating the auth dependency)
        auth_result = auth_service.sign_in(test_email, test_password)
        user = auth_result["user"]
        access_token = auth_result["session"].access_token
        
        print(f"✅ Authentication successful!")
        print(f"   User ID: {user.id}")
        
        # Simulate the FastAPI router logic
        print(f"\n📤 Step 2: Simulating FastAPI file upload logic...")
        
        # Create the "uploaded file" content (simulating what FastAPI receives)
        file_content = b"This is test content for e2e testing."
        file_name = "e2e_test_document.txt"
        content_type = "text/plain"
        
        print(f"   File name: {file_name}")
        print(f"   User ID from auth: {user.id}")
        print(f"   Token length: {len(access_token)}")
        
        # Call storage service exactly like the FastAPI router does
        storage_result = SupabaseStorageService.upload_file(
            user_id=str(user.id),  # Convert to string like FastAPI does
            file_name=file_name,
            file_content=file_content,
            content_type=content_type,
            user_token=access_token
        )
        
        print(f"✅ FastAPI flow simulation successful!")
        print(f"   File ID: {storage_result.get('file_id')}")
        print(f"   File URL: {storage_result.get('url')}")
        
    except Exception as e:
        print(f"❌ FastAPI flow simulation failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_fastapi_flow() 