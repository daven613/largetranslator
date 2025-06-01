#!/usr/bin/env python3

"""
Test script to debug database operations with user authentication context
"""
import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Add backend to Python path
backend_dir = Path(__file__).resolve().parent
sys.path.append(str(backend_dir))

import sys
sys.path.append('/Users/shmuel/dev/large_translate')

from largetranslator.backend.external_services.supabase.auth_service import SupabaseAuthService
from largetranslator.backend.db.crud.files import create_document, get_document_by_user_and_name
from largetranslator.backend.db.models import DocumentCreate

# Load environment variables
test_env_path = backend_dir / "test_end_to_end" / ".test_env"
env_path = backend_dir / ".env"

load_dotenv(env_path)
load_dotenv(test_env_path, override=True)

async def test_db_operation():
    print("=== Database Operation Test ===")
    
    try:
        # Authenticate user
        auth_service = SupabaseAuthService()
        user_data = auth_service.sign_in("daven613us@gmail.com", "12341234")
        access_token = user_data["session"].access_token
        user_id = user_data["user"].id
        
        print(f"User ID: {user_id}")
        print(f"Access token (first 50 chars): {access_token[:50]}...")
        
        # Test creating a document
        print(f"\n=== Testing Document Creation ===")
        document_create_data = DocumentCreate(
            user_id=user_id,
            name="test_debug_db.txt",
            file_size=42,
            file_path="test/path/test_debug_db.txt",
            metadata={"test": "data", "source": "db_operation_test"}
        )
        
        result = await create_document(document_create_data, user_token=access_token)
        print(f"✓ Document created successfully: {result.id}")
        
        # Test getting the document
        print(f"\n=== Testing Document Retrieval ===")
        retrieved_doc = await get_document_by_user_and_name(
            user_id=user_id,
            document_name="test_debug_db.txt",
            user_token=access_token
        )
        
        if retrieved_doc:
            print(f"✓ Document retrieved successfully: {retrieved_doc.name}")
        else:
            print("✗ Failed to retrieve document")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_db_operation()) 