#!/usr/bin/env python3

import asyncio
import httpx
import sys
import os
import traceback

async def test_download_fix():
    """Test if the download works by manually triggering document assembly"""
    
    # Token for authentication
    token = "eyJhbGciOiJIUzI1NiIsImtpZCI6IktPWVdKbDkweWlTcDlydlUiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL2V2Z2d1cGpudGd4cXp5ZHZxc2VsLnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiIxMjM2ODc4ZS01MjIxLTQ4ZGItOTllMy04OTBjZDNhODNlMWYiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzQ4MzE5OTE2LCJpYXQiOjE3NDgzMTYzMTYsImVtYWlsIjoiZGF2ZW42MTN1c0BnbWFpbC5jb20iLCJwaG9uZSI6IiIsImFwcF9tZXRhZGF0YSI6eyJwcm92aWRlciI6ImVtYWlsIiwicHJvdmlkZXJzIjpbImVtYWlsIl19LCJ1c2VyX21ldGFkYXRhIjp7ImVtYWlsIjoiZGF2ZW42MTN1c0BnbWFpbC5jb20iLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwicGhvbmVfdmVyaWZpZWQiOmZhbHNlLCJzdWIiOiIxMjM2ODc4ZS01MjIxLTQ4ZGItOTllMy04OTBjZDNhODNlMWYifSwicm9sZSI6ImF1dGhlbnRpY2F0ZWQiLCJhYWwiOiJhYWwxIiwiYW1yIjpbeyJtZXRob2QiOiJwYXNzd29yZCIsInRpbWVzdGFtcCI6MTc0ODMxNjMxNn1dLCJzZXNzaW9uX2lkIjoiOTExOWZmY2ItM2RjOC00MjNjLTg4OTctMTY4ZWQxMTc2MmQxIiwiaXNfYW5vbnltb3VzIjpmYWxzZX0.I7FeJuwXZ_0xanKPGSqJlnAcITN686D6v3vSvbt6mAk"
    
    # Use one of the completed translations
    translation_id = "07e9f98a-5b7d-4bba-b5b3-52d85071afde"
    
    headers = {"Authorization": f"Bearer {token}"}
    base_url = "http://localhost:8000/api"
    
    print(f"🔧 Testing download fix for translation: {translation_id}")
    
    try:
        async with httpx.AsyncClient() as client:
            # First, let's check the current status
            print("📊 Checking current translation status...")
            response = await client.get(f"{base_url}/translations/{translation_id}", headers=headers)
            if response.status_code == 200:
                translation = response.json()
                print(f"   Status: {translation['status']}")
                print(f"   Completed chunks: {translation['completed_chunks']}/{translation['total_chunks']}")
                print(f"   Output file path: {translation['output_file_path']}")
            else:
                print(f"   Error getting translation: {response.status_code} - {response.text}")
                return False
            
            # Try to trigger document assembly by calling the start endpoint
            print("🚀 Triggering document assembly...")
            response = await client.post(f"{base_url}/translations/{translation_id}/start", headers=headers)
            print(f"   Start response: {response.status_code}")
            if response.status_code != 202:
                print(f"   Start error: {response.text}")
            
            # Wait a moment for processing
            print("⏳ Waiting for processing...")
            await asyncio.sleep(3)
            
            # Check status again
            print("📊 Checking status after assembly trigger...")
            response = await client.get(f"{base_url}/translations/{translation_id}", headers=headers)
            if response.status_code == 200:
                translation = response.json()
                print(f"   Status: {translation['status']}")
                print(f"   Output file path: {translation['output_file_path']}")
            
            # Now try to download
            print("📥 Attempting download...")
            response = await client.get(f"{base_url}/translations/{translation_id}/download", headers=headers)
            
            if response.status_code == 200:
                print("✅ Download successful!")
                print(f"   Content-Type: {response.headers.get('content-type')}")
                print(f"   Content-Length: {len(response.content)} bytes")
                
                # Save the file to verify it's valid
                filename = f"downloaded_translation_{translation_id}.txt"
                with open(filename, "wb") as f:
                    f.write(response.content)
                print(f"   Saved to: {filename}")
                
                # Show first 200 characters of content
                content_preview = response.content.decode('utf-8')[:200]
                print(f"   Content preview: {content_preview}...")
                
                return True
            else:
                print(f"❌ Download failed: {response.status_code}")
                print(f"   Error: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Test failed with exception: {str(e)}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_download_fix())
    if success:
        print("\n🎉 Download test PASSED! The filename sanitization fix works!")
    else:
        print("\n💥 Download test FAILED!") 