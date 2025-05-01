#!/usr/bin/env python3
"""
End-to-end tests for authentication endpoints.
Tests both signup and login functionality using random user credentials.
"""
import pytest
import random
import string
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.append(str(project_root))

# Set environment variables for testing
os.environ["SUPABASE_URL"] = "https://test-project.supabase.co"
os.environ["SUPABASE_KEY"] = "test-key"
os.environ["SUPABASE_JWT_SECRET"] = "test-secret"

# Import the FastAPI app
from backend.api.main import app

# Create test client
client = TestClient(app)

def generate_random_email():
    """Generate a random email for testing."""
    random_string = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    return f"{random_string}@example.com"

def generate_random_password():
    """Generate a random password that meets minimum requirements."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=12))

# Create mock response objects
def create_mock_user(email):
    return MagicMock(
        id="test-user-id",
        email=email,
        dict=lambda: {"id": "test-user-id", "email": email}
    )

def create_mock_session():
    return MagicMock(
        access_token="test-access-token",
        refresh_token="test-refresh-token"
    )

class TestAuthentication:
    """Test class for authentication endpoints."""
    
    @patch('backend.external_services.supabase.auth_service.SupabaseAuthService.sign_up')
    @patch('backend.external_services.supabase.auth_service.SupabaseAuthService.sign_in')
    def test_signup_and_login(self, mock_sign_in, mock_sign_up):
        """
        End-to-end test that:
        1. Creates a new user with random credentials
        2. Attempts to log in with those credentials
        """
        # Generate random credentials
        email = generate_random_email()
        password = generate_random_password()
        
        # Setup mocks
        mock_user = create_mock_user(email)
        mock_session = create_mock_session()
        
        # Mock signup response
        mock_sign_up.return_value = {
            "user": mock_user,
            "session": mock_session
        }
        
        # Mock login response
        mock_sign_in.return_value = {
            "user": mock_user,
            "session": mock_session
        }
        
        # Test signup
        signup_data = {
            "email": email,
            "password": password
        }
        
        print(f"Testing signup with email: {email}")
        signup_response = client.post("/api/auth/signup", json=signup_data)
        
        # Check if signup was successful
        assert signup_response.status_code == 201, f"Signup failed with response: {signup_response.json()}"
        signup_result = signup_response.json()
        
        # Validate signup response structure
        assert "user" in signup_result, "User data missing from signup response"
        assert "token" in signup_result, "Token data missing from signup response"
        assert signup_result["user"]["email"] == email, "Email in response doesn't match request"
        assert "access_token" in signup_result["token"], "Access token missing from response"
        
        # Verify the mock was called correctly
        mock_sign_up.assert_called_once_with(email=email, password=password)
        
        print("Signup successful, testing login...")
        
        # Test login with same credentials
        login_data = {
            "email": email,
            "password": password
        }
        
        login_response = client.post("/api/auth/login", json=login_data)
        
        # Check if login was successful
        assert login_response.status_code == 200, f"Login failed with response: {login_response.json()}"
        login_result = login_response.json()
        
        # Validate login response structure
        assert "user" in login_result, "User data missing from login response"
        assert "token" in login_result, "Token data missing from login response"
        assert login_result["user"]["email"] == email, "Email in response doesn't match request"
        assert "access_token" in login_result["token"], "Access token missing from response"
        
        # Verify the mock was called correctly
        mock_sign_in.assert_called_once_with(email=email, password=password)
        
        print("Login successful, test passed!")
    
    @patch('backend.external_services.supabase.auth_service.SupabaseAuthService.sign_in')
    def test_login_with_invalid_credentials(self, mock_sign_in):
        """Test that login fails with invalid credentials."""
        # Generate random credentials that haven't been registered
        email = generate_random_email()
        password = generate_random_password()
        
        # Mock login to raise exception for invalid credentials
        mock_sign_in.side_effect = Exception("Invalid credentials")
        
        login_data = {
            "email": email,
            "password": password
        }
        
        print(f"Testing login with non-existent email: {email}")
        login_response = client.post("/api/auth/login", json=login_data)
        
        # Check that login fails
        assert login_response.status_code == 401, "Login with invalid credentials should fail"
        
        # Verify the mock was called correctly
        mock_sign_in.assert_called_once_with(email=email, password=password)
        
        print("Login with invalid credentials failed as expected, test passed!")

if __name__ == "__main__":
    print("Running authentication end-to-end tests...\n")
    
    # Create test instance
    test_instance = TestAuthentication()
    
    # Run tests
    try:
        test_instance.test_signup_and_login()
        print("\n--------------------------------------------------\n")
        test_instance.test_login_with_invalid_credentials()
        print("\n--------------------------------------------------\n")
        print("🎉 All authentication tests passed successfully!")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)
        
    sys.exit(0) 