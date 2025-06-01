// Large Translator Frontend - Translation History Logic

let allTranslations = [];
let filteredTranslations = [];
let statusPollingIntervals = {};

document.addEventListener('DOMContentLoaded', () => {
    // Redirect if not authenticated
    Navigation.redirectIfNotAuthenticated();

    // Get DOM elements
    const statusFilter = document.getElementById('statusFilter');
    const sortBy = document.getElementById('sortBy');
    const searchQuery = document.getElementById('searchQuery');
    const clearFiltersBtn = document.getElementById('clearFiltersBtn');
    const refreshHistoryBtn = document.getElementById('refreshHistoryBtn');
    const translationHistoryList = document.getElementById('translationHistoryList');

    // Initialize page
    init();

    async function init() {
        await loadTranslationHistory();
        setupEventListeners();
    }

    // Setup event listeners
    function setupEventListeners() {
        statusFilter.addEventListener('change', applyFilters);
        sortBy.addEventListener('change', applyFilters);
        searchQuery.addEventListener('input', debounce(applyFilters, 300));
        clearFiltersBtn.addEventListener('click', clearFilters);
        refreshHistoryBtn.addEventListener('click', loadTranslationHistory);
    }

    // Load translation history
    async function loadTranslationHistory() {
        try {
            translationHistoryList.innerHTML = '<div class="loading"><div class="spinner"></div>Loading translation history...</div>';
            
            const response = await API.getTranslations();
            allTranslations = response.translations || [];

            if (allTranslations.length === 0) {
                translationHistoryList.innerHTML = `
                    <div class="empty-state">
                        <span class="icon">📋</span>
                        <h3>No translation history yet</h3>
                        <p>Your completed and ongoing translations will appear here</p>
                        <a href="translate.html" class="btn btn-primary" style="margin-top: 20px;">
                            🔤 Create Your First Translation
                        </a>
                    </div>
                `;
                return;
            }

            applyFilters();
            startStatusPolling();

        } catch (error) {
            translationHistoryList.innerHTML = `
                <div class="alert alert-error">
                    Failed to load translation history: ${error.message}
                </div>
            `;
        }
    }

    // Apply filters and sorting
    function applyFilters() {
        const statusValue = statusFilter.value;
        const sortValue = sortBy.value;
        const searchValue = searchQuery.value.toLowerCase().trim();

        // Filter translations
        filteredTranslations = allTranslations.filter(translation => {
            // Status filter
            if (statusValue && translation.status !== statusValue) {
                return false;
            }

            // Search filter
            if (searchValue) {
                const searchableText = [
                    translation.name || '',
                    translation.ai_model || '',
                    translation.status || ''
                ].join(' ').toLowerCase();
                
                if (!searchableText.includes(searchValue)) {
                    return false;
                }
            }

            return true;
        });

        // Sort translations
        filteredTranslations.sort((a, b) => {
            switch (sortValue) {
                case 'created_desc':
                    return new Date(b.created_at) - new Date(a.created_at);
                case 'created_asc':
                    return new Date(a.created_at) - new Date(b.created_at);
                case 'status':
                    return a.status.localeCompare(b.status);
                case 'progress':
                    const progressA = TranslationStatus.calculateProgress(a.completed_chunks, a.total_chunks);
                    const progressB = TranslationStatus.calculateProgress(b.completed_chunks, b.total_chunks);
                    return progressB - progressA;
                default:
                    return new Date(b.created_at) - new Date(a.created_at);
            }
        });

        renderTranslationHistory();
    }

    // Clear all filters
    function clearFilters() {
        statusFilter.value = '';
        sortBy.value = 'created_desc';
        searchQuery.value = '';
        applyFilters();
    }

    // Render translation history
    function renderTranslationHistory() {
        if (filteredTranslations.length === 0) {
            translationHistoryList.innerHTML = `
                <div class="empty-state">
                    <span class="icon">🔍</span>
                    <h3>No translations match your filters</h3>
                    <p>Try adjusting your search criteria or clearing filters</p>
                    <button class="btn btn-secondary" onclick="clearFilters()" style="margin-top: 15px;">
                        Clear Filters
                    </button>
                </div>
            `;
            return;
        }

        translationHistoryList.innerHTML = filteredTranslations.map(job => {
            const statusDisplay = TranslationStatus.getStatusDisplay(job.status);
            const progress = TranslationStatus.calculateProgress(job.completed_chunks, job.total_chunks);
            
            return `
                <div class="job-item" data-job-id="${job.id}">
                    <div class="job-header">
                        <div class="job-title">${job.name || 'Translation Job'}</div>
                        <div class="status-indicator ${statusDisplay.class}">
                            ${statusDisplay.text}
                        </div>
                    </div>
                    
                    <div class="job-details">
                        <p><strong>AI Model:</strong> ${job.ai_model}</p>
                        <p><strong>Created:</strong> ${UI.formatDate(job.created_at)}</p>
                        <p><strong>Progress:</strong> ${job.completed_chunks} / ${job.total_chunks} chunks (${progress}%)</p>
                        ${job.updated_at && job.updated_at !== job.created_at ? `
                            <p><strong>Last Updated:</strong> ${UI.formatDate(job.updated_at)}</p>
                        ` : ''}
                    </div>

                    <div class="job-progress">
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: ${progress}%"></div>
                        </div>
                    </div>

                    <div class="job-actions">
                        ${job.completed_chunks > 0 ? `
                            <button class="btn btn-small btn-success" onclick="downloadTranslation('${job.id}')">
                                💾 Download${job.status !== 'completed' ? ' (Partial)' : ''}
                            </button>
                            <button class="btn btn-small btn-secondary" onclick="previewTranslation('${job.id}')">
                                👁️ Preview
                            </button>
                        ` : ''}
                        
                        ${job.status === 'failed' ? `
                            <button class="btn btn-small btn-danger" onclick="retryTranslation('${job.id}')">
                                🔄 Retry
                            </button>
                        ` : ''}
                        
                        <button class="btn btn-small btn-secondary" onclick="refreshJobStatus('${job.id}')">
                            🔄 Refresh Status
                        </button>
                        
                        <button class="btn btn-small btn-danger" onclick="deleteTranslation('${job.id}')" 
                                title="Delete this translation job">
                            🗑️ Delete
                        </button>
                    </div>
                </div>
            `;
        }).join('');
    }

    // Start polling for active translations
    function startStatusPolling() {
        // Clear existing intervals
        Object.values(statusPollingIntervals).forEach(clearInterval);
        statusPollingIntervals = {};

        // Start polling for active translations
        allTranslations.forEach(job => {
            if (job.status === 'pending' || job.status === 'in_progress') {
                statusPollingIntervals[job.id] = setInterval(() => {
                    pollTranslationStatus(job.id);
                }, 5000); // Poll every 5 seconds (less frequent than current translation page)
            }
        });
    }

    // Poll individual translation status
    async function pollTranslationStatus(translationId) {
        try {
            const translation = await API.getTranslation(translationId);
            
            // Update the job in our local array
            const jobIndex = allTranslations.findIndex(job => job.id === translationId);
            if (jobIndex !== -1) {
                allTranslations[jobIndex] = translation;
                
                // If job is complete or failed, stop polling
                if (translation.status === 'completed' || translation.status === 'failed') {
                    if (statusPollingIntervals[translationId]) {
                        clearInterval(statusPollingIntervals[translationId]);
                        delete statusPollingIntervals[translationId];
                    }
                }
                
                applyFilters(); // Re-render with updated data
            }
        } catch (error) {
            console.error(`Failed to poll status for translation ${translationId}:`, error);
        }
    }

    // Global functions for job actions
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
            
            UI.showSuccess('New translation job created! Refreshing list...');
            await loadTranslationHistory();
        } catch (error) {
            UI.showError(`Failed to retry translation: ${error.message}`);
        }
    };

    window.refreshJobStatus = async function(translationId) {
        try {
            await pollTranslationStatus(translationId);
            UI.showAlert('Status refreshed!', 'info');
        } catch (error) {
            UI.showError(`Failed to refresh status: ${error.message}`);
        }
    };

    window.deleteTranslation = async function(translationId) {
        if (!confirm('Are you sure you want to delete this translation? This action cannot be undone.')) {
            return;
        }

        try {
            // Note: This assumes there's a delete API endpoint. 
            // If not available, you might want to hide this button or implement it differently
            await API.deleteTranslation(translationId);
            UI.showSuccess('Translation deleted successfully!');
            await loadTranslationHistory();
        } catch (error) {
            // If delete endpoint doesn't exist, show appropriate message
            if (error.message.includes('404') || error.message.includes('not found')) {
                UI.showError('Delete functionality not yet implemented in the backend');
            } else {
                UI.showError(`Failed to delete translation: ${error.message}`);
            }
        }
    };

    // Utility function for debouncing search input
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    // Make clearFilters available globally
    window.clearFilters = clearFilters;

    // Cleanup intervals when page unloads
    window.addEventListener('beforeunload', () => {
        Object.values(statusPollingIntervals).forEach(clearInterval);
    });
}); 