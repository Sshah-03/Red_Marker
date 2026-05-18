/**
 * History & Navigation Module
 */

let historyState = {
    currentIndex: 0,
    totalImages: 0,
    navigationHistory: []
};

// ============================================
// Navigation Controls
// ============================================

const historyPrevBtn = document.getElementById('history-prev-btn');
const historyNextBtn = document.getElementById('history-next-btn');
const goToBtn = document.getElementById('go-to-btn');
const historyResetBtn = document.getElementById('history-reset-btn');
const imageIndexInput = document.getElementById('image-index');
const sessionInfoBox = document.getElementById('session-info');
const historyListContainer = document.getElementById('history-list');

historyPrevBtn.addEventListener('click', goToPreviousImage);
historyNextBtn.addEventListener('click', goToNextImage);
goToBtn.addEventListener('click', goToImage);
historyResetBtn.addEventListener('click', resetToStart);

// ============================================
// Session History
// ============================================

async function loadSessionHistory() {
    if (!appState.sessionId) {
        sessionInfoBox.innerHTML = '<p>No active session. Please upload an image first.</p>';
        return;
    }

    try {
        const response = await fetch(`/api/session/${appState.sessionId}/history`);

        if (!response.ok) {
            // Session might not exist yet, create default
            sessionInfoBox.innerHTML = '<p>Session initialized. Navigate through images using the controls below.</p>';
            return;
        }

        const history = await response.json();

        historyState.currentIndex = history.current_image_index;
        historyState.totalImages = history.total_images;

        displaySessionInfo(history);
        updateNavigationUI();

    } catch (error) {
        console.error('Error loading history:', error);
        sessionInfoBox.innerHTML = '<p>Ready for navigation</p>';
    }
}

function displaySessionInfo(history) {
    const drillInfo = history.drill_mode ? 
        ` | Drill Mode (Seed: ${history.drill_seed})` : '';

    sessionInfoBox.innerHTML = `
        <div class="info-box">
            <p><strong>Current Index:</strong> ${history.current_image_index}</p>
            <p><strong>Total Images:</strong> ${history.total_images}</p>
            <p><strong>Created:</strong> ${new Date(history.created_at).toLocaleString()}</p>
            <p><strong>Mode:</strong> ${history.drill_mode ? 'Deterministic Drill' : 'Continuous Generation'}${drillInfo}</p>
        </div>
    `;
}

// ============================================
// Navigation Functions
// ============================================

async function navigateToImage(index) {
    if (!appState.sessionId) {
        showError('No active session');
        return;
    }

    if (index < 0 || (historyState.totalImages > 0 && index >= historyState.totalImages)) {
        showError('Image index out of range');
        return;
    }

    try {
        const response = await fetch(`/api/session/${appState.sessionId}/navigate?image_index=${index}`, {
            method: 'PUT'
        });

        if (!response.ok) throw new Error('Failed to navigate');

        const data = await response.json();

        historyState.currentIndex = index;
        addToNavigationHistory(index);
        updateNavigationUI();

        showSuccess(`Navigated to image ${index}`);

    } catch (error) {
        console.error('Error navigating:', error);
        showError('Error navigating to image');
    }
}

function goToPreviousImage() {
    if (historyState.currentIndex > 0) {
        navigateToImage(historyState.currentIndex - 1);
    } else {
        showError('Already at first image');
    }
}

function goToNextImage() {
    if (historyState.totalImages === 0 || historyState.currentIndex < historyState.totalImages - 1) {
        navigateToImage(historyState.currentIndex + 1);
    } else {
        showError('Already at last image');
    }
}

function goToImage() {
    const index = parseInt(imageIndexInput.value);
    if (isNaN(index)) {
        showError('Please enter a valid image index');
        return;
    }
    navigateToImage(index);
}

async function resetToStart() {
    if (!appState.sessionId) {
        showError('No active session');
        return;
    }

    try {
        const response = await fetch(`/api/session/${appState.sessionId}/reset`, {
            method: 'POST'
        });

        if (!response.ok) throw new Error('Failed to reset');

        historyState.currentIndex = 0;
        historyState.navigationHistory = [];
        updateNavigationUI();

        showSuccess('Session reset to start');

    } catch (error) {
        console.error('Error resetting:', error);
        showError('Error resetting session');
    }
}

// ============================================
// Navigation History Tracking
// ============================================

function addToNavigationHistory(index) {
    const timestamp = new Date().toLocaleTimeString();
    historyState.navigationHistory.unshift({
        index: index,
        timestamp: timestamp
    });

    // Keep only last 20 items
    if (historyState.navigationHistory.length > 20) {
        historyState.navigationHistory.pop();
    }

    displayNavigationHistory();
}

function displayNavigationHistory() {
    if (historyState.navigationHistory.length === 0) {
        historyListContainer.innerHTML = '<p class="placeholder">No navigation history yet</p>';
        return;
    }

    historyListContainer.innerHTML = historyState.navigationHistory.map((item, idx) => `
        <div class="history-item">
            <div class="history-item-info">
                <h4>Image ${item.index}</h4>
                <p>${item.timestamp}</p>
            </div>
            <button class="btn btn-sm btn-secondary" onclick="navigateToImage(${item.index})">Go To</button>
        </div>
    `).join('');
}

// ============================================
// UI Updates
// ============================================

function updateNavigationUI() {
    imageIndexInput.value = historyState.currentIndex;

    // Update button states
    historyPrevBtn.disabled = historyState.currentIndex === 0;
    historyNextBtn.disabled = historyState.totalImages > 0 && historyState.currentIndex >= historyState.totalImages - 1;
}

// ============================================
// Back/Reset Features
// ============================================

function getNavigationStats() {
    return {
        currentIndex: historyState.currentIndex,
        totalImages: historyState.totalImages,
        historyLength: historyState.navigationHistory.length
    };
}

// ============================================
// Initialization
// ============================================

document.addEventListener('DOMContentLoaded', () => {
    // Load history when tab is switched
    document.querySelector('[data-tab="history"]').addEventListener('click', () => {
        loadSessionHistory();
    });
});
