/**
 * AI Image Generation & Deterministic Drill Module
 */

let generationState = {
    isGenerating: false,
    currentPage: 0,
    totalPages: 0,
    pageSize: 10,
    totalImages: 0
};

let drillState = {
    drills: []
};

// ============================================
// Generation Controls
// ============================================

const generationPromptsInput = document.getElementById('generation-prompts');
const generationIntervalInput = document.getElementById('generation-interval');
const generationMaxImagesInput = document.getElementById('generation-max-images');
const startGenerationBtn = document.getElementById('start-generation-btn');
const stopGenerationBtn = document.getElementById('stop-generation-btn');

startGenerationBtn.addEventListener('click', startImageGeneration);
stopGenerationBtn.addEventListener('click', stopImageGeneration);

// Pagination
const genPrevBtn = document.getElementById('gen-prev-btn');
const genNextBtn = document.getElementById('gen-next-btn');
const genPageInfo = document.getElementById('gen-page-info');

genPrevBtn.addEventListener('click', () => previousGeneratedPage());
genNextBtn.addEventListener('click', () => nextGeneratedPage());

// ============================================
// Drill Controls
// ============================================

const drillNameInput = document.getElementById('drill-name');
const drillSeedInput = document.getElementById('drill-seed');
const drillNumImagesInput = document.getElementById('drill-num-images');
const createDrillBtn = document.getElementById('create-drill-btn');

createDrillBtn.addEventListener('click', createDeterministicDrill);

// ============================================
// Image Generation
// ============================================

async function startImageGeneration() {
    if (!appState.sessionId) {
        showError('Please upload an image first');
        return;
    }

    const promptsText = generationPromptsInput.value.trim();
    if (!promptsText) {
        showError('Please enter at least one prompt');
        return;
    }

    const prompts = promptsText.split('\n').map(p => p.trim()).filter(p => p.length > 0);
    const interval = parseInt(generationIntervalInput.value) || 5;
    const maxImages = parseInt(generationMaxImagesInput.value) || 0;

    showLoading(true, 'Starting image generation...');

    try {
        const response = await fetch('/api/generate/start?' + new URLSearchParams({
            session_id: appState.sessionId,
            interval: interval,
            max_images: maxImages || null,
            prompts: prompts.join('|||')
        }), {
            method: 'POST'
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail);
        }

        const data = await response.json();

        generationState.isGenerating = true;
        updateGenerationUI();

        showSuccess('Image generation started! Check the Generated Images section.');

        // Poll for new images
        pollForGeneratedImages();

    } catch (error) {
        console.error('Error starting generation:', error);
        showError('Error: ' + error.message);
    } finally {
        showLoading(false);
    }
}

async function stopImageGeneration() {
    if (!appState.sessionId) return;

    try {
        const response = await fetch(`/api/generate/stop?session_id=${appState.sessionId}`, {
            method: 'POST'
        });

        if (!response.ok) throw new Error('Failed to stop generation');

        generationState.isGenerating = false;
        updateGenerationUI();
        showSuccess('Image generation stopped');

    } catch (error) {
        console.error('Error:', error);
        showError('Error stopping generation');
    }
}

async function loadGeneratedImages(page = 0) {
    if (!appState.sessionId) return;

    try {
        const response = await fetch(
            `/api/generated-images/${appState.sessionId}?page=${page}&page_size=${generationState.pageSize}`
        );

        if (!response.ok) throw new Error('Failed to load images');

        const data = await response.json();

        generationState.currentPage = page;
        generationState.totalPages = data.total_pages;
        generationState.totalImages = data.total_count;

        displayGeneratedImages(data.images);
        updatePaginationUI();

    } catch (error) {
        console.error('Error loading images:', error);
        showError('Error loading generated images');
    }
}

function displayGeneratedImages(images) {
    const container = document.getElementById('generated-images-container');

    if (!images || images.length === 0) {
        container.innerHTML = '<p class="placeholder">No images generated yet</p>';
        return;
    }

    container.innerHTML = images.map(img => `
        <div class="image-card">
            <img src="/api/generated-image/${img.id}/data" alt="Generated image" onerror="this.src='data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+P+/HgAFhAJ/wlseKgAAAABJRU5ErkJggg=='">
            <div class="image-card-info">
                <p><strong>ID: ${img.id}</strong></p>
                <p>${img.prompt.substring(0, 30)}...</p>
                <p><small>${new Date(img.created_at).toLocaleString()}</small></p>
            </div>
        </div>
    `).join('');
}

function updatePaginationUI() {
    genPageInfo.textContent = `Page ${generationState.currentPage + 1} of ${generationState.totalPages || 1}`;
    genPrevBtn.disabled = generationState.currentPage === 0;
    genNextBtn.disabled = generationState.currentPage >= generationState.totalPages - 1;
}

function previousGeneratedPage() {
    if (generationState.currentPage > 0) {
        loadGeneratedImages(generationState.currentPage - 1);
    }
}

function nextGeneratedPage() {
    if (generationState.currentPage < generationState.totalPages - 1) {
        loadGeneratedImages(generationState.currentPage + 1);
    }
}

function updateGenerationUI() {
    if (generationState.isGenerating) {
        startGenerationBtn.classList.add('hidden');
        stopGenerationBtn.classList.remove('hidden');
    } else {
        startGenerationBtn.classList.remove('hidden');
        stopGenerationBtn.classList.add('hidden');
    }
}

function pollForGeneratedImages() {
    if (!generationState.isGenerating) return;

    // Poll every 3 seconds
    loadGeneratedImages(generationState.currentPage);

    setTimeout(pollForGeneratedImages, 3000);
}

// ============================================
// Deterministic Drill
// ============================================

async function createDeterministicDrill() {
    if (!appState.sessionId) {
        showError('Please upload an image first');
        return;
    }

    const drillName = drillNameInput.value.trim();
    if (!drillName) {
        showError('Please enter a drill name');
        return;
    }

    const promptsText = generationPromptsInput.value.trim();
    if (!promptsText) {
        showError('Please enter prompts for the drill');
        return;
    }

    const prompts = promptsText.split('\n').map(p => p.trim()).filter(p => p.length > 0);
    const seed = parseInt(drillSeedInput.value) || 42;
    const numImages = parseInt(drillNumImagesInput.value) || 10;

    showLoading(true, 'Creating deterministic drill...');

    try {
        const response = await fetch('/api/drill/create?' + new URLSearchParams({
            session_id: appState.sessionId,
            drill_name: drillName,
            seed: seed,
            num_images: numImages,
            prompts: prompts.join('|||')
        }), {
            method: 'POST'
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail);
        }

        const data = await response.json();

        showSuccess(`Drill "${drillName}" created successfully!`);

        // Reload drills list
        loadSessionDrills();

        // Clear inputs
        drillNameInput.value = '';

    } catch (error) {
        console.error('Error creating drill:', error);
        showError('Error: ' + error.message);
    } finally {
        showLoading(false);
    }
}

async function loadSessionDrills() {
    if (!appState.sessionId) return;

    try {
        const response = await fetch(`/api/drills/${appState.sessionId}`);

        if (!response.ok) throw new Error('Failed to load drills');

        const data = await response.json();
        displayDrills(data.drills);

    } catch (error) {
        console.error('Error loading drills:', error);
        showError('Error loading drills');
    }
}

function displayDrills(drills) {
    const container = document.getElementById('saved-drills-list');

    if (!drills || drills.length === 0) {
        container.innerHTML = '<p class="placeholder">No drills created yet</p>';
        return;
    }

    container.innerHTML = drills.map(drill => `
        <div class="drill-item">
            <div class="drill-item-info">
                <h4>${drill.name}</h4>
                <p>Seed: ${drill.seed} | Created: ${new Date(drill.created_at).toLocaleDateString()}</p>
                <p>${drill.description || 'No description'}</p>
            </div>
            <button class="btn btn-primary btn-sm" onclick="recreateDrill(${drill.id})">Recreate</button>
        </div>
    `).join('');
}

async function recreateDrill(drillId) {
    showLoading(true, 'Recreating drill...');

    try {
        const response = await fetch(`/api/drill/${drillId}/recreate`);

        if (!response.ok) throw new Error('Failed to recreate drill');

        showSuccess('Drill recreated successfully! Check the Generated Images section.');

    } catch (error) {
        console.error('Error:', error);
        showError('Error recreating drill');
    } finally {
        showLoading(false);
    }
}

// ============================================
// Initialization
// ============================================

document.addEventListener('DOMContentLoaded', () => {
    // Load initial data when tab is switched to generation
    document.querySelector('[data-tab="generate"]').addEventListener('click', () => {
        if (appState.sessionId) {
            loadGeneratedImages();
            loadSessionDrills();
        }
    });
});
