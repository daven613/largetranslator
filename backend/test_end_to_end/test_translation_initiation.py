"""
End-to-end test for the translation initiation API (simplified).

Uses a predefined chunk_set_id to initiate translation and verifies the response.
"""
import asyncio
import os
import sys
import logging
from pathlib import Path

import httpx

# Add project root to Python path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000/api"
TRANSLATIONS_URL = f"{BASE_URL}/translations"

# Hardcoded chunk_set_id
CHUNK_SET_ID_TO_TEST = "24af3fbe-7f38-4fc4-8a36-bf60f4624bf0"

# --- Helper to get auth token ---
async def get_auth_token():
    """Retrieves the auth token from .test_env or by running get_auth_token.py."""
    token_file = Path(__file__).resolve().parent / ".test_env"
    if token_file.exists():
        lines = token_file.read_text().splitlines()
        for line in lines:
            if line.startswith("SUPABASE_TEST_JWT="):
                token = line.split("=", 1)[1].strip()
                if token:
                    logger.info("Using token from .test_env")
                    return token
        logger.warning("SUPABASE_TEST_JWT not found in .test_env, though file exists.")
    
    logger.info("No token in .test_env or not found, attempting to generate a new one...")
    script_path = Path(__file__).resolve().parent / "get_auth_token.py"
    if not script_path.exists():
        logger.error(f"{script_path} not found. Cannot generate token.")
        return None

    process = await asyncio.create_subprocess_exec(
        sys.executable, str(script_path),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()

    if process.returncode == 0:
        logger.info("Successfully generated new token.")
        token_from_script = (Path(__file__).resolve().parent / ".test_env").read_text().strip()
        if token_from_script.startswith("SUPABASE_TEST_JWT="):
             token_from_script = token_from_script.split("=",1)[1]
        if token_from_script: # Check if token is not empty
             logger.info("Token read from .test_env after generation.")
             return token_from_script
        logger.error("get_auth_token.py ran but .test_env was not updated or token is empty.")
        return None 
    else:
        logger.error(f"Failed to generate token: {stderr.decode()}")
        return None

async def main():
    """Runs the simplified end-to-end test for translation initiation."""
    logger.info("=== Starting SIMPLIFIED Translation Initiation API Test ===")
    
    auth_token = await get_auth_token()
    if not auth_token:
        logger.error("Failed to get auth token. Exiting test.")
        return

    headers = {"Authorization": f"Bearer {auth_token}"}
    translation_id_to_delete = None # Keep for potential future cleanup if needed

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            chunk_set_id = CHUNK_SET_ID_TO_TEST
            translation_prompt = "Translate this to English."
            
            logger.info(f"Initiating translation for Chunk Set ID: {chunk_set_id} with prompt: '{translation_prompt}'")

            translation_payload = {
                "chunk_set_id": chunk_set_id,
                "prompt": translation_prompt
            }

            response = await client.post(TRANSLATIONS_URL, json=translation_payload, headers=headers)
            
            logger.info(f"Translation Initiation Status Code: {response.status_code}")
            assert response.status_code == 201, f"Translation initiation failed with status {response.status_code}. Response: {response.text}"
            translation_response_json = response.json()
            logger.info(f"Translation Initiation Response JSON: {translation_response_json}")

            translation_id_to_delete = translation_response_json.get("id")
            assert translation_id_to_delete, "Translation ID not in response"
            assert translation_response_json.get("status") == "pending", "Initial status should be pending"
            assert translation_response_json.get("chunk_set_id") == chunk_set_id, "Chunk set ID mismatch"
            
            total_chunks_in_response = translation_response_json.get("total_chunks")
            assert total_chunks_in_response is not None and isinstance(total_chunks_in_response, int) and total_chunks_in_response >= 0, \
                f"Total chunks missing, not an int, or negative: {total_chunks_in_response}"
            logger.info(f"Total chunks reported in response: {total_chunks_in_response}")

            assert translation_response_json.get("target_language") == "N/A (prompt-defined)", "Target language should be placeholder"
            assert translation_response_json.get("ai_model") == "mock_model", "AI model should be placeholder"
            assert translation_response_json.get("name") == f"Translation for {chunk_set_id}", "Name mismatch or not auto-generated as expected"

            logger.info(f"Translation job {translation_id_to_delete} initiated successfully. Status: {translation_response_json.get('status')}")

            logger.info("=== SIMPLIFIED Translation Initiation API Test COMPLETED SUCCESSFULLY ===")

    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP status error during translation initiation: {e.response.status_code} - {e.response.text}")
    except httpx.RequestError as e:
        logger.error(f"HTTP request error during translation initiation: {e}")
    except AssertionError as e:
        logger.error(f"Test assertion failed: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
    finally:
        # No file cleanup needed as we are not uploading
        # if translation_id_to_delete: # Placeholder for potential future cleanup API call
        #    logger.info(f"Translation job {translation_id_to_delete} was created.")
        logger.info("=== SIMPLIFIED Translation Initiation API Test Finished ===")

if __name__ == "__main__":
    asyncio.run(main())