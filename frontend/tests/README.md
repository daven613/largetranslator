# Large Translator API - Frontend Testing Interface

## Overview

This directory contains comprehensive HTML-based testing interfaces for all Large Translator API endpoints. These pages allow you to test the complete API workflow with real data, proper authentication, and organized output display.

## Test Pages

### 🔐 Authentication (`auth-test.html`)
- **Login/logout** with email and password
- **Token management** with copy-to-clipboard functionality
- **User information** display
- **Token validation** testing
- **Shared authentication** across all test pages

### 🌐 Translation (`translation-test.html`)
- **Start new translations** with chunk set ID and custom prompts
- **Check translation status** and progress
- **Get detailed translation information**
- **Download completed** translated documents
- **List all user translations**

### 📊 API Overview (`api-overview.html`)
- **Complete endpoint reference** with descriptions
- **HTTP method indicators** (GET, POST, DELETE)
- **Authentication requirements** for each endpoint
- **Direct links** to relevant test pages
- **Server information** and documentation links

### 📁 File Management (`file-management-test.html`)
- **Upload files** for processing
- **List uploaded files**
- **Get file details**
- **Delete files**

### 🔪 Text Chunking (`chunking-test.html`)
- **Create chunk sets** from uploaded files
- **List all chunk sets**
- **View chunk set details** and individual chunks
- **Configure chunking parameters**

## Getting Started

1. **Start the API server**:
   ```bash
   cd largetranslator
   python main.py
   ```

2. **Open the authentication page**:
   - Navigate to `frontend/tests/auth-test.html` in your browser
   - Or visit: `file:///path/to/largetranslator/frontend/tests/auth-test.html`

3. **Login with your credentials**:
   - Enter your email and password
   - Click "Login" to get an authentication token
   - The token will be automatically shared across all test pages

4. **Test the complete workflow**:
   - **Upload a file** using the file management page
   - **Create chunks** using the chunking page
   - **Start a translation** using the translation page
   - **Monitor progress** and download results

## Key Features

### 🔄 Seamless Integration
- **Authentication tokens** are automatically shared between pages
- **IDs and outputs** can be easily copied and pasted between different APIs
- **Real-time auth status** displayed on every page

### 📋 Copy-to-Clipboard
- **Authentication tokens** and headers
- **File IDs, chunk set IDs, translation IDs**
- **Complete JSON responses** for debugging

### 🎨 Clean Interface
- **Organized sections** for different operations
- **Color-coded status messages** (success, error, info)
- **Formatted JSON output** for easy reading
- **Responsive design** that works on different screen sizes

### 🔍 Comprehensive Testing
- **All API endpoints** covered
- **Error handling** and validation
- **Real data workflow** from start to finish
- **Status monitoring** for long-running operations

## API Workflow

The typical workflow for testing the complete translation process:

1. **Authentication** → Get token
2. **File Upload** → Get file ID
3. **Text Chunking** → Get chunk set ID
4. **Translation** → Get translation ID
5. **Status Monitoring** → Check progress
6. **Download** → Get translated document

## Navigation

Each test page includes navigation links to other test pages, making it easy to move through the complete workflow without losing your authentication state.

## Troubleshooting

- **Authentication issues**: Make sure the API server is running on `http://localhost:8000`
- **CORS errors**: The API should be configured to allow requests from file:// origins
- **Token expiration**: Re-authenticate if you get 401 errors
- **Missing data**: Use the API overview page to understand required parameters

## Development

These test pages are designed to be:
- **Self-contained** (no external dependencies)
- **Easy to modify** for testing new endpoints
- **Debugger-friendly** with clear error messages and JSON output
- **Production-ready** for manual testing and QA workflows 