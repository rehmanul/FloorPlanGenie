class FloorPlanGenieAdvanced {
    constructor() {
        this.currentPlanId = null;
        this.optimizationResult = null;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupDragAndDrop();
    }

    setupEventListeners() {
        // File input
        document.getElementById('fileInput').addEventListener('change', (e) => this.handleFileSelect(e));

        // Optimize button
        document.getElementById('optimizeBtn').addEventListener('click', () => this.optimizeLayout());

        // Download button
        document.getElementById('downloadBtn').addEventListener('click', () => this.downloadResult());

        // Regenerate button
        document.getElementById('regenerateBtn').addEventListener('click', () => this.regenerateLayout());

        // Configuration changes
        ['boxWidth', 'boxHeight', 'corridorWidth'].forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.addEventListener('change', () => this.updateConfiguration());
            }
        });
    }

    setupDragAndDrop() {
        const uploadArea = document.getElementById('uploadArea');

        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });

        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('dragover');
        });

        uploadArea.addEventListener('drop', async (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            const files = Array.from(e.dataTransfer.files);
            await this.handleFiles(files);
        });

        uploadArea.addEventListener('click', () => {
            document.getElementById('fileInput').click();
        });
    }

    async handleFileSelect(event) {
        const files = event.target.files;
        if (files.length === 0) return;

        this.showProgress(true, 'Uploading and processing...');
        this.updateUploadStatus('Uploading file...');

        const formData = new FormData();
        formData.append('file', files[0]);

        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                // Handle non-200 responses
                if (response.status === 413) {
                    throw new Error('File too large. Maximum size is 50MB.');
                }
                throw new Error(`Server error: ${response.status}`);
            }

            const result = await response.json();

            if (result.success) {
                this.currentPlanId = result.plan_id;
                this.updateUploadStatus('✅ File processed successfully!');
                this.displayPlanInfo(result);
                this.displayProcessedPlan(result);
                document.getElementById('optimizeBtn').disabled = false;
                this.showNotification('Plan uploaded successfully!', 'success');
            } else {
                this.updateUploadStatus('❌ Error: ' + result.error);
                this.showNotification(`Error: ${result.error}`, 'error');
            }
        } catch (error) {
            this.updateUploadStatus('❌ Upload failed: ' + error.message);
            this.showNotification(`Upload failed: ${error.message}`, 'error');
        } finally {
            this.showProgress(false);
        }
    }

    updateUploadStatus(message) {
        const statusElement = document.querySelector('.upload-text p');
        if (statusElement) {
            statusElement.textContent = message;
        }
    }

    displayProcessedPlan(result) {
        // Show the processed plan visual
        if (result.visual_path) {
            // Show in results section
            const resultImage = document.getElementById('resultImage');
            if (resultImage) {
                resultImage.src = result.visual_path + '?t=' + Date.now(); // Cache busting
                resultImage.style.display = 'block';
            }

            // Show in processed plan section
            const processedSection = document.getElementById('processedPlanSection');
            const processedImage = document.getElementById('processedPlanImage');
            if (processedSection && processedImage) {
                processedImage.src = result.visual_path + '?t=' + Date.now();
                processedSection.style.display = 'block';

                // Update plan info
                const planDimensions = document.getElementById('planDimensions');
                const wallsCount = document.getElementById('wallsCount');
                const zonesCount = document.getElementById('zonesCount');

                if (planDimensions) planDimensions.textContent = `${result.dimensions.width}m × ${result.dimensions.height}m`;
                if (wallsCount) wallsCount.textContent = result.walls ? result.walls.length : '0';
                if (zonesCount) zonesCount.textContent = result.zones ? 
                    (result.zones.no_entry?.length || 0) + (result.zones.entry_exit?.length || 0) : '0';
            }

            // Update statistics with initial plan info
            this.updateStatistic('totalBoxes', '0');
            this.updateStatistic('totalCorridors', '0');
            this.updateStatistic('utilizationRate', '0%');
            this.updateStatistic('totalArea', `${(result.dimensions.width * result.dimensions.height).toFixed(1)} m²`);
        }
    }

    updateStatistic(id, value) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    }

    async handleFiles(files) {
        if (files.length === 0) return;

        const file = files[0];
        this.showProgress(true, 'Processing file...');

        try {
            const formData = new FormData();
            formData.append('file', file);

            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (result.success) {
                this.currentPlanId = result.plan_id;
                this.displayPlanInfo(result);
                this.displayProcessedPlan(result);
                document.getElementById('optimizeBtn').disabled = false;
                this.showNotification('Plan uploaded successfully!', 'success');
            } else {
                this.showNotification(`Error: ${result.error}`, 'error');
            }
        } catch (error) {
            this.showNotification(`Upload failed: ${error.message}`, 'error');
        } finally {
            this.showProgress(false);
        }
    }

    displayPlanInfo(planData) {
        // Display basic plan information
        console.log('Plan data:', planData);
        // Could add a preview section here showing detected walls, zones, etc.
    }

    async optimizeLayout() {
        if (!this.currentPlanId) {
            this.showNotification('Please upload a floor plan first', 'error');
            return;
        }

        this.showProgress(true, 'Optimizing layout...');

        try {
            const boxWidth = parseFloat(document.getElementById('boxWidth').value) || 3.0;
            const boxHeight = parseFloat(document.getElementById('boxHeight').value) || 4.0;
            const corridorWidth = parseFloat(document.getElementById('corridorWidth').value) || 1.2;

            const response = await fetch('/optimize', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    plan_id: this.currentPlanId,
                    box_dimensions: { width: boxWidth, height: boxHeight },
                    corridor_width: corridorWidth
                })
            });

            const result = await response.json();

            if (result.success) {
                this.optimizationResult = result;
                this.displayOptimizationResult(result);
                await this.generateVisual(result);
                this.showNotification('Layout optimized successfully!', 'success');
            } else {
                this.showNotification(`Optimization failed: ${result.error}`, 'error');
            }
        } catch (error) {
            this.showNotification(`Optimization failed: ${error.message}`, 'error');
        } finally {
            this.showProgress(false);
        }
    }

    async generateVisual(optimizationResult) {
        if (!optimizationResult) return;

        try {
            const outputFormat = document.getElementById('outputFormat')?.value || '2d';

            const response = await fetch('/generate_visual', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    ...optimizationResult,
                    format: outputFormat
                })
            });

            if (response.ok) {
                const blob = await response.blob();
                const imageUrl = URL.createObjectURL(blob);

                const resultImage = document.getElementById('resultImage');
                if (resultImage) {
                    resultImage.src = imageUrl;
                    resultImage.style.display = 'block';
                }
            }
        } catch (error) {
            console.error('Visual generation failed:', error);
        }
    }

    displayResults(result) {
        // Update statistics
        this.updateStatistic('totalBoxes', result.statistics.total_boxes);
        this.updateStatistic('totalCorridors', result.statistics.total_corridors);
        this.updateStatistic('utilizationRate', `${result.statistics.utilization_rate.toFixed(1)}%`);
        this.updateStatistic('totalArea', `${result.statistics.total_area.toFixed(1)} m²`);

        // Show results section
        const resultsSection = document.getElementById('resultsSection');
        if (resultsSection) {
            resultsSection.style.display = 'block';
            resultsSection.scrollIntoView({ behavior: 'smooth' });
        }
    }

    getConfiguration() {
        return {
            box_dimensions: {
                width: parseFloat(document.getElementById('boxWidth')?.value || '3.0'),
                height: parseFloat(document.getElementById('boxHeight')?.value || '4.0')
            },
            corridor_width: parseFloat(document.getElementById('corridorWidth')?.value || '1.2')
        };
    }

    updateConfiguration() {
        // Configuration changed - could trigger live preview if needed
        console.log('Configuration updated:', this.getConfiguration());
    }

    async regenerateLayout() {
        // Regenerate with slightly different parameters or random seed
        await this.optimizeLayout();
    }

    downloadResult() {
        if (!this.optimizationResult) return;

        // Download the current visual result
        const resultImage = document.getElementById('resultImage');
        if (resultImage && resultImage.src) {
            const link = document.createElement('a');
            link.href = resultImage.src;
            link.download = `floorplan-optimized-${new Date().toISOString().split('T')[0]}.png`;
            link.click();
        }
    }

    showProgress(show, message = 'Processing...') {
        const progressBar = document.getElementById('uploadProgress');
        if (progressBar) {
            if (show) {
                progressBar.style.display = 'block';
                const progressFill = progressBar.querySelector('.progress-fill');
                if (progressFill) {
                    progressFill.style.width = '100%';
                }
            } else {
                progressBar.style.display = 'none';
            }
        }
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 1rem 1.5rem;
            border-radius: 8px;
            color: white;
            font-weight: 600;
            z-index: 1000;
            max-width: 300px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        `;

        // Set color based on type
        switch(type) {
            case 'success':
                notification.style.backgroundColor = '#28a745';
                break;
            case 'error':
                notification.style.backgroundColor = '#dc3545';
                break;
            default:
                notification.style.backgroundColor = '#007bff';
        }

        document.body.appendChild(notification);

        // Auto remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 5000);
    }

    // Placeholder for the actual display of optimization results
    displayOptimizationResult(result) {
        console.log("Displaying optimization results:", result);
        // In a real scenario, this would update UI elements with calculated metrics,
        // optimized layout visualizations, etc.
        // For now, we'll just log it.
        if (result.statistics) {
            this.updateStatistic('totalBoxes', result.statistics.total_boxes);
            this.updateStatistic('totalCorridors', result.statistics.total_corridors);
            this.updateStatistic('utilizationRate', `${result.statistics.utilization_rate.toFixed(1)}%`);
            this.updateStatistic('totalArea', `${result.statistics.total_area.toFixed(1)} m²`);
        }
    }
}

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    new FloorPlanGenieAdvanced();
});