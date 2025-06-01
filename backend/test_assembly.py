#!/usr/bin/env python3

import asyncio
import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Now import with the correct path structure
from api.translations.router import assemble_document, update_translation
from db import models

async def test_document_assembly():
    """Test document assembly for a completed translation"""
    
    # Use one of the completed translations
    translation_id = "07e9f98a-5b7d-4bba-b5b3-52d85071afde"
    
    print(f"🔧 Testing document assembly for translation: {translation_id}")
    
    try:
        # Attempt to assemble the document
        print("📄 Assembling document...")
        document_path = await assemble_document(translation_id)
        print(f"✅ Document assembled successfully!")
        print(f"📁 Document path: {document_path}")
        
        # Update the translation with the output file path
        print("💾 Updating translation with output file path...")
        await update_translation(
            translation_id,
            models.TranslationUpdate(
                output_file_path=document_path,
                status="completed"
            )
        )
        print("✅ Translation updated successfully!")
        
        return True
        
    except Exception as e:
        print(f"❌ Document assembly failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_document_assembly())
    if success:
        print("\n🎉 Document assembly test PASSED! The filename sanitization fix works!")
    else:
        print("\n💥 Document assembly test FAILED!") 