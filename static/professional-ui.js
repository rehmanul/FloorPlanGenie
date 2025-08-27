
class ProfessionalUI {
    constructor() {
        this.currentPlanId = null;
        this.currentOptimization = null;
        this.isProcessing = false;
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.setupFileUpload();
    }
    
    setupEventListeners() {
        // Optimization button
        const optimizeBtn = document.getElementById('optimizeBtn');
        if (optimizeBtn) {
            optimizeBtn.addEventListener('click', () => this.runOptimization());
        }
        
        // Control inputs
        const inputs = document.querySelectorAll('.control-input');
        inputs.forEach(input => {
            input.addEventListener('change', () => this.onParameterChange());
        });
    }
    
    setupFileUpload() {
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput');
        
        if (!uploadArea || !fileInput) return;
        
        // Drag and drop
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('drag-over');
        });
        
        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('drag-over');
        });
        
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('drag-over');
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                this.handleFileUpload(files[0]);
            }
        });
        
        // Click upload
        uploadArea.addEventListener('click', () => {
            fileInput.click();
        });
        
        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                this.handleFileUpload(e.target.files[0]);
            }
        });
    }
    
    async handleFileUpload(file) {
        if (this.isProcessing) return;
        
        this.showLoading(true, 'Processing CAD file...');
        this.isProcessing = true;
        
        const formData = new FormData();
        formData.append('file', file);
        
        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.currentPlanId = result.plan_id;
                this.displayPlanData(result);
                this.showNotification('File uploaded successfully!', 'success');
            } else {
                this.showNotification(`Error: ${result.error}`, 'error');
            }
        } catch (error) {
            this.showNotification(`Upload failed: ${error.message}`, 'error');
        } finally {
            this.showLoading(false);
            this.isProcessing = false;
        }
    }
    
    async runOptimization() {
        if (!this.currentPlanId || this.isProcessing) return;
        
        this.showLoading(true, 'Optimizing placement...');
        this.isProcessing = true;
        
        const params = {
            plan_id: this.currentPlanId,
            layout_profile: document.getElementById('layoutProfile').value,
            box_width: parseFloat(document.getElementById('boxWidth').value),
            box_height: parseFloat(document.getElementById('boxHeight').value),
            corridor_width: parseFloat(document.getElementById('corridorWidth').value),
            box_dimensions: {
                width: parseFloat(document.getElementById('boxWidth').value),
                height: parseFloat(document.getElementById('boxHeight').value)
            }
        };
        
        try {
            const response = await fetch('/advanced_optimize', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(params)
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.currentOptimization = result;
                this.displayOptimizationResults(result);
                this.updateStatistics(result.statistics);
                this.showNotification('Optimization completed!', 'success');
            } else {
                this.showNotification(`Optimization failed: ${result.error}`, 'error');
            }
        } catch (error) {
            this.showNotification(`Optimization error: ${error.message}`, 'error');
        } finally {
            this.showLoading(false);
            this.isProcessing = false;
        }
    }
    
    displayPlanData(planData) {
        const container = document.getElementById('canvasContainer');
        if (!container) return;
        
        // Remove placeholder
        const placeholder = container.querySelector('.canvas-placeholder');
        if (placeholder) {
            placeholder.style.display = 'none';
        }
        
        // Add basic plan visualization
        const planInfo = document.createElement('div');
        planInfo.className = 'plan-info';
        planInfo.innerHTML = `
            <h3>📐 Plan Dimensions</h3>
            <p>Width: ${planData.dimensions?.width?.toFixed(2) || 'Unknown'}m</p>
            <p>Height: ${planData.dimensions?.height?.toFixed(2) || 'Unknown'}m</p>
            <p>Walls: ${planData.walls?.length || 0}</p>
            <p>Zones: ${planData.zones?.length || 0}</p>
            <p>Doors: ${planData.doors?.length || 0}</p>
        `;
        
        container.innerHTML = '';
        container.appendChild(planInfo);
    }
    
    displayOptimizationResults(results) {
        const container = document.getElementById('canvasContainer');
        if (!container) return;
        
        // Create results display
        const resultsDiv = document.createElement('div');
        resultsDiv.className = 'optimization-results';
        
        const ilots = results.ilots || results.boxes || [];
        const corridors = results.corridors || [];
        
        resultsDiv.innerHTML = `
            <h3>🎯 Optimization Results</h3>
            <div class="results-grid">
                <div class="result-item">
                    <strong>${ilots.length}</strong>
                    <span>Îlots Placed</span>
                </div>
                <div class="result-item">
                    <strong>${corridors.length}</strong>
                    <span>Corridors Generated</span>
                </div>
                <div class="result-item">
                    <strong>${results.statistics?.utilization_rate?.toFixed(1) || 0}%</strong>
                    <span>Space Utilization</span>
                </div>
                <div class="result-item">
                    <strong>${results.statistics?.efficiency_score?.toFixed(0) || 0}</strong>
                    <span>Efficiency Score</span>
                </div>
            </div>
            
            <div class="ilots-list">
                <h4>Îlot Details:</h4>
                ${ilots.map((ilot, index) => `
                    <div class="ilot-item">
                        <span class="ilot-category ${ilot.category || 'medium'}">${ilot.category || 'medium'}</span>
                        <span>${ilot.area?.toFixed(1) || (ilot.width * ilot.height).toFixed(1)}m²</span>
                        <span>@(${ilot.x.toFixed(1)}, ${ilot.y.toFixed(1)})</span>
                    </div>
                `).join('')}
            </div>
            
            <button class="btn btn-primary" onclick="professionalUI.generateInteractiveView()">
                🎨 Generate Interactive View
            </button>
        `;
        
        container.innerHTML = '';
        container.appendChild(resultsDiv);
    }
    
    async generateInteractiveView() {
        if (!this.currentOptimization) return;
        
        this.showLoading(true, 'Generating interactive visualization...');
        
        try {
            const response = await fetch('/interactive_visual', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(this.currentOptimization)
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.displayInteractiveView(result.visual_path, result.svg_string);
                this.showNotification('Interactive view generated!', 'success');
            } else {
                this.showNotification(`Error generating view: ${result.error}`, 'error');
            }
        } catch (error) {
            this.showNotification(`Visualization error: ${error.message}`, 'error');
        } finally {
            this.showLoading(false);
        }
    }
    
    displayInteractiveView(visualPath, svgString) {
        const container = document.getElementById('canvasContainer');
        if (!container) return;
        
        if (svgString) {
            container.innerHTML = svgString;
        } else if (visualPath) {
            container.innerHTML = `<img src="${visualPath}" alt="Interactive Floor Plan" style="max-width: 100%; height: auto;">`;
        }
    }
    
    updateStatistics(statistics) {
        const updates = {
            totalBoxes: statistics?.total_boxes || statistics?.total_ilots || 0,
            utilizationRate: (statistics?.utilization_rate || 0).toFixed(1) + '%',
            totalCorridors: statistics?.total_corridors || 0,
            efficiencyScore: (statistics?.efficiency_score || 0).toFixed(0)
        };
        
        Object.entries(updates).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = value;
            }
        });
    }
    
    showLoading(show, message = 'Processing...') {
        const loading = document.getElementById('canvasLoading');
        if (loading) {
            if (show) {
                loading.style.display = 'flex';
                const text = loading.querySelector('p');
                if (text) text.textContent = message;
            } else {
                loading.style.display = 'none';
            }
        }
    }
    
    showNotification(message, type = 'info') {
        // Create notification
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
                notification.style.backgroundColor = '#10B981';
                break;
            case 'error':
                notification.style.backgroundColor = '#EF4444';
                break;
            default:
                notification.style.backgroundColor = '#3B82F6';
        }
        
        document.body.appendChild(notification);
        
        // Remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 5000);
    }
    
    onParameterChange() {
        // Handle parameter changes - could trigger real-time preview
        console.log('Parameters changed');
    }
}

// Global export functions
function exportPlan(format) {
    if (!professionalUI.currentOptimization) {
        professionalUI.showNotification('No optimization data to export', 'error');
        return;
    }
    
    professionalUI.showLoading(true, `Exporting as ${format.toUpperCase()}...`);
    
    fetch('/export_plan', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            format: format,
            plan_data: professionalUI.currentOptimization
        })
    })
    .then(response => {
        if (response.ok) {
            return response.blob();
        }
        throw new Error('Export failed');
    })
    .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `floorplan.${format}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        professionalUI.showNotification(`Exported as ${format.toUpperCase()}!`, 'success');
    })
    .catch(error => {
        professionalUI.showNotification(`Export failed: ${error.message}`, 'error');
    })
    .finally(() => {
        professionalUI.showLoading(false);
    });
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.professionalUI = new ProfessionalUI();
});
