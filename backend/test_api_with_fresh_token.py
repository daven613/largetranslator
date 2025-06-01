#!/usr/bin/env python3

"""
Test the API endpoint with a fresh token to see if the token is the issue
"""
import os
import sys
import asyncio
import httpx
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

async def test_api_with_fresh_token():
    print("=== API Test with Fresh Token ===")
    
    try:
        # Get fresh token
        print("1. Getting fresh token...")
        auth_service = SupabaseAuthService()
        user_data = auth_service.sign_in("daven613us@gmail.com", "12341234")
        fresh_token = user_data["session"].access_token
        user_id = user_data["user"].id
        
        print(f"✓ Fresh token obtained for user: {user_id}")
        
        # Prepare test file
        print("\n2. Preparing test file...")
        test_content = "This is a test file for API testing with fresh token."
        
        # Call the API endpoint directly
        print("\n3. Calling API endpoint...")
        base_url = "http://localhost:8000"  # Assuming FastAPI runs on port 8000
        
        # Create the file data
        files = {
            "file": ("fresh_token_test.txt", test_content, "text/plain")
        }
        
        headers = {
            "Authorization": f"Bearer {fresh_token}"
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{base_url}/api/files/upload",
                    files=files,
                    headers=headers,
                    timeout=30.0
                )
                
                print(f"Response status: {response.status_code}")
                print(f"Response content: {response.text}")
                
                if response.status_code == 201:
                    print("✓ API call successful!")
                    response_data = response.json()
                    print(f"File ID: {response_data.get('file_id')}")
                else:
                    print(f"✗ API call failed with status {response.status_code}")
                    
            except httpx.ConnectError:
                print("✗ Could not connect to API server. Is it running on localhost:8000?")
                print("Try starting the server with: uvicorn main:app --reload")
                return
                
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_api_with_fresh_token()) 