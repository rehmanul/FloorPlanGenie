
"""
Pixel-Perfect Floor Plan Renderer - Production Grade
SVG-based rendering with professional architectural styling
"""
import xml.etree.ElementTree as ET
from typing import Dict, List, Any
import math
import os

class PixelPerfectRenderer:
    """Professional architectural renderer with pixel-perfect SVG output"""
    
    def __init__(self):
        self.architectural_styles = {
            'walls': {
                'stroke': '#6B7280',  # Gray-500
                'stroke_width': '3',
                'fill': 'none',
                'line_cap': 'round',
                'line_join': 'round'
            },
            'restricted_zones': {
                'fill': '#3B82F6',  # Blue-500
                'fill_opacity': '0.3',
                'stroke': '#2563EB',
                'stroke_width': '1',
                'stroke_dasharray': '5,5'
            },
            'entrances_exits': {
                'fill': '#EF4444',  # Red-500
                'fill_opacity': '0.4',
                'stroke': '#DC2626',
                'stroke_width': '2'
            },
            'doors': {
                'stroke': '#EF4444',
                'stroke_width': '2',
                'fill': 'none'
            },
            'windows': {
                'stroke': '#60A5FA',  # Blue-400
                'stroke_width': '1',
                'fill': 'white'
            },
            'ilots': {
                'small': {'fill': '#10B981', 'stroke': '#047857', 'stroke_width': '2'},
                'medium': {'fill': '#059669', 'stroke': '#047857', 'stroke_width': '2'},
                'large': {'fill': '#047857', 'stroke': '#065F46', 'stroke_width': '2'}
            },
            'corridors': {
                'fill': '#EC4899',  # Pink-500
                'fill_opacity': '0.2',
                'stroke': '#BE185D',
                'stroke_width': '1',
                'stroke_dasharray': '3,3'
            }
        }
    
    def generate_interactive_svg(self, plan_data: Dict[str, Any], 
                                width: int = 1200, height: int = 800) -> str:
        """Generate interactive SVG with zoom, pan, and select functionality"""
        
        # Calculate viewport and scaling
        dimensions = plan_data.get('dimensions', {})
        plan_width = dimensions.get('width', 50)
        plan_height = dimensions.get('height', 40)
        
        # Calculate scale to fit viewport with padding
        padding = 50
        scale_x = (width - 2 * padding) / plan_width
        scale_y = (height - 2 * padding) / plan_height
        scale = min(scale_x, scale_y) * 0.8  # 80% to ensure comfortable margins
        
        # Create SVG root
        svg = ET.Element('svg', {
            'width': str(width),
            'height': str(height),
            'viewBox': f'0 0 {width} {height}',
            'xmlns': 'http://www.w3.org/2000/svg',
            'xmlns:xlink': 'http://www.w3.org/1999/xlink',
            'class': 'interactive-floorplan'
        })
        
        # Add CSS styles
        style = ET.SubElement(svg, 'style')
        style.text = self._get_interactive_css()
        
        # Add definitions for patterns and gradients
        defs = ET.SubElement(svg, 'defs')
        self._add_patterns_and_gradients(defs)
        
        # Create main group with transform for centering
        offset_x = (width - plan_width * scale) / 2
        offset_y = (height - plan_height * scale) / 2
        
        main_group = ET.SubElement(svg, 'g', {
            'id': 'main-floorplan',
            'transform': f'translate({offset_x}, {offset_y}) scale({scale})',
            'class': 'zoomable-group'
        })
        
        # Add background
        background = ET.SubElement(main_group, 'rect', {
            'x': '0', 'y': '0',
            'width': str(plan_width), 'height': str(plan_height),
            'fill': '#FAFAFA',
            'stroke': '#E5E7EB',
            'stroke_width': '0.5'
        })
        
        # Render architectural elements in correct order
        self._render_zones(main_group, plan_data.get('zones', []))
        self._render_walls(main_group, plan_data.get('walls', []))
        self._render_doors_windows(main_group, plan_data.get('doors', []), plan_data.get('windows', []))
        self._render_ilots(main_group, plan_data.get('ilots', plan_data.get('boxes', [])))
        self._render_corridors(main_group, plan_data.get('corridors', []))
        
        # Add interactive controls
        self._add_interactive_controls(svg, width, height)
        
        # Add legend
        self._add_legend(svg, width, height)
        
        # Add JavaScript for interactivity
        script = ET.SubElement(svg, 'script')
        script.text = self._get_interactive_javascript()
        
        return ET.tostring(svg, encoding='unicode')
    
    def _render_walls(self, parent, walls):
        """Render walls with professional architectural styling"""
        walls_group = ET.SubElement(parent, 'g', {'id': 'walls', 'class': 'walls-layer'})
        
        for i, wall in enumerate(walls):
            if wall.get('type') == 'line':
                start, end = wall['start'], wall['end']
                line = ET.SubElement(walls_group, 'line', {
                    'x1': str(start['x']), 'y1': str(start['y']),
                    'x2': str(end['x']), 'y2': str(end['y']),
                    'id': f'wall-{i}',
                    'class': 'wall-element selectable',
                    **self.architectural_styles['walls']
                })
    
    def _render_zones(self, parent, zones):
        """Render zones with proper architectural colors"""
        zones_group = ET.SubElement(parent, 'g', {'id': 'zones', 'class': 'zones-layer'})
        
        for i, zone in enumerate(zones):
            zone_type = zone.get('zone_type', 'general')
            style_key = f'{zone_type}_zones' if f'{zone_type}_zones' in self.architectural_styles else 'restricted_zones'
            
            if zone.get('type') == 'polyline' and zone.get('points'):
                points = ' '.join([f"{p['x']},{p['y']}" for p in zone['points']])
                polygon = ET.SubElement(zones_group, 'polygon', {
                    'points': points,
                    'id': f'zone-{i}',
                    'class': f'zone-element zone-{zone_type} selectable',
                    **self.architectural_styles[style_key]
                })
    
    def _render_ilots(self, parent, ilots):
        """Render îlots with category-based styling"""
        ilots_group = ET.SubElement(parent, 'g', {'id': 'ilots', 'class': 'ilots-layer'})
        
        for i, ilot in enumerate(ilots):
            category = ilot.get('category', 'medium')
            style = self.architectural_styles['ilots'].get(category, self.architectural_styles['ilots']['medium'])
            
            rect = ET.SubElement(ilots_group, 'rect', {
                'x': str(ilot['x'] - ilot['width']/2),
                'y': str(ilot['y'] - ilot['height']/2),
                'width': str(ilot['width']),
                'height': str(ilot['height']),
                'id': f'ilot-{i}',
                'class': f'ilot-element ilot-{category} selectable draggable',
                'data-category': category,
                'rx': '0.2',  # Rounded corners
                **style
            })
            
            # Add label
            text = ET.SubElement(ilots_group, 'text', {
                'x': str(ilot['x']),
                'y': str(ilot['y']),
                'text-anchor': 'middle',
                'dominant-baseline': 'middle',
                'class': 'ilot-label',
                'font-size': str(min(ilot['width'], ilot['height']) * 0.2)
            })
            text.text = f"{category.upper()}\n{ilot.get('area', ilot['width'] * ilot['height']):.1f}m²"
    
    def _render_corridors(self, parent, corridors):
        """Render corridors with professional pathfinding visualization"""
        corridors_group = ET.SubElement(parent, 'g', {'id': 'corridors', 'class': 'corridors-layer'})
        
        for i, corridor in enumerate(corridors):
            if corridor.get('start') and corridor.get('end'):
                # Draw corridor as connecting line with width
                start, end = corridor['start'], corridor['end']
                width = corridor.get('width', 1.2)
                
                # Create path with proper width
                path_d = f"M {start['x']} {start['y']} L {end['x']} {end['y']}"
                path = ET.SubElement(corridors_group, 'path', {
                    'd': path_d,
                    'id': f'corridor-{i}',
                    'class': 'corridor-element selectable',
                    'stroke-width': str(width),
                    **self.architectural_styles['corridors']
                })
    
    def _render_doors_windows(self, parent, doors, windows):
        """Render doors and windows with swing directions"""
        openings_group = ET.SubElement(parent, 'g', {'id': 'openings', 'class': 'openings-layer'})
        
        # Render doors with swing arcs
        for i, door in enumerate(doors):
            if door.get('type') == 'arc':
                center = door['center']
                radius = door['radius']
                start_angle = math.radians(door.get('start_angle', 0))
                end_angle = math.radians(door.get('end_angle', 90))
                
                # Draw door swing arc
                x1 = center['x'] + radius * math.cos(start_angle)
                y1 = center['y'] + radius * math.sin(start_angle)
                x2 = center['x'] + radius * math.cos(end_angle)
                y2 = center['y'] + radius * math.sin(end_angle)
                
                large_arc = "1" if abs(end_angle - start_angle) > math.pi else "0"
                path_d = f"M {center['x']} {center['y']} L {x1} {y1} A {radius} {radius} 0 {large_arc} 1 {x2} {y2} Z"
                
                path = ET.SubElement(openings_group, 'path', {
                    'd': path_d,
                    'id': f'door-{i}',
                    'class': 'door-element selectable',
                    **self.architectural_styles['doors'],
                    'fill_opacity': '0.3'
                })
        
        # Render windows
        for i, window in enumerate(windows):
            if window.get('type') == 'line':
                start, end = window['start'], window['end']
                line = ET.SubElement(openings_group, 'line', {
                    'x1': str(start['x']), 'y1': str(start['y']),
                    'x2': str(end['x']), 'y2': str(end['y']),
                    'id': f'window-{i}',
                    'class': 'window-element selectable',
                    **self.architectural_styles['windows']
                })
    
    def _add_interactive_controls(self, svg, width, height):
        """Add zoom/pan/select controls"""
        controls_group = ET.SubElement(svg, 'g', {
            'id': 'controls',
            'class': 'controls-overlay'
        })
        
        # Control panel
        panel = ET.SubElement(controls_group, 'rect', {
            'x': '10', 'y': '10', 'width': '200', 'height': '80',
            'fill': 'rgba(0,0,0,0.8)', 'rx': '8',
            'class': 'control-panel'
        })
        
        # Zoom controls
        zoom_in = ET.SubElement(controls_group, 'circle', {
            'cx': '30', 'cy': '35', 'r': '12',
            'fill': '#3B82F6', 'class': 'zoom-control',
            'id': 'zoom-in', 'cursor': 'pointer'
        })
        
        zoom_out = ET.SubElement(controls_group, 'circle', {
            'cx': '60', 'cy': '35', 'r': '12',
            'fill': '#3B82F6', 'class': 'zoom-control',
            'id': 'zoom-out', 'cursor': 'pointer'
        })
        
        # Reset view
        reset = ET.SubElement(controls_group, 'rect', {
            'x': '80', 'y': '23', 'width': '24', 'height': '24',
            'fill': '#10B981', 'rx': '4',
            'class': 'reset-control', 'id': 'reset-view',
            'cursor': 'pointer'
        })
    
    def _add_legend(self, svg, width, height):
        """Add interactive legend"""
        legend_group = ET.SubElement(svg, 'g', {
            'id': 'legend',
            'class': 'legend-overlay'
        })
        
        # Legend background
        legend_bg = ET.SubElement(legend_group, 'rect', {
            'x': str(width - 220), 'y': '10',
            'width': '200', 'height': '150',
            'fill': 'rgba(255,255,255,0.95)',
            'stroke': '#E5E7EB', 'stroke_width': '1',
            'rx': '8', 'class': 'legend-panel'
        })
        
        # Legend items
        legend_items = [
            ('Walls', '#6B7280'),
            ('Restricted Zones', '#3B82F6'),
            ('Entrances/Exits', '#EF4444'),
            ('Îlots', '#10B981'),
            ('Corridors', '#EC4899')
        ]
        
        for i, (label, color) in enumerate(legend_items):
            y_pos = 35 + i * 25
            
            # Color indicator
            indicator = ET.SubElement(legend_group, 'rect', {
                'x': str(width - 210), 'y': str(y_pos - 8),
                'width': '16', 'height': '16',
                'fill': color, 'class': 'legend-color'
            })
            
            # Label
            text = ET.SubElement(legend_group, 'text', {
                'x': str(width - 185), 'y': str(y_pos),
                'font-size': '12', 'fill': '#374151',
                'dominant-baseline': 'middle',
                'class': 'legend-text'
            })
            text.text = label
    
    def _add_patterns_and_gradients(self, defs):
        """Add SVG patterns and gradients for professional rendering"""
        # Hatching pattern for restricted zones
        pattern = ET.SubElement(defs, 'pattern', {
            'id': 'restricted-hatch',
            'patternUnits': 'userSpaceOnUse',
            'width': '4', 'height': '4'
        })
        ET.SubElement(pattern, 'path', {
            'd': 'M 0,4 l 4,-4 M -1,1 l 2,-2 M 3,5 l 2,-2',
            'stroke': '#3B82F6', 'stroke_width': '0.5'
        })
    
    def _get_interactive_css(self):
        """Generate CSS for interactive elements"""
        return """
        .interactive-floorplan { cursor: grab; }
        .interactive-floorplan:active { cursor: grabbing; }
        .selectable { cursor: pointer; }
        .selectable:hover { opacity: 0.8; stroke-width: 2; }
        .selected { stroke: #F59E0B !important; stroke-width: 3 !important; }
        .draggable:hover { cursor: move; }
        .control-panel { opacity: 0.9; }
        .zoom-control:hover { fill: #2563EB; }
        .reset-control:hover { fill: #059669; }
        .legend-panel { backdrop-filter: blur(4px); }
        .ilot-label { font-family: Arial, sans-serif; fill: white; pointer-events: none; }
        """
    
    def _get_interactive_javascript(self):
        """Generate JavaScript for zoom/pan/select functionality"""
        return """
        document.addEventListener('DOMContentLoaded', function() {
            const svg = document.querySelector('.interactive-floorplan');
            const mainGroup = document.getElementById('main-floorplan');
            let isPanning = false;
            let startPoint = { x: 0, y: 0 };
            let currentTransform = { x: 0, y: 0, scale: 1 };
            
            // Pan functionality
            svg.addEventListener('mousedown', function(e) {
                if (e.target.classList.contains('selectable')) return;
                isPanning = true;
                startPoint.x = e.clientX;
                startPoint.y = e.clientY;
            });
            
            svg.addEventListener('mousemove', function(e) {
                if (!isPanning) return;
                const dx = e.clientX - startPoint.x;
                const dy = e.clientY - startPoint.y;
                currentTransform.x += dx;
                currentTransform.y += dy;
                updateTransform();
                startPoint.x = e.clientX;
                startPoint.y = e.clientY;
            });
            
            svg.addEventListener('mouseup', () => isPanning = false);
            
            // Zoom functionality
            svg.addEventListener('wheel', function(e) {
                e.preventDefault();
                const scaleFactor = e.deltaY > 0 ? 0.9 : 1.1;
                currentTransform.scale *= scaleFactor;
                updateTransform();
            });
            
            // Selection functionality
            document.querySelectorAll('.selectable').forEach(element => {
                element.addEventListener('click', function(e) {
                    e.stopPropagation();
                    document.querySelectorAll('.selected').forEach(el => el.classList.remove('selected'));
                    this.classList.add('selected');
                });
            });
            
            // Control buttons
            document.getElementById('zoom-in')?.addEventListener('click', () => {
                currentTransform.scale *= 1.2;
                updateTransform();
            });
            
            document.getElementById('zoom-out')?.addEventListener('click', () => {
                currentTransform.scale *= 0.8;
                updateTransform();
            });
            
            document.getElementById('reset-view')?.addEventListener('click', () => {
                currentTransform = { x: 0, y: 0, scale: 1 };
                updateTransform();
            });
            
            function updateTransform() {
                const baseTransform = mainGroup.getAttribute('transform').match(/translate\\(([^)]+)\\)\\s*scale\\(([^)]+)\\)/);
                const baseTranslate = baseTransform[1].split(',').map(Number);
                const baseScale = Number(baseTransform[2]);
                
                mainGroup.setAttribute('transform', 
                    `translate(${baseTranslate[0] + currentTransform.x}, ${baseTranslate[1] + currentTransform.y}) 
                     scale(${baseScale * currentTransform.scale})`
                );
            }
        });
        """
    
    def save_svg(self, svg_content: str, filename: str = None) -> str:
        """Save SVG content to file"""
        if not filename:
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"interactive_floorplan_{timestamp}.svg"
        
        filepath = os.path.join('static', 'outputs', filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(svg_content)
        
        return filepath
