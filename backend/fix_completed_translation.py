#!/usr/bin/env python3

import asyncio
import httpx

async def fix_completed_translation():
    """Fix a completed translation by manually triggering document assembly"""
    
    # Token for authentication
    token = "eyJhbGciOiJIUzI1NiIsImtpZCI6IktPWVdKbDkweWlTcDlydlUiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL2V2Z2d1cGpudGd4cXp5ZHZxc2VsLnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiIxMjM2ODc4ZS01MjIxLTQ4ZGItOTllMy04OTBjZDNhODNlMWYiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzQ4MzE5OTE2LCJpYXQiOjE3NDgzMTYzMTYsImVtYWlsIjoiZGF2ZW42MTN1c0BnbWFpbC5jb20iLCJwaG9uZSI6IiIsImFwcF9tZXRhZGF0YSI6eyJwcm92aWRlciI6ImVtYWlsIiwicHJvdmlkZXJzIjpbImVtYWlsIl19LCJ1c2VyX21ldGFkYXRhIjp7ImVtYWlsIjoiZGF2ZW42MTN1c0BnbWFpbC5jb20iLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwicGhvbmVfdmVyaWZpZWQiOmZhbHNlLCJzdWIiOiIxMjM2ODc4ZS01MjIxLTQ4ZGItOTllMy04OTBjZDNhODNlMWYifSwicm9sZSI6ImF1dGhlbnRpY2F0ZWQiLCJhYWwiOiJhYWwxIiwiYW1yIjpbeyJtZXRob2QiOiJwYXNzd29yZCIsInRpbWVzdGFtcCI6MTc0ODMxNjMxNn1dLCJzZXNzaW9uX2lkIjoiOTExOWZmY2ItM2RjOC00MjNjLTg4OTctMTY4ZWQxMTc2MmQxIiwiaXNfYW5vbnltb3VzIjpmYWxzZX0.I7FeJuwXZ_0xanKPGSqJlnAcITN686D6v3vSvbt6mAk"
    
    # Translation that needs fixing
    translation_id = "a9504b70-2709-4c14-b24e-f7b9ef162b8e"
    
    headers = {"Authorization": f"Bearer {token}"}
    base_url = "http://localhost:8000/api"
    
    print(f"🔧 Fixing completed translation: {translation_id}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Check current status
            print("📊 Checking current status...")
            response = await client.get(f"{base_url}/translations/{translation_id}", headers=headers)
            if response.status_code == 200:
                translation = response.json()
                print(f"   Status: {translation['status']}")
                print(f"   Completed chunks: {translation['completed_chunks']}/{translation['total_chunks']}")
                print(f"   Output file path: {translation['output_file_path']}")
                
                if translation['completed_chunks'] == translation['total_chunks'] and translation['completed_chunks'] > 0:
                    print("✅ All chunks are completed, proceeding with document assembly...")
                else:
                    print("❌ Not all chunks are completed, cannot fix this translation")
                    return False
            else:
                print(f"❌ Failed to get translation status: {response.status_code}")
                return False
            
            # Trigger document assembly by calling regenerate endpoint
            # This will re-run the background job which should now work with the filename fix
            print("🚀 Triggering document assembly via regenerate...")
            regenerate_data = {
                "prompt": "Translate this text to Hebrew"  # Use the same prompt
            }
            
            response = await client.post(
                f"{base_url}/translations/{translation_id}/regenerate", 
                headers=headers,
                json=regenerate_data
            )
            
            if response.status_code == 200:
                print("✅ Regenerate request successful!")
                print("⏳ Waiting for background processing...")
                
                # Wait for processing
                await asyncio.sleep(5)
                
                # Check status again
                print("📊 Checking final status...")
                response = await client.get(f"{base_url}/translations/{translation_id}", headers=headers)
                if response.status_code == 200:
                    translation = response.json()
                    print(f"   Status: {translation['status']}")
                    print(f"   Output file path: {translation['output_file_path']}")
                    
                    if translation['status'] == 'completed' and translation['output_file_path']:
                        print("🎉 Translation successfully fixed!")
                        
                        # Test download
                        print("📥 Testing download...")
                        response = await client.get(f"{base_url}/translations/{translation_id}/download", headers=headers)
                        if response.status_code == 200:
                            print("✅ Download works!")
                            print(f"   Downloaded {len(response.content)} bytes")
                            return True
                        else:
                            print(f"❌ Download still fails: {response.status_code} - {response.text}")
                            return False
                    else:
                        print("❌ Translation status not properly updated")
                        return False
                else:
                    print("❌ Failed to check final status")
                    return False
            else:
                print(f"❌ Regenerate failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return False

if __name__ == "__main__":
    success = asyncio.run(fix_completed_translation())
    if success:
        print("\n🎉 TRANSLATION SUCCESSFULLY FIXED!")
        print("✅ Document assembly completed")
        print("✅ Status updated to 'completed'")
        print("✅ Download now works!")
    else:
        print("\n💥 FAILED TO FIX TRANSLATION!") 