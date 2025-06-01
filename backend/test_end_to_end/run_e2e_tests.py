import os
import time
import json
from pathlib import Path
import requests
from dotenv import load_dotenv

# --- Configuration ---
SCRIPT_DIR = Path(__file__).resolve().parent
# .env file for backend (e.g., for SUPABASE_URL if used for base API url)
BACKEND_ENV_PATH = SCRIPT_DIR.parent / ".env"
# .test_env file for test-specific variables like JWT and user credentials
TEST_ENV_PATH = SCRIPT_DIR / ".test_env"
TEST_DOCUMENT_PATH = SCRIPT_DIR / "test_document.txt"

TARGET_LANGUAGE = "Spanish" # Example target language
POLLING_INTERVAL_SECONDS = 15 # Time between status checks
MAX_POLLING_ATTEMPTS = 40     # Max attempts (15s * 40 = 600s = 10 minutes)
API_BASE_URL = "http://localhost:8000/api" # Adjust if your FastAPI runs elsewhere

# --- Load Environment Variables ---
# Load backend .env primarily if API_BASE_URL needs to be dynamic (though hardcoded for now)
# load_dotenv(dotenv_path=BACKEND_ENV_PATH)
# API_BASE_URL = os.getenv("YOUR_API_BASE_URL_ENV_VAR", "http://localhost:8000/api")

# Load test .env for JWT
if not TEST_ENV_PATH.exists():
    print(f"Error: Test environment file not found at {TEST_ENV_PATH}")
    print("Please ensure .test_env exists with SUPABASE_TEST_JWT.")
    exit(1)
load_dotenv(dotenv_path=TEST_ENV_PATH)
JWT_TOKEN = os.getenv("SUPABASE_TEST_JWT")
if not JWT_TOKEN:
    print(f"Error: SUPABASE_TEST_JWT not found in {TEST_ENV_PATH}. Run get_auth_token.py first.")
    exit(1)

HEADERS = {
    "Authorization": f"Bearer {JWT_TOKEN}"
}

# --- Helper Functions ---
def print_step(message):
    print(f"\n=== {message} ===")

def print_response_details(response):
    print(f"Status Code: {response.status_code}")
    try:
        print(f"Response JSON: {json.dumps(response.json(), indent=2)}")
    except requests.exceptions.JSONDecodeError:
        print(f"Response Text: {response.text[:500]}...") # Print first 500 chars for brevity

# --- API Call Functions ---
def upload_file(file_path):
    print_step(f"Uploading file: {file_path.name}")
    if not file_path.exists():
        print(f"Error: Test document {file_path} not found.")
        return None
    with open(file_path, 'rb') as f:
        files = {'file': (file_path.name, f, 'text/plain')}
        try:
            response = requests.post(f"{API_BASE_URL}/files/upload", headers=HEADERS, files=files, timeout=30)
            print_response_details(response)
            response.raise_for_status() 
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error during file upload: {e}")
            return None

def chunk_document(document_id):
    print_step(f"Requesting chunking for document_id: {document_id}")
    payload = {"document_id": str(document_id)}
    try:
        response = requests.post(f"{API_BASE_URL}/chunking/", headers=HEADERS, json=payload, timeout=30)
        print_response_details(response)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error during chunking request: {e}")
        return None

def create_translation(chunk_set_id, target_language, name="E2E Test Translation"):
    print_step(f"Creating translation for chunk_set_id: {chunk_set_id} to {target_language}")
    payload = {
        "chunk_set_id": str(chunk_set_id),
        "target_language": target_language,
        "name": name
    }
    try:
        response = requests.post(f"{API_BASE_URL}/translations/", headers=HEADERS, json=payload, timeout=30)
        print_response_details(response)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error creating translation: {e}")
        return None

def get_translation_status(translation_id):
    # print_step(f"Getting status for translation_id: {translation_id}") # Too verbose for polling loop
    try:
        response = requests.get(f"{API_BASE_URL}/translations/{translation_id}", headers=HEADERS, timeout=30)
        # print_response_details(response) # Too verbose for polling loop
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error getting translation status for {translation_id}: {e}")
        return None

def download_translation(translation_id, output_filename_prefix="translated_document_e2e"):
    print_step(f"Downloading translation_id: {translation_id}")
    try:
        response = requests.get(f"{API_BASE_URL}/translations/{translation_id}/download", headers=HEADERS, stream=True, timeout=120) # Increased timeout for download
        print(f"Download - Status Code: {response.status_code}")
        response.raise_for_status()
        
        # Extract original filename from Content-Disposition or use a default
        content_disposition = response.headers.get('content-disposition')
        original_filename = "downloaded_file.txt"
        if content_disposition:
            import re
            fname = re.findall('filename=(.+)', content_disposition)
            if fname:
                original_filename = fname[0].strip('"')

        output_filename = f"{output_filename_prefix}_{original_filename}"
        output_path = SCRIPT_DIR / output_filename
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Translated document saved to: {output_path}")
        return output_path
    except requests.exceptions.RequestException as e:
        print(f"Error downloading translation: {e}")
        return None

# --- Main Test Execution ---
def run_tests():
    print_step("Starting End-to-End API Tests")

    # 1. Upload file
    upload_response = upload_file(TEST_DOCUMENT_PATH)
    if not upload_response or "id" not in upload_response:
        print("Halting tests: File upload failed or document ID missing.")
        return
    document_id = upload_response["id"]
    print(f"Step 1 complete. Document ID: {document_id}")

    # 2. Chunk document
    chunk_response = chunk_document(document_id)
    if not chunk_response or "id" not in chunk_response:
        print("Halting tests: Chunking failed or chunk_set ID missing.")
        return
    chunk_set_id = chunk_response["id"]
    print(f"Step 2 complete. Chunk Set ID: {chunk_set_id}")

    # 3. Create translation
    translation_name = f"E2E Test - {Path(TEST_DOCUMENT_PATH).stem} to {TARGET_LANGUAGE}"
    translation_response = create_translation(chunk_set_id, TARGET_LANGUAGE, name=translation_name)
    if not translation_response or "id" not in translation_response:
        print("Halting tests: Creating translation failed or translation ID missing.")
        return
    translation_id = translation_response["id"]
    print(f"Step 3 complete. Translation ID: {translation_id}")

    # 4. Poll for translation status
    print_step(f"Polling translation status for Translation ID: {translation_id}")
    final_status_response = None
    for attempt in range(MAX_POLLING_ATTEMPTS):
        print(f"Polling attempt {attempt + 1}/{MAX_POLLING_ATTEMPTS}...")
        status_response = get_translation_status(translation_id)
        if status_response:
            final_status_response = status_response # Store last good response
            current_status = status_response.get("status")
            completed_chunks = status_response.get("completed_chunks", 0)
            total_chunks = status_response.get("total_chunks", "N/A")
            print(f"  Status: {current_status}, Chunks: {completed_chunks}/{total_chunks}")
            if current_status == "completed":
                print("Translation completed successfully!")
                break
            elif current_status == "failed":
                print("Translation failed. Check server logs for details.")
                return # Halt tests
        else:
            print("  Failed to get translation status on this attempt.")
        
        if attempt < MAX_POLLING_ATTEMPTS - 1:
            time.sleep(POLLING_INTERVAL_SECONDS)
    else: # Loop finished without break (timeout)
        print(f"Halting tests: Translation ID {translation_id} did not complete within the timeout period ({MAX_POLLING_ATTEMPTS * POLLING_INTERVAL_SECONDS}s).")
        if final_status_response: print_response_details(type('obj', (object,), {'status_code': 'N/A', 'json': lambda: final_status_response, 'text': str(final_status_response)}) ) # Show last known status
        return
    print(f"Step 4 complete. Translation status: {final_status_response.get('status') if final_status_response else 'Unknown'}")

    # 5. Download translation (now supports partial downloads, but we'll wait for completion in this E2E test)
    if final_status_response and final_status_response.get("status") == "completed":
        download_path = download_translation(translation_id)
        if download_path:
            print(f"Step 5 complete. Translated file downloaded to {download_path}")
        else:
            print("Step 5 failed: Error downloading translated file.")
    elif final_status_response and final_status_response.get("completed_chunks", 0) > 0:
        print(f"Note: Partial download would be available ({final_status_response.get('completed_chunks')}/{final_status_response.get('total_chunks')} chunks), but waiting for completion in this E2E test.")
        print("Skipping download as translation did not complete successfully.")
    else:
        print("Skipping download as translation did not complete successfully.")
    
    print_step("End-to-End API Tests Finished")

if __name__ == "__main__":
    if not TEST_DOCUMENT_PATH.exists():
        print(f"Critical Error: Test document not found at {TEST_DOCUMENT_PATH}")
        print("Please create the test document before running the tests.")
    else:
        run_tests()
