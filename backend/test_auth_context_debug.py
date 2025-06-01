#!/usr/bin/env python3
"""
Debug script to test what auth.uid() returns during storage operations.
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
from external_services.supabase.client import get_user_supabase_client

def test_auth_context():
    """Test what auth.uid() returns during actual operations."""
    
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
        
        # Test auth context with user client
        print(f"\n🔧 Step 2: Testing auth context with user client...")
        user_client = get_user_supabase_client(access_token)
        
        # Call our debug function
        result = user_client.rpc("debug_storage_auth").execute()
        
        if result.data:
            data = result.data[0]
            print(f"   Current user ID from auth.uid(): {data.get('current_user_id')}")
            print(f"   Current role from auth.role(): {data.get('current_role_name')}")
            print(f"   Test path: {data.get('test_path')}")
            print(f"   Extracted user ID from path: {data.get('extracted_user_id')}")
            print(f"   Do they match? {data.get('do_they_match')}")
            
            if not data.get('do_they_match'):
                print(f"❌ MISMATCH! This explains the RLS failure.")
            else:
                print(f"✅ Match! The issue is somewhere else.")
        else:
            print(f"❌ No data returned from debug function")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_auth_context() 