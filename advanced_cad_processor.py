"""
Advanced CAD File Processor - Production Grade
Layer-aware extraction with element classification
"""
import uuid
import json
import os
import math
import ezdxf
from shapely.geometry import LineString, Polygon, Point
from shapely.ops import unary_union
import networkx as nx
import numpy as np
from collections import defaultdict

class AdvancedCADProcessor:
    def __init__(self):
        self.plans = {}
        self.layer_mapping = {
            'walls': ['walls', 'wall', 'mur', 'murs', '0', 'outline'],
            'doors': ['doors', 'door', 'porte', 'portes', 'opening'],
            'windows': ['windows', 'window', 'fenetre', 'fenetres'],
            'restricted': ['restricted', 'no_entry', 'blocked'],
            'entry_exit': ['entry', 'exit', 'entrance', 'sortie', 'entree']
        }
        
    def process_cad_file(self, filepath, plan_id):
        """Advanced CAD processing with layer-aware extraction"""
        try:
            doc = ezdxf.readfile(filepath)
            
            # Process all layouts and find main floor plan
            main_layout = self._identify_main_floor_plan(doc)
            
            # Extract architectural elements with layer classification
            elements = self._extract_architectural_elements(main_layout)
            
            # Perform geometric analysis
            geometry = self._analyze_geometry(elements)
            
            # Generate zones based on architectural logic
            zones = self._generate_intelligent_zones(elements, geometry)
            
            # Calculate accurate dimensions and scaling
            dimensions = self._calculate_precise_dimensions(geometry)
            
            plan_data = {
                'id': plan_id,
                'dimensions': dimensions,
                'walls': elements['walls'],
                'doors': elements['doors'],
                'windows': elements['windows'],
                'zones': zones,
                'geometry': geometry,
                'metadata': {
                    'layers_found': list(elements['layers'].keys()),
                    'total_elements': sum(len(v) for v in elements.values() if isinstance(v, list)),
                    'processing_method': 'advanced_layer_aware'
                }
            }
            
            self.plans[plan_id] = plan_data
            return plan_data
            
        except Exception as e:
            print(f"Advanced CAD processing error: {e}")
            raise ValueError(f"Unable to process architectural file: {filepath}. Please ensure you're uploading a valid DXF file with actual floor plan data.")
    
    def _identify_main_floor_plan(self, doc):
        """Identify the main floor plan among multiple layouts"""
        layouts = [doc.modelspace()]
        
        # Add paper space layouts if they exist
        for layout_name in doc.layout_names():
            if layout_name.lower() != 'model':
                try:
                    layouts.append(doc.layouts.get(layout_name))
                except:
                    continue
        
        # Score each layout based on architectural content
        best_layout = None
        best_score = 0
        
        for layout in layouts:
            score = self._score_layout_for_floor_plan(layout)
            if score > best_score:
                best_score = score
                best_layout = layout
        
        return best_layout or doc.modelspace()
    
    def _score_layout_for_floor_plan(self, layout):
        """Score layout based on typical floor plan characteristics"""
        score = 0
        line_count = 0
        total_length = 0
        
        for entity in layout:
            if entity.dxftype() in ['LINE', 'POLYLINE', 'LWPOLYLINE']:
                line_count += 1
                if hasattr(entity, 'dxf'):
                    layer = getattr(entity.dxf, 'layer', '').lower()
                    # Boost score for wall-like layers
                    if any(wall_keyword in layer for wall_keyword in self.layer_mapping['walls']):
                        score += 10
                    
                # Calculate line length for architectural significance
                if entity.dxftype() == 'LINE':
                    start, end = entity.dxf.start, entity.dxf.end
                    length = math.sqrt((end.x - start.x)**2 + (end.y - start.y)**2)
                    total_length += length
        
        # Prefer layouts with substantial line content (typical of floor plans)
        score += min(line_count * 2, 100)  # Cap at 100
        score += min(total_length / 1000, 50)  # Normalize and cap
        
        return score
    
    def _extract_architectural_elements(self, layout):
        """Extract and classify architectural elements by layer"""
        elements = {
            'walls': [],
            'doors': [],
            'windows': [],
            'annotations': [],
            'layers': defaultdict(list)
        }
        
        bounds = {'min_x': float('inf'), 'min_y': float('inf'), 
                  'max_x': float('-inf'), 'max_y': float('-inf')}
        
        for entity in layout:
            layer_name = getattr(entity.dxf, 'layer', 'Default').lower()
            element_type = self._classify_element_by_layer(layer_name)
            
            # Process different entity types
            if entity.dxftype() == 'LINE':
                element = self._process_line_entity(entity, element_type, bounds)
                elements[element_type].append(element)
                elements['layers'][layer_name].append(element)
                
            elif entity.dxftype() in ['POLYLINE', 'LWPOLYLINE']:
                polyline_elements = self._process_polyline_entity(entity, element_type, bounds)
                elements[element_type].extend(polyline_elements)
                elements['layers'][layer_name].extend(polyline_elements)
                
            elif entity.dxftype() == 'CIRCLE':
                element = self._process_circle_entity(entity, bounds)
                if element:
                    elements['doors'].append(element)
                    elements['layers'][layer_name].append(element)
                    
            elif entity.dxftype() == 'ARC':
                element = self._process_arc_entity(entity, bounds)
                if element:
                    elements['doors'].append(element)
                    elements['layers'][layer_name].append(element)
        
        elements['bounds'] = bounds
        return elements
    
    def _classify_element_by_layer(self, layer_name):
        """Classify architectural elements based on layer names"""
        layer_lower = layer_name.lower()
        
        for element_type, keywords in self.layer_mapping.items():
            if any(keyword in layer_lower for keyword in keywords):
                return element_type if element_type in ['walls', 'doors', 'windows'] else 'walls'
        
        # Default classification based on common patterns
        if any(term in layer_lower for term in ['door', 'porte', 'opening']):
            return 'doors'
        elif any(term in layer_lower for term in ['window', 'fenetre']):
            return 'windows'
        else:
            return 'walls'  # Default to walls
    
    def _process_line_entity(self, entity, element_type, bounds):
        """Process LINE entities"""
        start, end = entity.dxf.start, entity.dxf.end
        
        # Update bounds
        bounds['min_x'] = min(bounds['min_x'], start.x, end.x)
        bounds['max_x'] = max(bounds['max_x'], start.x, end.x)
        bounds['min_y'] = min(bounds['min_y'], start.y, end.y)
        bounds['max_y'] = max(bounds['max_y'], start.y, end.y)
        
        length = math.sqrt((end.x - start.x)**2 + (end.y - start.y)**2)
        
        return {
            'start': {'x': float(start.x), 'y': float(start.y)},
            'end': {'x': float(end.x), 'y': float(end.y)},
            'layer': getattr(entity.dxf, 'layer', 'Default'),
            'length': length,
            'type': 'line',
            'element_type': element_type
        }
    
    def _process_polyline_entity(self, entity, element_type, bounds):
        """Process POLYLINE/LWPOLYLINE entities"""
        elements = []
        try:
            points = list(entity.get_points())
            for i in range(len(points) - 1):
                start, end = points[i], points[i + 1]
                
                # Update bounds
                bounds['min_x'] = min(bounds['min_x'], start[0], end[0])
                bounds['max_x'] = max(bounds['max_x'], start[0], end[0])
                bounds['min_y'] = min(bounds['min_y'], start[1], end[1])
                bounds['max_y'] = max(bounds['max_y'], start[1], end[1])
                
                element = {
                    'start': {'x': float(start[0]), 'y': float(start[1])},
                    'end': {'x': float(end[0]), 'y': float(end[1])},
                    'layer': getattr(entity.dxf, 'layer', 'Default'),
                    'type': 'polyline',
                    'element_type': element_type
                }
                elements.append(element)
        except:
            pass
        
        return elements
    
    def _process_circle_entity(self, entity, bounds):
        """Process CIRCLE entities (often doors)"""
        center = entity.dxf.center
        radius = entity.dxf.radius
        
        # Filter for reasonable door/window sizes
        if 0.3 < radius < 3.0:
            bounds['min_x'] = min(bounds['min_x'], center.x - radius)
            bounds['max_x'] = max(bounds['max_x'], center.x + radius)
            bounds['min_y'] = min(bounds['min_y'], center.y - radius)
            bounds['max_y'] = max(bounds['max_y'], center.y + radius)
            
            return {
                'center': {'x': float(center.x), 'y': float(center.y)},
                'radius': float(radius),
                'type': 'circle',
                'element_type': 'door'
            }
        return None
    
    def _process_arc_entity(self, entity, bounds):
        """Process ARC entities (door swings)"""
        try:
            center = entity.dxf.center
            radius = entity.dxf.radius
            start_angle = entity.dxf.start_angle
            end_angle = entity.dxf.end_angle
            
            if 0.5 < radius < 2.5:  # Reasonable door swing size
                bounds['min_x'] = min(bounds['min_x'], center.x - radius)
                bounds['max_x'] = max(bounds['max_x'], center.x + radius)
                bounds['min_y'] = min(bounds['min_y'], center.y - radius)
                bounds['max_y'] = max(bounds['max_y'], center.y + radius)
                
                return {
                    'center': {'x': float(center.x), 'y': float(center.y)},
                    'radius': float(radius),
                    'start_angle': float(start_angle),
                    'end_angle': float(end_angle),
                    'type': 'arc',
                    'element_type': 'door'
                }
        except:
            pass
        return None
    
    def _analyze_geometry(self, elements):
        """Perform geometric analysis of architectural elements"""
        bounds = elements['bounds']
        
        # Create Shapely geometries for spatial analysis
        wall_lines = []
        for wall in elements['walls']:
            line = LineString([
                (wall['start']['x'], wall['start']['y']),
                (wall['end']['x'], wall['end']['y'])
            ])
            wall_lines.append(line)
        
        # Find building outline
        outline = self._create_building_outline(wall_lines, bounds)
        
        # Identify interior spaces
        interior_spaces = self._identify_interior_spaces(wall_lines, outline)
        
        return {
            'bounds': bounds,
            'wall_lines': wall_lines,
            'outline': outline,
            'interior_spaces': interior_spaces,
            'total_area': self._calculate_area(outline)
        }
    
    def _create_building_outline(self, wall_lines, bounds):
        """Create building outline from wall network"""
        try:
            # Create a buffer around all walls and take the union
            buffered_walls = [line.buffer(0.1) for line in wall_lines]
            union_walls = unary_union(buffered_walls)
            
            # Extract the outer boundary
            if hasattr(union_walls, 'exterior'):
                return union_walls.exterior
            else:
                # Fallback to bounding box
                return Polygon([
                    (bounds['min_x'], bounds['min_y']),
                    (bounds['max_x'], bounds['min_y']),
                    (bounds['max_x'], bounds['max_y']),
                    (bounds['min_x'], bounds['max_y'])
                ])
        except:
            # Fallback to bounding box
            return Polygon([
                (bounds['min_x'], bounds['min_y']),
                (bounds['max_x'], bounds['min_y']),
                (bounds['max_x'], bounds['max_y']),
                (bounds['min_x'], bounds['max_y'])
            ])
    
    def _identify_interior_spaces(self, wall_lines, outline):
        """Identify interior spaces using wall network analysis"""
        # This is a simplified version - production would use more advanced algorithms
        spaces = []
        
        try:
            # Create a grid for space detection
            bounds = outline.bounds
            grid_resolution = min((bounds[2] - bounds[0]), (bounds[3] - bounds[1])) / 20
            
            x_coords = np.arange(bounds[0], bounds[2], grid_resolution)
            y_coords = np.arange(bounds[1], bounds[3], grid_resolution)
            
            for x in x_coords:
                for y in y_coords:
                    point = Point(x, y)
                    if outline.contains(point):
                        # Check if point is not too close to walls
                        min_wall_distance = min([point.distance(wall) for wall in wall_lines] or [float('inf')])
                        if min_wall_distance > 1.0:  # 1 meter from walls
                            spaces.append({'center': (x, y), 'type': 'available'})
        except:
            pass
        
        return spaces
    
    def _generate_intelligent_zones(self, elements, geometry):
        """Generate zones using architectural intelligence"""
        zones = {
            'entry_exit': [],
            'no_entry': [],
            'available': [],
            'restricted': []
        }
        
        bounds = geometry['bounds']
        
        # Generate entry/exit zones near doors
        for door in elements['doors']:
            if door['type'] in ['circle', 'arc']:
                center = door['center']
                radius = door.get('radius', 1.0)
                
                zone = {
                    'x': center['x'] - radius * 1.5,
                    'y': center['y'] - radius * 1.5,
                    'width': radius * 3,
                    'height': radius * 3,
                    'type': 'entry_exit'
                }
                zones['entry_exit'].append(zone)
        
        # Generate no-entry zones near building perimeter
        margin = min(bounds['max_x'] - bounds['min_x'], bounds['max_y'] - bounds['min_y']) * 0.1
        
        perimeter_zones = [
            {'x': bounds['min_x'], 'y': bounds['min_y'], 'width': margin, 'height': margin},
            {'x': bounds['max_x'] - margin, 'y': bounds['max_y'] - margin, 'width': margin, 'height': margin}
        ]
        
        for zone in perimeter_zones:
            zone['type'] = 'no_entry'
            zones['no_entry'].append(zone)
        
        # Available zones are calculated dynamically during optimization
        
        return zones
    
    def _calculate_precise_dimensions(self, geometry):
        """Calculate precise building dimensions"""
        bounds = geometry['bounds']
        
        width = bounds['max_x'] - bounds['min_x']
        height = bounds['max_y'] - bounds['min_y']
        
        # Normalize coordinates to start from origin
        normalized_bounds = {
            'min_x': 0,
            'min_y': 0,
            'max_x': width,
            'max_y': height
        }
        
        return {
            'width': float(width),
            'height': float(height),
            'area': float(width * height),
            'bounds': normalized_bounds,
            'units': 'meters'  # Assume meters for architectural drawings
        }
    
    def _calculate_area(self, polygon):
        """Calculate area of a polygon"""
        try:
            return polygon.area
        except:
            return 0.0
    
    def get_plan_data(self, plan_id):
        """Retrieve processed plan data"""
        return self.plans.get(plan_id)
    
    def normalize_coordinates(self, elements, bounds):
        """Normalize coordinates to start from origin"""
        offset_x = bounds['min_x']
        offset_y = bounds['min_y']
        
        normalized_elements = []
        for element in elements:
            if 'start' in element and 'end' in element:
                normalized = element.copy()
                normalized['start'] = {
                    'x': element['start']['x'] - offset_x,
                    'y': element['start']['y'] - offset_y
                }
                normalized['end'] = {
                    'x': element['end']['x'] - offset_x,
                    'y': element['end']['y'] - offset_y
                }
                normalized_elements.append(normalized)
        
        return normalized_elements