#!/usr/bin/env python3

"""
Test storage bucket access and policies
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add paths
backend_dir = Path(__file__).resolve().parent
sys.path.append(str(backend_dir))
sys.path.append('/Users/shmuel/dev/large_translate')

from largetranslator.backend.external_services.supabase.client import get_supabase_client, get_user_supabase_client
from largetranslator.backend.external_services.supabase.auth_service import SupabaseAuthService

# Load environment
test_env_path = backend_dir / "test_end_to_end" / ".test_env"
env_path = backend_dir / ".env"
load_dotenv(env_path)
load_dotenv(test_env_path, override=True)

def main():
    print("=== Storage Policies Test ===")
    
    try:
        # Test with service key (admin) client
        print("1. Testing with service key client...")
        admin_client = get_supabase_client()
        
        # List buckets
        buckets = admin_client.storage.list_buckets()
        print(f"Available buckets: {[b.name for b in buckets]}")
        
        # Check if our bucket exists
        bucket_exists = any(b.name == "user-text-files" for b in buckets)
        print(f"user-text-files bucket exists: {bucket_exists}")
        
        if bucket_exists:
            # Try to list files as admin
            try:
                files = admin_client.storage.from_("user-text-files").list()
                print(f"Admin can list files: {len(files)} files found")
            except Exception as e:
                print(f"Admin cannot list files: {e}")
        
        # Test with user client
        print("\n2. Testing with user client...")
        auth_service = SupabaseAuthService()
        user_data = auth_service.sign_in("daven613us@gmail.com", "12341234")
        access_token = user_data["session"].access_token
        user_id = user_data["user"].id
        
        user_client = get_user_supabase_client(access_token)
        
        # Try to list files as user
        try:
            files = user_client.storage.from_("user-text-files").list()
            print(f"User can list files: {len(files)} files found")
        except Exception as e:
            print(f"User cannot list files: {e}")
        
        # Try to list files in user's folder
        try:
            user_files = user_client.storage.from_("user-text-files").list(user_id)
            print(f"User can list own folder: {len(user_files)} files found")
        except Exception as e:
            print(f"User cannot list own folder: {e}")
        
        # Try to upload a simple file
        print(f"\n3. Testing file upload as user...")
        test_content = b"Storage policy test file"
        test_path = f"{user_id}/policy_test.txt"
        
        try:
            result = user_client.storage.from_("user-text-files").upload(
                path=test_path,
                file=test_content,
                file_options={"content-type": "text/plain", "x-upsert": "true"}
            )
            print(f"✓ User upload successful: {result}")
        except Exception as e:
            print(f"✗ User upload failed: {e}")
            print(f"Error type: {type(e)}")
            
            # Try to get more details about the error
            if hasattr(e, 'response'):
                print(f"Response status: {e.response.status_code}")
                print(f"Response content: {e.response.text}")
        
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 