# Large Translator - Frontend Development Plan

## Project Overview
Creating a simple, user-friendly frontend for the Large Translator application. The backend already exists with comprehensive APIs for authentication, file management, chunking, and translation.

## Backend API Analysis (COMPLETED)
✅ **Authentication**: `/api/auth/login` and `/api/auth/signup` endpoints
✅ **File Upload**: `/api/files/upload` endpoint (text files only)
✅ **File Management**: `/api/files/documents` for listing uploaded files
✅ **Translation**: `/api/translations` endpoints for creating and managing translations
✅ **Download**: `/api/translations/{id}/download` for downloading completed translations

## Frontend Requirements

### Core Pages Needed
1. **Login Page** - User authentication
2. **Upload Page** - File upload interface  
3. **Translate Page** - Translation management and download

### Key Features
- Simple, clean UI with no unnecessary complexity
- Default chunk size of 2000 characters (or user configurable)
- Hide chunking complexity from user completely
- File upload → translate → download workflow
- Ability to view translated content before download

### Technical Approach
- **Framework**: Vanilla HTML/CSS/JavaScript (keeping it simple)
- **Styling**: Modern, responsive design similar to existing test interfaces
- **API Integration**: Use existing FastAPI backend at `http://localhost:8000/api`
- **Authentication**: JWT token-based auth with localStorage persistence
- **File Handling**: Text file uploads only, as per backend constraints

## Implementation Plan

### Phase 1: Core Pages
1. **Login/Signup Page (`auth.html`)**
   - Email/password form
   - JWT token storage
   - Redirect to upload page on success
   - Simple signup option

2. **File Upload Page (`upload.html`)**
   - Drag & drop file upload interface
   - File validation (text files only)
   - Display uploaded files list
   - Navigate to translation page

3. **Translation Page (`translate.html`)**
   - Select uploaded file for translation
   - Translation prompt input field
   - Chunk size configuration (default 2000)
   - Start translation process
   - Real-time status updates
   - Download completed translation
   - Preview translated content

### Phase 2: Enhanced UX
1. **Navigation & State Management**
   - Persistent login state
   - Breadcrumb navigation
   - Progress indicators

2. **Error Handling & Feedback**
   - Clear error messages
   - Loading states
   - Success confirmations

### Phase 3: Polish
1. **Responsive Design**
   - Mobile-friendly interface
   - Clean, modern styling
   - Consistent visual hierarchy

2. **Performance & Accessibility**
   - Fast loading
   - Keyboard navigation
   - Screen reader support

## API Integration Notes
- **Authentication**: Store JWT in localStorage, include in Authorization header
- **File Upload**: Use FormData for multipart file uploads
- **Translation Flow**: 
  1. Upload file → get document_id
  2. Create translation job with chunk_set (backend handles chunking)
  3. Poll translation status until complete
  4. Download or preview result
- **Error Handling**: Backend returns standard HTTP status codes with JSON error details

## File Structure
```
largetranslator/frontend/
├── index.html (redirects to auth.html)
├── auth.html (login/signup)
├── upload.html (file upload)
├── translate.html (translation management)
├── css/
│   └── styles.css (shared styles)
└── js/
    ├── auth.js (authentication logic)
    ├── upload.js (file upload logic)
    ├── translate.js (translation logic)
    └── shared.js (common utilities)
```

## Development Notes
- **Backend Study**: Carefully review backend API signatures in `/api/` directories
- **Test Files**: Use existing test files (`test_document.txt`) for development
- **Existing Tests**: Reference HTML test interfaces in `frontend/tests/` for API patterns
- **Keep Simple**: No frameworks, no build process, just clean HTML/CSS/JS
- **Default Chunk Size**: 2000 characters (configurable in translate page)
