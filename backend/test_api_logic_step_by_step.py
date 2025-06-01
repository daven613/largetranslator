#!/usr/bin/env python3

"""
Test that replicates the exact API endpoint logic step by step
"""
import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime, timezone as dt_timezone

# Add paths
backend_dir = Path(__file__).resolve().parent
sys.path.append(str(backend_dir))
sys.path.append('/Users/shmuel/dev/large_translate')

from largetranslator.backend.external_services.supabase.auth_service import SupabaseAuthService
from largetranslator.backend.external_services.supabase.storage_service import SupabaseStorageService
from largetranslator.backend.db.crud.files import create_document, get_document_by_user_and_name, update_document
from largetranslator.backend.db.models import DocumentCreate, DocumentUpdate

# Load environment
test_env_path = backend_dir / "test_end_to_end" / ".test_env"
env_path = backend_dir / ".env"
load_dotenv(env_path)
load_dotenv(test_env_path, override=True)

class MockUploadFile:
    def __init__(self, filename, content, content_type):
        self.filename = filename
        self.content = content
        self.content_type = content_type
    
    async def read(self):
        return self.content

async def test_api_logic_step_by_step():
    print("=== API Logic Step-by-Step Test ===")
    
    try:
        # Simulate the exact API endpoint flow
        
        # Step 1: Get user and token (simulating get_current_user_with_token)
        print("Step 1: Getting user and token...")
        auth_service = SupabaseAuthService()
        user_data = auth_service.sign_in("daven613us@gmail.com", "12341234")
        token = user_data["session"].access_token
        user = {"id": user_data["user"].id, "email": user_data["user"].email}
        user_with_token = (user, token)
        
        print(f"✓ User: {user['id']}")
        
        # Step 2: Simulate file upload (simulating UploadFile)
        print("\nStep 2: Simulating file upload...")
        file_content = b"This is a step-by-step API test file."
        mock_file = MockUploadFile("step_by_step_test.txt", file_content, "text/plain")
        
        # Step 3: Extract user and token (exact API code)
        print("\nStep 3: Extracting user and token...")
        user, token = user_with_token
        
        # Step 4: Read file content (exact API code)
        print("\nStep 4: Reading file content...")
        content = await mock_file.read()
        
        # Step 5: Check if it's a text file (exact API code)
        print("\nStep 5: Validating text file...")
        try:
            text_content = content.decode('utf-8')
            print(f"✓ Text content decoded: {len(text_content)} chars")
        except UnicodeDecodeError:
            print("✗ File is not valid text")
            return
        
        # Step 6: Upload file to Supabase storage (exact API code)
        print("\nStep 6: Uploading to storage...")
        try:
            storage_result = SupabaseStorageService.upload_file(
                user_id=str(user["id"]),
                file_name=mock_file.filename,
                file_content=content,
                content_type=mock_file.content_type,
                user_token=token
            )
            print(f"✓ Storage upload successful: {storage_result['file_id']}")
        except Exception as storage_error:
            print(f"✗ Storage upload failed: {storage_error}")
            print(f"Storage error type: {type(storage_error)}")
            return
        
        # Step 7: Check for existing document (exact API code)
        print("\nStep 7: Checking for existing document...")
        try:
            existing_document = await get_document_by_user_and_name(
                user_id=user["id"],
                document_name=mock_file.filename,
                user_token=token
            )
            
            if existing_document:
                print(f"✓ Found existing document: {existing_document.id}")
            else:
                print("✓ No existing document found")
                
        except Exception as db_check_error:
            print(f"✗ Document check failed: {db_check_error}")
            return
        
        # Step 8: Create or update document (exact API code)
        print("\nStep 8: Creating/updating document...")
        try:
            current_time = datetime.now(dt_timezone.utc)
            
            if existing_document:
                # Update existing document (exact API code)
                print("Updating existing document...")
                document_update_data = DocumentUpdate(
                    file_path=storage_result["file_id"],
                    file_size=len(content),
                    metadata={
                        **existing_document.metadata,
                        "content_type": mock_file.content_type,
                        "upload_source": "api_upload_upsert_test",
                        "upload_time": storage_result["created_at"],
                        "last_known_storage_path": storage_result["file_id"]
                    },
                )
                db_document = await update_document(
                    document_id=existing_document.id, 
                    update_data=document_update_data,
                    user_token=token
                )
                if not db_document:
                    print("✗ Failed to update document record")
                    return
                print(f"✓ Document updated: {db_document.id}")
            else:
                # Create new document (exact API code)
                print("Creating new document...")
                document_create_data = DocumentCreate(
                    user_id=user["id"],
                    name=mock_file.filename,
                    file_size=len(content),
                    file_path=storage_result["file_id"], 
                    metadata={
                        "content_type": mock_file.content_type,
                        "upload_source": "api_upload_create_test",
                        "upload_time": storage_result["created_at"],
                        "initial_storage_path": storage_result["file_id"]
                    }
                )
                db_document = await create_document(document_create_data, user_token=token)
                print(f"✓ Document created: {db_document.id}")
                
        except Exception as db_error:
            print(f"✗ Database operation failed: {db_error}")
            print(f"DB error type: {type(db_error)}")
            import traceback
            traceback.print_exc()
            return
        
        print(f"\n🎉 All steps completed successfully!")
        print(f"Final result: Storage {storage_result['file_id']}, DB {db_document.id}")
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_api_logic_step_by_step()) 