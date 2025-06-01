#!/usr/bin/env python3

"""
Test script to compare tokens from different sources
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add paths
backend_dir = Path(__file__).resolve().parent
sys.path.append(str(backend_dir))
sys.path.append('/Users/shmuel/dev/large_translate')

from largetranslator.backend.external_services.supabase.auth_service import SupabaseAuthService

# Load environment variables
test_env_path = backend_dir / "test_end_to_end" / ".test_env"
env_path = backend_dir / ".env"

load_dotenv(env_path)
load_dotenv(test_env_path, override=True)

def main():
    print("=== Token Comparison Test ===")
    
    # Get fresh token from sign_in
    print("1. Getting fresh token from sign_in...")
    auth_service = SupabaseAuthService()
    user_data = auth_service.sign_in("daven613us@gmail.com", "12341234")
    fresh_token = user_data["session"].access_token
    
    # Get token from environment
    print("2. Getting token from .test_env...")
    env_token = os.getenv("SUPABASE_TEST_JWT")
    
    print(f"\nFresh token (first 50 chars): {fresh_token[:50]}...")
    print(f"Env token (first 50 chars):   {env_token[:50]}...")
    
    print(f"\nTokens are identical: {fresh_token == env_token}")
    
    # Test both tokens with get_user
    print(f"\n3. Testing both tokens with get_user...")
    
    fresh_user = SupabaseAuthService.get_user(fresh_token)
    env_user = SupabaseAuthService.get_user(env_token)
    
    print(f"Fresh token user: {fresh_user}")
    print(f"Env token user:   {env_user}")
    
    print(f"Both tokens valid: {fresh_user is not None and env_user is not None}")

if __name__ == "__main__":
    main() 