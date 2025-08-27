
import json
import os
import uuid
from typing import Dict, List, Any, Optional, Tuple
import xml.etree.ElementTree as ET
from xml.dom import minidom
import base64
import io
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import logging

class InteractiveCanvasRenderer:
    """Production-grade interactive canvas renderer with SVG and Canvas support"""
    
    def __init__(self):
        self.color_scheme = {
            'walls': {'color': '#6B7280', 'thickness': 3, 'opacity': 1.0},
            'restricted_zones': {'color': '#3B82F6', 'opacity': 0.3, 'stroke': '#1D4ED8'},
            'entrance_zones': {'color': '#EF4444', 'opacity': 0.4, 'stroke': '#DC2626'},
            'doors': {'color': '#EF4444', 'thickness': 2, 'swing': True},
            'windows': {'color': '#60A5FA', 'thickness': 1},
            'ilots': {
                'small': {'fill': '#10B981', 'stroke': '#047857', 'stroke_width': 2},
                'medium': {'fill': '#059669', 'stroke': '#065F46', 'stroke_width': 2},
                'large': {'fill': '#047857', 'stroke': '#064E3B', 'stroke_width': 2}
            },
            'corridors': {'color': '#EC4899', 'opacity': 0.6, 'stroke': '#BE185D'},
            'labels': {'color': '#374151', 'font_family': 'Inter', 'font_size': 12},
            'background': '#F9FAFB',
            'grid': {'color': '#E5E7EB', 'opacity': 0.5}
        }
        
        self.canvas_config = {
            'width': 1200,
            'height': 800,
            'padding': 50,
            'zoom_levels': [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 3.0, 4.0],
            'grid_size': 20
        }
    
    def generate_interactive_svg(self, plan_data: Dict[str, Any], 
                               optimization_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate interactive SVG with professional architectural styling"""
        try:
            # Calculate drawing bounds
            bounds = self._calculate_drawing_bounds(plan_data, optimization_data)
            
            # Create SVG root element
            svg = ET.Element('svg')
            svg.set('xmlns', 'http://www.w3.org/2000/svg')
            svg.set('xmlns:xlink', 'http://www.w3.org/1999/xlink')
            svg.set('viewBox', f"0 0 {self.canvas_config['width']} {self.canvas_config['height']}")
            svg.set('width', str(self.canvas_config['width']))
            svg.set('height', str(self.canvas_config['height']))
            
            # Add CSS styles
            self._add_svg_styles(svg)
            
            # Add background and grid
            self._add_background_and_grid(svg, bounds)
            
            # Add legend
            self._add_interactive_legend(svg)
            
            # Create main drawing group
            main_group = ET.SubElement(svg, 'g')
            main_group.set('id', 'main-drawing')
            main_group.set('transform', self._calculate_transform(bounds))
            
            # Render architectural elements in correct order
            self._render_walls(main_group, plan_data.get('walls', []))
            self._render_zones(main_group, plan_data.get('zones', []))
            self._render_doors_and_windows(main_group, plan_data.get('doors', []), plan_data.get('windows', []))
            
            # Render optimization results if provided
            if optimization_data:
                self._render_ilots(main_group, optimization_data.get('ilots', optimization_data.get('boxes', [])))
                self._render_corridors(main_group, optimization_data.get('corridors', []))
            
            # Add interactive controls
            self._add_interactive_controls(svg)
            
            # Add JavaScript for interactivity
            self._add_svg_javascript(svg)
            
            # Convert to string and save
            svg_string = self._prettify_svg(svg)
            svg_path = self._save_svg(svg_string)
            
            return {
                'success': True,
                'svg_path': svg_path,
                'svg_string': svg_string,
                'interactive': True,
                'bounds': bounds
            }
            
        except Exception as e:
            logging.error(f"Error generating interactive SVG: {e}")
            raise
    
    def generate_canvas_html(self, plan_data: Dict[str, Any], 
                           optimization_data: Optional[Dict[str, Any]] = None) -> str:
        """Generate HTML with Canvas-based interactive renderer"""
        bounds = self._calculate_drawing_bounds(plan_data, optimization_data)
        
        html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FloorPlanGenie - Interactive Canvas</title>
    <style>
        {self._get_canvas_css()}
    </style>
</head>
<body>
    <div class="canvas-container">
        <canvas id="floorPlanCanvas" width="{self.canvas_config['width']}" height="{self.canvas_config['height']}"></canvas>
        <div class="canvas-controls">
            {self._get_canvas_controls_html()}
        </div>
        <div class="canvas-legend">
            {self._get_canvas_legend_html()}
        </div>
    </div>
    
    <script>
        {self._get_canvas_javascript(plan_data, optimization_data, bounds)}
    </script>
</body>
</html>
"""
        return html_template
    
    def _calculate_drawing_bounds(self, plan_data: Dict[str, Any], 
                                optimization_data: Optional[Dict[str, Any]] = None) -> Dict[str, float]:
        """Calculate optimal drawing bounds for all elements"""
        min_x, min_y = float('inf'), float('inf')
        max_x, max_y = float('-inf'), float('-inf')
        
        # Check plan dimensions
        dims = plan_data.get('dimensions', {})
        if dims:
            min_x = min(min_x, dims.get('min_x', 0))
            min_y = min(min_y, dims.get('min_y', 0))
            max_x = max(max_x, dims.get('max_x', dims.get('width', 50)))
            max_y = max(max_y, dims.get('max_y', dims.get('height', 40)))
        
        # Check walls
        for wall in plan_data.get('walls', []):
            if wall.get('type') == 'line':
                start, end = wall['start'], wall['end']
                min_x = min(min_x, start['x'], end['x'])
                min_y = min(min_y, start['y'], end['y'])
                max_x = max(max_x, start['x'], end['x'])
                max_y = max(max_y, start['y'], end['y'])
        
        # Check optimization elements
        if optimization_data:
            for ilot in optimization_data.get('ilots', optimization_data.get('boxes', [])):
                x, y = ilot['x'], ilot['y']
                w, h = ilot['width'], ilot['height']
                min_x = min(min_x, x - w/2)
                min_y = min(min_y, y - h/2)
                max_x = max(max_x, x + w/2)
                max_y = max(max_y, y + h/2)
        
        # Add padding
        padding = 5
        return {
            'min_x': min_x - padding,
            'min_y': min_y - padding,
            'max_x': max_x + padding,
            'max_y': max_y + padding,
            'width': max_x - min_x + 2 * padding,
            'height': max_y - min_y + 2 * padding
        }
    
    def _add_svg_styles(self, svg: ET.Element):
        """Add comprehensive CSS styles to SVG"""
        style_content = """
        .wall { stroke: #6B7280; stroke-width: 3; stroke-linecap: round; }
        .restricted-zone { fill: #3B82F6; fill-opacity: 0.3; stroke: #1D4ED8; stroke-width: 1; }
        .entrance-zone { fill: #EF4444; fill-opacity: 0.4; stroke: #DC2626; stroke-width: 1; }
        .door { stroke: #EF4444; stroke-width: 2; stroke-linecap: round; }
        .window { stroke: #60A5FA; stroke-width: 1; stroke-linecap: round; }
        .ilot-small { fill: #10B981; stroke: #047857; stroke-width: 2; }
        .ilot-medium { fill: #059669; stroke: #065F46; stroke-width: 2; }
        .ilot-large { fill: #047857; stroke: #064E3B; stroke-width: 2; }
        .corridor { stroke: #EC4899; stroke-width: 8; stroke-opacity: 0.6; stroke-linecap: round; }
        .label { fill: #374151; font-family: Inter, sans-serif; font-size: 12px; text-anchor: middle; }
        .grid-line { stroke: #E5E7EB; stroke-width: 0.5; stroke-opacity: 0.5; }
        .legend { font-family: Inter, sans-serif; font-size: 14px; }
        .interactive { cursor: pointer; }
        .interactive:hover { opacity: 0.8; }
        .highlighted { stroke: #F59E0B; stroke-width: 3; }
        """
        
        style = ET.SubElement(svg, 'style')
        style.text = style_content
    
    def _add_background_and_grid(self, svg: ET.Element, bounds: Dict[str, float]):
        """Add background and grid to SVG"""
        # Background
        background = ET.SubElement(svg, 'rect')
        background.set('width', '100%')
        background.set('height', '100%')
        background.set('fill', self.color_scheme['background'])
        
        # Grid group
        grid_group = ET.SubElement(svg, 'g')
        grid_group.set('id', 'grid')
        
        # Add grid lines based on bounds and canvas size
        grid_size = self.canvas_config['grid_size']
        
        # Vertical grid lines
        for x in range(0, self.canvas_config['width'], grid_size):
            line = ET.SubElement(grid_group, 'line')
            line.set('x1', str(x))
            line.set('y1', '0')
            line.set('x2', str(x))
            line.set('y2', str(self.canvas_config['height']))
            line.set('class', 'grid-line')
        
        # Horizontal grid lines
        for y in range(0, self.canvas_config['height'], grid_size):
            line = ET.SubElement(grid_group, 'line')
            line.set('x1', '0')
            line.set('y1', str(y))
            line.set('x2', str(self.canvas_config['width']))
            line.set('y2', str(y))
            line.set('class', 'grid-line')
    
    def _add_interactive_legend(self, svg: ET.Element):
        """Add interactive legend to SVG"""
        legend_group = ET.SubElement(svg, 'g')
        legend_group.set('id', 'legend')
        legend_group.set('transform', 'translate(20, 20)')
        
        # Legend background
        legend_bg = ET.SubElement(legend_group, 'rect')
        legend_bg.set('width', '200')
        legend_bg.set('height', '180')
        legend_bg.set('fill', 'white')
        legend_bg.set('stroke', '#D1D5DB')
        legend_bg.set('stroke-width', '1')
        legend_bg.set('rx', '8')
        legend_bg.set('fill-opacity', '0.95')
        
        # Legend title
        title = ET.SubElement(legend_group, 'text')
        title.set('x', '100')
        title.set('y', '20')
        title.set('class', 'legend')
        title.set('font-weight', 'bold')
        title.set('text-anchor', 'middle')
        title.text = 'Legend'
        
        # Legend items
        legend_items = [
            {'color': '#6B7280', 'label': 'Walls', 'type': 'line'},
            {'color': '#3B82F6', 'label': 'Restricted Zones', 'type': 'rect'},
            {'color': '#EF4444', 'label': 'Entrances/Exits', 'type': 'rect'},
            {'color': '#10B981', 'label': 'Small Îlots', 'type': 'rect'},
            {'color': '#059669', 'label': 'Medium Îlots', 'type': 'rect'},
            {'color': '#047857', 'label': 'Large Îlots', 'type': 'rect'},
            {'color': '#EC4899', 'label': 'Corridors', 'type': 'line'}
        ]
        
        y_offset = 40
        for item in legend_items:
            # Legend symbol
            if item['type'] == 'line':
                line = ET.SubElement(legend_group, 'line')
                line.set('x1', '15')
                line.set('y1', str(y_offset))
                line.set('x2', '35')
                line.set('y2', str(y_offset))
                line.set('stroke', item['color'])
                line.set('stroke-width', '3')
            else:
                rect = ET.SubElement(legend_group, 'rect')
                rect.set('x', '15')
                rect.set('y', str(y_offset - 8))
                rect.set('width', '20')
                rect.set('height', '16')
                rect.set('fill', item['color'])
                rect.set('stroke', item['color'])
                rect.set('stroke-width', '1')
            
            # Legend text
            text = ET.SubElement(legend_group, 'text')
            text.set('x', '45')
            text.set('y', str(y_offset + 4))
            text.set('class', 'legend')
            text.text = item['label']
            
            y_offset += 20
    
    def _render_walls(self, parent: ET.Element, walls: List[Dict[str, Any]]):
        """Render walls with professional architectural styling"""
        walls_group = ET.SubElement(parent, 'g')
        walls_group.set('id', 'walls')
        
        for wall in walls:
            if wall.get('type') == 'line':
                line = ET.SubElement(walls_group, 'line')
                line.set('x1', str(wall['start']['x']))
                line.set('y1', str(wall['start']['y']))
                line.set('x2', str(wall['end']['x']))
                line.set('y2', str(wall['end']['y']))
                line.set('class', 'wall')
    
    def _render_zones(self, parent: ET.Element, zones: List[Dict[str, Any]]):
        """Render zones with proper color coding"""
        zones_group = ET.SubElement(parent, 'g')
        zones_group.set('id', 'zones')
        
        for zone in zones:
            if zone.get('type') == 'polyline' and zone.get('points'):
                polygon = ET.SubElement(zones_group, 'polygon')
                points_str = ' '.join([f"{p['x']},{p['y']}" for p in zone['points']])
                polygon.set('points', points_str)
                
                zone_type = zone.get('zone_type', 'general')
                if zone_type == 'restricted':
                    polygon.set('class', 'restricted-zone')
                elif zone_type == 'entrance':
                    polygon.set('class', 'entrance-zone')
    
    def _render_doors_and_windows(self, parent: ET.Element, doors: List[Dict[str, Any]], windows: List[Dict[str, Any]]):
        """Render doors and windows with swing indicators"""
        doors_group = ET.SubElement(parent, 'g')
        doors_group.set('id', 'doors')
        
        for door in doors:
            if door.get('type') == 'line':
                line = ET.SubElement(doors_group, 'line')
                line.set('x1', str(door['start']['x']))
                line.set('y1', str(door['start']['y']))
                line.set('x2', str(door['end']['x']))
                line.set('y2', str(door['end']['y']))
                line.set('class', 'door')
                
                # Add door swing arc if specified
                if door.get('render_style', {}).get('swing'):
                    self._add_door_swing(doors_group, door)
        
        windows_group = ET.SubElement(parent, 'g')
        windows_group.set('id', 'windows')
        
        for window in windows:
            if window.get('type') == 'line':
                line = ET.SubElement(windows_group, 'line')
                line.set('x1', str(window['start']['x']))
                line.set('y1', str(window['start']['y']))
                line.set('x2', str(window['end']['x']))
                line.set('y2', str(window['end']['y']))
                line.set('class', 'window')
    
    def _add_door_swing(self, parent: ET.Element, door: Dict[str, Any]):
        """Add curved door swing indicator"""
        start = door['start']
        end = door['end']
        
        # Calculate door swing arc
        mid_x = (start['x'] + end['x']) / 2
        mid_y = (start['y'] + end['y']) / 2
        
        # Create arc path
        path = ET.SubElement(parent, 'path')
        path_data = f"M {start['x']},{start['y']} Q {mid_x + 10},{mid_y + 10} {end['x']},{end['y']}"
        path.set('d', path_data)
        path.set('stroke', '#EF4444')
        path.set('stroke-width', '1')
        path.set('stroke-dasharray', '3,3')
        path.set('fill', 'none')
    
    def _render_ilots(self, parent: ET.Element, ilots: List[Dict[str, Any]]):
        """Render îlots with category-based styling"""
        ilots_group = ET.SubElement(parent, 'g')
        ilots_group.set('id', 'ilots')
        
        for ilot in ilots:
            # Create îlot rectangle
            rect = ET.SubElement(ilots_group, 'rect')
            rect.set('x', str(ilot['x'] - ilot['width']/2))
            rect.set('y', str(ilot['y'] - ilot['height']/2))
            rect.set('width', str(ilot['width']))
            rect.set('height', str(ilot['height']))
            
            category = ilot.get('category', 'medium')
            rect.set('class', f'ilot-{category} interactive')
            rect.set('data-ilot-id', ilot.get('id', ''))
            
            # Add îlot label
            text = ET.SubElement(ilots_group, 'text')
            text.set('x', str(ilot['x']))
            text.set('y', str(ilot['y'] + 4))
            text.set('class', 'label')
            text.text = f"{ilot.get('area', 0):.1f}m²"
    
    def _render_corridors(self, parent: ET.Element, corridors: List[Dict[str, Any]]):
        """Render corridors with area labels"""
        corridors_group = ET.SubElement(parent, 'g')
        corridors_group.set('id', 'corridors')
        
        for corridor in corridors:
            # Create corridor line
            line = ET.SubElement(corridors_group, 'line')
            line.set('x1', str(corridor['start']['x']))
            line.set('y1', str(corridor['start']['y']))
            line.set('x2', str(corridor['end']['x']))
            line.set('y2', str(corridor['end']['y']))
            line.set('class', 'corridor interactive')
            line.set('stroke-width', str(corridor.get('width', 1.2) * 10))  # Scale for visibility
            line.set('data-corridor-id', corridor.get('id', ''))
            
            # Add corridor label
            mid_x = (corridor['start']['x'] + corridor['end']['x']) / 2
            mid_y = (corridor['start']['y'] + corridor['end']['y']) / 2
            
            text = ET.SubElement(corridors_group, 'text')
            text.set('x', str(mid_x))
            text.set('y', str(mid_y))
            text.set('class', 'label')
            text.text = corridor.get('label', f"{corridor.get('area', 0):.2f}m²")
    
    def _calculate_transform(self, bounds: Dict[str, float]) -> str:
        """Calculate transform to fit drawing in canvas"""
        canvas_width = self.canvas_config['width'] - 2 * self.canvas_config['padding']
        canvas_height = self.canvas_config['height'] - 2 * self.canvas_config['padding']
        
        scale_x = canvas_width / bounds['width'] if bounds['width'] > 0 else 1
        scale_y = canvas_height / bounds['height'] if bounds['height'] > 0 else 1
        scale = min(scale_x, scale_y)
        
        translate_x = self.canvas_config['padding'] - bounds['min_x'] * scale
        translate_y = self.canvas_config['padding'] - bounds['min_y'] * scale
        
        return f"translate({translate_x}, {translate_y}) scale({scale})"
    
    def _add_interactive_controls(self, svg: ET.Element):
        """Add interactive zoom/pan controls"""
        controls_group = ET.SubElement(svg, 'g')
        controls_group.set('id', 'controls')
        controls_group.set('transform', f"translate({self.canvas_config['width'] - 150}, 20)")
        
        # Controls background
        controls_bg = ET.SubElement(controls_group, 'rect')
        controls_bg.set('width', '120')
        controls_bg.set('height', '100')
        controls_bg.set('fill', 'white')
        controls_bg.set('stroke', '#D1D5DB')
        controls_bg.set('rx', '8')
        controls_bg.set('fill-opacity', '0.95')
        
        # Zoom in button
        zoom_in = ET.SubElement(controls_group, 'circle')
        zoom_in.set('cx', '30')
        zoom_in.set('cy', '30')
        zoom_in.set('r', '15')
        zoom_in.set('fill', '#3B82F6')
        zoom_in.set('class', 'interactive')
        zoom_in.set('onclick', 'zoomIn()')
        
        zoom_in_text = ET.SubElement(controls_group, 'text')
        zoom_in_text.set('x', '30')
        zoom_in_text.set('y', '36')
        zoom_in_text.set('text-anchor', 'middle')
        zoom_in_text.set('fill', 'white')
        zoom_in_text.set('font-size', '16')
        zoom_in_text.text = '+'
        
        # Zoom out button
        zoom_out = ET.SubElement(controls_group, 'circle')
        zoom_out.set('cx', '60')
        zoom_out.set('cy', '30')
        zoom_out.set('r', '15')
        zoom_out.set('fill', '#EF4444')
        zoom_out.set('class', 'interactive')
        zoom_out.set('onclick', 'zoomOut()')
        
        zoom_out_text = ET.SubElement(controls_group, 'text')
        zoom_out_text.set('x', '60')
        zoom_out_text.set('y', '36')
        zoom_out_text.set('text-anchor', 'middle')
        zoom_out_text.set('fill', 'white')
        zoom_out_text.set('font-size', '16')
        zoom_out_text.text = '−'
        
        # Reset button
        reset = ET.SubElement(controls_group, 'rect')
        reset.set('x', '15')
        reset.set('y', '55')
        reset.set('width', '60')
        reset.set('height', '25')
        reset.set('fill', '#6B7280')
        reset.set('class', 'interactive')
        reset.set('rx', '4')
        reset.set('onclick', 'resetView()')
        
        reset_text = ET.SubElement(controls_group, 'text')
        reset_text.set('x', '45')
        reset_text.set('y', '72')
        reset_text.set('text-anchor', 'middle')
        reset_text.set('fill', 'white')
        reset_text.set('font-size', '12')
        reset_text.text = 'Reset'
    
    def _add_svg_javascript(self, svg: ET.Element):
        """Add JavaScript for SVG interactivity"""
        script = ET.SubElement(svg, 'script')
        script.set('type', 'text/javascript')
        script.text = """
        let currentZoom = 1;
        let currentPan = { x: 0, y: 0 };
        let isPanning = false;
        let lastPanPoint = { x: 0, y: 0 };
        
        function zoomIn() {
            currentZoom *= 1.2;
            updateTransform();
        }
        
        function zoomOut() {
            currentZoom /= 1.2;
            updateTransform();
        }
        
        function resetView() {
            currentZoom = 1;
            currentPan = { x: 0, y: 0 };
            updateTransform();
        }
        
        function updateTransform() {
            const mainGroup = document.getElementById('main-drawing');
            if (mainGroup) {
                const baseTransform = mainGroup.getAttribute('transform') || '';
                const zoomTransform = `translate(${currentPan.x}, ${currentPan.y}) scale(${currentZoom})`;
                mainGroup.style.transform = zoomTransform;
            }
        }
        
        // Pan functionality
        document.addEventListener('mousedown', function(e) {
            if (e.target.closest('#main-drawing')) {
                isPanning = true;
                lastPanPoint = { x: e.clientX, y: e.clientY };
                e.preventDefault();
            }
        });
        
        document.addEventListener('mousemove', function(e) {
            if (isPanning) {
                const dx = e.clientX - lastPanPoint.x;
                const dy = e.clientY - lastPanPoint.y;
                currentPan.x += dx;
                currentPan.y += dy;
                updateTransform();
                lastPanPoint = { x: e.clientX, y: e.clientY };
            }
        });
        
        document.addEventListener('mouseup', function() {
            isPanning = false;
        });
        
        // Element highlighting
        document.querySelectorAll('.interactive').forEach(element => {
            element.addEventListener('mouseenter', function() {
                this.classList.add('highlighted');
            });
            element.addEventListener('mouseleave', function() {
                this.classList.remove('highlighted');
            });
        });
        """
    
    def _prettify_svg(self, svg: ET.Element) -> str:
        """Convert SVG element to prettified string"""
        rough_string = ET.tostring(svg, encoding='unicode')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")
    
    def _save_svg(self, svg_string: str) -> str:
        """Save SVG string to file"""
        os.makedirs('static/outputs', exist_ok=True)
        filename = f"interactive_floorplan_{uuid.uuid4().hex[:8]}.svg"
        filepath = os.path.join('static/outputs', filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(svg_string)
        
        return filepath
    
    def _get_canvas_css(self) -> str:
        """Get CSS for Canvas-based renderer"""
        return """
        body {
            margin: 0;
            font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif;
            background: #F9FAFB;
        }
        .canvas-container {
            position: relative;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
        }
        #floorPlanCanvas {
            border: 1px solid #D1D5DB;
            background: white;
            cursor: grab;
        }
        #floorPlanCanvas:active {
            cursor: grabbing;
        }
        .canvas-controls {
            position: absolute;
            top: 20px;
            right: 20px;
            background: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }
        .canvas-legend {
            position: absolute;
            top: 20px;
            left: 20px;
            background: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            min-width: 180px;
        }
        .control-btn {
            margin: 5px;
            padding: 8px 12px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
        }
        .zoom-btn {
            background: #3B82F6;
            color: white;
        }
        .reset-btn {
            background: #6B7280;
            color: white;
        }
        .legend-item {
            display: flex;
            align-items: center;
            margin: 8px 0;
        }
        .legend-color {
            width: 20px;
            height: 3px;
            margin-right: 10px;
            border-radius: 2px;
        }
        """
    
    def _get_canvas_controls_html(self) -> str:
        """Get HTML for canvas controls"""
        return """
        <button class="control-btn zoom-btn" onclick="canvasRenderer.zoomIn()">Zoom In</button>
        <button class="control-btn zoom-btn" onclick="canvasRenderer.zoomOut()">Zoom Out</button>
        <button class="control-btn reset-btn" onclick="canvasRenderer.resetView()">Reset View</button>
        """
    
    def _get_canvas_legend_html(self) -> str:
        """Get HTML for canvas legend"""
        return """
        <h3 style="margin-top: 0;">Legend</h3>
        <div class="legend-item">
            <div class="legend-color" style="background: #6B7280;"></div>
            <span>Walls</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: #3B82F6;"></div>
            <span>Restricted Zones</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: #EF4444;"></div>
            <span>Entrances/Exits</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: #10B981;"></div>
            <span>Small Îlots</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: #059669;"></div>
            <span>Medium Îlots</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: #047857;"></div>
            <span>Large Îlots</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: #EC4899;"></div>
            <span>Corridors</span>
        </div>
        """
    
    def _get_canvas_javascript(self, plan_data: Dict[str, Any], 
                             optimization_data: Optional[Dict[str, Any]], 
                             bounds: Dict[str, float]) -> str:
        """Get JavaScript for Canvas interactivity"""
        return f"""
        class CanvasRenderer {{
            constructor() {{
                this.canvas = document.getElementById('floorPlanCanvas');
                this.ctx = this.canvas.getContext('2d');
                this.zoom = 1;
                this.panX = 0;
                this.panY = 0;
                this.isDragging = false;
                this.lastMouseX = 0;
                this.lastMouseY = 0;
                
                this.planData = {json.dumps(plan_data)};
                this.optimizationData = {json.dumps(optimization_data) if optimization_data else 'null'};
                this.bounds = {json.dumps(bounds)};
                
                this.setupEventListeners();
                this.render();
            }}
            
            setupEventListeners() {{
                this.canvas.addEventListener('mousedown', (e) => this.handleMouseDown(e));
                this.canvas.addEventListener('mousemove', (e) => this.handleMouseMove(e));
                this.canvas.addEventListener('mouseup', (e) => this.handleMouseUp(e));
                this.canvas.addEventListener('wheel', (e) => this.handleWheel(e));
            }}
            
            handleMouseDown(e) {{
                this.isDragging = true;
                this.lastMouseX = e.clientX;
                this.lastMouseY = e.clientY;
            }}
            
            handleMouseMove(e) {{
                if (this.isDragging) {{
                    const deltaX = e.clientX - this.lastMouseX;
                    const deltaY = e.clientY - this.lastMouseY;
                    this.panX += deltaX;
                    this.panY += deltaY;
                    this.lastMouseX = e.clientX;
                    this.lastMouseY = e.clientY;
                    this.render();
                }}
            }}
            
            handleMouseUp(e) {{
                this.isDragging = false;
            }}
            
            handleWheel(e) {{
                e.preventDefault();
                const zoomFactor = e.deltaY > 0 ? 0.9 : 1.1;
                this.zoom *= zoomFactor;
                this.render();
            }}
            
            zoomIn() {{
                this.zoom *= 1.2;
                this.render();
            }}
            
            zoomOut() {{
                this.zoom /= 1.2;
                this.render();
            }}
            
            resetView() {{
                this.zoom = 1;
                this.panX = 0;
                this.panY = 0;
                this.render();
            }}
            
            render() {{
                this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
                
                // Apply transformations
                this.ctx.save();
                this.ctx.translate(this.panX, this.panY);
                this.ctx.scale(this.zoom, this.zoom);
                
                // Calculate scale and offset to fit drawing
                const scaleX = (this.canvas.width - 100) / this.bounds.width;
                const scaleY = (this.canvas.height - 100) / this.bounds.height;
                const scale = Math.min(scaleX, scaleY);
                
                this.ctx.scale(scale, scale);
                this.ctx.translate(-this.bounds.min_x + 50/scale, -this.bounds.min_y + 50/scale);
                
                // Render elements
                this.renderWalls();
                this.renderZones();
                this.renderIlots();
                this.renderCorridors();
                
                this.ctx.restore();
            }}
            
            renderWalls() {{
                this.ctx.strokeStyle = '#6B7280';
                this.ctx.lineWidth = 3;
                this.ctx.lineCap = 'round';
                
                for (const wall of this.planData.walls || []) {{
                    if (wall.type === 'line') {{
                        this.ctx.beginPath();
                        this.ctx.moveTo(wall.start.x, wall.start.y);
                        this.ctx.lineTo(wall.end.x, wall.end.y);
                        this.ctx.stroke();
                    }}
                }}
            }}
            
            renderZones() {{
                for (const zone of this.planData.zones || []) {{
                    if (zone.type === 'polyline' && zone.points) {{
                        this.ctx.beginPath();
                        this.ctx.moveTo(zone.points[0].x, zone.points[0].y);
                        for (let i = 1; i < zone.points.length; i++) {{
                            this.ctx.lineTo(zone.points[i].x, zone.points[i].y);
                        }}
                        this.ctx.closePath();
                        
                        if (zone.zone_type === 'restricted') {{
                            this.ctx.fillStyle = 'rgba(59, 130, 246, 0.3)';
                            this.ctx.strokeStyle = '#1D4ED8';
                        }} else if (zone.zone_type === 'entrance') {{
                            this.ctx.fillStyle = 'rgba(239, 68, 68, 0.4)';
                            this.ctx.strokeStyle = '#DC2626';
                        }}
                        
                        this.ctx.fill();
                        this.ctx.stroke();
                    }}
                }}
            }}
            
            renderIlots() {{
                if (!this.optimizationData) return;
                
                const ilots = this.optimizationData.ilots || this.optimizationData.boxes || [];
                
                for (const ilot of ilots) {{
                    const x = ilot.x - ilot.width/2;
                    const y = ilot.y - ilot.height/2;
                    
                    // Fill color based on category
                    const colors = {{
                        'small': '#10B981',
                        'medium': '#059669',
                        'large': '#047857'
                    }};
                    
                    this.ctx.fillStyle = colors[ilot.category] || '#059669';
                    this.ctx.strokeStyle = '#047857';
                    this.ctx.lineWidth = 2;
                    
                    this.ctx.fillRect(x, y, ilot.width, ilot.height);
                    this.ctx.strokeRect(x, y, ilot.width, ilot.height);
                    
                    // Add label
                    this.ctx.fillStyle = '#374151';
                    this.ctx.font = '12px Inter';
                    this.ctx.textAlign = 'center';
                    this.ctx.fillText(
                        `${{ilot.area.toFixed(1)}}m²`,
                        ilot.x,
                        ilot.y + 4
                    );
                }}
            }}
            
            renderCorridors() {{
                if (!this.optimizationData) return;
                
                const corridors = this.optimizationData.corridors || [];
                
                this.ctx.strokeStyle = '#EC4899';
                this.ctx.globalAlpha = 0.6;
                this.ctx.lineCap = 'round';
                
                for (const corridor of corridors) {{
                    this.ctx.lineWidth = (corridor.width || 1.2) * 10;
                    this.ctx.beginPath();
                    this.ctx.moveTo(corridor.start.x, corridor.start.y);
                    this.ctx.lineTo(corridor.end.x, corridor.end.y);
                    this.ctx.stroke();
                    
                    // Add label
                    this.ctx.globalAlpha = 1;
                    this.ctx.fillStyle = '#BE185D';
                    this.ctx.font = '12px Inter';
                    this.ctx.textAlign = 'center';
                    
                    const midX = (corridor.start.x + corridor.end.x) / 2;
                    const midY = (corridor.start.y + corridor.end.y) / 2;
                    
                    this.ctx.fillText(
                        corridor.label || `${{corridor.area.toFixed(2)}}m²`,
                        midX,
                        midY
                    );
                }}
                
                this.ctx.globalAlpha = 1;
            }}
        }}
        
        const canvasRenderer = new CanvasRenderer();
        """
