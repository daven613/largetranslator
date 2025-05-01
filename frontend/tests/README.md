# Frontend Test Pages

This directory contains standalone HTML test pages that can be used to manually test specific features of the application.

## Available Test Pages

### Authentication Test Page (`auth-test.html`)

A simple page for testing user registration and login functionality. The page connects to the backend authentication API endpoints.

#### How to Use

1. Make sure your backend server is running (usually on port 8000)
2. Open the `auth-test.html` file in a web browser
   - You can use any simple HTTP server to serve the file, or open it directly
3. The page contains two forms:
   - **Create an Account** - To register a new user
   - **Sign In** - To log in with existing credentials

#### Features

- User registration with email and password
- User login with email and password
- Display of API responses
- Auto-filling login form after successful registration
- Token storage in session storage after successful login

#### Notes

- The page assumes your API is running at `http://localhost:8000/api`
- If your API is hosted elsewhere, update the `API_BASE_URL` in the JavaScript code
- This is a testing tool and not intended for production use 