"""
Test script for the file chunking API endpoint (/api/chunking).
This test will first upload a file, then request it to be chunked,
verify the chunking, and finally clean up.
"""
import os
import requests
import logging
import uuid # For session_id if needed, though API might generate
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env and .test_env
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(os.path.dirname(BASE_DIR), '.env') # Path to backend/.env
TEST_ENV_PATH = os.path.join(BASE_DIR, '.test_env')      # Path to backend/test_end_to_end/.test_env

load_dotenv(dotenv_path=ENV_PATH)
load_dotenv(dotenv_path=TEST_ENV_PATH, override=True) # Test env overrides general .env

# API Configuration
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000/api")
JWT_TOKEN = os.getenv("SUPABASE_TEST_JWT")

if not JWT_TOKEN:
    logger.error("SUPABASE_TEST_JWT not found. Please run get_auth_token.py first.")
    exit(1)

HEADERS = {
    "Authorization": f"Bearer {JWT_TOKEN}"
}

# Test file details
TEST_FILE_NAME = "test_document.txt"
TEST_FILE_PATH = os.path.join(BASE_DIR, TEST_FILE_NAME)

def main():
    logger.info("=== Starting File Chunking API Test ===")

    uploaded_document_uuid = None
    uploaded_file_id_storage_path = None # This is the 'user_id/file_name' path for storage
    chunk_set_id_from_response = None

    try:
        # === 1. Setup: Upload file ===
        logger.info(f"Uploading file: {TEST_FILE_NAME} for chunking test...")
        with open(TEST_FILE_PATH, 'rb') as f_obj:
            files_for_upload = {'file': (TEST_FILE_NAME, f_obj, 'text/plain')}
            upload_url = f"{BASE_URL}/files/upload"
            upload_response = requests.post(upload_url, headers=HEADERS, files=files_for_upload)
        
        logger.info(f"Upload Status Code: {upload_response.status_code}")
        upload_response_json = upload_response.json()
        logger.info(f"Upload Response JSON: {upload_response_json}")

        assert upload_response.status_code == 201, f"Upload failed with status {upload_response.status_code}"
        assert "id" in upload_response_json, "'id' (document UUID) not in upload response"
        assert "file_id" in upload_response_json, "'file_id' (storage path) not in upload response"
        
        uploaded_document_uuid = upload_response_json["id"]
        uploaded_file_id_storage_path = upload_response_json["file_id"]
        logger.info(f"File uploaded. Document UUID: {uploaded_document_uuid}, Storage Path: {uploaded_file_id_storage_path}")

        # === 2. Chunking Phase ===
        logger.info(f"Requesting chunking for file_id: {uploaded_file_id_storage_path}...")
        chunking_payload = {
            "file_id": uploaded_file_id_storage_path,
            "target_chunk_size": 1000, # Using a smaller size for testing
            "processor_type": "text_chunker" # Default from schema
            # session_id is optional, API will generate if not provided
        }
        chunking_url = f"{BASE_URL}/chunking"
        chunking_response = requests.post(chunking_url, headers=HEADERS, json=chunking_payload)

        logger.info(f"Chunking Status Code: {chunking_response.status_code}")
        chunking_response_json = chunking_response.json()
        logger.info(f"Chunking Response JSON: {chunking_response_json}")

        assert chunking_response.status_code == 201, f"Chunking failed with status {chunking_response.status_code}"
        assert "document_id" in chunking_response_json, "'document_id' not in chunking response"
        assert chunking_response_json["document_id"] == uploaded_document_uuid, "Document ID in chunking response mismatch with upload"
        assert "chunk_set_id" in chunking_response_json, "'chunk_set_id' not in chunking response"
        assert "chunk_count" in chunking_response_json and chunking_response_json["chunk_count"] > 0, "'chunk_count' not in response or not > 0"
        assert "chunk_ids" in chunking_response_json and len(chunking_response_json["chunk_ids"]) == chunking_response_json["chunk_count"], "'chunk_ids' mismatch with 'chunk_count'"

        chunk_set_id_from_response = chunking_response_json["chunk_set_id"]
        chunk_count_from_response = chunking_response_json["chunk_count"]
        logger.info(f"File chunked successfully. Chunk Set ID: {chunk_set_id_from_response}, Chunks Created: {chunk_count_from_response}")

        # === 3. Verification Phase: List Chunks ===
        logger.info(f"Listing chunks for chunk_set_id: {chunk_set_id_from_response}...")
        list_chunks_url = f"{BASE_URL}/chunking/chunks/by-chunk-set/{chunk_set_id_from_response}"
        list_chunks_response = requests.get(list_chunks_url, headers=HEADERS)

        logger.info(f"List Chunks Status Code: {list_chunks_response.status_code}")
        list_chunks_response_json = list_chunks_response.json()
        # logger.info(f"List Chunks Response JSON: {list_chunks_response_json}") # Can be verbose

        assert list_chunks_response.status_code == 200, f"List chunks failed with status {list_chunks_response.status_code}"
        assert "chunks" in list_chunks_response_json, "'chunks' not in list_chunks response"
        assert len(list_chunks_response_json["chunks"]) == chunk_count_from_response, "Number of listed chunks does not match expected chunk_count"
        logger.info(f"Successfully listed {len(list_chunks_response_json['chunks'])} chunks for chunk_set_id {chunk_set_id_from_response}.")

    except AssertionError as e:
        logger.error(f"Test assertion failed: {e}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
    except Exception as e:
        logger.error(f"An error occurred during the chunking test: {e}")
    finally:
        # === 4. Cleanup: Delete the original uploaded file ===
        if uploaded_file_id_storage_path: # Check if upload was successful enough to get a file_id
            logger.info(f"Cleaning up: Deleting original uploaded file '{TEST_FILE_NAME}'...")
            delete_url = f"{BASE_URL}/files/{TEST_FILE_NAME}" # Delete uses file_name
            del_response = requests.delete(delete_url, headers=HEADERS)
            
            logger.info(f"Delete Status Code for original file: {del_response.status_code}")
            if del_response.status_code == 200:
                logger.info(f"Original file '{TEST_FILE_NAME}' deleted successfully.")
            else:
                logger.warning(f"Failed to delete original file '{TEST_FILE_NAME}'. Status: {del_response.status_code}, Response: {del_response.text}")
        else:
            logger.info("Skipping cleanup of original file as it was not confirmed uploaded.")
        
        # Note: No direct cleanup for chunk_sets or chunks via API in this test script yet,
        # as dedicated delete endpoints for those might not exist or are not being tested here.

    logger.info("=== File Chunking API Test Finished ===")

if __name__ == "__main__":
    # Ensure the test document exists
    if not os.path.exists(TEST_FILE_PATH):
        logger.warning(f"Test file '{TEST_FILE_PATH}' not found. Creating a dummy one.")
        with open(TEST_FILE_PATH, "w") as f:
            f.write("This is a test document for the file chunking API test.\nIt has multiple lines of text to ensure some chunks can be created.\nLorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.\nUt enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.\nDuis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.\nExcepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.")
            
    main()
