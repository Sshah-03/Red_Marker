/**
 * Vision Analysis Module
 */

let analysisState = {
    currentAnalysis: null,
    sessionAnalyses: []
};

// ============================================
// Analysis Controls
// ============================================

const analyzeImageIdInput = document.getElementById('analyze-image-id');
const analyzeBtn = document.getElementById('analyze-btn');
const analysisResultsBox = document.getElementById('analysis-results');
const sessionAnalysesContainer = document.getElementById('session-analyses');

analyzeBtn.addEventListener('click', analyzeImage);

// ============================================
// Image Analysis
// ============================================

async function analyzeImage() {
    const imageId = parseInt(analyzeImageIdInput.value);

    if (isNaN(imageId) || imageId < 0) {
        showError('Please enter a valid image ID');
        return;
    }

    showLoading(true, 'Analyzing image...');

    try {
        const response = await fetch(`/api/analyze/image/${imageId}`, {
            method: 'POST'
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Analysis failed');
        }

        const analysis = await response.json();

        analysisState.currentAnalysis = analysis;
        displayAnalysisResults(analysis);
        showSuccess('Analysis completed!');

    } catch (error) {
        console.error('Error analyzing image:', error);
        showError('Error: ' + error.message);
    } finally {
        showLoading(false);
    }
}

function displayAnalysisResults(analysis) {
    const resultsHtml = `
        <div class="analysis-box">
            <h4>Analysis Results</h4>
            <p><strong>Image ID:</strong> ${analysis.image_id}</p>
            <p><strong>Model:</strong> ${analysis.model}</p>
            <p><strong>Timestamp:</strong> ${analysis.created_at}</p>
            ${analysis.confidence !== null ? `<p><strong>Confidence:</strong> <span class="confidence-score">${(analysis.confidence * 100).toFixed(2)}%</span></p>` : ''}
            <h5 style="margin-top: 15px;">Results:</h5>
            <pre>${JSON.stringify(analysis.results, null, 2)}</pre>
        </div>
    `;

    analysisResultsBox.innerHTML = resultsHtml;
}

// ============================================
// Session Analyses
// ============================================

async function loadSessionAnalyses() {
    if (!appState.sessionId) {
        sessionAnalysesContainer.innerHTML = '<p class="placeholder">No active session</p>';
        return;
    }

    try {
        const response = await fetch(`/api/analyses/${appState.sessionId}?limit=10`);

        if (!response.ok) throw new Error('Failed to load analyses');

        const data = await response.json();

        analysisState.sessionAnalyses = data.analyses;
        displaySessionAnalyses(data.analyses);

    } catch (error) {
        console.error('Error loading analyses:', error);
        sessionAnalysesContainer.innerHTML = '<p class="placeholder">Error loading analyses</p>';
    }
}

function displaySessionAnalyses(analyses) {
    if (!analyses || analyses.length === 0) {
        sessionAnalysesContainer.innerHTML = '<p class="placeholder">No analyses yet</p>';
        return;
    }

    sessionAnalysesContainer.innerHTML = analyses.map(analysis => `
        <div class="analysis-item">
            <div class="analysis-item-header">
                <h5>Image ${analysis.image_id}</h5>
                <span>${analysis.model}</span>
            </div>
            <p><small>${new Date(analysis.created_at).toLocaleString()}</small></p>
            ${analysis.confidence !== null ? `
                <p>Confidence: <span class="confidence-score">${(analysis.confidence * 100).toFixed(2)}%</span></p>
            ` : ''}
            <button class="btn btn-sm btn-primary" onclick="displayAnalysisResults({
                image_id: ${analysis.image_id},
                model: '${analysis.model}',
                results: ${JSON.stringify(analysis.results).replace(/"/g, '&quot;')},
                confidence: ${analysis.confidence},
                created_at: '${analysis.created_at}'
            })">View Details</button>
        </div>
    `).join('');
}

// ============================================
// Batch Analysis
// ============================================

async function analyzeGeneratedImages(imageIds) {
    if (!imageIds || imageIds.length === 0) {
        showError('No images to analyze');
        return;
    }

    showLoading(true, `Analyzing ${imageIds.length} images...`);

    const results = [];

    for (const imageId of imageIds) {
        try {
            const response = await fetch(`/api/analyze/image/${imageId}`, {
                method: 'POST'
            });

            if (response.ok) {
                const analysis = await response.json();
                results.push(analysis);
            }
        } catch (error) {
            console.error(`Error analyzing image ${imageId}:`, error);
        }

        // Small delay between requests
        await new Promise(resolve => setTimeout(resolve, 500));
    }

    showLoading(false);
    showSuccess(`Analyzed ${results.length} images`);

    // Display results
    displayBatchAnalysisResults(results);
}

function displayBatchAnalysisResults(results) {
    const container = document.createElement('div');
    container.className = 'analysis-box';

    const html = `
        <h4>Batch Analysis Results (${results.length} images)</h4>
        <div style="max-height: 400px; overflow-y: auto;">
            ${results.map(result => `
                <div style="margin-bottom: 15px; padding: 10px; border-bottom: 1px solid #ddd;">
                    <p><strong>Image ${result.image_id}</strong> - ${result.model}</p>
                    ${result.confidence !== null ? `
                        <p>Confidence: <span class="confidence-score">${(result.confidence * 100).toFixed(2)}%</span></p>
                    ` : ''}
                </div>
            `).join('')}
        </div>
    `;

    container.innerHTML = html;
    analysisResultsBox.innerHTML = container.innerHTML;
}

// ============================================
// Analysis Statistics
// ============================================

function getAnalysisStats() {
    if (analysisState.sessionAnalyses.length === 0) {
        return null;
    }

    const confidences = analysisState.sessionAnalyses
        .filter(a => a.confidence !== null)
        .map(a => a.confidence);

    if (confidences.length === 0) {
        return null;
    }

    return {
        totalAnalyses: analysisState.sessionAnalyses.length,
        averageConfidence: (confidences.reduce((a, b) => a + b, 0) / confidences.length * 100).toFixed(2),
        maxConfidence: (Math.max(...confidences) * 100).toFixed(2),
        minConfidence: (Math.min(...confidences) * 100).toFixed(2)
    };
}

function displayAnalysisStats() {
    const stats = getAnalysisStats();

    if (!stats) {
        return '<p>No confidence data available</p>';
    }

    return `
        <p><strong>Total Analyses:</strong> ${stats.totalAnalyses}</p>
        <p><strong>Avg Confidence:</strong> ${stats.averageConfidence}%</p>
        <p><strong>Max Confidence:</strong> ${stats.maxConfidence}%</p>
        <p><strong>Min Confidence:</strong> ${stats.minConfidence}%</p>
    `;
}

// ============================================
// Initialization
// ============================================

document.addEventListener('DOMContentLoaded', () => {
    // Load analyses when tab is switched
    document.querySelector('[data-tab="analysis"]').addEventListener('click', () => {
        loadSessionAnalyses();
    });
});
