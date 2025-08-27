
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
            document.getElementById(id).addEventListener('change', () => this.updateConfiguration());
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
        
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            this.handleFiles(e.dataTransfer.files);
        });
        
        uploadArea.addEventListener('click', () => {
            document.getElementById('fileInput').click();
        });
    }

    handleFileSelect(e) {
        this.handleFiles(e.target.files);
    }

    async handleFiles(files) {
        if (files.length === 0) return;

        const file = files[0];
        this.showProgress(true);

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
            this.showNotification('Please upload a plan first', 'error');
            return;
        }

        this.showProgress(true, 'Optimizing layout...');

        try {
            const config = this.getConfiguration();
            
            const response = await fetch('/optimize', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    plan_id: this.currentPlanId,
                    ...config
                })
            });

            const result = await response.json();

            if (result.success) {
                this.optimizationResult = result;
                await this.generateVisual();
                this.displayResults(result);
                this.showNotification('Layout optimized successfully!', 'success');
            } else {
                this.showNotification(`Optimization failed: ${result.error}`, 'error');
            }
        } catch (error) {
            this.showNotification(`Error: ${error.message}`, 'error');
        } finally {
            this.showProgress(false);
        }
    }

    async generateVisual() {
        if (!this.optimizationResult) return;

        try {
            const outputFormat = document.getElementById('outputFormat').value;
            
            const response = await fetch('/generate_visual', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    ...this.optimizationResult,
                    format: outputFormat
                })
            });

            if (response.ok) {
                const blob = await response.blob();
                const imageUrl = URL.createObjectURL(blob);
                
                const resultImage = document.getElementById('resultImage');
                resultImage.src = imageUrl;
                resultImage.style.display = 'block';
            }
        } catch (error) {
            console.error('Visual generation failed:', error);
        }
    }

    displayResults(result) {
        // Update statistics
        document.getElementById('totalBoxes').textContent = result.statistics.total_boxes;
        document.getElementById('totalCorridors').textContent = result.statistics.total_corridors;
        document.getElementById('utilizationRate').textContent = `${result.statistics.utilization_rate.toFixed(1)}%`;
        document.getElementById('totalArea').textContent = `${result.statistics.total_area.toFixed(1)} m²`;

        // Show results section
        document.getElementById('resultsSection').style.display = 'block';
        document.getElementById('resultsSection').scrollIntoView({ behavior: 'smooth' });
    }

    getConfiguration() {
        return {
            box_dimensions: {
                width: parseFloat(document.getElementById('boxWidth').value),
                height: parseFloat(document.getElementById('boxHeight').value)
            },
            corridor_width: parseFloat(document.getElementById('corridorWidth').value)
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
        if (resultImage.src) {
            const link = document.createElement('a');
            link.href = resultImage.src;
            link.download = `floorplan-optimized-${new Date().toISOString().split('T')[0]}.png`;
            link.click();
        }
    }

    showProgress(show, message = 'Processing...') {
        const progressBar = document.getElementById('uploadProgress');
        if (show) {
            progressBar.style.display = 'block';
            progressBar.querySelector('.progress-fill').style.width = '100%';
        } else {
            progressBar.style.display = 'none';
        }
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 5000);
    }
}

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    new FloorPlanGenieAdvanced();
});
