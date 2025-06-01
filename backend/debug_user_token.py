#!/usr/bin/env python3

"""
Debug script to decode JWT token and check user ID extraction
"""
import os
import sys
import jwt
import json
from pathlib import Path
from dotenv import load_dotenv

# Add backend to Python path
backend_dir = Path(__file__).resolve().parent
sys.path.append(str(backend_dir))

from external_services.supabase.auth_service import SupabaseAuthService

# Load environment variables
test_env_path = backend_dir / "test_end_to_end" / ".test_env"
env_path = backend_dir / ".env"

load_dotenv(env_path)
load_dotenv(test_env_path, override=True)

def decode_token(token):
    """Decode JWT token without verification for debugging"""
    try:
        # Decode without verification to see the payload
        decoded = jwt.decode(token, options={"verify_signature": False})
        return decoded
    except Exception as e:
        print(f"Error decoding token: {e}")
        return None

def main():
    print("=== JWT Token Debug ===")
    
    # Get token from environment
    jwt_token = os.getenv("SUPABASE_TEST_JWT")
    if not jwt_token:
        print("ERROR: SUPABASE_TEST_JWT not found in environment")
        return
    
    print(f"JWT Token (first 50 chars): {jwt_token[:50]}...")
    
    # Decode the token
    payload = decode_token(jwt_token)
    if payload:
        print(f"Token payload:")
        print(json.dumps(payload, indent=2))
        
        # Extract user ID
        user_id = payload.get("sub")
        print(f"\nUser ID from token: {user_id}")
        
        # Simulate storage path construction
        test_filename = "test_document.txt"
        storage_path = f"{user_id}/{test_filename}"
        print(f"Storage path would be: {storage_path}")
    else:
        print("Failed to decode token")

if __name__ == "__main__":
    main() 