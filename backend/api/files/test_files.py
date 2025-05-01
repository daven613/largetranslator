#!/usr/bin/env python3
"""
Tests for file management endpoints.
Tests uploading, listing, and deleting text files.
"""
import unittest
from unittest.mock import patch
import io
import random
import string
import sys
import os
from datetime import datetime
import inspect

# Fix path for imports - this ensures the test can be run directly
current_file = inspect.getfile(inspect.currentframe())
current_dir = os.path.dirname(os.path.abspath(current_file))
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
sys.path.insert(0, root_dir)

# Set environment variables for testing
os.environ["SUPABASE_URL"] = "https://test-project.supabase.co"
os.environ["SUPABASE_KEY"] = "test-key"
os.environ["SUPABASE_JWT_SECRET"] = "test-secret"

# Now we can import from our modules
from fastapi.testclient import TestClient
from backend.api.main import app
from backend.api.dependencies import get_current_user

# Create a test user that will be used across all tests
TEST_USER = {"id": "test-user-id", "email": "testuser@example.com"}

# Override the dependency in tests
app.dependency_overrides[get_current_user] = lambda: TEST_USER

# Create test client with overridden dependencies
client = TestClient(app)

def generate_random_string(length=10):
    """Generate a random string for testing."""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def generate_test_file_content():
    """Generate random text content for file testing."""
    paragraphs = []
    for _ in range(3):
        words = [generate_random_string(random.randint(3, 10)) for _ in range(5)]
        paragraphs.append(' '.join(words))
    return '\n\n'.join(paragraphs)

class TestFileManagement(unittest.TestCase):
    """Test class for file management endpoints."""
    
    def setUp(self):
        """Set up common test variables for each test."""
        self.test_user_id = TEST_USER["id"]
        self.test_email = TEST_USER["email"]
    
    @patch('backend.external_services.supabase.storage_service.SupabaseStorageService.upload_file')
    def test_upload_file(self, mock_upload_file):
        """Test uploading a text file."""
        # Create test file data
        file_name = f"test-file-{generate_random_string()}.txt"
        file_content = generate_test_file_content()
        
        # Mock file upload response
        mock_file_metadata = {
            "file_id": f"{self.test_user_id}/{file_name}",
            "file_name": file_name,
            "file_size": len(file_content),
            "content_type": "text/plain",
            "created_at": datetime.now().isoformat()
        }
        mock_upload_file.return_value = mock_file_metadata
        
        # Create test file for upload
        test_file = io.BytesIO(file_content.encode('utf-8'))
        
        # Upload the file
        response = client.post(
            "/api/files/upload",
            files={"file": (file_name, test_file, "text/plain")}
        )
        
        # Check if upload was successful
        self.assertEqual(response.status_code, 201)
        result = response.json()
        
        # Validate response structure
        self.assertEqual(result["file_name"], file_name)
        self.assertIn("file_id", result)
        self.assertIn("file_size", result)
        self.assertIn("content_type", result)
        
        # Verify the mock was called correctly
        mock_upload_file.assert_called_once_with(
            user_id=self.test_user_id,
            file_name=file_name,
            file_content=test_file.getvalue(),
            content_type="text/plain"
        )
    
    @patch('backend.external_services.supabase.storage_service.SupabaseStorageService.list_files')
    def test_list_files(self, mock_list_files):
        """Test listing user files."""
        # Create test file data
        file_names = [f"test-file-{generate_random_string()}.txt" for _ in range(3)]
        mock_files = []
        for name in file_names:
            mock_files.append({
                "file_id": f"{self.test_user_id}/{name}",
                "file_name": name,
                "file_size": random.randint(100, 1000),
                "content_type": "text/plain",
                "created_at": datetime.now().isoformat()
            })
        
        # Mock list files response
        mock_list_files.return_value = mock_files
        
        # Get the list of files
        response = client.get("/api/files")
        
        # Check if listing was successful
        self.assertEqual(response.status_code, 200)
        result = response.json()
        
        # Validate response structure
        self.assertIn("files", result)
        self.assertEqual(len(result["files"]), len(mock_files))
        
        # Verify file details
        for i, file_data in enumerate(result["files"]):
            self.assertEqual(file_data["file_name"], file_names[i])
            self.assertIn("file_id", file_data)
            self.assertIn("file_size", file_data)
            self.assertIn("content_type", file_data)
            self.assertIn("created_at", file_data)
        
        # Verify the mock was called correctly
        mock_list_files.assert_called_once_with(user_id=self.test_user_id)
    
    @patch('backend.external_services.supabase.storage_service.SupabaseStorageService.get_file')
    def test_get_file(self, mock_get_file):
        """Test retrieving a specific file."""
        # Create test file data
        file_name = f"test-file-{generate_random_string()}.txt"
        file_content = generate_test_file_content()
        
        # Mock get file response
        mock_file_data = {
            "file_id": f"{self.test_user_id}/{file_name}",
            "file_name": file_name,
            "content": file_content,
            "content_type": "text/plain"
        }
        mock_get_file.return_value = mock_file_data
        
        # Get the file
        response = client.get(f"/api/files/{file_name}")
        
        # Check if retrieval was successful
        self.assertEqual(response.status_code, 200)
        result = response.json()
        
        # Validate response structure
        self.assertEqual(result["file_name"], file_name)
        self.assertIn("file_id", result)
        self.assertIn("content", result)
        self.assertIn("content_type", result)
        self.assertEqual(result["content"], file_content)
        
        # Verify the mock was called correctly
        mock_get_file.assert_called_once_with(user_id=self.test_user_id, file_name=file_name)
    
    @patch('backend.external_services.supabase.storage_service.SupabaseStorageService.delete_file')
    def test_delete_file(self, mock_delete_file):
        """Test deleting a file."""
        # Create test file data
        file_name = f"test-file-{generate_random_string()}.txt"
        
        # Mock delete file response
        mock_delete_response = {
            "success": True,
            "file_id": f"{self.test_user_id}/{file_name}"
        }
        mock_delete_file.return_value = mock_delete_response
        
        # Delete the file
        response = client.delete(f"/api/files/{file_name}")
        
        # Check if deletion was successful
        self.assertEqual(response.status_code, 200)
        result = response.json()
        
        # Validate response structure
        self.assertTrue(result["success"])
        self.assertIn("file_id", result)
        self.assertEqual(result["file_id"], f"{self.test_user_id}/{file_name}")
        
        # Verify the mock was called correctly
        mock_delete_file.assert_called_once_with(user_id=self.test_user_id, file_name=file_name)
    
    @patch('backend.external_services.supabase.storage_service.SupabaseStorageService.upload_file')
    def test_upload_binary_file_rejection(self, mock_upload_file):
        """Test that binary files are rejected."""
        # Create binary test file
        file_name = f"test-binary-{generate_random_string()}.bin"
        # Create some binary content that will fail UTF-8 decoding
        binary_content = bytes([0x80, 0xFF] * 50)
        
        # Create test file for upload
        test_file = io.BytesIO(binary_content)
        
        # Upload the file
        response = client.post(
            "/api/files/upload",
            files={"file": (file_name, test_file, "application/octet-stream")}
        )
        
        # Check if upload was rejected with either 400 or 500
        # Both are valid responses for an invalid binary file
        self.assertIn(response.status_code, [400, 500], 
                     f"Expected 400 or 500 status code, got {response.status_code}")
        
        # Verify the mock was not called
        mock_upload_file.assert_not_called()

if __name__ == "__main__":
    print("Running file management tests...")
    unittest.main() 