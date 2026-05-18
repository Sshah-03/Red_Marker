/**
 * Model Configuration Module
 */

let modelsState = {
    currentConfig: null
};

// ============================================
// Model Configuration Controls
// ============================================

const modelConfigBox = document.getElementById('models-config');
const imageGenModelSelect = document.getElementById('image-gen-model');
const imageGenApiKeyInput = document.getElementById('image-gen-api-key');
const setImageGenModelBtn = document.getElementById('set-image-gen-model-btn');

const visionModelSelect = document.getElementById('vision-model');
const visionModelPathInput = document.getElementById('vision-model-path');
const setVisionModelBtn = document.getElementById('set-vision-model-btn');

setImageGenModelBtn.addEventListener('click', updateImageGenerationModel);
setVisionModelBtn.addEventListener('click', updateVisionModel);

// ============================================
// Load Current Configuration
// ============================================

async function loadModelConfiguration() {
    try {
        const response = await fetch('/api/models/config');

        if (!response.ok) throw new Error('Failed to load configuration');

        const data = await response.json();

        modelsState.currentConfig = data.config;
        displayCurrentConfiguration(data.config);

    } catch (error) {
        console.error('Error loading configuration:', error);
        modelConfigBox.innerHTML = '<p>Error loading model configuration</p>';
    }
}

function displayCurrentConfiguration(config) {
    const html = `
        <div class="config-box">
            <h4>Active Configuration</h4>
            <p><strong>Image Generation Model:</strong> ${config.image_generation_model}</p>
            <p><strong>Vision Model:</strong> ${config.vision_model}</p>
            <p><strong>Image Size:</strong> ${config.image_size[0]} x ${config.image_size[1]}</p>
        </div>
    `;

    modelConfigBox.innerHTML = html;
}

// ============================================
// Image Generation Model Configuration
// ============================================

async function updateImageGenerationModel() {
    const modelName = imageGenModelSelect.value;
    const apiKey = imageGenApiKeyInput.value || null;

    if (!modelName) {
        showError('Please select a model');
        return;
    }

    showLoading(true, 'Updating image generation model...');

    try {
        const params = new URLSearchParams({
            model_name: modelName
        });

        if (apiKey) {
            params.append('api_key', apiKey);
        }

        const response = await fetch(`/api/models/image-generation?${params}`, {
            method: 'PUT'
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Update failed');
        }

        const data = await response.json();

        showSuccess(`Image generation model updated to: ${modelName}`);

        // Clear API key input for security
        imageGenApiKeyInput.value = '';

        // Reload configuration
        loadModelConfiguration();

    } catch (error) {
        console.error('Error updating model:', error);
        showError('Error: ' + error.message);
    } finally {
        showLoading(false);
    }
}

// ============================================
// Vision Model Configuration
// ============================================

async function updateVisionModel() {
    const modelName = visionModelSelect.value;
    const modelPath = visionModelPathInput.value || null;

    if (!modelName) {
        showError('Please select a model');
        return;
    }

    if (modelName === 'custom' && !modelPath) {
        showError('Please provide a path for custom model');
        return;
    }

    showLoading(true, 'Updating vision model...');

    try {
        const params = new URLSearchParams({
            model_name: modelName
        });

        if (modelPath) {
            params.append('model_path', modelPath);
        }

        const response = await fetch(`/api/models/vision?${params}`, {
            method: 'PUT'
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Update failed');
        }

        const data = await response.json();

        showSuccess(`Vision model updated to: ${modelName}`);

        // Reload configuration
        loadModelConfiguration();

    } catch (error) {
        console.error('Error updating model:', error);
        showError('Error: ' + error.message);
    } finally {
        showLoading(false);
    }
}

// ============================================
// Model Information
// ============================================

function getModelInfo(modelName) {
    const modelInfo = {
        'gemini-1.5-pro': {
            name: 'Gemini 1.5 Pro',
            type: 'Image Generation',
            description: 'Advanced image generation model from Google',
            requiresAuth: true
        },
        'gemini-1.0-pro-vision': {
            name: 'Gemini 1.0 Pro Vision',
            type: 'Image Generation',
            description: 'Vision-enabled image generation model',
            requiresAuth: true
        },
        'resnet50': {
            name: 'ResNet50',
            type: 'Vision - Classification',
            description: 'Image classification model (1000 classes)',
            requiresAuth: false
        },
        'clip': {
            name: 'CLIP',
            type: 'Vision - Vision-Language',
            description: 'Contrastive Language-Image Pre-training model',
            requiresAuth: false
        },
        'yolo': {
            name: 'YOLOv8',
            type: 'Vision - Object Detection',
            description: 'Real-time object detection model',
            requiresAuth: false
        },
        'custom': {
            name: 'Custom Model',
            type: 'Vision - Custom',
            description: 'Load your own model from a file path',
            requiresAuth: false
        }
    };

    return modelInfo[modelName] || null;
}

// ============================================
// Model Recommendations
// ============================================

function getModelRecommendations() {
    return {
        imageGeneration: [
            {
                name: 'gemini-1.5-pro',
                pros: ['High quality', 'Fast generation'],
                cons: ['Requires API key'],
                bestFor: 'Production use'
            },
            {
                name: 'gemini-1.0-pro-vision',
                pros: ['Vision-aware', 'Good quality'],
                cons: ['Requires API key'],
                bestFor: 'Vision-guided generation'
            }
        ],
        vision: [
            {
                name: 'resnet50',
                pros: ['Lightweight', 'Fast', 'No dependencies'],
                cons: ['Image classification only'],
                bestFor: 'Quick classification'
            },
            {
                name: 'clip',
                pros: ['Semantic understanding', 'Flexible'],
                cons: ['Larger model size'],
                bestFor: 'Text-image matching'
            },
            {
                name: 'yolo',
                pros: ['Object detection', 'Real-time'],
                cons: ['More computational overhead'],
                bestFor: 'Detecting specific objects'
            }
        ]
    };
}

// ============================================
// Initialization
// ============================================

document.addEventListener('DOMContentLoaded', () => {
    // Load configuration when tab is switched
    document.querySelector('[data-tab="models"]').addEventListener('click', () => {
        loadModelConfiguration();
    });

    // Load initial configuration
    loadModelConfiguration();
});
