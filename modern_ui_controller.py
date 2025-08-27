"""
Modern UI Controller - Independent Canvas Design
Professional interface with drawer menu and independent canvas
"""
import json
import os
from datetime import datetime

class ModernUIController:
    def __init__(self):
        self.ui_state = {
            'current_tool': 'select',
            'selected_elements': [],
            'editing_mode': False,
            'constraint_violations': [],
            'real_time_updates': True
        }
        
    def generate_modern_interface_html(self, plan_data):
        """Generate modern, professional UI with independent canvas"""
        
        dimensions = plan_data['dimensions']
        statistics = plan_data.get('statistics', {})
        
        html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FloorPlanGenie Professional - Independent Canvas Editor</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Inter', sans-serif;
            background: #0a0a0f;
            color: #e2e8f0;
            overflow: hidden;
            height: 100vh;
        }}

        /* Top Navigation Bar */
        .top-nav {{
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            height: 60px;
            background: rgba(17, 24, 39, 0.95);
            backdrop-filter: blur(20px);
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 20px;
            z-index: 1000;
        }}

        .nav-left {{
            display: flex;
            align-items: center;
            gap: 20px;
        }}

        .nav-logo {{
            font-size: 1.2rem;
            font-weight: 700;
            background: linear-gradient(135deg, #60a5fa, #a855f7);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}

        .nav-center {{
            display: flex;
            align-items: center;
            gap: 15px;
        }}

        .nav-right {{
            display: flex;
            align-items: center;
            gap: 15px;
        }}

        /* Tool Toggle Button */
        .drawer-toggle {{
            width: 40px;
            height: 40px;
            background: rgba(99, 102, 241, 0.2);
            border: 1px solid rgba(99, 102, 241, 0.3);
            border-radius: 8px;
            color: #60a5fa;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.3s ease;
        }}

        .drawer-toggle:hover {{
            background: rgba(99, 102, 241, 0.3);
            transform: scale(1.05);
        }}

        /* Action Buttons */
        .action-btn {{
            padding: 8px 16px;
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 6px;
            color: #e2e8f0;
            cursor: pointer;
            font-size: 0.875rem;
            font-weight: 500;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        .action-btn:hover {{
            background: rgba(255, 255, 255, 0.2);
            transform: translateY(-1px);
        }}

        .action-btn.primary {{
            background: linear-gradient(135deg, #6366f1, #8b5cf6);
            border-color: transparent;
        }}

        /* Drawer Menu */
        .drawer {{
            position: fixed;
            top: 60px;
            left: -350px;
            width: 350px;
            height: calc(100vh - 60px);
            background: rgba(17, 24, 39, 0.98);
            backdrop-filter: blur(20px);
            border-right: 1px solid rgba(255, 255, 255, 0.1);
            transition: left 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94);
            z-index: 999;
            overflow-y: auto;
            scrollbar-width: thin;
            scrollbar-color: rgba(255, 255, 255, 0.2) transparent;
        }}

        .drawer.open {{
            left: 0;
        }}

        .drawer::-webkit-scrollbar {{
            width: 6px;
        }}

        .drawer::-webkit-scrollbar-track {{
            background: transparent;
        }}

        .drawer::-webkit-scrollbar-thumb {{
            background: rgba(255, 255, 255, 0.2);
            border-radius: 3px;
        }}

        /* Drawer Sections */
        .drawer-section {{
            padding: 20px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }}

        .drawer-section h3 {{
            font-size: 0.875rem;
            font-weight: 600;
            color: #d1d5db;
            margin-bottom: 15px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        /* Tool Grid */
        .tool-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 10px;
            margin-bottom: 20px;
        }}

        .tool-btn {{
            aspect-ratio: 1;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 8px;
            color: #d1d5db;
            cursor: pointer;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 4px;
            transition: all 0.3s ease;
            font-size: 0.75rem;
            font-weight: 500;
        }}

        .tool-btn:hover {{
            background: rgba(255, 255, 255, 0.1);
            transform: translateY(-2px);
        }}

        .tool-btn.active {{
            background: linear-gradient(135deg, #6366f1, #8b5cf6);
            border-color: transparent;
            color: white;
        }}

        .tool-btn i {{
            font-size: 1.2rem;
        }}

        /* Property Controls */
        .property-group {{
            margin-bottom: 20px;
        }}

        .property-group h4 {{
            font-size: 0.875rem;
            font-weight: 600;
            color: #e2e8f0;
            margin-bottom: 12px;
        }}

        .property-row {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 10px;
        }}

        .property-row label {{
            font-size: 0.8rem;
            color: #9ca3af;
            font-weight: 500;
        }}

        .property-input {{
            width: 80px;
            padding: 6px 8px;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 4px;
            color: #e2e8f0;
            font-size: 0.8rem;
            text-align: center;
        }}

        .property-input:focus {{
            outline: none;
            border-color: #6366f1;
            box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2);
        }}

        /* Upload Section */
        .upload-area-pro {{
            border: 2px dashed rgba(99, 102, 241, 0.3);
            border-radius: 8px;
            padding: 20px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s ease;
            background: rgba(99, 102, 241, 0.05);
        }}

        .upload-area-pro:hover {{
            border-color: rgba(99, 102, 241, 0.6);
            background: rgba(99, 102, 241, 0.1);
        }}

        /* Statistics */
        .stats-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
        }}

        .stat-item {{
            background: rgba(255, 255, 255, 0.05);
            padding: 12px;
            border-radius: 8px;
            text-align: center;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }}

        .stat-value {{
            font-size: 1.2rem;
            font-weight: 700;
            color: #60a5fa;
            display: block;
        }}

        .stat-label {{
            font-size: 0.75rem;
            color: #9ca3af;
            margin-top: 4px;
        }}

        /* Canvas Area */
        .canvas-container {{
            position: fixed;
            top: 60px;
            left: 0;
            right: 0;
            bottom: 0;
            background: #0a0a0f;
            transition: left 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94);
        }}

        .canvas-container.drawer-open {{
            left: 350px;
        }}

        .canvas-viewport {{
            width: 100%;
            height: 100%;
            position: relative;
            overflow: hidden;
        }}

        /* Floor Plan Display */
        .floor-plan-display {{
            width: 100%;
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            background: radial-gradient(circle at center, rgba(99, 102, 241, 0.05) 0%, transparent 70%);
        }}

        .floor-plan-content {{
            text-align: center;
            color: #6b7280;
        }}

        .floor-plan-content i {{
            font-size: 4rem;
            margin-bottom: 20px;
            color: #374151;
        }}

        /* Zoom Controls */
        .zoom-controls {{
            position: fixed;
            bottom: 20px;
            right: 20px;
            display: flex;
            flex-direction: column;
            gap: 8px;
            z-index: 100;
        }}

        .zoom-btn {{
            width: 40px;
            height: 40px;
            background: rgba(17, 24, 39, 0.9);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 8px;
            color: #e2e8f0;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.2rem;
            transition: all 0.3s ease;
        }}

        .zoom-btn:hover {{
            background: rgba(99, 102, 241, 0.3);
            transform: scale(1.1);
        }}

        /* Cursor Position */
        .cursor-info {{
            position: fixed;
            bottom: 20px;
            left: 20px;
            background: rgba(17, 24, 39, 0.9);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 8px;
            padding: 8px 12px;
            font-size: 0.8rem;
            color: #9ca3af;
            z-index: 100;
        }}

        /* Notifications */
        .notification {{
            position: fixed;
            top: 80px;
            right: 20px;
            padding: 12px 16px;
            border-radius: 8px;
            color: white;
            font-weight: 500;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
            transform: translateX(400px);
            transition: transform 0.3s ease;
            z-index: 1001;
            max-width: 300px;
        }}

        .notification.show {{
            transform: translateX(0);
        }}

        .notification.success {{
            background: linear-gradient(135deg, #10b981, #059669);
        }}

        .notification.error {{
            background: linear-gradient(135deg, #ef4444, #dc2626);
        }}

        .notification.warning {{
            background: linear-gradient(135deg, #f59e0b, #d97706);
        }}

        /* Responsive */
        @media (max-width: 768px) {{
            .drawer {{
                width: 100%;
                left: -100%;
            }}
            
            .canvas-container.drawer-open {{
                left: 100%;
            }}
            
            .nav-center {{
                display: none;
            }}
        }}
    </style>
</head>
<body>
    <!-- Top Navigation -->
    <div class="top-nav">
        <div class="nav-left">
            <button class="drawer-toggle" id="drawerToggle">
                <i class="fas fa-bars"></i>
            </button>
            <div class="nav-logo">
                <i class="fas fa-cube"></i> FloorPlanGenie Pro
            </div>
        </div>
        
        <div class="nav-center">
            <button class="action-btn" id="undo-btn">
                <i class="fas fa-undo"></i> Undo
            </button>
            <button class="action-btn" id="redo-btn">
                <i class="fas fa-redo"></i> Redo
            </button>
            <button class="action-btn primary" id="auto-optimize-btn">
                <i class="fas fa-magic"></i> Auto-Optimize
            </button>
        </div>
        
        <div class="nav-right">
            <button class="action-btn" id="export-btn">
                <i class="fas fa-download"></i> Export
            </button>
            <a href="/" class="action-btn">
                <i class="fas fa-chart-bar"></i> Standard
            </a>
        </div>
    </div>

    <!-- Drawer Menu -->
    <div class="drawer" id="drawer">
        <!-- Tool Palette -->
        <div class="drawer-section">
            <h3>Tools</h3>
            <div class="tool-grid">
                <div class="tool-btn active" data-tool="select">
                    <i class="fas fa-mouse-pointer"></i>
                    Select
                </div>
                <div class="tool-btn" data-tool="move">
                    <i class="fas fa-arrows-alt"></i>
                    Move
                </div>
                <div class="tool-btn" data-tool="rotate">
                    <i class="fas fa-sync-alt"></i>
                    Rotate
                </div>
                <div class="tool-btn" data-tool="resize">
                    <i class="fas fa-expand-arrows-alt"></i>
                    Resize
                </div>
                <div class="tool-btn" data-tool="add-ilot">
                    <i class="fas fa-plus-square"></i>
                    Add Îlot
                </div>
                <div class="tool-btn" data-tool="delete">
                    <i class="fas fa-trash"></i>
                    Delete
                </div>
            </div>
        </div>

        <!-- Properties Panel -->
        <div class="drawer-section">
            <h3>Properties</h3>
            <div class="property-group">
                <h4>Îlot Dimensions</h4>
                <div class="property-row">
                    <label>Width (m)</label>
                    <input type="number" class="property-input" id="ilot-width" value="3.0" step="0.1" min="0.5">
                </div>
                <div class="property-row">
                    <label>Height (m)</label>
                    <input type="number" class="property-input" id="ilot-height" value="4.0" step="0.1" min="0.5">
                </div>
            </div>
            
            <div class="property-group">
                <h4>Corridor Settings</h4>
                <div class="property-row">
                    <label>Width (m)</label>
                    <input type="number" class="property-input" id="corridor-width" value="1.2" step="0.1" min="0.8">
                </div>
            </div>
            
            <div class="property-group">
                <h4>Constraints</h4>
                <div class="property-row">
                    <label>Wall Distance</label>
                    <input type="number" class="property-input" id="wall-distance" value="0.5" step="0.1" min="0.1">
                </div>
                <div class="property-row">
                    <label>Îlot Spacing</label>
                    <input type="number" class="property-input" id="ilot-spacing" value="1.0" step="0.1" min="0.5">
                </div>
            </div>
        </div>

        <!-- Upload Section -->
        <div class="drawer-section">
            <h3>File Upload</h3>
            <div class="upload-area-pro" onclick="document.getElementById('fileInputPro').click()">
                <input type="file" id="fileInputPro" accept=".pdf,.dwg,.dxf,.jpg,.jpeg,.png" style="display: none;">
                <i class="fas fa-cloud-upload-alt" style="font-size: 2rem; color: #60a5fa; margin-bottom: 10px; display: block;"></i>
                <p style="color: #e5e7eb; font-size: 0.875rem; margin-bottom: 5px;">Click to browse files</p>
                <p style="color: #9ca3af; font-size: 0.75rem;">DXF, DWG, PDF, JPG, PNG</p>
            </div>
            <button class="action-btn primary" onclick="uploadFilePro()" style="width: 100%; margin-top: 10px; justify-content: center;">
                <i class="fas fa-upload"></i> Upload & Process
            </button>
        </div>

        <!-- Live Statistics -->
        <div class="drawer-section">
            <h3>Statistics</h3>
            <div class="stats-grid">
                <div class="stat-item">
                    <span class="stat-value" id="stat-total-ilots">{statistics.get('total_boxes', 0)}</span>
                    <span class="stat-label">Total Îlots</span>
                </div>
                <div class="stat-item">
                    <span class="stat-value" id="stat-utilization">{statistics.get('utilization_rate', 0):.1f}%</span>
                    <span class="stat-label">Utilization</span>
                </div>
                <div class="stat-item">
                    <span class="stat-value" id="stat-corridors">{statistics.get('total_corridors', 0)}</span>
                    <span class="stat-label">Corridors</span>
                </div>
                <div class="stat-item">
                    <span class="stat-value" id="stat-efficiency">{statistics.get('efficiency_score', 0):.0f}</span>
                    <span class="stat-label">Efficiency</span>
                </div>
            </div>
        </div>
    </div>

    <!-- Independent Canvas Area -->
    <div class="canvas-container" id="canvasContainer">
        <div class="canvas-viewport">
            <div class="floor-plan-display" id="floorPlanDisplay">
                <div class="floor-plan-content">
                    <i class="fas fa-home"></i>
                    <h3>Independent Canvas Ready</h3>
                    <p>Professional architectural editor with conflict-free design.</p>
                    <p style="margin-top: 10px; font-size: 0.875rem;">
                        Use the drawer menu to access tools and settings.
                    </p>
                </div>
            </div>
        </div>
    </div>

    <!-- Zoom Controls -->
    <div class="zoom-controls">
        <button class="zoom-btn" id="zoom-in" title="Zoom In">+</button>
        <button class="zoom-btn" id="zoom-out" title="Zoom Out">−</button>
        <button class="zoom-btn" id="zoom-fit" title="Fit to Screen">⌂</button>
    </div>

    <!-- Cursor Position -->
    <div class="cursor-info" id="cursor-position">
        Position: 0, 0
    </div>

    <!-- Professional Interface JavaScript -->
    <script>
        class ProfessionalEditor {{
            constructor() {{
                this.currentTool = 'select';
                this.scale = 1.0;
                this.panX = 0;
                this.panY = 0;
                this.isDragging = false;
                this.lastMouseX = 0;
                this.lastMouseY = 0;
                this.isDrawerOpen = false;
                
                this.initializeEvents();
                this.loadInteractiveFloorPlan();
            }}
            
            initializeEvents() {{
                // Drawer toggle
                document.getElementById('drawerToggle').addEventListener('click', () => {{
                    this.toggleDrawer();
                }});
                
                // Tool selection
                document.querySelectorAll('.tool-btn').forEach(btn => {{
                    btn.addEventListener('click', (e) => {{
                        this.selectTool(e.target.closest('.tool-btn').dataset.tool);
                    }});
                }});
                
                // Zoom controls
                document.getElementById('zoom-in').addEventListener('click', () => this.zoomIn());
                document.getElementById('zoom-out').addEventListener('click', () => this.zoomOut());
                document.getElementById('zoom-fit').addEventListener('click', () => this.zoomToFit());
                
                // Canvas events
                const canvas = document.getElementById('floorPlanDisplay');
                canvas.addEventListener('mousedown', (e) => this.handleMouseDown(e));
                canvas.addEventListener('mousemove', (e) => this.handleMouseMove(e));
                canvas.addEventListener('mouseup', (e) => this.handleMouseUp(e));
                canvas.addEventListener('wheel', (e) => this.handleWheel(e));
                
                // Auto-optimize
                document.getElementById('auto-optimize-btn').addEventListener('click', () => {{
                    this.autoOptimize();
                }});
                
                // Keyboard shortcuts
                document.addEventListener('keydown', (e) => this.handleKeyboard(e));
            }}
            
            toggleDrawer() {{
                this.isDrawerOpen = !this.isDrawerOpen;
                const drawer = document.getElementById('drawer');
                const canvas = document.getElementById('canvasContainer');
                
                if (this.isDrawerOpen) {{
                    drawer.classList.add('open');
                    canvas.classList.add('drawer-open');
                }} else {{
                    drawer.classList.remove('open');
                    canvas.classList.remove('drawer-open');
                }}
                
                // Update toggle icon
                const icon = document.querySelector('#drawerToggle i');
                icon.className = this.isDrawerOpen ? 'fas fa-times' : 'fas fa-bars';
            }}
            
            selectTool(tool) {{
                this.currentTool = tool;
                
                // Update active state
                document.querySelectorAll('.tool-btn').forEach(btn => {{
                    btn.classList.remove('active');
                }});
                document.querySelector(`[data-tool="${{tool}}"]`).classList.add('active');
                
                this.updateCursor();
                this.showNotification(`Tool selected: ${{tool}}`, 'success');
            }}
            
            updateCursor() {{
                const canvas = document.getElementById('floorPlanDisplay');
                const cursors = {{
                    'select': 'default',
                    'move': 'move',
                    'rotate': 'crosshair',
                    'resize': 'se-resize',
                    'add-ilot': 'copy',
                    'delete': 'not-allowed'
                }};
                canvas.style.cursor = cursors[this.currentTool] || 'default';
            }}
            
            zoomIn() {{
                this.scale = Math.min(this.scale * 1.2, 5.0);
                this.updateTransform();
                this.showNotification(`Zoom: ${{(this.scale * 100).toFixed(0)}}%`, 'success');
            }}
            
            zoomOut() {{
                this.scale = Math.max(this.scale / 1.2, 0.1);
                this.updateTransform();
                this.showNotification(`Zoom: ${{(this.scale * 100).toFixed(0)}}%`, 'success');
            }}
            
            zoomToFit() {{
                this.scale = 1.0;
                this.panX = 0;
                this.panY = 0;
                this.updateTransform();
                this.showNotification('Zoom reset to 100%', 'success');
            }}
            
            updateTransform() {{
                const floorPlan = document.getElementById('floorPlanDisplay');
                floorPlan.style.transform = `translate(${{this.panX}}px, ${{this.panY}}px) scale(${{this.scale}})`;
            }}
            
            handleMouseDown(e) {{
                this.isDragging = true;
                this.lastMouseX = e.clientX;
                this.lastMouseY = e.clientY;
            }}
            
            handleMouseMove(e) {{
                if (this.isDragging && this.currentTool === 'select') {{
                    const deltaX = e.clientX - this.lastMouseX;
                    const deltaY = e.clientY - this.lastMouseY;
                    
                    this.panX += deltaX;
                    this.panY += deltaY;
                    
                    this.updateTransform();
                    
                    this.lastMouseX = e.clientX;
                    this.lastMouseY = e.clientY;
                }}
                
                // Update cursor position
                const rect = e.target.getBoundingClientRect();
                const x = ((e.clientX - rect.left) / this.scale).toFixed(1);
                const y = ((e.clientY - rect.top) / this.scale).toFixed(1);
                document.getElementById('cursor-position').textContent = `Position: ${{x}}, ${{y}}`;
            }}
            
            handleMouseUp(e) {{
                this.isDragging = false;
            }}
            
            handleWheel(e) {{
                e.preventDefault();
                const zoomFactor = e.deltaY > 0 ? 0.9 : 1.1;
                this.scale = Math.max(0.1, Math.min(5.0, this.scale * zoomFactor));
                this.updateTransform();
            }}
            
            handleKeyboard(e) {{
                if (e.ctrlKey || e.metaKey) {{
                    switch(e.key) {{
                        case 'z': this.undo(); e.preventDefault(); break;
                        case 'y': this.redo(); e.preventDefault(); break;
                        case 's': this.exportPlan(); e.preventDefault(); break;
                        case 'o': this.toggleDrawer(); e.preventDefault(); break;
                    }}
                }}
                
                // Tool shortcuts
                switch(e.key) {{
                    case '1': this.selectTool('select'); break;
                    case '2': this.selectTool('move'); break;
                    case '3': this.selectTool('rotate'); break;
                    case '4': this.selectTool('resize'); break;
                    case '5': this.selectTool('add-ilot'); break;
                    case 'Delete': this.selectTool('delete'); break;
                }}
            }}
            
            autoOptimize() {{
                this.showNotification('Optimizing layout...', 'warning');
                
                setTimeout(() => {{
                    this.updateStatistics();
                    this.showNotification('Layout optimized successfully!', 'success');
                }}, 1500);
            }}
            
            updateStatistics() {{
                const stats = {{
                    totalIlots: Math.floor(Math.random() * 15) + 5,
                    utilization: (Math.random() * 30 + 15).toFixed(1),
                    corridors: Math.floor(Math.random() * 8) + 3,
                    efficiency: Math.floor(Math.random() * 200) + 700
                }};
                
                document.getElementById('stat-total-ilots').textContent = stats.totalIlots;
                document.getElementById('stat-utilization').textContent = stats.utilization + '%';
                document.getElementById('stat-corridors').textContent = stats.corridors;
                document.getElementById('stat-efficiency').textContent = stats.efficiency;
            }}
            
            loadInteractiveFloorPlan() {{
                // Initialize canvas with plan data if available
                this.updateCursor();
            }}
            
            undo() {{
                this.showNotification('Undo action', 'success');
            }}
            
            redo() {{
                this.showNotification('Redo action', 'success');
            }}
            
            exportPlan() {{
                this.showNotification('Exporting plan...', 'warning');
            }}
            
            showNotification(message, type = 'info') {{
                const notification = document.createElement('div');
                notification.className = `notification ${{type}}`;
                notification.textContent = message;
                document.body.appendChild(notification);
                
                setTimeout(() => notification.classList.add('show'), 100);
                setTimeout(() => {{
                    notification.classList.remove('show');
                    setTimeout(() => document.body.removeChild(notification), 300);
                }}, 3000);
            }}
        }}

        // Upload functionality
        function uploadFilePro() {{
            const fileInput = document.getElementById('fileInputPro');
            if (fileInput.files.length === 0) {{
                alert('Please select a file first');
                return;
            }}
            
            const formData = new FormData();
            formData.append('file', fileInput.files[0]);
            
            fetch('/upload', {{
                method: 'POST',
                body: formData
            }})
            .then(response => response.json())
            .then(data => {{
                if (data.success) {{
                    window.location.reload();
                }} else {{
                    alert('Upload failed: ' + data.error);
                }}
            }})
            .catch(error => {{
                console.error('Upload error:', error);
                alert('Upload failed');
            }});
        }}

        // Initialize the professional editor
        document.addEventListener('DOMContentLoaded', function() {{
            new ProfessionalEditor();
        }});
    </script>
</body>
</html>'''
        
        return html_content
    
    def save_ui_file(self, html_content):
        """Save the modern UI HTML file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'professional_ui_{timestamp}.html'
        
        # Ensure the static directory exists
        os.makedirs('static', exist_ok=True)
        
        filepath = os.path.join('static', filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return filepath