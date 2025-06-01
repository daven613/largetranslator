#!/usr/bin/env python3
"""
Debug script to test storage authentication and see what auth.uid() resolves to.
"""
import asyncio
import os
import jwt
import uuid
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

def test_storage_auth():
    """Test storage authentication to see what auth.uid() resolves to."""
    
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
        print(f"   User ID from auth result: {user.id}")
        
        # Decode the JWT to see what's in it
        print(f"\n🔍 Step 2: Decoding JWT...")
        decoded = jwt.decode(access_token, options={"verify_signature": False})
        print(f"   JWT 'sub' field (what auth.uid() uses): {decoded.get('sub')}")
        print(f"   JWT 'role' field: {decoded.get('role')}")
        
        # Test what happens when we query the database with auth.uid()
        print(f"\n🔧 Step 3: Testing auth.uid() in database...")
        user_client = get_user_supabase_client(access_token)
        
        # Query to see what auth.uid() returns
        result = user_client.rpc("auth_uid_test").execute()
        print(f"   auth.uid() from database: {result.data}")
        
        # Compare the values
        print(f"\n📊 Step 4: Comparison...")
        print(f"   User ID from auth result: {user.id}")
        print(f"   JWT 'sub' field: {decoded.get('sub')}")
        print(f"   auth.uid() from DB: {result.data}")
        print(f"   Do they match? {user.id == decoded.get('sub') == result.data}")
        
        # Also test the storage path format
        print(f"\n📂 Step 5: Storage path test...")
        expected_path = f"{user.id}/test_file.txt"
        print(f"   Expected storage path: {expected_path}")
        print(f"   First folder from path would be: {user.id}")
        print(f"   Does first folder match auth.uid()? {user.id == result.data}")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_storage_auth() 