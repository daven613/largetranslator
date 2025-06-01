// Large Translator Frontend - Upload Logic

document.addEventListener('DOMContentLoaded', () => {
    // Redirect if not authenticated
    Navigation.redirectIfNotAuthenticated();

    // Get DOM elements
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');
    const filesList = document.getElementById('filesList');
    const refreshBtn = document.getElementById('refreshBtn');

    // Initialize page
    loadFiles();

    // File upload event handlers
    dropZone.addEventListener('click', () => {
        fileInput.click();
    });

    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFileUpload(files[0]);
        }
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileUpload(e.target.files[0]);
        }
    });

    refreshBtn.addEventListener('click', () => {
        loadFiles();
    });

    // Handle file upload
    async function handleFileUpload(file) {
        // Validate file
        const validationErrors = FileValidation.validateFile(file);
        if (validationErrors.length > 0) {
            UI.showError(validationErrors.join(', '));
            return;
        }

        // Show upload progress
        const progressDiv = document.createElement('div');
        progressDiv.className = 'alert alert-info';
        progressDiv.innerHTML = `
            <div>Uploading ${file.name}...</div>
            <div class="progress-bar">
                <div class="progress-fill" style="width: 0%"></div>
            </div>
        `;
        
        const container = document.querySelector('.container');
        container.insertBefore(progressDiv, container.firstChild);

        // Simulate progress
        const progressFill = progressDiv.querySelector('.progress-fill');
        let progress = 0;
        const progressInterval = setInterval(() => {
            progress += Math.random() * 30;
            if (progress > 90) progress = 90;
            progressFill.style.width = progress + '%';
        }, 200);

        try {
            const response = await API.uploadFile(file);
            
            // Complete progress
            clearInterval(progressInterval);
            progressFill.style.width = '100%';
            
            UI.showSuccess(`File "${file.name}" uploaded successfully!`);
            
            // Remove progress indicator and reload files
            setTimeout(() => {
                progressDiv.remove();
                loadFiles();
            }, 1000);

            // Clear file input
            fileInput.value = '';

        } catch (error) {
            clearInterval(progressInterval);
            progressDiv.remove();
            UI.showError(`Upload failed: ${error.message}`);
        }
    }

    // Load and display files
    async function loadFiles() {
        try {
            filesList.innerHTML = '<div class="loading"><div class="spinner"></div>Loading files...</div>';
            
            const response = await API.getDocuments();
            const documents = response.documents || [];

            if (documents.length === 0) {
                filesList.innerHTML = `
                    <div class="empty-state">
                        <span class="icon">📂</span>
                        <h3>No files uploaded yet</h3>
                        <p>Upload your first text file to get started</p>
                    </div>
                `;
                return;
            }

            // Sort documents by creation date (newest first)
            documents.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));

            filesList.innerHTML = documents.map(doc => `
                <div class="file-item" data-document-id="${doc.id}">
                    <div class="file-info">
                        <h4>${doc.name}</h4>
                        <p>Size: ${UI.formatFileSize(doc.file_size)} • Uploaded: ${UI.formatDate(doc.created_at)}</p>
                    </div>
                    <div class="file-actions">
                        <button class="btn btn-small btn-success" onclick="translateFile('${doc.id}', '${doc.name}')">
                            🔤 Translate
                        </button>
                        <button class="btn btn-small btn-secondary" onclick="viewFile('${doc.id}', '${doc.name}')">
                            👁️ View
                        </button>
                    </div>
                </div>
            `).join('');

        } catch (error) {
            filesList.innerHTML = `
                <div class="alert alert-error">
                    Failed to load files: ${error.message}
                </div>
            `;
        }
    }

    // Global functions for file actions
    window.translateFile = function(documentId, fileName) {
        // Store selected file info and redirect to translation page
        localStorage.setItem('selectedDocument', JSON.stringify({
            id: documentId,
            name: fileName
        }));
        window.location.href = 'translate.html';
    };

    window.viewFile = async function(documentId, fileName) {
        try {
            // For now, just show a placeholder. In a full implementation,
            // you'd fetch the file content from the backend
            UI.showAlert(`File viewing not implemented yet. Document ID: ${documentId}`, 'info');
            
            // Future implementation would call something like:
            // const fileContent = await API.getFileContent(documentId);
            // showFilePreviewModal(fileName, fileContent);
            
        } catch (error) {
            UI.showError(`Failed to view file: ${error.message}`);
        }
    };
}); 