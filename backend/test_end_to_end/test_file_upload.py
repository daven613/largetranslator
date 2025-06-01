"""
Test script for the file upload API endpoint (/api/files/upload)
and its corresponding delete endpoint for cleanup.
"""
import os
import requests
import logging
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
    logger.info("=== Starting File Upload API Test ===")

    uploaded_file_name_from_response = None
    uploaded_document_id = None

    try:
        # === 1. Upload file ===
        logger.info(f"Uploading file: {TEST_FILE_NAME}...")
        files = {'file': (TEST_FILE_NAME, open(TEST_FILE_PATH, 'rb'), 'text/plain')}
        
        upload_url = f"{BASE_URL}/files/upload"
        response = requests.post(upload_url, headers=HEADERS, files=files)
        
        logger.info(f"Upload Status Code: {response.status_code}")
        try:
            response_json = response.json()
            logger.info(f"Upload Response JSON: {response_json}")
        except requests.exceptions.JSONDecodeError:
            response_json = None
            logger.error(f"Upload Response is not valid JSON: {response.text}")

        assert response.status_code == 201, f"Upload failed with status {response.status_code}"
        assert response_json is not None, "Upload response was not JSON"
        assert "id" in response_json, "'id' not in upload response"
        assert "file_id" in response_json, "'file_id' not in upload response"
        assert response_json.get("file_name") == TEST_FILE_NAME, "File name in response mismatch"

        uploaded_document_id = response_json["id"]
        uploaded_file_name_from_response = response_json["file_name"] # Should be TEST_FILE_NAME
        logger.info(f"File uploaded successfully. Document ID: {uploaded_document_id}, Storage Path (file_id): {response_json['file_id']}")

    except AssertionError as e:
        logger.error(f"Test assertion failed: {e}")
    except Exception as e:
        logger.error(f"An error occurred during the upload test: {e}")
    finally:
        # === 2. Cleanup: Delete the uploaded file ===
        if uploaded_file_name_from_response:
            logger.info(f"Cleaning up: Deleting file '{uploaded_file_name_from_response}'...")
            delete_url = f"{BASE_URL}/files/{uploaded_file_name_from_response}"
            del_response = requests.delete(delete_url, headers=HEADERS)
            
            logger.info(f"Delete Status Code: {del_response.status_code}")
            try:
                del_response_json = del_response.json()
                logger.info(f"Delete Response JSON: {del_response_json}")
            except requests.exceptions.JSONDecodeError:
                del_response_json = None
                logger.error(f"Delete Response is not valid JSON: {del_response.text}")

            # Expect 200 OK for successful delete with a response body
            assert del_response.status_code == 200, f"Delete failed with status {del_response.status_code}"
            assert del_response_json is not None, "Delete response was not JSON"
            assert del_response_json.get("success") is True, "Delete response did not indicate success"
            logger.info(f"File '{uploaded_file_name_from_response}' deleted successfully.")
        else:
            logger.info("Skipping cleanup as no file was confirmed uploaded.")

    logger.info("=== File Upload API Test Finished ===")

if __name__ == "__main__":
    # Ensure the test document exists
    if not os.path.exists(TEST_FILE_PATH):
        logger.warning(f"Test file '{TEST_FILE_PATH}' not found. Creating a dummy one.")
        with open(TEST_FILE_PATH, "w") as f:
            f.write("This is a test document for the file upload API test.\nIt has multiple lines.")
            
    main()
