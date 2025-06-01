// Large Translator Frontend - Shared Utilities

const API_BASE_URL = 'http://localhost:8000/api';

// Authentication utilities
const Auth = {
  getToken() {
    return localStorage.getItem('auth_token');
  },

  setToken(token) {
    localStorage.setItem('auth_token', token);
  },

  getUserInfo() {
    const userInfo = localStorage.getItem('user_info');
    return userInfo ? JSON.parse(userInfo) : null;
  },

  setUserInfo(userInfo) {
    localStorage.setItem('user_info', JSON.stringify(userInfo));
  },

  clearAuth() {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user_info');
  },

  isAuthenticated() {
    return !!this.getToken();
  },

  getAuthHeaders() {
    const token = this.getToken();
    return token ? { 'Authorization': `Bearer ${token}` } : {};
  }
};

// API utilities
const API = {
  async request(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    const defaultOptions = {
      headers: {
        'Content-Type': 'application/json',
        ...Auth.getAuthHeaders(),
        ...options.headers
      }
    };

    try {
      const response = await fetch(url, { ...defaultOptions, ...options });
      
      // Handle authentication errors
      if (response.status === 401) {
        Auth.clearAuth();
        window.location.href = 'auth.html';
        return null;
      }

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || `HTTP ${response.status}`);
      }

      return data;
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  },

  async login(email, password) {
    return this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password })
    });
  },

  async signup(email, password) {
    return this.request('/auth/signup', {
      method: 'POST',
      body: JSON.stringify({ email, password })
    });
  },

  async uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);

    return this.request('/files/upload', {
      method: 'POST',
      headers: {
        // Remove Content-Type to let browser set it for FormData
        ...Auth.getAuthHeaders()
      },
      body: formData
    });
  },

  async getDocuments() {
    return this.request('/files/documents');
  },

  async createTranslation(chunkSetId, prompt, aiModel = 'gpt-4o-mini') {
    return this.request('/translations', {
      method: 'POST',
      body: JSON.stringify({
        chunk_set_id: chunkSetId,
        prompt: prompt
      })
    });
  },

  async getTranslations() {
    return this.request('/translations');
  },

  async getTranslation(translationId) {
    return this.request(`/translations/${translationId}`);
  },

  async downloadTranslation(translationId) {
    const token = Auth.getToken();
    const url = `${API_BASE_URL}/translations/${translationId}/download`;
    
    const response = await fetch(url, {
      headers: Auth.getAuthHeaders()
    });

    if (!response.ok) {
      throw new Error(`Download failed: ${response.status}`);
    }

    return response;
  },

  async createChunkSet(fileId, chunkSize = 2000) {
    return this.request('/chunking', {
      method: 'POST',
      body: JSON.stringify({
        file_id: fileId,
        target_chunk_size: chunkSize,
        processor_type: 'text_chunker'
      })
    });
  },

  async deleteTranslation(translationId) {
    return this.request(`/translations/${translationId}`, {
      method: 'DELETE'
    });
  }
};

// UI utilities
const UI = {
  showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type}`;
    alertDiv.textContent = message;

    const container = document.querySelector('.container');
    container.insertBefore(alertDiv, container.firstChild);

    // Auto-remove after 5 seconds
    setTimeout(() => {
      if (alertDiv.parentNode) {
        alertDiv.remove();
      }
    }, 5000);
  },

  showError(message) {
    this.showAlert(message, 'error');
  },

  showSuccess(message) {
    this.showAlert(message, 'success');
  },

  setLoading(element, loading = true) {
    if (loading) {
      element.disabled = true;
      element.innerHTML = '<div class="loading"><div class="spinner"></div>Loading...</div>';
    } else {
      element.disabled = false;
      element.innerHTML = element.dataset.originalText || 'Submit';
    }
  },

  formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  },

  formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
  },

  truncateText(text, maxLength = 100) {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
  }
};

// Navigation utilities
const Navigation = {
  redirectIfNotAuthenticated() {
    if (!Auth.isAuthenticated()) {
      window.location.href = 'auth.html';
    }
  },

  redirectIfAuthenticated() {
    if (Auth.isAuthenticated()) {
      window.location.href = 'upload.html';
    }
  },

  logout() {
    Auth.clearAuth();
    window.location.href = 'auth.html';
  },

  setupNavigation() {
    // Add navigation buttons if user is authenticated
    if (Auth.isAuthenticated()) {
      const nav = document.createElement('div');
      nav.className = 'navigation';
      
      const userInfo = Auth.getUserInfo();
      const userEmail = userInfo ? userInfo.email : 'User';
      
      nav.innerHTML = `
        <span class="nav-btn">${userEmail}</span>
        <a href="upload.html" class="nav-btn">Upload</a>
        <a href="translate.html" class="nav-btn">New Translation</a>
        <a href="history.html" class="nav-btn">History</a>
        <button class="nav-btn logout-btn" onclick="Navigation.logout()">Logout</button>
      `;
      
      document.body.appendChild(nav);
    }
  }
};

// File validation utilities
const FileValidation = {
  isTextFile(file) {
    // Check MIME type
    if (file.type.startsWith('text/')) {
      return true;
    }

    // Check file extension
    const textExtensions = ['.txt', '.md', '.csv', '.json', '.xml', '.html', '.css', '.js', '.py', '.java', '.cpp', '.c'];
    const fileName = file.name.toLowerCase();
    return textExtensions.some(ext => fileName.endsWith(ext));
  },

  validateFile(file) {
    const errors = [];

    if (!file) {
      errors.push('No file selected');
      return errors;
    }

    if (!this.isTextFile(file)) {
      errors.push('Only text files are supported');
    }

    if (file.size > 10 * 1024 * 1024) { // 10MB limit
      errors.push('File size must be less than 10MB');
    }

    if (file.size === 0) {
      errors.push('File cannot be empty');
    }

    return errors;
  }
};

// Translation status utilities
const TranslationStatus = {
  getStatusDisplay(status) {
    const statusMap = {
      'pending': { class: 'status-pending', text: '⏳ Pending', description: 'Translation queued' },
      'in_progress': { class: 'status-processing', text: '⚙️ Processing', description: 'Translation in progress' },
      'completed': { class: 'status-completed', text: '✅ Completed', description: 'Translation finished' },
      'failed': { class: 'status-failed', text: '❌ Failed', description: 'Translation failed' }
    };

    return statusMap[status] || { class: 'status-pending', text: '❓ Unknown', description: 'Unknown status' };
  },

  calculateProgress(completedChunks, totalChunks) {
    if (totalChunks === 0) {
      return 0;
    }
    const progress = Math.round((completedChunks / totalChunks) * 100);
    return progress;
  }
};

// Initialize shared functionality when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  Navigation.setupNavigation();
}); 