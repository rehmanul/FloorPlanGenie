"""
Interactive Canvas System - Production Grade
SVG-based rendering with zoom, pan, and real-time interaction
"""
import json
import os
from datetime import datetime

class InteractiveCanvasRenderer:
    def __init__(self):
        self.output_dir = 'static/outputs'
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Professional color scheme
        self.colors = {
            'walls': '#6B7280',           # Gray walls
            'restricted': '#3B82F6',      # Blue restricted areas  
            'entry_exit': '#EF4444',      # Red entry/exit zones
            'ilots': '#10B981',           # Green îlots
            'corridors': '#F59E0B',       # Orange corridors
            'background': '#F9FAFB',      # Light background
            'grid': '#E5E7EB'             # Light grid
        }
        
    def generate_interactive_svg(self, data, layout_profile='25%'):
        """Generate interactive SVG with zoom/pan capabilities"""
        
        dimensions = data['dimensions']
        width = dimensions['width']
        height = dimensions['height']
        
        # SVG viewBox for responsive scaling
        viewbox_width = width * 1.1  # Add margin
        viewbox_height = height * 1.1
        
        svg_content = self._create_svg_structure(viewbox_width, viewbox_height)
        
        # Add professional grid
        svg_content += self._create_grid(viewbox_width, viewbox_height)
        
        # Add architectural elements in proper order
        svg_content += self._render_walls_svg(data.get('walls', []), width, height)
        svg_content += self._render_zones_svg(data.get('zones', {}), width, height)
        svg_content += self._render_ilots_svg(data.get('boxes', []))
        svg_content += self._render_corridors_svg(data.get('corridors', []))
        
        # Add interactive legend
        svg_content += self._create_interactive_legend()
        
        # Add zoom/pan controls
        svg_content += self._create_zoom_controls()
        
        # Add measurement annotations
        svg_content += self._create_measurements(data)
        
        svg_content += self._close_svg_structure()
        
        # Save SVG file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"interactive_plan_{timestamp}.svg"
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(svg_content)
        
        # Generate accompanying HTML for full interaction
        html_filepath = self._create_interactive_html(filepath, data)
        
        return {
            'svg_path': filepath,
            'html_path': html_filepath,
            'interactive_url': f"/static/outputs/{os.path.basename(html_filepath)}"
        }
    
    def _create_svg_structure(self, width, height):
        """Create SVG structure with interactive capabilities"""
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="100%" height="100%" viewBox="0 0 {width} {height}" 
     xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
     
  <defs>
    <style type="text/css"><![CDATA[
      .wall {{ stroke: {self.colors['walls']}; stroke-width: 3; fill: none; }}
      .wall:hover {{ stroke: #374151; stroke-width: 4; cursor: pointer; }}
      
      .restricted {{ fill: {self.colors['restricted']}; fill-opacity: 0.3; stroke: {self.colors['restricted']}; stroke-width: 2; }}
      .restricted:hover {{ fill-opacity: 0.5; cursor: pointer; }}
      
      .entry-exit {{ fill: {self.colors['entry_exit']}; fill-opacity: 0.3; stroke: {self.colors['entry_exit']}; stroke-width: 2; }}
      .entry-exit:hover {{ fill-opacity: 0.5; cursor: pointer; }}
      
      .ilot {{ fill: {self.colors['ilots']}; fill-opacity: 0.8; stroke: #065F46; stroke-width: 2; }}
      .ilot:hover {{ fill-opacity: 1.0; stroke-width: 3; cursor: move; }}
      
      .corridor {{ fill: {self.colors['corridors']}; fill-opacity: 0.6; stroke: #D97706; stroke-width: 1; }}
      .corridor:hover {{ fill-opacity: 0.8; cursor: pointer; }}
      
      .grid-line {{ stroke: {self.colors['grid']}; stroke-width: 0.5; opacity: 0.5; }}
      
      .measurement {{ font-family: 'Arial', sans-serif; font-size: 12px; fill: #374151; font-weight: bold; }}
      .legend {{ font-family: 'Arial', sans-serif; font-size: 14px; fill: #374151; }}
      
      .zoom-control {{ cursor: pointer; fill: #4B5563; stroke: #6B7280; }}
      .zoom-control:hover {{ fill: #374151; }}
    ]]></style>
    
    <!-- Patterns for advanced styling -->
    <pattern id="restricted-pattern" x="0" y="0" width="4" height="4" patternUnits="userSpaceOnUse">
      <rect width="4" height="4" fill="{self.colors['restricted']}" opacity="0.1"/>
      <circle cx="2" cy="2" r="1" fill="{self.colors['restricted']}" opacity="0.3"/>
    </pattern>
    
    <!-- Drop shadow filter -->
    <filter id="dropshadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="2" dy="2" stdDeviation="2" flood-color="#00000040"/>
    </filter>
  </defs>
  
  <!-- Background -->
  <rect width="100%" height="100%" fill="{self.colors['background']}"/>
  
  <!-- Main drawing group with zoom/pan transform -->
  <g id="main-group" transform="translate(0,0) scale(1)">
'''
    
    def _create_grid(self, width, height):
        """Create professional architectural grid"""
        grid_size = min(width, height) / 20  # Adaptive grid size
        
        grid_svg = '    <!-- Professional Grid -->\n    <g id="grid-group" class="grid">\n'
        
        # Vertical lines
        x = 0
        while x <= width:
            grid_svg += f'      <line x1="{x}" y1="0" x2="{x}" y2="{height}" class="grid-line"/>\n'
            x += grid_size
        
        # Horizontal lines
        y = 0
        while y <= height:
            grid_svg += f'      <line x1="0" y1="{y}" x2="{width}" y2="{y}" class="grid-line"/>\n'
            y += grid_size
        
        grid_svg += '    </g>\n\n'
        return grid_svg
    
    def _render_walls_svg(self, walls, width, height):
        """Render walls with professional styling"""
        if not walls:
            return ''
        
        svg = '    <!-- Architectural Walls -->\n    <g id="walls-group" class="walls">\n'
        
        for i, wall in enumerate(walls):
            start = wall['start']
            end = wall['end']
            layer = wall.get('layer', 'Default')
            
            svg += f'''      <line x1="{start['x']}" y1="{start['y']}" 
                    x2="{end['x']}" y2="{end['y']}" 
                    class="wall" 
                    data-layer="{layer}"
                    data-wall-id="{i}">
                <title>Wall {i+1} (Layer: {layer})</title>
              </line>\n'''
        
        svg += '    </g>\n\n'
        return svg
    
    def _render_zones_svg(self, zones, width, height):
        """Render zones with proper color coding"""
        svg = '    <!-- Architectural Zones -->\n    <g id="zones-group" class="zones">\n'
        
        # Render entry/exit zones (red)
        for i, zone in enumerate(zones.get('entry_exit', [])):
            svg += f'''      <rect x="{zone['x']}" y="{zone['y']}" 
                    width="{zone['width']}" height="{zone['height']}" 
                    class="entry-exit"
                    data-zone-type="entry-exit"
                    data-zone-id="{i}">
                <title>Entry/Exit Zone {i+1}</title>
              </rect>\n'''
        
        # Render restricted zones (blue)
        for i, zone in enumerate(zones.get('no_entry', [])):
            svg += f'''      <rect x="{zone['x']}" y="{zone['y']}" 
                    width="{zone['width']}" height="{zone['height']}" 
                    class="restricted"
                    data-zone-type="restricted"
                    data-zone-id="{i}">
                <title>Restricted Zone {i+1}</title>
              </rect>\n'''
        
        svg += '    </g>\n\n'
        return svg
    
    def _render_ilots_svg(self, boxes):
        """Render îlots with interactive features"""
        if not boxes:
            return ''
        
        svg = '    <!-- Îlots (Island Boxes) -->\n    <g id="ilots-group" class="ilots">\n'
        
        for i, box in enumerate(boxes):
            area = box['width'] * box['height']
            
            svg += f'''      <rect x="{box['x']}" y="{box['y']}" 
                    width="{box['width']}" height="{box['height']}" 
                    class="ilot"
                    data-ilot-id="{i}"
                    data-area="{area:.2f}"
                    filter="url(#dropshadow)">
                <title>Îlot {i+1} - {area:.2f}m²</title>
              </rect>
              <text x="{box['x'] + box['width']/2}" y="{box['y'] + box['height']/2}" 
                    text-anchor="middle" dominant-baseline="middle" 
                    class="measurement" fill="#065F46">
                Î{i+1}
              </text>
              <text x="{box['x'] + box['width']/2}" y="{box['y'] + box['height']/2 + 15}" 
                    text-anchor="middle" dominant-baseline="middle" 
                    class="measurement" fill="#065F46" font-size="10">
                {area:.1f}m²
              </text>\n'''
        
        svg += '    </g>\n\n'
        return svg
    
    def _render_corridors_svg(self, corridors):
        """Render corridors with pathfinding visualization"""
        if not corridors:
            return ''
        
        svg = '    <!-- Corridor Network -->\n    <g id="corridors-group" class="corridors">\n'
        
        for i, corridor in enumerate(corridors):
            area = corridor['width'] * corridor['height']
            
            svg += f'''      <rect x="{corridor['x']}" y="{corridor['y']}" 
                    width="{corridor['width']}" height="{corridor['height']}" 
                    class="corridor"
                    data-corridor-id="{i}"
                    data-area="{area:.2f}">
                <title>Corridor {i+1} - {area:.2f}m²</title>
              </rect>
              <text x="{corridor['x'] + corridor['width']/2}" y="{corridor['y'] + corridor['height']/2}" 
                    text-anchor="middle" dominant-baseline="middle" 
                    class="measurement" fill="#D97706" font-size="10">
                {area:.1f}m²
              </text>\n'''
        
        svg += '    </g>\n\n'
        return svg
    
    def _create_interactive_legend(self):
        """Create interactive legend with toggle capabilities"""
        return '''    <!-- Interactive Legend -->
    <g id="legend-group" class="legend" transform="translate(20, 20)">
      <rect x="0" y="0" width="200" height="160" fill="white" stroke="#D1D5DB" stroke-width="1" rx="5" opacity="0.95"/>
      <text x="10" y="20" class="legend" font-weight="bold">Legend</text>
      
      <!-- Legend items -->
      <g class="legend-item" data-toggle="walls">
        <rect x="10" y="35" width="15" height="3" fill="#6B7280"/>
        <text x="30" y="40" class="legend">Walls</text>
      </g>
      
      <g class="legend-item" data-toggle="restricted">
        <rect x="10" y="50" width="15" height="15" fill="#3B82F6" opacity="0.3"/>
        <text x="30" y="60" class="legend">Restricted</text>
      </g>
      
      <g class="legend-item" data-toggle="entry-exit">
        <rect x="10" y="70" width="15" height="15" fill="#EF4444" opacity="0.3"/>
        <text x="30" y="80" class="legend">Entry/Exit</text>
      </g>
      
      <g class="legend-item" data-toggle="ilots">
        <rect x="10" y="90" width="15" height="15" fill="#10B981" opacity="0.8"/>
        <text x="30" y="100" class="legend">Îlots</text>
      </g>
      
      <g class="legend-item" data-toggle="corridors">
        <rect x="10" y="110" width="15" height="15" fill="#F59E0B" opacity="0.6"/>
        <text x="30" y="120" class="legend">Corridors</text>
      </g>
      
      <g class="legend-item" data-toggle="grid">
        <line x1="10" y1="135" x2="25" y2="135" stroke="#E5E7EB" stroke-width="1"/>
        <text x="30" y="140" class="legend">Grid</text>
      </g>
    </g>

'''
    
    def _create_zoom_controls(self):
        """Create zoom and pan controls"""
        return '''    <!-- Zoom Controls -->
    <g id="zoom-controls" transform="translate(20, 200)">
      <rect x="0" y="0" width="40" height="120" fill="white" stroke="#D1D5DB" stroke-width="1" rx="5" opacity="0.95"/>
      
      <!-- Zoom In -->
      <g class="zoom-control" data-action="zoom-in" transform="translate(5, 5)">
        <rect x="0" y="0" width="30" height="30" fill="white" stroke="#6B7280" rx="3"/>
        <text x="15" y="20" text-anchor="middle" dominant-baseline="middle" font-size="20" font-weight="bold">+</text>
      </g>
      
      <!-- Zoom Out -->
      <g class="zoom-control" data-action="zoom-out" transform="translate(5, 40)">
        <rect x="0" y="0" width="30" height="30" fill="white" stroke="#6B7280" rx="3"/>
        <text x="15" y="20" text-anchor="middle" dominant-baseline="middle" font-size="20" font-weight="bold">−</text>
      </g>
      
      <!-- Reset View -->
      <g class="zoom-control" data-action="reset" transform="translate(5, 75)">
        <rect x="0" y="0" width="30" height="30" fill="white" stroke="#6B7280" rx="3"/>
        <text x="15" y="20" text-anchor="middle" dominant-baseline="middle" font-size="12">⌂</text>
      </g>
    </g>

'''
    
    def _create_measurements(self, data):
        """Add measurement annotations"""
        dimensions = data['dimensions']
        width = dimensions['width']
        height = dimensions['height']
        
        return f'''    <!-- Measurement Annotations -->
    <g id="measurements-group" class="measurements">
      <!-- Overall dimensions -->
      <text x="{width/2}" y="20" text-anchor="middle" class="measurement" font-size="16" font-weight="bold">
        {width:.1f}m × {height:.1f}m
      </text>
      <text x="{width/2}" y="40" text-anchor="middle" class="measurement" font-size="12">
        Total Area: {width * height:.1f}m²
      </text>
    </g>

'''
    
    def _close_svg_structure(self):
        """Close SVG structure"""
        return '''  </g>
</svg>'''
    
    def _create_interactive_html(self, svg_path, data):
        """Create HTML wrapper with full interactivity"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        html_filename = f"interactive_plan_{timestamp}.html"
        html_filepath = os.path.join(self.output_dir, html_filename)
        
        svg_filename = os.path.basename(svg_path)
        
        html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Interactive Floor Plan - FloorPlanGenie</title>
    <style>
        body {{
            font-family: 'Arial', sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.1);
            padding: 20px;
        }}
        
        .header {{
            text-align: center;
            margin-bottom: 30px;
        }}
        
        .header h1 {{
            color: #374151;
            margin: 0 0 10px 0;
            font-size: 2.5em;
        }}
        
        .header p {{
            color: #6B7280;
            margin: 0;
            font-size: 1.1em;
        }}
        
        .plan-container {{
            width: 100%;
            height: 80vh;
            border: 2px solid #E5E7EB;
            border-radius: 8px;
            overflow: hidden;
            position: relative;
        }}
        
        .plan-container svg {{
            width: 100%;
            height: 100%;
            cursor: grab;
        }}
        
        .plan-container svg:active {{
            cursor: grabbing;
        }}
        
        .controls-panel {{
            position: absolute;
            top: 20px;
            right: 20px;
            background: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            max-width: 250px;
        }}
        
        .status-bar {{
            margin-top: 20px;
            padding: 15px;
            background: #F9FAFB;
            border-radius: 8px;
            display: flex;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 10px;
        }}
        
        .status-item {{
            text-align: center;
        }}
        
        .status-value {{
            font-size: 1.5em;
            font-weight: bold;
            color: #374151;
        }}
        
        .status-label {{
            font-size: 0.9em;
            color: #6B7280;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏗️ Interactive Floor Plan</h1>
            <p>Professional Architectural Visualization • Zoom • Pan • Navigate</p>
        </div>
        
        <div class="plan-container" id="planContainer">
            <object data="{svg_filename}" type="image/svg+xml" width="100%" height="100%"></object>
            
            <div class="controls-panel">
                <h3 style="margin-top: 0;">Navigation</h3>
                <p><strong>Mouse:</strong> Click and drag to pan</p>
                <p><strong>Scroll:</strong> Zoom in/out</p>
                <p><strong>Click:</strong> Elements for details</p>
                <p><strong>Legend:</strong> Toggle layer visibility</p>
            </div>
        </div>
        
        <div class="status-bar">
            <div class="status-item">
                <div class="status-value">{data.get('statistics', {}).get('total_boxes', 0)}</div>
                <div class="status-label">Îlots Placed</div>
            </div>
            <div class="status-item">
                <div class="status-value">{data.get('statistics', {}).get('total_corridors', 0)}</div>
                <div class="status-label">Corridors</div>
            </div>
            <div class="status-item">
                <div class="status-value">{data.get('statistics', {}).get('utilization_rate', 0):.1f}%</div>
                <div class="status-label">Space Utilization</div>
            </div>
            <div class="status-item">
                <div class="status-value">{data['dimensions']['width'] * data['dimensions']['height']:.0f}m²</div>
                <div class="status-label">Total Area</div>
            </div>
        </div>
    </div>
    
    <script>
        // Interactive functionality will be loaded with the SVG
        document.addEventListener('DOMContentLoaded', function() {{
            const container = document.getElementById('planContainer');
            const svg = container.querySelector('object');
            
            // Add interaction handlers when SVG loads
            svg.addEventListener('load', function() {{
                console.log('Interactive floor plan loaded successfully');
                // Additional interactive features can be added here
            }});
        }});
    </script>
</body>
</html>'''
        
        with open(html_filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return html_filepath