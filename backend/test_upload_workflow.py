#!/usr/bin/env python3

"""
Test script to replicate the exact file upload workflow
"""
import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Add paths
backend_dir = Path(__file__).resolve().parent
sys.path.append(str(backend_dir))
sys.path.append('/Users/shmuel/dev/large_translate')

from largetranslator.backend.external_services.supabase.auth_service import SupabaseAuthService
from largetranslator.backend.external_services.supabase.storage_service import SupabaseStorageService
from largetranslator.backend.db.crud.files import create_document, get_document_by_user_and_name
from largetranslator.backend.db.models import DocumentCreate

# Load environment variables
test_env_path = backend_dir / "test_end_to_end" / ".test_env"
env_path = backend_dir / ".env"

load_dotenv(env_path)
load_dotenv(test_env_path, override=True)

async def test_full_upload_workflow():
    print("=== Full Upload Workflow Test ===")
    
    try:
        # Step 1: Authenticate user
        print("Step 1: Authenticating user...")
        auth_service = SupabaseAuthService()
        user_data = auth_service.sign_in("daven613us@gmail.com", "12341234")
        access_token = user_data["session"].access_token
        user_id = user_data["user"].id
        
        print(f"✓ User authenticated: {user_id}")
        
        # Step 2: Prepare file data (simulating upload)
        print("\nStep 2: Preparing file data...")
        test_filename = "workflow_test.txt"
        test_content = b"This is a test file for the full upload workflow."
        content_type = "text/plain"
        
        print(f"✓ File prepared: {test_filename} ({len(test_content)} bytes)")
        
        # Step 3: Upload to storage (exact same call as API)
        print("\nStep 3: Uploading to storage...")
        storage_result = SupabaseStorageService.upload_file(
            user_id=str(user_id),
            file_name=test_filename,
            file_content=test_content,
            content_type=content_type,
            user_token=access_token
        )
        
        print(f"✓ Storage upload successful: {storage_result['file_id']}")
        
        # Step 4: Check for existing document (exact same call as API)
        print("\nStep 4: Checking for existing document...")
        existing_document = await get_document_by_user_and_name(
            user_id=user_id,
            document_name=test_filename,
            user_token=access_token
        )
        
        if existing_document:
            print(f"✓ Found existing document: {existing_document.id}")
        else:
            print("✓ No existing document found")
        
        # Step 5: Create new document (exact same call as API)
        print("\nStep 5: Creating new document...")
        document_create_data = DocumentCreate(
            user_id=user_id,
            name=test_filename,
            file_size=len(test_content),
            file_path=storage_result["file_id"], 
            metadata={
                "content_type": content_type,
                "upload_source": "workflow_test",
                "upload_time": storage_result["created_at"],
                "initial_storage_path": storage_result["file_id"]
            }
        )
        
        db_document = await create_document(document_create_data, user_token=access_token)
        print(f"✓ Document created in database: {db_document.id}")
        
        print(f"\n🎉 Full workflow completed successfully!")
        print(f"Storage path: {storage_result['file_id']}")
        print(f"Database ID: {db_document.id}")
        
    except Exception as e:
        print(f"✗ Workflow failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_full_upload_workflow()) 