"""
Comprehensive End-to-End Translation Test with Live Tokens
Tests the complete workflow: Upload -> Chunk -> Translate -> Monitor -> Download

This test uses real authentication tokens and API calls to test the actual system.
"""
import asyncio
import os
import time
import logging
import httpx
from typing import Optional, Dict, Any
from uuid import UUID

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
API_BASE_URL = "http://localhost:8000/api"
TEST_FILE_CONTENT = """This is a test document for translation.
It contains multiple sentences that will be chunked.
Each chunk will be translated individually.
The system should handle this gracefully.
This is the final sentence of our test document."""

class TranslationE2ETest:
    def __init__(self, auth_token: str):
        self.auth_token = auth_token
        self.headers = {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
        self.file_headers = {
            "Authorization": f"Bearer {auth_token}"
        }
        
        # Test data tracking
        self.document_id: Optional[str] = None
        self.chunk_set_id: Optional[str] = None
        self.translation_id: Optional[str] = None
        self.file_name = "test_translation_e2e.txt"
        
    async def run_complete_test(self, prompt: str = "Translate this text to Spanish"):
        """Run the complete end-to-end test"""
        logger.info("🚀 Starting Complete Translation E2E Test")
        
        try:
            # Step 1: Upload file
            await self.upload_test_file()
            
            # Step 2: Chunk the file
            await self.chunk_file()
            
            # Step 3: Start translation
            await self.start_translation(prompt)
            
            # Step 4: Monitor translation progress
            await self.monitor_translation()
            
            # Step 5: Check final results
            await self.check_final_results()
            
            logger.info("✅ Complete E2E Test Finished Successfully!")
            
        except Exception as e:
            logger.error(f"❌ E2E Test Failed: {str(e)}", exc_info=True)
            await self.debug_current_state()
            raise
    
    async def upload_test_file(self):
        """Upload a test file"""
        logger.info("📁 Step 1: Uploading test file...")
        
        async with httpx.AsyncClient() as client:
            files = {
                'file': (self.file_name, TEST_FILE_CONTENT.encode(), 'text/plain')
            }
            
            response = await client.post(
                f"{API_BASE_URL}/files/upload",
                headers=self.file_headers,
                files=files,
                timeout=30.0
            )
            
            if response.status_code != 201:
                raise Exception(f"File upload failed: {response.status_code} - {response.text}")
            
            data = response.json()
            self.document_id = data["id"]
            logger.info(f"✅ File uploaded successfully. Document ID: {self.document_id}")
            
    async def chunk_file(self):
        """Chunk the uploaded file"""
        logger.info("🔪 Step 2: Chunking file...")
        
        # First get the file_path from documents
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_BASE_URL}/files/documents",
                headers=self.headers,
                timeout=30.0
            )
            
            if response.status_code != 200:
                raise Exception(f"Failed to get documents: {response.status_code} - {response.text}")
            
            documents = response.json()["documents"]
            file_path = None
            for doc in documents:
                if doc["id"] == self.document_id:
                    file_path = doc["file_path"]
                    break
            
            if not file_path:
                raise Exception(f"Could not find file_path for document {self.document_id}")
            
            # Now chunk the file
            chunk_request = {
                "file_id": file_path,
                "target_chunk_size": 100,  # Small chunks for testing
                "processor_type": "text_chunker"
            }
            
            response = await client.post(
                f"{API_BASE_URL}/chunking",
                headers=self.headers,
                json=chunk_request,
                timeout=30.0
            )
            
            if response.status_code != 201:
                raise Exception(f"Chunking failed: {response.status_code} - {response.text}")
            
            data = response.json()
            self.chunk_set_id = data["chunk_set_id"]
            chunk_count = data["chunk_count"]
            logger.info(f"✅ File chunked successfully. Chunk Set ID: {self.chunk_set_id}, Chunks: {chunk_count}")
    
    async def start_translation(self, prompt: str):
        """Start the translation process"""
        logger.info("🌐 Step 3: Starting translation...")
        
        translation_request = {
            "chunk_set_id": self.chunk_set_id,
            "prompt": prompt
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE_URL}/translations",
                headers=self.headers,
                json=translation_request,
                timeout=30.0
            )
            
            if response.status_code != 200:
                raise Exception(f"Translation creation failed: {response.status_code} - {response.text}")
            
            data = response.json()
            self.translation_id = data["id"]
            logger.info(f"✅ Translation started. Translation ID: {self.translation_id}")
            logger.info(f"📊 Initial status: {data.get('status')}, Total chunks: {data.get('total_chunks')}")
    
    async def monitor_translation(self, max_attempts: int = 30, interval: int = 2):
        """Monitor translation progress"""
        logger.info("👀 Step 4: Monitoring translation progress...")
        
        async with httpx.AsyncClient() as client:
            for attempt in range(max_attempts):
                try:
                    response = await client.get(
                        f"{API_BASE_URL}/translations/{self.translation_id}/status",
                        headers=self.headers,
                        timeout=30.0
                    )
                    
                    if response.status_code != 200:
                        logger.warning(f"Status check failed: {response.status_code} - {response.text}")
                        continue
                    
                    data = response.json()
                    status = data["status"]
                    completed = data["completed_chunks"]
                    total = data["total_chunks"]
                    progress = data["progress"]
                    
                    logger.info(f"📈 Attempt {attempt + 1}: Status={status}, Progress={completed}/{total} ({progress:.1%})")
                    
                    if status == "completed":
                        logger.info("🎉 Translation completed successfully!")
                        return
                    elif status == "failed":
                        logger.error("❌ Translation failed!")
                        await self.debug_translation_failure()
                        raise Exception("Translation failed")
                    
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(interval)
                        
                except Exception as e:
                    logger.warning(f"Error during status check: {str(e)}")
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(interval)
            
            logger.error("⏰ Translation monitoring timed out")
            await self.debug_translation_failure()
            raise Exception("Translation monitoring timed out")
    
    async def debug_translation_failure(self):
        """Debug why translation failed"""
        logger.info("🔍 Debugging translation failure...")
        
        async with httpx.AsyncClient() as client:
            # Get full translation details
            response = await client.get(
                f"{API_BASE_URL}/translations/{self.translation_id}",
                headers=self.headers,
                timeout=30.0
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"🔍 Translation details: {data}")
                
                # Check what target_language and ai_model are set to
                target_lang = data.get("target_language")
                ai_model = data.get("ai_model")
                logger.info(f"🔍 Target Language: '{target_lang}', AI Model: '{ai_model}'")
                
                if target_lang == "N/A (prompt-defined)":
                    logger.error("❌ ISSUE FOUND: target_language is placeholder value!")
                if ai_model == "mock_model":
                    logger.error("❌ ISSUE FOUND: ai_model is placeholder value!")
            
            # Check chunks
            response = await client.get(
                f"{API_BASE_URL}/chunking/chunks/by-chunk-set/{self.chunk_set_id}",
                headers=self.headers,
                timeout=30.0
            )
            
            if response.status_code == 200:
                chunks_data = response.json()
                chunks = chunks_data.get("chunks", [])
                logger.info(f"🔍 Found {len(chunks)} chunks in chunk set")
                for i, chunk in enumerate(chunks[:3]):  # Show first 3 chunks
                    logger.info(f"🔍 Chunk {i+1}: {chunk['content'][:50]}...")
    
    async def check_final_results(self):
        """Check the final translation results"""
        logger.info("📋 Step 5: Checking final results...")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_BASE_URL}/translations/{self.translation_id}",
                headers=self.headers,
                timeout=30.0
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"📋 Final translation status: {data.get('status')}")
                logger.info(f"📋 Completed chunks: {data.get('completed_chunks')}/{data.get('total_chunks')}")
                
                if data.get("output_file_path"):
                    logger.info(f"📋 Output file: {data.get('output_file_path')}")
                else:
                    logger.warning("📋 No output file path found")
    
    async def debug_current_state(self):
        """Debug the current state of all components"""
        logger.info("🔍 Debugging current state...")
        
        if self.document_id:
            logger.info(f"🔍 Document ID: {self.document_id}")
        if self.chunk_set_id:
            logger.info(f"🔍 Chunk Set ID: {self.chunk_set_id}")
        if self.translation_id:
            logger.info(f"🔍 Translation ID: {self.translation_id}")

async def run_test_with_token(auth_token: str, prompt: str = "Translate this text to Spanish"):
    """Run the test with a provided auth token"""
    test = TranslationE2ETest(auth_token)
    await test.run_complete_test(prompt)

if __name__ == "__main__":
    # You can run this with a real token
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python test_translation_e2e_live.py <auth_token> [prompt]")
        print("Example: python test_translation_e2e_live.py 'your_jwt_token_here' 'Translate to French'")
        sys.exit(1)
    
    token = sys.argv[1]
    prompt = sys.argv[2] if len(sys.argv) > 2 else "Translate this text to Spanish"
    
    asyncio.run(run_test_with_token(token, prompt)) 