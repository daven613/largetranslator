// Large Translator Frontend - Translation Details Logic

let translationId = null;
let translationDetails = null;

document.addEventListener('DOMContentLoaded', () => {
    // Redirect if not authenticated
    Navigation.redirectIfNotAuthenticated();

    // Get translation ID from URL parameters
    const urlParams = new URLSearchParams(window.location.search);
    translationId = urlParams.get('id');

    if (!translationId) {
        showError('No translation ID provided in URL');
        return;
    }

    // Load translation details
    loadTranslationDetails();
});

// Load translation details and chunks
async function loadTranslationDetails() {
    try {
        showLoading('Loading translation details...');
        
        // Try the new unified API first, fall back to old approach if it fails
        try {
            translationDetails = await API.getTranslationDetails(translationId);
            console.log('Translation details debug (unified API):', translationDetails);
        } catch (error) {
            console.warn('Unified API not available, falling back to legacy approach:', error);
            
            // Fallback to old approach
            const translation = await API.getTranslation(translationId);
            const translatedChunksResponse = await API.getTranslatedChunks(translationId);
            const translatedChunks = translatedChunksResponse.translated_chunks || [];
            const originalChunksResponse = await API.getOriginalChunks(translation.chunk_set_id);
            const originalChunks = originalChunksResponse.chunks || [];
            
            // Create chunk pairs manually
            const translatedChunkMap = new Map();
            translatedChunks.forEach(chunk => {
                // Handle both old format (chunk_id) and new format (parent_chunk_id)
                const parentId = chunk.parent_chunk_id || chunk.chunk_id;
                if (parentId) {
                    translatedChunkMap.set(parentId, {
                        ...chunk,
                        content: chunk.content || chunk.translated_content // Handle both field names
                    });
                }
            });
            
            const chunkPairs = originalChunks.sort((a, b) => a.sequence_number - b.sequence_number).map(originalChunk => ({
                original_chunk: originalChunk,
                translated_chunk: translatedChunkMap.get(originalChunk.id) || null,
                sequence_number: originalChunk.sequence_number
            }));
            
            // Calculate statistics
            let errorCount = 0;
            chunkPairs.forEach(pair => {
                if (pair.translated_chunk?.metadata?.status === 'failed') {
                    errorCount++;
                }
            });
            
            const totalChunks = chunkPairs.length;
            const successRate = totalChunks > 0 ? ((totalChunks - errorCount) / totalChunks) * 100 : 0;
            
            // Create unified response format
            translationDetails = {
                translation: translation,
                chunk_pairs: chunkPairs,
                success_rate: successRate,
                error_count: errorCount,
                total_chunks: totalChunks
            };
            
            console.log('Translation details debug (legacy fallback):', translationDetails);
        }
        
        // Display the translation details
        displayTranslationDetails();
        
        hideLoading();
        
    } catch (error) {
        console.error('Error loading translation details:', error);
        showError(`Failed to load translation details: ${error.message}`);
        hideLoading();
    }
}

// Display translation details and chunks
function displayTranslationDetails() {
    // Update page title
    document.title = `Translation Details - ${translationDetails.translation.name || translationDetails.translation.id}`;
    
    // Display translation header information
    displayTranslationHeader();
    
    // Display chunks comparison
    displayChunksComparison();
}

// Display translation header with metadata
function displayTranslationHeader() {
    const headerContainer = document.getElementById('translation-header');
    if (!headerContainer) return;
    
    const translation = translationDetails.translation;
    
    headerContainer.innerHTML = `
        <h1>Translation Details</h1>
        <div class="translation-meta">
            <div class="meta-item">
                <strong>Translation ID:</strong>
                <span>${translation.id}</span>
            </div>
            <div class="meta-item">
                <strong>Status:</strong>
                <span class="status-badge status-${translation.status.replace('_', '-')}">${getStatusDisplay(translation.status)}</span>
            </div>
            <div class="meta-item">
                <strong>Progress:</strong>
                <span>${translation.completed_chunks}/${translation.total_chunks} chunks (${Math.round(translation.completed_chunks / translation.total_chunks * 100)}%)</span>
            </div>
            <div class="meta-item">
                <strong>Success Rate:</strong>
                <span class="${translationDetails.success_rate < 100 ? 'text-warning' : 'text-success'}">${translationDetails.success_rate.toFixed(1)}% (${translationDetails.total_chunks - translationDetails.error_count}/${translationDetails.total_chunks})</span>
            </div>
            <div class="meta-item">
                <strong>AI Model:</strong>
                <span>${translation.ai_model}</span>
            </div>
            <div class="meta-item">
                <strong>Created:</strong>
                <span>${formatDate(translation.created_at)}</span>
            </div>
        </div>
        
        ${translationDetails.error_count > 0 ? `
        <div class="error-summary">
            <h3>⚠️ Translation Issues</h3>
            <p>${translationDetails.error_count} chunk(s) failed to translate. See details below for specific error information.</p>
        </div>
        ` : ''}
    `;
}

// Display chunks side by side
function displayChunksComparison() {
    const chunksContainer = document.getElementById('chunks-container');
    if (!chunksContainer) return;
    
    let chunksHtml = '';
    
    translationDetails.chunk_pairs.forEach((chunkPair, index) => {
        const originalChunk = chunkPair.original_chunk;
        const translatedChunk = chunkPair.translated_chunk;
        
        // Determine if chunk has an actual error
        const isChunkFailed = translatedChunk?.metadata?.status === 'failed';
        const hasTranslatedContent = translatedChunk?.content?.trim();
        const hasError = isChunkFailed || (!hasTranslatedContent && translatedChunk); // Only error if chunk exists but has no content
        
        chunksHtml += `
            <div class="chunk-pair ${hasError ? 'chunk-error' : ''}">
                <div class="chunk-header">
                    <span class="chunk-number">Chunk ${index + 1}</span>
                    <span class="chunk-sequence">Sequence: ${originalChunk.sequence_number}</span>
                    ${hasError ? `<span class="error-indicator">⚠️ ${isChunkFailed ? 'Translation Failed' : 'No Translation'}</span>` : ''}
                </div>
                
                <div class="chunks-row">
                    <div class="chunk-column original-chunk">
                        <div class="chunk-label">Original Text</div>
                        <div class="chunk-content">
                            ${escapeHtml(originalChunk.content)}
                        </div>
                        <div class="chunk-info">
                            Length: ${originalChunk.content.length} characters
                        </div>
                    </div>
                    
                    <div class="chunk-column translated-chunk">
                        <div class="chunk-label">Translated Text</div>
                        <div class="chunk-content ${hasError ? 'error-content' : ''}">
                            ${hasError ? getErrorDisplay(translatedChunk) : (hasTranslatedContent ? escapeHtml(translatedChunk.content) : '<em class="placeholder-text">Translation not yet available</em>')}
                        </div>
                        <div class="chunk-info">
                            ${translatedChunk ? `
                                Length: ${translatedChunk.content ? translatedChunk.content.length : 0} characters
                                ${translatedChunk.metadata?.attempts ? `| Attempts: ${translatedChunk.metadata.attempts}` : ''}
                                ${translatedChunk.target_language ? `| Language: ${translatedChunk.target_language}` : ''}
                            ` : 'Not translated yet'}
                        </div>
                    </div>
                </div>
                
                ${hasError && translatedChunk?.metadata ? `
                <div class="error-details">
                    <strong>Error Details:</strong>
                    <div class="error-info">
                        <span class="error-type">Type: ${translatedChunk.metadata.error_type || 'Unknown'}</span>
                        <span class="error-message">Message: ${translatedChunk.metadata.error_message || 'No details available'}</span>
                        ${translatedChunk.metadata.attempts ? `<span class="error-attempts">Attempts: ${translatedChunk.metadata.attempts}</span>` : ''}
                        ${translatedChunk.metadata.is_transient !== undefined ? `<span class="error-transient">Transient: ${translatedChunk.metadata.is_transient ? 'Yes' : 'No'}</span>` : ''}
                    </div>
                </div>
                ` : ''}
            </div>
        `;
    });
    
    chunksContainer.innerHTML = chunksHtml;
}

// Get error display for failed chunks
function getErrorDisplay(translatedChunk) {
    if (!translatedChunk) {
        return '<em class="error-text">No translation record found</em>';
    }
    
    if (translatedChunk.metadata?.status === 'failed') {
        const errorType = translatedChunk.metadata.error_type || 'Unknown Error';
        const isTransient = translatedChunk.metadata.is_transient;
        
        return `
            <div class="error-display">
                <div class="error-icon">❌</div>
                <div class="error-summary">
                    <strong>${errorType}</strong>
                    <br>
                    <small>${isTransient ? 'Transient error - could be retried' : 'Permanent error - needs manual review'}</small>
                </div>
            </div>
        `;
    }
    
    return '<em class="error-text">Empty translation - processing may have failed</em>';
}

// Get status display with proper formatting
function getStatusDisplay(status) {
    const statusMap = {
        'pending': 'Pending',
        'in_progress': 'In Progress',
        'completed': 'Completed',
        'completed_with_errors': 'Completed with Errors',
        'failed': 'Failed'
    };
    
    return statusMap[status] || status;
}

// Utility functions
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatDate(dateString) {
    try {
        return new Date(dateString).toLocaleString();
    } catch (error) {
        return dateString;
    }
}

function showLoading(message) {
    const loadingDiv = document.getElementById('loading');
    if (loadingDiv) {
        loadingDiv.textContent = message;
        loadingDiv.style.display = 'block';
    }
}

function hideLoading() {
    const loadingDiv = document.getElementById('loading');
    if (loadingDiv) {
        loadingDiv.style.display = 'none';
    }
}

function showError(message) {
    const errorDiv = document.getElementById('error-message');
    if (errorDiv) {
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
    }
    
    // Also log to console
    console.error('Translation Details Error:', message);
} 