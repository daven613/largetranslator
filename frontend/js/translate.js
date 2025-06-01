// Large Translator Frontend - New Translation Logic

let currentTranslation = null;
// Removed statusPollingInterval as we're removing automatic polling

document.addEventListener('DOMContentLoaded', () => {
    // Redirect if not authenticated
    Navigation.redirectIfNotAuthenticated();

    // Get DOM elements
    const fileSelector = document.getElementById('fileSelector');
    const translationPrompt = document.getElementById('translationPrompt');
    const chunkSize = document.getElementById('chunkSize');
    const startTranslationBtn = document.getElementById('startTranslationBtn');
    const refreshStatusBtn = document.getElementById('refreshStatusBtn');
    const currentTranslationSection = document.getElementById('currentTranslationSection');
    const currentTranslationStatus = document.getElementById('currentTranslationStatus');

    // Initialize page
    init();

    async function init() {
        await loadFiles();
        
        // Check if a file was pre-selected from upload page
        const selectedDocument = localStorage.getItem('selectedDocument');
        if (selectedDocument) {
            const doc = JSON.parse(selectedDocument);
            // Find the option with matching document ID and select it
            const options = fileSelector.querySelectorAll('option');
            for (const option of options) {
                if (option.dataset.documentId === doc.id) {
                    fileSelector.value = option.value;
                    break;
                }
            }
            localStorage.removeItem('selectedDocument');
        }

        // Check for any active translation
        await checkForActiveTranslation();
    }

    // Load available files into selector
    async function loadFiles() {
        try {
            const response = await API.getDocuments();
            const documents = response.documents || [];
            
            fileSelector.innerHTML = '<option value="">Select a file to translate...</option>';
            
            documents.forEach(doc => {
                const option = document.createElement('option');
                option.value = doc.file_path; // Use file_path instead of id for chunking
                option.textContent = `${doc.name} (${UI.formatFileSize(doc.file_size)})`;
                option.dataset.documentId = doc.id; // Store document ID for reference
                fileSelector.appendChild(option);
            });

            if (documents.length === 0) {
                fileSelector.innerHTML = '<option value="">No files available - upload a file first</option>';
                startTranslationBtn.disabled = true;
            }

        } catch (error) {
            fileSelector.innerHTML = '<option value="">Error loading files</option>';
            UI.showError(`Failed to load files: ${error.message}`);
        }
    }

    // Check for any active translation
    async function checkForActiveTranslation() {
        try {
            const response = await API.getTranslations();
            const translations = response.translations || [];
            
            // Find the most recent active translation
            const activeTranslation = translations.find(t => 
                t.status === 'pending' || t.status === 'in_progress'
            );
            
            if (activeTranslation) {
                currentTranslation = activeTranslation;
                showCurrentTranslation();
                // Removed automatic polling - user must manually refresh
            }
        } catch (error) {
            console.error('Failed to check for active translations:', error);
        }
    }

    // Handle translation start
    startTranslationBtn.addEventListener('click', async () => {
        const selectedFilePath = fileSelector.value;
        const prompt = translationPrompt.value.trim();
        const chunkSizeValue = parseInt(chunkSize.value);

        // Validation
        if (!selectedFilePath) {
            UI.showError('Please select a file to translate');
            return;
        }

        if (!prompt) {
            UI.showError('Please enter a translation prompt');
            return;
        }

        if (chunkSizeValue < 500 || chunkSizeValue > 5000) {
            UI.showError('Chunk size must be between 500 and 5000 characters');
            return;
        }

        UI.setLoading(startTranslationBtn, true);

        try {
            // Step 1: Create chunk set
            UI.showAlert('Creating document chunks...', 'info');
            const chunkSetResponse = await API.createChunkSet(selectedFilePath, chunkSizeValue);
            
            // Step 2: Create and start translation (now happens automatically)
            UI.showAlert('Starting translation process...', 'info');
            const translationResponse = await API.createTranslation(
                chunkSetResponse.chunk_set_id,
                prompt
            );

            UI.showSuccess('Translation started successfully! Use the refresh button to check progress.');
            
            // Set current translation and show status
            currentTranslation = translationResponse;
            showCurrentTranslation();
            // Removed automatic polling - user must manually refresh
            
            // Clear form
            translationPrompt.value = '';
            fileSelector.value = '';

        } catch (error) {
            UI.showError(`Failed to start translation: ${error.message}`);
        } finally {
            UI.setLoading(startTranslationBtn, false);
        }
    });

    // Refresh status button
    refreshStatusBtn.addEventListener('click', () => {
        if (currentTranslation) {
            pollTranslationStatus();
        }
    });

    // Show current translation status
    function showCurrentTranslation() {
        if (!currentTranslation) {
            currentTranslationSection.style.display = 'none';
            return;
        }

        currentTranslationSection.style.display = 'block';
        renderCurrentTranslation();
    }

    // Render current translation status
    function renderCurrentTranslation() {
        if (!currentTranslation) return;

        const statusDisplay = TranslationStatus.getStatusDisplay(currentTranslation.status);
        const progress = TranslationStatus.calculateProgress(currentTranslation.completed_chunks, currentTranslation.total_chunks);
        
        currentTranslationStatus.innerHTML = `
            <div class="translation-status">
                <div class="status-header">
                    <div class="status-title">${currentTranslation.name || 'Translation Job'}</div>
                    <div class="status-indicator ${statusDisplay.class}">
                        ${statusDisplay.text}
                    </div>
                </div>
                
                <div class="job-details">
                    <p><strong>AI Model:</strong> ${currentTranslation.ai_model}</p>
                    <p><strong>Created:</strong> ${UI.formatDate(currentTranslation.created_at)}</p>
                    <p><strong>Progress:</strong> ${currentTranslation.completed_chunks} / ${currentTranslation.total_chunks} chunks (${progress}%)</p>
                </div>

                <div class="status-progress">
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${progress}%"></div>
                    </div>
                </div>

                <div class="status-actions">
                    ${currentTranslation.completed_chunks > 0 ? `
                        <button class="btn btn-small btn-success" onclick="downloadTranslation('${currentTranslation.id}')">
                            💾 Download${currentTranslation.status !== 'completed' ? ' (Partial)' : ''}
                        </button>
                        <button class="btn btn-small btn-secondary" onclick="previewTranslation('${currentTranslation.id}')">
                            👁️ Preview
                        </button>
                    ` : ''}
                    
                    ${currentTranslation.status === 'failed' || currentTranslation.status === 'completed_with_errors' ? `
                        <button class="btn btn-small btn-danger" onclick="retryTranslation('${currentTranslation.id}')">
                            🔄 Retry${currentTranslation.status === 'completed_with_errors' ? ' Failed Chunks' : ''}
                        </button>
                    ` : ''}
                    
                    <button class="btn btn-small btn-secondary" onclick="refreshCurrentStatus()">
                        🔄 Refresh Status
                    </button>
                    
                    ${currentTranslation.status === 'completed' || currentTranslation.status === 'failed' || currentTranslation.status === 'completed_with_errors' ? `
                        <button class="btn btn-small btn-secondary" onclick="clearCurrentTranslation()">
                            ✕ Clear
                        </button>
                    ` : ''}
                </div>
            </div>
        `;
    }

    // Removed startStatusPolling() function - no more automatic polling

    // Poll translation status (now only used for manual refresh)
    async function pollTranslationStatus() {
        if (!currentTranslation) return;

        try {
            const updatedTranslation = await API.getTranslation(currentTranslation.id);
            
            currentTranslation = updatedTranslation;
            
            // Show notification for completed translations
            if (currentTranslation.status === 'completed') {
                UI.showSuccess(`Translation completed!`);
            } else if (currentTranslation.status === 'failed') {
                UI.showError(`Translation failed.`);
            } else if (currentTranslation.status === 'completed_with_errors') {
                UI.showAlert(`Translation completed with errors! Some chunks may have failed.`, 'warning');
            }
            
            renderCurrentTranslation();
        } catch (error) {
            console.error(`Failed to poll status for translation ${currentTranslation.id}:`, error);
        }
    }

    // Global functions for translation actions
    window.downloadTranslation = async function(translationId) {
        try {
            // Get translation details first to show appropriate feedback
            const translation = await API.getTranslation(translationId);
            const isPartial = translation.status !== 'completed';
            const progress = `${translation.completed_chunks}/${translation.total_chunks}`;
            
            if (isPartial) {
                UI.showAlert(`Preparing partial download (${progress} chunks completed)...`, 'info');
            } else {
                UI.showAlert('Preparing download...', 'info');
            }
            
            const response = await API.downloadTranslation(translationId);
            
            // Create download link
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            
            // Extract filename from response headers or use default
            const contentDisposition = response.headers.get('content-disposition');
            let filename = 'translated_document.txt';
            if (contentDisposition) {
                const filenameMatch = contentDisposition.match(/filename="(.+)"/);
                if (filenameMatch) {
                    filename = filenameMatch[1];
                }
            }
            
            // Add partial indicator to filename if needed
            if (isPartial) {
                const nameParts = filename.split('.');
                if (nameParts.length > 1) {
                    const ext = nameParts.pop();
                    filename = `${nameParts.join('.')}_partial_${progress.replace('/', '_of_')}.${ext}`;
                } else {
                    filename = `${filename}_partial_${progress.replace('/', '_of_')}`;
                }
            }
            
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            if (isPartial) {
                UI.showSuccess(`Partial download started! (${progress} chunks)`);
            } else {
                UI.showSuccess('Download started!');
            }
            
        } catch (error) {
            UI.showError(`Download failed: ${error.message}`);
        }
    };

    window.previewTranslation = async function(translationId) {
        // For now, show a placeholder. In a full implementation,
        // you'd fetch the translation content and show it in a modal
        UI.showAlert('Preview functionality coming soon!', 'info');
    };

    window.retryTranslation = async function(translationId) {
        try {
            // Get the original translation details
            const originalTranslation = await API.getTranslation(translationId);
            
            UI.showAlert('Creating new translation job...', 'info');
            
            // Create a new translation job with the same parameters
            const newTranslation = await API.createTranslation(
                originalTranslation.chunk_set_id,
                `Retry: ${originalTranslation.name || 'Translation'}`
            );
            
            UI.showSuccess('New translation job created!');
            
            // Set as current translation
            currentTranslation = newTranslation;
            showCurrentTranslation();
            // Removed automatic polling - user must manually refresh
        } catch (error) {
            UI.showError(`Failed to retry translation: ${error.message}`);
        }
    };

    window.refreshCurrentStatus = async function() {
        try {
            await pollTranslationStatus();
            UI.showAlert('Status refreshed!', 'info');
        } catch (error) {
            UI.showError(`Failed to refresh status: ${error.message}`);
        }
    };

    window.clearCurrentTranslation = function() {
        currentTranslation = null;
        // No need to clear interval since we removed automatic polling
        showCurrentTranslation();
        UI.showAlert('Current translation cleared', 'info');
    };

    // Removed beforeunload event listener since there's no more polling interval to clean up
}); 