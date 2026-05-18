/**
 * Red Marker Pro - Main Frontend Application Logic
 * Handles image upload, annotation, and tab navigation
 */

// Global state
const appState = {
    sessionId: null,
    imageWidth: 0,
    imageHeight: 0,
    markers: [],
    originalFilename: '',
    currentTab: 'upload'
};

// ============================================
// Tab Navigation
// ============================================

document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', function() {
        const tabName = this.getAttribute('data-tab');
        switchTab(tabName);
    });
});

function switchTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });

    // Remove active class from all buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });

    // Show selected tab
    const selectedTab = document.getElementById(`${tabName}-tab`);
    if (selectedTab) {
        selectedTab.classList.add('active');
    }

    // Set active button
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
    appState.currentTab = tabName;
}

// ============================================
// DOM Elements - Upload
// ============================================

const uploadArea = document.getElementById('upload-area');
const fileInput = document.getElementById('file-input');
const uploadError = document.getElementById('upload-error');
const displayImage = document.getElementById('display-image');
const canvasOverlay = document.getElementById('canvas-overlay');
const markerCount = document.getElementById('marker-count');
const markerList = document.getElementById('marker-list');
const loadingIndicator = document.getElementById('loading');
const loadingText = document.getElementById('loading-text');

// Buttons
const undoBtn = document.getElementById('undo-btn');
const clearBtn = document.getElementById('clear-btn');
const downloadBtn = document.getElementById('download-btn');
const newUploadBtn = document.getElementById('new-upload-btn');
const resetBtn = document.getElementById('reset-btn');
const markerDetailSelect = document.getElementById('marker-detail-select');
const generateMarkerDetailBtn = document.getElementById('generate-marker-detail-btn');
const markerDetailResult = document.getElementById('marker-detail-result');

// Toasts
const errorToast = document.getElementById('error-toast');
const successToast = document.getElementById('success-toast');
const errorMessage = document.getElementById('error-message');
const successMessage = document.getElementById('success-message');

// ============================================
// Upload Event Listeners
// ============================================

uploadArea.addEventListener('click', () => fileInput.click());

uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadArea.classList.add('dragover');
});

uploadArea.addEventListener('dragleave', () => {
    uploadArea.classList.remove('dragover');
});

uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadArea.classList.remove('dragover');

    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFileSelect(files[0]);
    }
});

fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleFileSelect(e.target.files[0]);
    }
});

// ============================================
// Annotation Event Listeners
// ============================================

canvasOverlay.addEventListener('click', handleCanvasClick);
undoBtn.addEventListener('click', handleUndo);
clearBtn.addEventListener('click', handleClear);
downloadBtn.addEventListener('click', handleDownload);
newUploadBtn.addEventListener('click', handleNewUpload);
resetBtn.addEventListener('click', handleReset);
generateMarkerDetailBtn.addEventListener('click', handleGenerateMarkerDetail);
window.addEventListener('resize', () => {
    if (appState.sessionId && displayImage.complete) {
        setupCanvasOverlay();
        redrawMarkers();
    }
});

// Toast close buttons
document.querySelectorAll('.toast-close').forEach(btn => {
    btn.addEventListener('click', function() {
        this.parentElement.classList.add('hidden');
    });
});

// ============================================
// Upload Handler
// ============================================

async function handleFileSelect(file) {
    // Validate file type
    const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
    if (!allowedTypes.includes(file.type)) {
        showError('Invalid file type. Please upload JPG, PNG, GIF, or WebP.');
        return;
    }

    // Validate file size (50MB)
    if (file.size > 50 * 1024 * 1024) {
        showError('File size exceeds 50MB limit.');
        return;
    }

    showLoading(true, 'Uploading image...');

    try {
        // Create FormData for file upload
        const formData = new FormData();
        formData.append('file', file);

        // Upload file to backend
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Upload failed');
        }

        const data = await response.json();

        // Store session data
        appState.sessionId = data.session_id;
        appState.imageWidth = data.width;
        appState.imageHeight = data.height;
        appState.originalFilename = data.filename;
        appState.markers = [];

        // Show image
        await displayUploadedImage();

        // Show annotation section
        document.getElementById('upload-section').classList.add('hidden');
        document.getElementById('annotation-section').classList.remove('hidden');

        showSuccess('Image uploaded successfully!');
        clearUploadError();

    } catch (error) {
        console.error('Upload error:', error);
        showError('Error: ' + error.message);
    } finally {
        showLoading(false);
    }
}

// ============================================
// Image Display
// ============================================

async function displayUploadedImage() {
    if (!appState.sessionId) return;

    try {
        const response = await fetch(`/api/image/${appState.sessionId}`);
        if (!response.ok) throw new Error('Failed to load image');

        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        displayImage.src = url;

        // Setup canvas overlay
        displayImage.onload = () => {
            setupCanvasOverlay();
            redrawMarkers();
        };

    } catch (error) {
        console.error('Error displaying image:', error);
        showError('Error displaying image');
    }
}

function setupCanvasOverlay() {
    const wrapperRect = displayImage.parentElement.getBoundingClientRect();
    const imageRect = displayImage.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;

    canvasOverlay.width = Math.round(imageRect.width * dpr);
    canvasOverlay.height = Math.round(imageRect.height * dpr);
    canvasOverlay.style.width = `${imageRect.width}px`;
    canvasOverlay.style.height = `${imageRect.height}px`;
    canvasOverlay.style.left = `${imageRect.left - wrapperRect.left}px`;
    canvasOverlay.style.top = `${imageRect.top - wrapperRect.top}px`;
    canvasOverlay.style.position = 'absolute';
    canvasOverlay.style.cursor = 'crosshair';

    const ctx = canvasOverlay.getContext('2d');
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
}

// ============================================
// Canvas Click Handler
// ============================================

async function handleCanvasClick(event) {
    if (!appState.sessionId) return;

    const canvasRect = canvasOverlay.getBoundingClientRect();
    const offsetX = event.clientX - canvasRect.left;
    const offsetY = event.clientY - canvasRect.top;

    if (offsetX < 0 || offsetY < 0 || offsetX > canvasRect.width || offsetY > canvasRect.height) {
        return;
    }

    const x = Math.max(0, Math.min(appState.imageWidth - 1, Math.round(offsetX * appState.imageWidth / canvasRect.width)));
    const y = Math.max(0, Math.min(appState.imageHeight - 1, Math.round(offsetY * appState.imageHeight / canvasRect.height)));

    try {
        const response = await fetch(`/api/markers/${appState.sessionId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ x, y })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail);
        }

        const data = await response.json();
        appState.markers = data.markers;
        updateMarkerDisplay();
        redrawMarkers();
        showSuccess(`Marker added at (${x}, ${y})`);

    } catch (error) {
        console.error('Error adding marker:', error);
        showError('Error: ' + error.message);
    }
}

// ============================================
// Marker Management
// ============================================

function updateMarkerDisplay() {
    markerCount.textContent = `Count: ${appState.markers.length}`;

    markerList.innerHTML = '';
    markerDetailSelect.innerHTML = '';

    appState.markers.forEach((marker, index) => {
        const item = document.createElement('div');
        item.className = 'marker-item';
        item.innerHTML = `
            <span>Marker ${index + 1}: (${marker[0]}, ${marker[1]})</span>
            <button onclick="removeMarker(${index})">Remove</button>
        `;
        markerList.appendChild(item);

        const option = document.createElement('option');
        option.value = index;
        option.textContent = `Marker ${index + 1}: (${marker[0]}, ${marker[1]})`;
        markerDetailSelect.appendChild(option);
    });

    generateMarkerDetailBtn.disabled = appState.markers.length === 0;
    if (appState.markers.length === 0) {
        const option = document.createElement('option');
        option.value = '';
        option.textContent = 'No markers yet';
        markerDetailSelect.appendChild(option);
    }
}

function redrawMarkers() {
    const ctx = canvasOverlay.getContext('2d');
    const canvasRect = canvasOverlay.getBoundingClientRect();
    ctx.clearRect(0, 0, canvasRect.width, canvasRect.height);

    const scaleX = canvasRect.width / appState.imageWidth;
    const scaleY = canvasRect.height / appState.imageHeight;

    appState.markers.forEach(marker => {
        const x = marker[0] * scaleX;
        const y = marker[1] * scaleY;

        // Draw circle
        ctx.strokeStyle = 'red';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(x, y, 15, 0, 2 * Math.PI);
        ctx.stroke();

        // Draw center dot
        ctx.fillStyle = 'red';
        ctx.beginPath();
        ctx.arc(x, y, 3, 0, 2 * Math.PI);
        ctx.fill();
    });
}

async function removeMarker(index) {
    try {
        const response = await fetch(`/api/markers/${appState.sessionId}/${index}`, {
            method: 'DELETE'
        });

        if (!response.ok) throw new Error('Failed to remove marker');

        const data = await response.json();
        appState.markers = data.markers;
        updateMarkerDisplay();
        redrawMarkers();
        showSuccess('Marker removed');

    } catch (error) {
        console.error('Error removing marker:', error);
        showError('Error removing marker');
    }
}

async function handleUndo() {
    if (appState.markers.length === 0) {
        showError('No markers to undo');
        return;
    }

    try {
        const response = await fetch(`/api/markers/${appState.sessionId}/last`, {
            method: 'DELETE'
        });

        if (!response.ok) throw new Error('Failed to undo');

        const data = await response.json();
        appState.markers = data.markers;
        updateMarkerDisplay();
        redrawMarkers();
        showSuccess('Last marker removed');

    } catch (error) {
        console.error('Error:', error);
        showError('Error removing marker');
    }
}

async function handleClear() {
    if (appState.markers.length === 0) return;

    try {
        const response = await fetch(`/api/markers/${appState.sessionId}`, {
            method: 'DELETE'
        });

        if (!response.ok) throw new Error('Failed to clear markers');

        appState.markers = [];
        updateMarkerDisplay();
        redrawMarkers();
        showSuccess('All markers cleared');

    } catch (error) {
        console.error('Error:', error);
        showError('Error clearing markers');
    }
}

async function handleGenerateMarkerDetail() {
    if (!appState.sessionId) {
        showError('Please upload an image first');
        return;
    }

    if (appState.markers.length === 0) {
        showError('Place a marker before generating a detail image');
        return;
    }

    const markerIndex = parseInt(markerDetailSelect.value, 10);

    if (Number.isNaN(markerIndex)) {
        showError('Please select a marker');
        return;
    }

    const marker = appState.markers[markerIndex];
    if (!marker) {
        showError('Selected marker is missing. Place the marker again.');
        return;
    }

    showLoading(true, 'Generating marker detail from vision context...');

    try {
        const response = await fetch(`/api/generate/from-marker?session_id=${encodeURIComponent(appState.sessionId)}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                marker_index: markerIndex,
                x: marker[0],
                y: marker[1]
            })
        });

        if (!response.ok) {
            let detail = 'Generation failed';
            try {
                const error = await response.json();
                detail = error.detail || detail;
            } catch (_error) {
                detail = await response.text() || detail;
            }
            throw new Error(detail);
        }

        const data = await response.json();
        markerDetailResult.innerHTML = `
            <div class="marker-detail-preview">
                <img src="/api/generated-image/${data.image_id}/data" alt="Generated marker detail">
                <p>Generated from marker ${data.marker_index + 1} at (${data.marker.x}, ${data.marker.y}) using ${data.vision_context?.model || 'vision'} context.</p>
            </div>
        `;

        if (typeof loadGeneratedImages === 'function') {
            loadGeneratedImages(0);
        }

        showSuccess('Marker detail image generated');
    } catch (error) {
        console.error('Error generating marker detail:', error);
        markerDetailResult.innerHTML = `<p class="placeholder">Generation failed: ${error.message}</p>`;
        showError('Generation failed: ' + error.message);
    } finally {
        showLoading(false);
    }
}

async function handleDownload() {
    try {
        const response = await fetch(`/api/download/${appState.sessionId}`);
        if (!response.ok) throw new Error('Download failed');

        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${appState.originalFilename.split('.')[0]}_marked.png`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        showSuccess('Image downloaded successfully!');

    } catch (error) {
        console.error('Error:', error);
        showError('Error downloading image');
    }
}

function handleNewUpload() {
    // Reset state
    appState.sessionId = null;
    appState.markers = [];
    appState.imageWidth = 0;
    appState.imageHeight = 0;
    updateMarkerDisplay();
    markerDetailResult.innerHTML = '<p class="placeholder">Generated marker detail images use the selected marker and vision-model context.</p>';

    // Reset UI
    fileInput.value = '';
    document.getElementById('upload-section').classList.remove('hidden');
    document.getElementById('annotation-section').classList.add('hidden');
    clearUploadError();
}

function handleReset() {
    handleClear();
    handleNewUpload();
}

// ============================================
// UI Helpers
// ============================================

function showLoading(show, message = 'Processing...') {
    if (show) {
        loadingText.textContent = message;
        loadingIndicator.classList.remove('hidden');
    } else {
        loadingIndicator.classList.add('hidden');
    }
}

function showError(message) {
    errorMessage.textContent = message;
    errorToast.classList.remove('hidden');

    // Auto-hide after 5 seconds
    setTimeout(() => {
        errorToast.classList.add('hidden');
    }, 5000);
}

function showSuccess(message) {
    successMessage.textContent = message;
    successToast.classList.remove('hidden');

    // Auto-hide after 3 seconds
    setTimeout(() => {
        successToast.classList.add('hidden');
    }, 3000);
}

function showUploadError(message) {
    uploadError.textContent = message;
    uploadError.classList.add('show');
}

function clearUploadError() {
    uploadError.textContent = '';
    uploadError.classList.remove('show');
}

// ============================================
// Initialization
// ============================================

document.addEventListener('DOMContentLoaded', () => {
    console.log('Red Marker Pro initialized');
    updateMarkerDisplay();
});
