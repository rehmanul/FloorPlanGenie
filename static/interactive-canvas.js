// Interactive Canvas JavaScript
class InteractiveFloorPlanCanvas {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        this.options = {
            width: options.width || 1200,
            height: options.height || 800,
            minZoom: 0.1,
            maxZoom: 10,
            panEnabled: true,
            zoomEnabled: true,
            ...options
        };

        this.state = {
            zoom: 1,
            pan: { x: 0, y: 0 },
            isDragging: false,
            dragStart: { x: 0, y: 0 },
            selectedElements: new Set(),
            planData: null
        };

        this.initializeCanvas();
        this.bindEvents();
        this.initUpload();
    }

    initUpload() {
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput');

        if (uploadArea && fileInput) {
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
                    this.uploadFile(files[0]);
                }
            });

            fileInput.addEventListener('change', (e) => {
                if (e.target.files.length > 0) {
                    this.uploadFile(e.target.files[0]);
                }
            });
        }
    }

    async uploadFile(file) {
        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();
            if (result.success) {
                console.log('Plan uploaded successfully:', result);
                window.currentPlanId = result.plan_id;
                this.loadPlan(result);
            } else {
                alert('Upload failed: ' + result.error);
            }
        } catch (error) {
            alert('Upload failed: ' + error.message);
        }
    }

    initializeCanvas() {
        // Create main SVG container
        this.svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
        this.svg.setAttribute("viewBox", `0 0 ${this.options.width} ${this.options.height}`);
        this.svg.style.width = "100%";
        this.svg.style.height = "100%";
        this.svg.style.border = "1px solid #ddd";
        this.svg.style.cursor = "move";
        this.svg.style.display = "block";

        // Create viewport group for zooming and panning
        this.viewport = document.createElementNS("http://www.w3.org/2000/svg", "g");
        this.svg.appendChild(this.viewport);

        // Create layers
        this.layers = {
            background: this.createLayer('background'),
            walls: this.createLayer('walls'),
            zones: this.createLayer('zones'),
            boxes: this.createLayer('boxes'),
            corridors: this.createLayer('corridors'),
            annotations: this.createLayer('annotations'),
            ui: this.createLayer('ui')
        };

        this.container.appendChild(this.svg);

        // Add zoom controls
        this.createZoomControls();
    }

    createLayer(name) {
        const layer = document.createElementNS("http://www.w3.org/2000/svg", "g");
        layer.setAttribute("class", `layer-${name}`);
        this.viewport.appendChild(layer);
        return layer;
    }

    createZoomControls() {
        const controls = document.createElement('div');
        controls.className = 'zoom-controls';
        controls.style.cssText = `
            position: absolute;
            top: 10px;
            right: 10px;
            display: flex;
            flex-direction: column;
            gap: 5px;
            z-index: 1000;
        `;

        const zoomIn = this.createControlButton('+', () => this.zoomIn());
        const zoomOut = this.createControlButton('−', () => this.zoomOut());
        const zoomFit = this.createControlButton('⌂', () => this.zoomToFit());

        controls.appendChild(zoomIn);
        controls.appendChild(zoomOut);
        controls.appendChild(zoomFit);

        this.container.style.position = 'relative';
        this.container.appendChild(controls);
    }

    createControlButton(text, onClick) {
        const button = document.createElement('button');
        button.textContent = text;
        button.style.cssText = `
            width: 32px;
            height: 32px;
            background: white;
            border: 1px solid #ddd;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
            line-height: 1;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        `;
        button.onclick = onClick;
        return button;
    }

    bindEvents() {
        // Tool selection with proper event handling
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('tool-btn') || e.target.closest('.tool-btn')) {
                const btn = e.target.classList.contains('tool-btn') ? e.target : e.target.closest('.tool-btn');
                document.querySelectorAll('.tool-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this.selectedTool = btn.dataset.tool || 'pan';
                e.preventDefault();
                e.stopPropagation();
            }
        });

        let isMouseDown = false;
        let lastMousePos = { x: 0, y: 0 };

        // Mouse events for pan and zoom
        this.svg.addEventListener('mousedown', (e) => {
            if (e.button === 0) { // Left mouse button
                isMouseDown = true;
                lastMousePos = { x: e.clientX, y: e.clientY };
                this.svg.style.cursor = 'grabbing';
                this.state.isDragging = true;
                this.state.dragStart = { x: e.clientX, y: e.clientY };
            }
        });

        this.svg.addEventListener('mousemove', (e) => {
            if (isMouseDown && this.options.panEnabled) {
                const deltaX = e.clientX - lastMousePos.x;
                const deltaY = e.clientY - lastMousePos.y;

                this.state.pan.x += deltaX;
                this.state.pan.y += deltaY;

                lastMousePos = { x: e.clientX, y: e.clientY };
                this.updateTransform();
            }
        });

        this.svg.addEventListener('mouseup', () => {
            isMouseDown = false;
            this.svg.style.cursor = 'move';
            this.state.isDragging = false;
        });

        this.svg.addEventListener('mouseleave', () => {
            isMouseDown = false;
            this.svg.style.cursor = 'move';
            this.state.isDragging = false;
        });

        // Zoom with mouse wheel
        this.svg.addEventListener('wheel', (e) => {
            if (this.options.zoomEnabled) {
                e.preventDefault();

                const rect = this.svg.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const y = e.clientY - rect.top;

                const delta = e.deltaY > 0 ? 0.9 : 1.1;
                this.zoomAt(x, y, delta);
            }
        });

        // Element selection
        this.svg.addEventListener('click', (e) => {
            if (e.target !== this.svg && e.target !== this.viewport) {
                this.selectElement(e.target);
            }
        });
    }

    updateTransform() {
        const transform = `translate(${this.state.pan.x}, ${this.state.pan.y}) scale(${this.state.zoom})`;
        this.viewport.setAttribute('transform', transform);
    }

    zoomIn() {
        this.state.zoom = Math.min(this.state.zoom * 1.2, this.options.maxZoom);
        this.updateTransform();
    }

    zoomOut() {
        this.state.zoom = Math.max(this.state.zoom / 1.2, this.options.minZoom);
        this.updateTransform();
    }

    zoomAt(x, y, factor) {
        const newZoom = Math.min(Math.max(this.state.zoom * factor, this.options.minZoom), this.options.maxZoom);

        if (newZoom !== this.state.zoom) {
            const zoomFactor = newZoom / this.state.zoom;

            this.state.pan.x = x - zoomFactor * (x - this.state.pan.x);
            this.state.pan.y = y - zoomFactor * (y - this.state.pan.y);
            this.state.zoom = newZoom;

            this.updateTransform();
        }
    }

    zoomToFit() {
        if (!this.state.planData) return;

        const bounds = this.calculateContentBounds();
        if (!bounds) return;

        const padding = 50;
        const scaleX = (this.options.width - padding * 2) / bounds.width;
        const scaleY = (this.options.height - padding * 2) / bounds.height;

        this.state.zoom = Math.min(scaleX, scaleY, this.options.maxZoom);
        this.state.pan.x = padding - bounds.left * this.state.zoom;
        this.state.pan.y = padding - bounds.top * this.state.zoom;

        this.updateTransform();
    }

    calculateContentBounds() {
        if (!this.state.planData) return null;

        const { dimensions } = this.state.planData;
        const scale = 100; // Convert meters to pixels

        return {
            left: 0,
            top: 0,
            right: dimensions.width * scale,
            bottom: dimensions.height * scale,
            width: dimensions.width * scale,
            height: dimensions.height * scale
        };
    }

    loadPlanData(planData) {
        this.state.planData = planData;
        this.renderPlan();
    }

    renderPlan() {
        if (!this.state.planData) return;

        // Clear existing content
        Object.values(this.layers).forEach(layer => {
            while (layer.firstChild) {
                layer.removeChild(layer.firstChild);
            }
        });

        const scale = 100; // Convert meters to pixels

        // Render background grid
        this.renderGrid(scale);

        // Render walls
        this.renderWalls(this.state.planData.walls, scale);

        // Render zones if available
        if (this.state.planData.zones) {
            this.renderZones(this.state.planData.zones, scale);
        }

        // Render boxes if available
        if (this.state.planData.boxes) {
            this.renderBoxes(this.state.planData.boxes, scale);
        }

        // Render corridors if available
        if (this.state.planData.corridors) {
            this.renderCorridors(this.state.planData.corridors, scale);
        }

        // Auto-fit to view
        setTimeout(() => this.zoomToFit(), 100);
    }

    renderGrid(scale) {
        const { dimensions } = this.state.planData;
        const width = dimensions.width * scale;
        const height = dimensions.height * scale;

        // Major grid lines (1m intervals)
        const gridGroup = document.createElementNS("http://www.w3.org/2000/svg", "g");
        gridGroup.setAttribute("class", "grid");

        for (let x = 0; x <= width; x += scale) {
            const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
            line.setAttribute("x1", x);
            line.setAttribute("y1", 0);
            line.setAttribute("x2", x);
            line.setAttribute("y2", height);
            line.setAttribute("stroke", "#f0f0f0");
            line.setAttribute("stroke-width", x % (scale * 5) === 0 ? "1" : "0.5");
            gridGroup.appendChild(line);
        }

        for (let y = 0; y <= height; y += scale) {
            const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
            line.setAttribute("x1", 0);
            line.setAttribute("y1", y);
            line.setAttribute("x2", width);
            line.setAttribute("y2", y);
            line.setAttribute("stroke", "#f0f0f0");
            line.setAttribute("stroke-width", y % (scale * 5) === 0 ? "1" : "0.5");
            gridGroup.appendChild(line);
        }

        this.layers.background.appendChild(gridGroup);
    }

    renderWalls(walls, scale) {
        walls.forEach((wall, index) => {
            const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
            line.setAttribute("x1", wall.start.x * scale);
            line.setAttribute("y1", wall.start.y * scale);
            line.setAttribute("x2", wall.end.x * scale);
            line.setAttribute("y2", wall.end.y * scale);
            line.setAttribute("stroke", "#333");
            line.setAttribute("stroke-width", "3");
            line.setAttribute("stroke-linecap", "round");
            line.setAttribute("class", "wall");
            line.setAttribute("data-wall-id", index);

            // Add hover effects
            line.addEventListener('mouseenter', (e) => {
                e.target.setAttribute("stroke", "#007acc");
                e.target.setAttribute("stroke-width", "4");
            });

            line.addEventListener('mouseleave', (e) => {
                if (!this.state.selectedElements.has(e.target)) {
                    e.target.setAttribute("stroke", "#333");
                    e.target.setAttribute("stroke-width", "3");
                }
            });

            this.layers.walls.appendChild(line);
        });
    }

    renderZones(zones, scale) {
        if (!zones || zones.length === 0) return;
        
        zones.forEach((zone, index) => {
            if (zone.points && zone.points.length > 2) {
                const polygon = document.createElementNS("http://www.w3.org/2000/svg", "polygon");
                
                // Convert points to SVG polygon format
                const points = zone.points.map(point => 
                    `${point.x * scale},${point.y * scale}`
                ).join(' ');
                
                polygon.setAttribute("points", points);
                polygon.setAttribute("fill", "rgba(173, 216, 230, 0.3)");
                polygon.setAttribute("stroke", "rgba(173, 216, 230, 0.8)");
                polygon.setAttribute("stroke-width", "1");
                polygon.setAttribute("class", "zone");
                polygon.setAttribute("data-zone-id", index);

                this.layers.annotations.appendChild(polygon);
            }
        });
    }

    renderBoxes(boxes, scale) {
        boxes.forEach((box, index) => {
            const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
            rect.setAttribute("x", box.x * scale);
            rect.setAttribute("y", box.y * scale);
            rect.setAttribute("width", box.width * scale);
            rect.setAttribute("height", box.height * scale);
            rect.setAttribute("fill", "#4CAF50");
            rect.setAttribute("fill-opacity", "0.7");
            rect.setAttribute("stroke", "#2E7D32");
            rect.setAttribute("stroke-width", "2");
            rect.setAttribute("rx", "4");
            rect.setAttribute("class", "box");
            rect.setAttribute("data-box-id", box.id);

            // Add label
            const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
            text.setAttribute("x", (box.x + box.width / 2) * scale);
            text.setAttribute("y", (box.y + box.height / 2) * scale);
            text.setAttribute("text-anchor", "middle");
            text.setAttribute("dominant-baseline", "middle");
            text.setAttribute("fill", "white");
            text.setAttribute("font-family", "Arial, sans-serif");
            text.setAttribute("font-size", "12");
            text.setAttribute("font-weight", "bold");
            text.textContent = box.id || `Box ${index + 1}`;

            // Add interaction
            rect.addEventListener('click', () => {
                this.selectBox(box, rect);
            });

            this.layers.boxes.appendChild(rect);
            this.layers.annotations.appendChild(text);
        });
    }

    renderCorridors(corridors, scale) {
        corridors.forEach((corridor, index) => {
            const path = document.createElementNS("http://www.w3.org/2000/svg", "path");

            if (corridor.path && corridor.path.length > 0) {
                let pathData = `M ${corridor.path[0].x * scale} ${corridor.path[0].y * scale}`;
                for (let i = 1; i < corridor.path.length; i++) {
                    pathData += ` L ${corridor.path[i].x * scale} ${corridor.path[i].y * scale}`;
                }
                path.setAttribute("d", pathData);
            } else if (corridor.x !== undefined && corridor.y !== undefined) {
                // Simple corridor rectangle
                const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
                rect.setAttribute("x", corridor.x * scale);
                rect.setAttribute("y", corridor.y * scale);
                rect.setAttribute("width", corridor.width * scale);
                rect.setAttribute("height", corridor.height * scale);
                rect.setAttribute("fill", "#f44336");
                rect.setAttribute("fill-opacity", "0.6");
                rect.setAttribute("stroke", "#d32f2f");
                rect.setAttribute("stroke-width", "1");
                rect.setAttribute("class", "corridor");

                this.layers.corridors.appendChild(rect);
                return;
            }

            path.setAttribute("stroke", "#f44336");
            path.setAttribute("stroke-width", (corridor.width || 1.2) * scale);
            path.setAttribute("stroke-linecap", "round");
            path.setAttribute("stroke-linejoin", "round");
            path.setAttribute("fill", "none");
            path.setAttribute("opacity", "0.8");
            path.setAttribute("class", "corridor");

            this.layers.corridors.appendChild(path);
        });
    }

    selectElement(element) {
        // Clear previous selections
        this.state.selectedElements.forEach(el => {
            el.setAttribute("stroke-width", el.getAttribute("data-original-width") || "2");
            el.setAttribute("stroke", el.getAttribute("data-original-stroke") || "#333");
        });
        this.state.selectedElements.clear();

        // Select new element
        if (element && element.classList.contains('wall') || element.classList.contains('box')) {
            element.setAttribute("data-original-width", element.getAttribute("stroke-width"));
            element.setAttribute("data-original-stroke", element.getAttribute("stroke"));
            element.setAttribute("stroke", "#007acc");
            element.setAttribute("stroke-width", "4");
            this.state.selectedElements.add(element);

            // Show info panel
            this.showElementInfo(element);
        }
    }

    selectBox(box, element) {
        this.selectElement(element);

        // Emit event for external handling
        this.container.dispatchEvent(new CustomEvent('boxSelected', {
            detail: { box, element }
        }));
    }

    showElementInfo(element) {
        // Create or update info panel
        let infoPanel = document.getElementById('element-info-panel');
        if (!infoPanel) {
            infoPanel = document.createElement('div');
            infoPanel.id = 'element-info-panel';
            infoPanel.style.cssText = `
                position: absolute;
                top: 10px;
                left: 10px;
                background: white;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 10px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.15);
                font-family: Arial, sans-serif;
                font-size: 12px;
                z-index: 1001;
                min-width: 200px;
            `;
            this.container.appendChild(infoPanel);
        }

        let info = '';
        if (element.classList.contains('wall')) {
            const wallId = element.getAttribute('data-wall-id');
            info = `<strong>Wall ${wallId}</strong><br>Type: Structural<br>Layer: ${element.getAttribute('data-layer') || 'Default'}`;
        } else if (element.classList.contains('box')) {
            const boxId = element.getAttribute('data-box-id');
            const rect = element.getBoundingClientRect();
            info = `<strong>${boxId}</strong><br>Type: Placement Box<br>Dimensions: ${element.getAttribute('width')}x${element.getAttribute('height')}`;
        }

        infoPanel.innerHTML = info;
        infoPanel.style.display = 'block';
    }

    // Public API methods
    updateVisualization(data) {
        if (data.boxes) {
            // Clear existing boxes and corridors
            while (this.layers.boxes.firstChild) {
                this.layers.boxes.removeChild(this.layers.boxes.firstChild);
            }
            while (this.layers.corridors.firstChild) {
                this.layers.corridors.removeChild(this.layers.corridors.firstChild);
            }
            while (this.layers.annotations.firstChild) {
                this.layers.annotations.removeChild(this.layers.annotations.firstChild);
            }

            // Render new data
            const scale = 100;
            this.renderBoxes(data.boxes, scale);
            if (data.corridors) {
                this.renderCorridors(data.corridors, scale);
            }
        }
    }

    exportSVG() {
        const serializer = new XMLSerializer();
        return serializer.serializeToString(this.svg);
    }

    destroy() {
        if (this.container && this.svg) {
            this.container.removeChild(this.svg);
        }
    }
}

// Export for use in other scripts
window.InteractiveFloorPlanCanvas = InteractiveFloorPlanCanvas;