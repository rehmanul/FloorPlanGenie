
class FloorPlanGenie {
    constructor() {
        this.canvas = document.getElementById('floorPlanCanvas');
        this.ctx = this.canvas.getContext('2d');
        this.currentTool = 'wall';
        this.isDrawing = false;
        this.startPoint = null;
        this.elements = [];
        this.selectedElement = null;
        this.scale = 1;
        this.offset = { x: 0, y: 0 };
        this.gridSize = 20;
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.updateCanvasSize();
        this.draw();
        this.updateWallLengthDisplay();
    }
    
    setupEventListeners() {
        // Tool buttons
        document.querySelectorAll('.tool-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.handleToolClick(e));
        });
        
        // Canvas events
        this.canvas.addEventListener('mousedown', (e) => this.handleMouseDown(e));
        this.canvas.addEventListener('mousemove', (e) => this.handleMouseMove(e));
        this.canvas.addEventListener('mouseup', (e) => this.handleMouseUp(e));
        this.canvas.addEventListener('click', (e) => this.handleCanvasClick(e));
        
        // Furniture buttons
        document.querySelectorAll('.furniture-item').forEach(btn => {
            btn.addEventListener('click', (e) => this.selectFurniture(e));
        });
        
        // Wall length slider
        document.getElementById('wallLengthSlider').addEventListener('input', (e) => {
            this.updateWallLengthDisplay();
        });
        
        // Canvas controls
        document.getElementById('zoomIn').addEventListener('click', () => this.zoom(1.2));
        document.getElementById('zoomOut').addEventListener('click', () => this.zoom(0.8));
        document.getElementById('resetView').addEventListener('click', () => this.resetView());
        
        // Clear and export
        document.getElementById('clearBtn').addEventListener('click', () => this.clearCanvas());
        document.getElementById('exportBtn').addEventListener('click', () => this.exportPlan());
        
        // Window resize
        window.addEventListener('resize', () => this.updateCanvasSize());
    }
    
    handleToolClick(e) {
        const toolId = e.target.id;
        
        // Remove active class from all tools
        document.querySelectorAll('.tool-btn').forEach(btn => btn.classList.remove('active'));
        e.target.classList.add('active');
        
        // Hide all option groups
        document.querySelectorAll('.options-group').forEach(group => group.classList.remove('active'));
        
        // Set current tool and show relevant options
        switch(toolId) {
            case 'wallTool':
                this.currentTool = 'wall';
                document.getElementById('wallOptions').classList.add('active');
                break;
            case 'roomTool':
                this.currentTool = 'room';
                document.getElementById('roomOptions').classList.add('active');
                break;
            case 'doorTool':
                this.currentTool = 'door';
                break;
            case 'windowTool':
                this.currentTool = 'window';
                break;
            case 'furnitureTool':
                this.currentTool = 'furniture';
                document.getElementById('furnitureOptions').classList.add('active');
                break;
        }
        
        this.canvas.style.cursor = this.getCursorForTool();
    }
    
    getCursorForTool() {
        switch(this.currentTool) {
            case 'wall': return 'crosshair';
            case 'room': return 'copy';
            case 'door': return 'pointer';
            case 'window': return 'pointer';
            case 'furniture': return 'grab';
            default: return 'default';
        }
    }
    
    handleMouseDown(e) {
        const rect = this.canvas.getBoundingClientRect();
        const x = (e.clientX - rect.left) / this.scale - this.offset.x;
        const y = (e.clientY - rect.top) / this.scale - this.offset.y;
        
        this.startPoint = this.snapToGrid({ x, y });
        this.isDrawing = true;
        
        if (this.currentTool === 'furniture' && this.selectedFurnitureType) {
            this.placeFurniture(this.startPoint);
        }
    }
    
    handleMouseMove(e) {
        const rect = this.canvas.getBoundingClientRect();
        const x = (e.clientX - rect.left) / this.scale - this.offset.x;
        const y = (e.clientY - rect.top) / this.scale - this.offset.y;
        const snappedPoint = this.snapToGrid({ x, y });
        
        // Update mouse coordinates display
        document.getElementById('mouseCoords').textContent = 
            `X: ${Math.round(snappedPoint.x / this.gridSize)}, Y: ${Math.round(snappedPoint.y / this.gridSize)}`;
        
        if (this.isDrawing && this.startPoint) {
            this.draw();
            this.drawPreview(this.startPoint, snappedPoint);
        }
    }
    
    handleMouseUp(e) {
        if (!this.isDrawing || !this.startPoint) return;
        
        const rect = this.canvas.getBoundingClientRect();
        const x = (e.clientX - rect.left) / this.scale - this.offset.x;
        const y = (e.clientY - rect.top) / this.scale - this.offset.y;
        const endPoint = this.snapToGrid({ x, y });
        
        this.createElement(this.startPoint, endPoint);
        
        this.isDrawing = false;
        this.startPoint = null;
        this.draw();
    }
    
    handleCanvasClick(e) {
        if (this.currentTool === 'furniture' && this.selectedFurnitureType) {
            const rect = this.canvas.getBoundingClientRect();
            const x = (e.clientX - rect.left) / this.scale - this.offset.x;
            const y = (e.clientY - rect.top) / this.scale - this.offset.y;
            this.placeFurniture(this.snapToGrid({ x, y }));
        }
    }
    
    snapToGrid(point) {
        return {
            x: Math.round(point.x / this.gridSize) * this.gridSize,
            y: Math.round(point.y / this.gridSize) * this.gridSize
        };
    }
    
    createElement(start, end) {
        const element = {
            id: Date.now(),
            type: this.currentTool,
            start: start,
            end: end,
            created: new Date()
        };
        
        switch(this.currentTool) {
            case 'wall':
                element.length = this.calculateDistance(start, end);
                element.thickness = 8;
                break;
            case 'room':
                element.roomType = document.getElementById('roomType').value;
                element.width = Math.abs(end.x - start.x);
                element.height = Math.abs(end.y - start.y);
                break;
            case 'door':
                element.width = 60;
                element.height = 8;
                break;
            case 'window':
                element.width = Math.abs(end.x - start.x) || 80;
                element.height = 8;
                break;
        }
        
        this.elements.push(element);
    }
    
    placeFurniture(position) {
        if (!this.selectedFurnitureType) return;
        
        const furnitureSizes = {
            bed: { width: 80, height: 120 },
            sofa: { width: 100, height: 40 },
            table: { width: 60, height: 60 },
            desk: { width: 120, height: 60 }
        };
        
        const size = furnitureSizes[this.selectedFurnitureType] || { width: 40, height: 40 };
        
        const element = {
            id: Date.now(),
            type: 'furniture',
            furnitureType: this.selectedFurnitureType,
            start: position,
            end: {
                x: position.x + size.width,
                y: position.y + size.height
            },
            width: size.width,
            height: size.height,
            created: new Date()
        };
        
        this.elements.push(element);
        this.draw();
    }
    
    selectFurniture(e) {
        document.querySelectorAll('.furniture-item').forEach(item => item.classList.remove('active'));
        e.target.classList.add('active');
        this.selectedFurnitureType = e.target.dataset.type;
    }
    
    drawPreview(start, end) {
        this.ctx.save();
        this.ctx.strokeStyle = '#667eea';
        this.ctx.setLineDash([5, 5]);
        this.ctx.lineWidth = 2;
        
        switch(this.currentTool) {
            case 'wall':
                this.ctx.beginPath();
                this.ctx.moveTo(start.x, start.y);
                this.ctx.lineTo(end.x, end.y);
                this.ctx.stroke();
                break;
            case 'room':
                this.ctx.strokeRect(start.x, start.y, end.x - start.x, end.y - start.y);
                break;
        }
        
        this.ctx.restore();
    }
    
    draw() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Draw grid
        this.drawGrid();
        
        // Draw elements
        this.elements.forEach(element => this.drawElement(element));
    }
    
    drawGrid() {
        this.ctx.save();
        this.ctx.strokeStyle = '#f0f0f0';
        this.ctx.lineWidth = 0.5;
        
        for (let x = 0; x <= this.canvas.width; x += this.gridSize * this.scale) {
            this.ctx.beginPath();
            this.ctx.moveTo(x, 0);
            this.ctx.lineTo(x, this.canvas.height);
            this.ctx.stroke();
        }
        
        for (let y = 0; y <= this.canvas.height; y += this.gridSize * this.scale) {
            this.ctx.beginPath();
            this.ctx.moveTo(0, y);
            this.ctx.lineTo(this.canvas.width, y);
            this.ctx.stroke();
        }
        
        this.ctx.restore();
    }
    
    drawElement(element) {
        this.ctx.save();
        
        switch(element.type) {
            case 'wall':
                this.drawWall(element);
                break;
            case 'room':
                this.drawRoom(element);
                break;
            case 'door':
                this.drawDoor(element);
                break;
            case 'window':
                this.drawWindow(element);
                break;
            case 'furniture':
                this.drawFurniture(element);
                break;
        }
        
        this.ctx.restore();
    }
    
    drawWall(wall) {
        this.ctx.strokeStyle = '#333';
        this.ctx.lineWidth = wall.thickness || 8;
        this.ctx.lineCap = 'round';
        
        this.ctx.beginPath();
        this.ctx.moveTo(wall.start.x, wall.start.y);
        this.ctx.lineTo(wall.end.x, wall.end.y);
        this.ctx.stroke();
        
        // Draw length annotation
        const midX = (wall.start.x + wall.end.x) / 2;
        const midY = (wall.start.y + wall.end.y) / 2;
        const length = Math.round(this.calculateDistance(wall.start, wall.end) / this.gridSize);
        
        this.ctx.fillStyle = '#667eea';
        this.ctx.font = '12px Arial';
        this.ctx.fillText(`${length}ft`, midX + 5, midY - 5);
    }
    
    drawRoom(room) {
        const colors = {
            bedroom: '#E8F5E8',
            kitchen: '#FFF0E0',
            bathroom: '#E0F0FF',
            living: '#F0E8FF',
            office: '#FFE8E8'
        };
        
        this.ctx.fillStyle = colors[room.roomType] || '#F5F5F5';
        this.ctx.fillRect(room.start.x, room.start.y, room.end.x - room.start.x, room.end.y - room.start.y);
        
        this.ctx.strokeStyle = '#999';
        this.ctx.lineWidth = 2;
        this.ctx.strokeRect(room.start.x, room.start.y, room.end.x - room.start.x, room.end.y - room.start.y);
        
        // Room label
        const centerX = room.start.x + (room.end.x - room.start.x) / 2;
        const centerY = room.start.y + (room.end.y - room.start.y) / 2;
        
        this.ctx.fillStyle = '#333';
        this.ctx.font = '14px Arial';
        this.ctx.textAlign = 'center';
        this.ctx.fillText(room.roomType.charAt(0).toUpperCase() + room.roomType.slice(1), centerX, centerY);
        this.ctx.textAlign = 'left';
    }
    
    drawDoor(door) {
        this.ctx.fillStyle = '#8B4513';
        this.ctx.fillRect(door.start.x, door.start.y, door.width || 60, door.height || 8);
        
        // Door arc
        this.ctx.strokeStyle = '#8B4513';
        this.ctx.lineWidth = 1;
        this.ctx.beginPath();
        this.ctx.arc(door.start.x, door.start.y, door.width || 60, 0, Math.PI / 2);
        this.ctx.stroke();
    }
    
    drawWindow(window) {
        this.ctx.fillStyle = '#87CEEB';
        this.ctx.fillRect(window.start.x, window.start.y, window.width || 80, window.height || 8);
        
        // Window cross
        this.ctx.strokeStyle = '#4682B4';
        this.ctx.lineWidth = 2;
        const centerX = window.start.x + (window.width || 80) / 2;
        this.ctx.beginPath();
        this.ctx.moveTo(centerX, window.start.y);
        this.ctx.lineTo(centerX, window.start.y + (window.height || 8));
        this.ctx.stroke();
    }
    
    drawFurniture(furniture) {
        const colors = {
            bed: '#DEB887',
            sofa: '#8FBC8F',
            table: '#D2691E',
            desk: '#708090'
        };
        
        const icons = {
            bed: '🛏️',
            sofa: '🛋️',
            table: '🪑',
            desk: '🗃️'
        };
        
        this.ctx.fillStyle = colors[furniture.furnitureType] || '#CCC';
        this.ctx.fillRect(furniture.start.x, furniture.start.y, furniture.width, furniture.height);
        
        this.ctx.strokeStyle = '#333';
        this.ctx.lineWidth = 1;
        this.ctx.strokeRect(furniture.start.x, furniture.start.y, furniture.width, furniture.height);
        
        // Icon
        const centerX = furniture.start.x + furniture.width / 2;
        const centerY = furniture.start.y + furniture.height / 2;
        
        this.ctx.font = '20px Arial';
        this.ctx.textAlign = 'center';
        this.ctx.fillText(icons[furniture.furnitureType] || '📦', centerX, centerY + 5);
        this.ctx.textAlign = 'left';
    }
    
    calculateDistance(point1, point2) {
        return Math.sqrt(Math.pow(point2.x - point1.x, 2) + Math.pow(point2.y - point1.y, 2));
    }
    
    updateWallLengthDisplay() {
        const length = document.getElementById('wallLengthSlider').value;
        document.getElementById('wallLength').textContent = length;
    }
    
    zoom(factor) {
        this.scale *= factor;
        this.scale = Math.max(0.5, Math.min(3, this.scale));
        this.draw();
    }
    
    resetView() {
        this.scale = 1;
        this.offset = { x: 0, y: 0 };
        this.draw();
    }
    
    updateCanvasSize() {
        const container = this.canvas.parentElement;
        const rect = container.getBoundingClientRect();
        this.canvas.width = rect.width - 40;
        this.canvas.height = Math.max(400, rect.height - 100);
        this.draw();
    }
    
    clearCanvas() {
        if (confirm('Are you sure you want to clear the floor plan?')) {
            this.elements = [];
            this.draw();
        }
    }
    
    exportPlan() {
        // Create export data
        const exportData = {
            elements: this.elements,
            metadata: {
                created: new Date().toISOString(),
                totalElements: this.elements.length,
                rooms: this.elements.filter(e => e.type === 'room').length,
                walls: this.elements.filter(e => e.type === 'wall').length
            }
        };
        
        // Download as JSON
        const dataStr = JSON.stringify(exportData, null, 2);
        const dataBlob = new Blob([dataStr], { type: 'application/json' });
        const url = URL.createObjectURL(dataBlob);
        
        const link = document.createElement('a');
        link.href = url;
        link.download = 'floorplan-' + new Date().toISOString().split('T')[0] + '.json';
        link.click();
        
        URL.revokeObjectURL(url);
        
        // Also create image export
        const imageData = this.canvas.toDataURL('image/png');
        const imageLink = document.createElement('a');
        imageLink.href = imageData;
        imageLink.download = 'floorplan-' + new Date().toISOString().split('T')[0] + '.png';
        imageLink.click();
    }
}

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    new FloorPlanGenie();
});
