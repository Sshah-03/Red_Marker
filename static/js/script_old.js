/**
 * Red Marker - Frontend Application Logic
 * Handles image upload, click detection, and marker management
 */

// State management
const state = {
    sessionId: null,
    imageWidth: 0,
    imageHeight: 0,
    markers: [],
    originalFilename: ''
};

// DOM Elements
const uploadSection = document.getElementById('upload-section');
const annotationSection = document.getElementById('annotation-section');
const uploadArea = document.getElementById('upload-area');
const fileInput = document.getElementById('file-input');
const uploadError = document.getElementById('upload-error');
const displayImage = document.getElementById('display-image');
const canvasOverlay = document.getElementById('canvas-overlay');
const markerCount = document.getElementById('marker-count');
const markerList = document.getElementById('marker-list');
const loadingIndicator = document.getElementById('loading');

// Buttons
const undoBtn = document.getElementById('undo-btn');
const clearBtn = document.getElementById('clear-btn');
const downloadBtn = document.getElementById('download-btn');
const newUploadBtn = document.getElementById('new-upload-btn');

// ============================================
// Event Listeners - Upload
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
// Event Listeners - Annotation
// ============================================

canvasOverlay.addEventListener('click', handleCanvasClick);
undoBtn.addEventListener('click', handleUndo);
clearBtn.addEventListener('click', handleClear);
downloadBtn.addEventListener('click', handleDownload);
newUploadBtn.addEventListener('click', handleNewUpload);

// ============================================
// Upload Handler
// ============================================

async function handleFileSelect(file) {
    // Validate file type
    const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
    if (!allowedTypes.includes(file.type)) {
        showUploadError('Invalid file type. Please upload JPG, PNG, GIF, or WebP.');
        return;
    }

    // Validate file size (50MB)
    if (file.size > 50 * 1024 * 1024) {
        showUploadError('File size exceeds 50MB limit.');
        return;
    }

    showLoading(true);

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
            throw new Error(error.detail || error.error || 'Upload failed');
        }

        const data = await response.json();

        // Update state
        state.sessionId = data.session_id;
        state.imageWidth = data.width;
        state.imageHeight = data.height;
        state.markers = [];
        state.originalFilename = data.filename;

        // Load and display image
        await loadImage();

        // Switch UI to annotation section
        uploadSection.classList.remove('active');
        annotationSection.classList.add('active');

        // Set up canvas overlay
        setupCanvasOverlay();
        updateMarkerDisplay();

        hideUploadError();
    } catch (error) {
        console.error('Upload error:', error);
        showUploadError(error.message || 'Error uploading image');
    } finally {
        showLoading(false);
    }
}

function showUploadError(message) {
    uploadError.textContent = message;
    uploadError.classList.add('show');
}

function hideUploadError() {
    uploadError.classList.remove('show');
}

// ============================================
// Image Loading
// ============================================

async function loadImage() {
    if (!state.sessionId) return;

    try {
        const response = await fetch(`/api/image/${state.sessionId}?t=${Date.now()}`);
        if (!response.ok) throw new Error('Failed to load image');

        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        displayImage.src = url;

        // Update image dimensions after loading
        displayImage.onload = () => {
            setupCanvasOverlay();
        };
    } catch (error) {
        console.error('Error loading image:', error);
    }
}

// ============================================
// Canvas Overlay Setup
// ============================================

function setupCanvasOverlay() {
    const rect = displayImage.getBoundingClientRect();
    const imageRect = displayImage.parentElement.getBoundingClientRect();

    canvasOverlay.width = displayImage.offsetWidth;
    canvasOverlay.height = displayImage.offsetHeight;

    // Position canvas to match image
    canvasOverlay.style.width = displayImage.offsetWidth + 'px';
    canvasOverlay.style.height = displayImage.offsetHeight + 'px';

    // Redraw markers on canvas
    redrawMarkers();
}

function redrawMarkers() {
    const ctx = canvasOverlay.getContext('2d');
    ctx.clearRect(0, 0, canvasOverlay.width, canvasOverlay.height);

    const scaleX = canvasOverlay.width / state.imageWidth;
    const scaleY = canvasOverlay.height / state.imageHeight;

    state.markers.forEach(([x, y]) => {
        const canvasX = x * scaleX;
        const canvasY = y * scaleY;

        // Draw circle
        ctx.strokeStyle = '#ff4444';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(canvasX, canvasY, 15, 0, Math.PI * 2);
        ctx.stroke();

        // Draw center dot
        ctx.fillStyle = '#ff4444';
        ctx.beginPath();
        ctx.arc(canvasX, canvasY, 3, 0, Math.PI * 2);
        ctx.fill();
    });
}

// ============================================
// Click Handler
// ============================================

async function handleCanvasClick(e) {
    const rect = canvasOverlay.getBoundingClientRect();
    const parentRect = canvasOverlay.parentElement.getBoundingClientRect();

    // Get click position relative to canvas
    const canvasX = e.clientX - rect.left;
    const canvasY = e.clientY - rect.top;

    // Convert canvas coordinates to image coordinates
    const scaleX = state.imageWidth / canvasOverlay.width;
    const scaleY = state.imageHeight / canvasOverlay.height;

    const imageX = Math.round(canvasX * scaleX);
    const imageY = Math.round(canvasY * scaleY);

    // Validate coordinates
    if (imageX < 0 || imageX > state.imageWidth || imageY < 0 || imageY > state.imageHeight) {
        return;
    }

    showLoading(true);

    try {
        // Send marker to backend
        const response = await fetch(`/api/markers/${state.sessionId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                x: imageX,
                y: imageY
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || error.error || 'Failed to add marker');
        }

        const data = await response.json();
        state.markers = data.markers;

        // Reload image with new marker
        await loadImage();
        updateMarkerDisplay();
    } catch (error) {
        console.error('Error adding marker:', error);
    } finally {
        showLoading(false);
    }
}

// ============================================
// Marker Management
// ============================================

async function handleUndo() {
    if (state.markers.length === 0) return;

    showLoading(true);

    try {
        // Remove last marker from state
        state.markers.pop();

        // Get current markers from server
        const response = await fetch(`/api/markers/${state.sessionId}`);
        if (!response.ok) throw new Error('Failed to get markers');

        const data = await response.json();
        state.markers = data.markers;

        // Clear all markers on server
        await fetch(`/api/markers/${state.sessionId}`, { method: 'DELETE' });

        // Re-add all markers except the last one
        for (const [x, y] of state.markers) {
            await fetch(`/api/markers/${state.sessionId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ x, y })
            });
        }

        // Reload image
        await loadImage();
        updateMarkerDisplay();
    } catch (error) {
        console.error('Error undoing marker:', error);
    } finally {
        showLoading(false);
    }
}

async function handleClear() {
    if (state.markers.length === 0) return;

    if (!confirm('Clear all markers? This cannot be undone.')) {
        return;
    }

    showLoading(true);

    try {
        const response = await fetch(`/api/markers/${state.sessionId}`, {
            method: 'DELETE'
        });

        if (!response.ok) throw new Error('Failed to clear markers');

        state.markers = [];

        // Reload image
        await loadImage();
        updateMarkerDisplay();
    } catch (error) {
        console.error('Error clearing markers:', error);
    } finally {
        showLoading(false);
    }
}

// ============================================
// Download Handler
// ============================================

async function handleDownload() {
    if (!state.sessionId) return;

    showLoading(true);

    try {
        const response = await fetch(`/api/download/${state.sessionId}`);
        if (!response.ok) throw new Error('Failed to download image');

        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${state.originalFilename.split('.')[0]}_marked.png`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    } catch (error) {
        console.error('Error downloading image:', error);
        alert('Failed to download image');
    } finally {
        showLoading(false);
    }
}

// ============================================
// New Upload Handler
// ============================================

async function handleNewUpload() {
    // Clear session on server
    if (state.sessionId) {
        try {
            await fetch(`/api/session/${state.sessionId}`, {
                method: 'DELETE'
            });
        } catch (error) {
            console.error('Error clearing session:', error);
        }
    }

    // Reset state
    state.sessionId = null;
    state.imageWidth = 0;
    state.imageHeight = 0;
    state.markers = [];
    state.originalFilename = '';

    // Reset UI
    fileInput.value = '';
    uploadSection.classList.add('active');
    annotationSection.classList.remove('active');
    hideUploadError();
    updateMarkerDisplay();
}

// ============================================
// UI Updates
// ============================================

function updateMarkerDisplay() {
    // Update marker count
    markerCount.textContent = `Count: ${state.markers.length}`;

    // Update marker list
    markerList.innerHTML = '';

    state.markers.forEach(([x, y], index) => {
        const item = document.createElement('div');
        item.className = 'marker-item';

        const coord = document.createElement('span');
        coord.className = 'marker-coord';
        coord.textContent = `#${index + 1}: (${x}, ${y})`;

        const removeBtn = document.createElement('button');
        removeBtn.className = 'marker-remove-btn';
        removeBtn.textContent = 'Remove';
        removeBtn.addEventListener('click', () => removeMarker(index));

        item.appendChild(coord);
        item.appendChild(removeBtn);
        markerList.appendChild(item);
    });

    // Update button states
    undoBtn.disabled = state.markers.length === 0;
    clearBtn.disabled = state.markers.length === 0;
    downloadBtn.disabled = state.markers.length === 0;
}

async function removeMarker(index) {
    showLoading(true);

    try {
        // Get current markers from server
        const response = await fetch(`/api/markers/${state.sessionId}`);
        if (!response.ok) throw new Error('Failed to get markers');

        const data = await response.json();
        const allMarkers = data.markers;

        // Remove the specific marker
        allMarkers.splice(index, 1);

        // Clear all markers on server
        await fetch(`/api/markers/${state.sessionId}`, { method: 'DELETE' });

        // Re-add remaining markers
        for (const [x, y] of allMarkers) {
            await fetch(`/api/markers/${state.sessionId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ x, y })
            });
        }

        state.markers = allMarkers;

        // Reload image
        await loadImage();
        updateMarkerDisplay();
    } catch (error) {
        console.error('Error removing marker:', error);
    } finally {
        showLoading(false);
    }
}

// ============================================
// Loading Indicator
// ============================================

function showLoading(show) {
    if (show) {
        loadingIndicator.classList.remove('hidden');
    } else {
        loadingIndicator.classList.add('hidden');
    }
}

// ============================================
// Initialization
// ============================================

console.log('Red Marker Application Ready');
