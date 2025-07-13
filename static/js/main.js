// Import Mermaid as ES6 module
import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';

// Initialize Mermaid with a dark theme consistent with the UI
mermaid.initialize({
    startOnLoad: true,
    theme: 'base',
    flowchart: {
        useMaxWidth: true,
        htmlLabels: true,
        curve: 'basis'
    },
    themeVariables: {
        background: '#0a192f',
        primaryColor: '#1a2a47',
        primaryTextColor: '#ffffff',
        primaryBorderColor: '#2c3e50',
        lineColor: '#667eea',
        secondaryColor: '#2c3e50',
        tertiaryColor: '#1a2a47',
        fontSize: '16px',
        fontFamily: '"Roboto Mono", monospace',
        nodeBkg: '#1a2a47',
        nodeBorder: '#667eea',
        clusterBkg: '#0d253f',
        clusterBorder: '#8e9eab',
        edgeLabelBackground: '#1a2a47',
        textColor: '#ffffff',
        titleColor: '#667eea',
        classText: '#ffffff'
    }
});

// Global variables
let currentResults = null;
let currentStep = 0;
let stepInterval = null;

// DOM Content Loaded Event
document.addEventListener('DOMContentLoaded', function() {
    console.log('Network Topology Analyzer initialized - Module Mode');
    
    // Get DOM elements
    const form = document.getElementById('topology-form');
    const fileInput = document.getElementById('topology-image');
    
    // Add event listeners
    if (form) form.addEventListener('submit', handleFormSubmit);
    if (fileInput) fileInput.addEventListener('change', handleFileSelect);
});

// Handle file selection and preview - FIXED
function handleFileSelect(event) {
    const files = event.target.files; // Get FileList object
    const file = files[0]; // Get the first file
    const filePreview = document.getElementById('file-preview');
    
    if (file) {
        // Validate file size
        const maxSize = parseInt(event.target.dataset.maxSize) || (10 * 1024 * 1024);
        if (file.size > maxSize) {
            showError(`File size too large. Please select an image smaller than ${formatFileSize(maxSize)}.`);
            event.target.value = '';
            return;
        }

        // Validate file type - FIXED: Check if file.type exists before calling startsWith
        if (!file.type || !file.type.startsWith('image/')) {
            showError('Please select a valid image file.');
            event.target.value = '';
            return;
        }

        const reader = new FileReader();
        reader.onload = function(e) {
            filePreview.innerHTML = `
                <img src="${e.target.result}" alt="Topology Preview">
                <p><strong>File:</strong> ${file.name} (${formatFileSize(file.size)})</p>
                <p><strong>Type:</strong> ${file.type}</p>
            `;
        };
        reader.readAsDataURL(file);
    } else {
        filePreview.innerHTML = '';
    }
}

// Handle form submission - FIXED
async function handleFormSubmit(event) {
    event.preventDefault();
    
    const fileInput = document.getElementById('topology-image');
    const replacementQuery = document.getElementById('replacement-query');
    
    // FIXED: Properly access file from FileList
    const files = fileInput.files;
    const imageFile = files[0]; // Get the first file from FileList
    const queryText = replacementQuery.value;
    
    // Validation
    if (!imageFile) {
        showError('Please select a network topology image');
        return;
    }
    
    if (!queryText.trim()) {
        showError('Please enter replacement requirements');
        return;
    }

    if (queryText.trim().length < 20) {
        showError('Please provide more detailed replacement requirements (at least 20 characters)');
        return;
    }
    
    // Show loading state
    showLoadingOverlay();
    hideError();
    hideResults();
    
    // Prepare form data - FIXED: Properly append file and query
    const formData = new FormData();
    formData.append('image', imageFile); // Append the actual file object
    formData.append('replacement_query', queryText);
    
    try {
        startProgressAnimation();
        
        console.log('Sending request to /analyze-topology...');
        console.log('File:', imageFile.name, 'Size:', imageFile.size, 'Type:', imageFile.type);
        console.log('Query length:', queryText.length);
        
        const response = await fetch('/analyze-topology', {
            method: 'POST',
            body: formData // Send FormData directly, don't set Content-Type header
        });
        
        console.log('Response status:', response.status);
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            console.error('Server error response:', errorData);
            throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        console.log('Analysis result:', result);
        
        if (result.success) {
            currentResults = result;
            await displayResults(result);
        } else {
            showError(result.error || 'Analysis failed');
        }
        
    } catch (error) {
        console.error('Error:', error);
        showError(`Failed to analyze topology: ${error.message}`);
    } finally {
        hideLoadingOverlay();
        stopProgressAnimation();
    }
}

// Display analysis results
async function displayResults(results) {
    try {
        console.log('Displaying results:', results);
        
        // Update analysis summary
        const summaryElement = document.getElementById('analysis-summary');
        if (summaryElement) {
            summaryElement.textContent = results.analysis_summary || 'No analysis summary available';
        }
        
        // Display context sources
        const contextSourcesContainer = document.getElementById('context-sources');
        if (contextSourcesContainer && results.context_sources) {
            // The backend now sends pre-formatted HTML
            contextSourcesContainer.innerHTML = results.context_sources;
        }
        
        // Update topology explanation
        const explanationElement = document.getElementById('topology-explanation');
        if (explanationElement) {
            explanationElement.textContent = results.topology_explanation || 'No topology explanation available';
        }
        
        // Update modification overview
        const overviewElement = document.getElementById('modification-overview');
        if (overviewElement && results.modification_details) {
            displayModificationOverview(results.modification_details);
        }
        
        // Update recommendations
        displayRecommendations(results.recommendations);
        
        // Update topology details
        displayTopologyDetails(results.original_topology, results.modified_topology);
        
        // Update diagrams
        await updateDiagram('original-diagram', results.diagrams?.original);
        await updateDiagram('modified-diagram', results.diagrams?.modified);
        await updateDiagram('comparison-diagram', results.diagrams?.comparison);

        // Handle download links for proposed topology
        const proposedPngUrl = results.diagrams?.proposed_png_url;
        const proposedSvgUrl = results.diagrams?.proposed_svg_url;
        const downloadPngLink = document.getElementById('download-png-link');
        const downloadSvgLink = document.getElementById('download-svg-link');

        if (proposedPngUrl && proposedSvgUrl) {
            downloadPngLink.href = proposedPngUrl;
            downloadSvgLink.href = proposedSvgUrl;
            downloadPngLink.style.display = 'inline-block';
            downloadSvgLink.style.display = 'inline-block';
        } else {
            downloadPngLink.style.display = 'none';
            downloadSvgLink.style.display = 'none';
        }
        
        // Show results section
        const resultsSection = document.getElementById('results-section');
        if (resultsSection) {
            resultsSection.style.display = 'block';
            resultsSection.scrollIntoView({ behavior: 'smooth' });
        }
        
    } catch (error) {
        console.error('Error displaying results:', error);
        showError('Error displaying analysis results');
    }
}

// Display modification overview
function displayModificationOverview(modificationDetails) {
    const container = document.getElementById('modification-overview');
    if (!container || !modificationDetails) return;
    
    let html = '<div class="overview-grid">';
    html += `<div class="overview-item">
        <h4>🔄 Total Replacements</h4>
        <p class="overview-value">${modificationDetails.total_replacements || 0}</p>
    </div>`;
    html += `<div class="overview-item">
        <h4>📋 Implementation Phases</h4>
        <p class="overview-value">${modificationDetails.implementation_phases || 'TBD'}</p>
    </div>`;
    html += `<div class="overview-item">
        <h4>⚠️ Risk Level</h4>
        <p class="overview-value">${modificationDetails.risk_level || 'Medium'}</p>
    </div>`;
    html += `<div class="overview-item">
        <h4>💰 Cost Category</h4>
        <p class="overview-value">${modificationDetails.cost_category || 'Not specified'}</p>
    </div>`;
    html += '</div>';
    
    container.innerHTML = html;
}

// Display recommendations
function displayRecommendations(recommendations) {
    const container = document.getElementById('recommendations-list');
    if (!container) return;
    
    if (!recommendations || !recommendations.replacements) {
        container.innerHTML = '<p>No recommendations data received.</p>';
        return;
    }
    
    const replacements = recommendations.replacements || [];
    if (replacements.length === 0) {
        container.innerHTML = '<p>No specific replacement recommendations generated.</p>';
        return;
    }
    
    let html = `<h4>🔄 Device Replacement Recommendations (${replacements.length} items)</h4>`;
    replacements.forEach((replacement, index) => {
        const original = replacement.original_device || {};
        const recommended = replacement.recommended_device || {};
        
        html += `<div class="recommendation-item">`;
        html += `<h4>Replacement ${index + 1}</h4>`;
        
        if (Object.keys(original).length > 0) {
            html += `<p><strong>Original Device:</strong> ${original.vendor || 'Unknown'} ${original.model || 'Unknown'}</p>`;
        }
        
        if (Object.keys(recommended).length > 0) {
            html += `<p><strong>Recommended Device:</strong> ${recommended.vendor || 'Unknown'} ${recommended.model || 'Unknown'}</p>`;
            
            if (recommended.features && recommended.features.length > 0) {
                html += `<p><strong>Features:</strong> ${recommended.features.join(', ')}</p>`;
            }
            
            if (recommended.justification) {
                html += `<p><strong>Justification:</strong> ${recommended.justification}</p>`;
            }
            
            if (recommended.cost_benefit) {
                html += `<div class="cost-benefit"><strong>Cost/Benefit:</strong> ${recommended.cost_benefit}</div>`;
            }
        }
        
        html += `</div>`;
    });
    
    container.innerHTML = html;
}

// Display topology details
function displayTopologyDetails(originalTopology, modifiedTopology) {
    const originalDetails = document.getElementById('original-details');
    const modifiedDetails = document.getElementById('modified-details');
    
    // Original topology
    if (originalDetails && originalTopology) {
        const devices = originalTopology.devices || [];
        let html = `<h4>📊 Current Infrastructure Analysis</h4>`;
        html += `<p><strong>Total Devices:</strong> ${devices.length}</p>`;
        
        if (originalTopology.topology_structure) {
            html += `<p><strong>Architecture:</strong> ${originalTopology.topology_structure}</p>`;
        }
        
        if (devices.length > 0) {
            html += '<h5>Device Inventory:</h5><ul>';
            devices.forEach(device => {
                html += `<li>${device.id || 'Unknown'}: ${device.vendor || 'Unknown'} ${device.model || 'Unknown'} (${device.type || 'Unknown'})</li>`;
            });
            html += '</ul>';
        }
        
        originalDetails.innerHTML = html;
    }
    
    // Modified topology
    if (modifiedDetails && modifiedTopology) {
        const devices = modifiedTopology.devices || [];
        let html = `<h4>✨ Proposed Infrastructure Changes</h4>`;
        html += `<p><strong>Total Devices:</strong> ${devices.length}</p>`;
        
        if (devices.length > 0) {
            html += '<h5>Updated Device List:</h5><ul>';
            devices.forEach(device => {
                const isReplaced = device.replacement_reason ? '🔄 ' : '';
                html += `<li>${isReplaced}${device.id || 'Unknown'}: ${device.vendor || 'Unknown'} ${device.model || 'Unknown'}`;
                if (device.replacement_reason) {
                    html += ` - <em>${device.replacement_reason}</em>`;
                }
                html += '</li>';
            });
            html += '</ul>';
        }
        
        modifiedDetails.innerHTML = html;
    }
}

// Update Mermaid diagram
async function updateDiagram(elementId, diagramCode) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    if (!diagramCode || diagramCode.trim() === '') {
        element.innerHTML = '<div class="no-diagram">No diagram data available</div>';
        return;
    }
    
    try {
        element.innerHTML = '';
        element.textContent = diagramCode;
        await mermaid.run();
    } catch (error) {
        console.error('Mermaid rendering error:', error);
        element.innerHTML = `<div class="diagram-error">Error rendering diagram: ${error.message}</div>`;
    }
}

// Tab functionality
function showTab(tabName) {
    document.querySelectorAll('.tab-pane').forEach(pane => {
        pane.classList.remove('active');
    });
    
    document.querySelectorAll('.tab-button').forEach(button => {
        button.classList.remove('active');
    });
    
    const targetTab = document.getElementById(`${tabName}-tab`);
    if (targetTab) {
        targetTab.classList.add('active');
    }
    
    // Add active class to clicked button
    if (event && event.target) {
        event.target.classList.add('active');
    }
    
    setTimeout(async () => {
        try {
            await mermaid.run();
        } catch (error) {
            console.error('Error re-rendering mermaid:', error);
        }
    }, 100);
}

// Loading overlay functions
function showLoadingOverlay() {
    const loadingOverlay = document.getElementById('loading-overlay');
    if (loadingOverlay) {
        loadingOverlay.style.display = 'flex';
    }
}

function hideLoadingOverlay() {
    const loadingOverlay = document.getElementById('loading-overlay');
    if (loadingOverlay) {
        loadingOverlay.style.display = 'none';
    }
}

function startProgressAnimation() {
    currentStep = 0;
    updateProgressStep();
    
    const steps = document.querySelectorAll('.step');
    stepInterval = setInterval(() => {
        if (currentStep < steps.length - 1) {
            currentStep++;
            updateProgressStep();
        }
    }, 3000);
}

function stopProgressAnimation() {
    if (stepInterval) {
        clearInterval(stepInterval);
        stepInterval = null;
    }
    
    document.querySelectorAll('.step').forEach(step => {
        step.classList.remove('active');
        step.classList.add('completed');
    });
}

function updateProgressStep() {
    document.querySelectorAll('.step').forEach((step, index) => {
        step.classList.remove('active', 'completed');
        if (index === currentStep) {
            step.classList.add('active');
        } else if (index < currentStep) {
            step.classList.add('completed');
        }
    });
}

// Error handling
function showError(message) {
    const errorSection = document.getElementById('error-section');
    const errorText = document.getElementById('error-text');
    
    if (errorText) errorText.textContent = message;
    if (errorSection) {
        errorSection.style.display = 'block';
        errorSection.scrollIntoView({ behavior: 'smooth' });
    }
}

function hideError() {
    const errorSection = document.getElementById('error-section');
    if (errorSection) {
        errorSection.style.display = 'none';
    }
}

function hideResults() {
    const resultsSection = document.getElementById('results-section');
    if (resultsSection) {
        resultsSection.style.display = 'none';
    }
}

// Utility functions
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Export functions for global access
window.showTab = showTab;
window.hideError = hideError;
window.exportResults = function() {
    if (currentResults) {
        const dataStr = JSON.stringify(currentResults, null, 2);
        const dataBlob = new Blob([dataStr], {type: 'application/json'});
        const url = URL.createObjectURL(dataBlob);
        const link = document.createElement('a');
        link.href = url;
        link.download = 'topology-analysis-results.json';
        link.click();
        URL.revokeObjectURL(url);
    }
};

window.shareResults = function() {
    if (navigator.share && currentResults) {
        navigator.share({
            title: 'Network Topology Analysis Results',
            text: 'Check out this AI-powered network topology analysis',
            url: window.location.href
        });
    } else {
        navigator.clipboard.writeText(window.location.href).then(() => {
            alert('URL copied to clipboard!');
        });
    }
};

window.startNewAnalysis = function() {
    const form = document.getElementById('topology-form');
    if (form) form.reset();
    
    const filePreview = document.getElementById('file-preview');
    if (filePreview) filePreview.innerHTML = '';
    
    hideResults();
    hideError();
    
    window.scrollTo({ top: 0, behavior: 'smooth' });
};

window.closeModal = function() {
    const modal = document.getElementById('device-modal');
    if (modal) modal.style.display = 'none';
};

window.reportIssue = function() {
    alert('Please contact support with details about the issue you encountered.');
};

window.showAbout = function() {
    alert('AI Network Topology Analyzer - Powered by Gemini AI and Groq for intelligent network infrastructure analysis.');
};

window.showHelp = function() {
    alert('Upload a network topology image and describe your requirements. The AI will analyze your network and provide comprehensive replacement recommendations.');
};

window.showPrivacy = function() {
    alert('Your uploaded images and queries are processed securely and are not stored permanently on our servers.');
};
