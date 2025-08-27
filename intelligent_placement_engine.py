
import numpy as np
import random
from typing import Dict, List, Tuple, Any, Optional
from scipy.spatial.distance import cdist
from scipy.optimize import minimize
import networkx as nx
from shapely.geometry import Point, Polygon, LineString, box
from shapely.ops import unary_union
import logging

class IntelligentPlacementEngine:
    """Production-grade intelligent placement engine with layout profiles and optimization algorithms"""
    
    def __init__(self):
        self.layout_profiles = {
            '10%': {'coverage': 0.10, 'ilot_density': 'sparse', 'min_spacing': 2.0},
            '25%': {'coverage': 0.25, 'ilot_density': 'normal', 'min_spacing': 1.5},
            '30%': {'coverage': 0.30, 'ilot_density': 'dense', 'min_spacing': 1.2},
            '35%': {'coverage': 0.35, 'ilot_density': 'very_dense', 'min_spacing': 1.0}
        }
        
        self.ilot_categories = {
            'small': {'width': 2.0, 'height': 2.5, 'color': '#10B981', 'priority': 3},
            'medium': {'width': 3.0, 'height': 4.0, 'color': '#059669', 'priority': 2},
            'large': {'width': 4.0, 'height': 5.0, 'color': '#047857', 'priority': 1}
        }
        
        self.corridor_config = {
            'default_width': 1.2,
            'min_width': 1.0,
            'max_width': 2.0,
            'color': '#EC4899',
            'label_color': '#BE185D'
        }
    
    def optimize_placement(self, plan_data: Dict[str, Any], box_dimensions: Dict[str, float], 
                         corridor_width: float, layout_profile: str = '25%') -> Dict[str, Any]:
        """Optimize placement of îlots using intelligent algorithms"""
        try:
            # Get layout profile configuration
            profile_config = self.layout_profiles.get(layout_profile, self.layout_profiles['25%'])
            
            # Create building geometry from plan data
            building_geometry = self._create_building_geometry(plan_data)
            
            # Identify available placement zones
            available_zones = self._identify_available_zones(plan_data, building_geometry)
            
            # Generate optimal îlot placement
            ilots = self._generate_optimal_ilot_placement(
                available_zones, box_dimensions, profile_config, plan_data
            )
            
            # Generate corridor network using graph algorithms
            corridors = self._generate_corridor_network(ilots, corridor_width, building_geometry)
            
            # Calculate comprehensive statistics
            statistics = self._calculate_optimization_statistics(
                ilots, corridors, building_geometry, plan_data
            )
            
            return {
                'success': True,
                'boxes': ilots,  # Keeping 'boxes' for compatibility
                'ilots': ilots,
                'corridors': corridors,
                'statistics': statistics,
                'layout_profile': layout_profile,
                'optimization_metadata': {
                    'algorithm': 'intelligent_placement_with_graph_optimization',
                    'profile_config': profile_config,
                    'total_iterations': getattr(self, '_last_iterations', 100),
                    'convergence_score': getattr(self, '_last_convergence', 0.95)
                }
            }
            
        except Exception as e:
            logging.error(f"Error in optimize_placement: {e}")
            raise
    
    def _create_building_geometry(self, plan_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create comprehensive building geometry from plan data"""
        geometry = {
            'walls': [],
            'restricted_zones': [],
            'entrance_zones': [],
            'boundary': None,
            'total_area': 0
        }
        
        # Process walls
        wall_lines = []
        for wall in plan_data.get('walls', []):
            if wall.get('type') == 'line':
                start = wall['start']
                end = wall['end']
                line = LineString([(start['x'], start['y']), (end['x'], end['y'])])
                wall_lines.append(line)
                geometry['walls'].append({
                    'geometry': line,
                    'thickness': wall.get('render_style', {}).get('thickness', 3),
                    'type': 'wall'
                })
        
        # Process zones
        for zone in plan_data.get('zones', []):
            zone_type = zone.get('zone_type', 'general')
            if zone.get('type') == 'polyline' and zone.get('points'):
                points = [(p['x'], p['y']) for p in zone['points']]
                if len(points) >= 3:
                    polygon = Polygon(points)
                    
                    if zone_type == 'restricted':
                        geometry['restricted_zones'].append({
                            'geometry': polygon,
                            'type': 'restricted'
                        })
                    elif zone_type == 'entrance':
                        geometry['entrance_zones'].append({
                            'geometry': polygon,
                            'type': 'entrance'
                        })
        
        # Create building boundary
        dims = plan_data.get('dimensions', {})
        if dims:
            min_x = dims.get('min_x', 0)
            min_y = dims.get('min_y', 0)
            max_x = dims.get('max_x', dims.get('width', 50))
            max_y = dims.get('max_y', dims.get('height', 40))
            
            geometry['boundary'] = box(min_x, min_y, max_x, max_y)
            geometry['total_area'] = (max_x - min_x) * (max_y - min_y)
        
        return geometry
    
    def _identify_available_zones(self, plan_data: Dict[str, Any], 
                                building_geometry: Dict[str, Any]) -> List[Polygon]:
        """Identify zones available for îlot placement"""
        available_zones = []
        
        if not building_geometry['boundary']:
            return available_zones
        
        # Start with the full building area
        available_area = building_geometry['boundary']
        
        # Remove restricted zones
        for restricted in building_geometry['restricted_zones']:
            available_area = available_area.difference(restricted['geometry'])
        
        # Remove entrance zones
        for entrance in building_geometry['entrance_zones']:
            available_area = available_area.difference(entrance['geometry'])
        
        # Create buffer around walls to prevent îlots from being too close
        wall_buffer_zones = []
        for wall in building_geometry['walls']:
            buffer_zone = wall['geometry'].buffer(0.5)  # 0.5m buffer
            wall_buffer_zones.append(buffer_zone)
        
        if wall_buffer_zones:
            wall_union = unary_union(wall_buffer_zones)
            # Only remove wall buffers near entrances, not all walls
            available_area = available_area.difference(wall_union)
        
        # Convert to list of polygons
        if hasattr(available_area, 'geoms'):
            available_zones = [geom for geom in available_area.geoms if isinstance(geom, Polygon)]
        elif isinstance(available_area, Polygon):
            available_zones = [available_area]
        
        return available_zones
    
    def _generate_optimal_ilot_placement(self, available_zones: List[Polygon], 
                                       box_dimensions: Dict[str, float],
                                       profile_config: Dict[str, Any],
                                       plan_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate optimal îlot placement using advanced algorithms"""
        ilots = []
        
        if not available_zones:
            return ilots
        
        # Calculate target coverage area
        total_available_area = sum(zone.area for zone in available_zones)
        target_area = total_available_area * profile_config['coverage']
        
        # Determine îlot mix based on profile
        ilot_mix = self._determine_ilot_mix(profile_config['ilot_density'])
        
        # Calculate required number of îlots
        avg_ilot_area = sum(
            self.ilot_categories[cat]['width'] * self.ilot_categories[cat]['height'] * ratio 
            for cat, ratio in ilot_mix.items()
        )
        target_ilot_count = int(target_area / avg_ilot_area)
        
        # Generate îlots using optimization
        placed_ilots = 0
        max_attempts = target_ilot_count * 3
        attempts = 0
        
        while placed_ilots < target_ilot_count and attempts < max_attempts:
            attempts += 1
            
            # Select îlot category based on mix
            category = self._select_ilot_category(ilot_mix)
            ilot_config = self.ilot_categories[category]
            
            # Try to place îlot in best available position
            best_position = self._find_optimal_position(
                available_zones, ilot_config, ilots, profile_config['min_spacing']
            )
            
            if best_position:
                ilot = {
                    'x': best_position[0],
                    'y': best_position[1],
                    'width': ilot_config['width'],
                    'height': ilot_config['height'],
                    'category': category,
                    'color': ilot_config['color'],
                    'id': f"ilot_{placed_ilots + 1}",
                    'area': ilot_config['width'] * ilot_config['height']
                }
                
                ilots.append(ilot)
                placed_ilots += 1
        
        # Store optimization metadata
        self._last_iterations = attempts
        self._last_convergence = placed_ilots / target_ilot_count if target_ilot_count > 0 else 0
        
        return ilots
    
    def _determine_ilot_mix(self, density: str) -> Dict[str, float]:
        """Determine îlot category mix based on density profile"""
        mixes = {
            'sparse': {'small': 0.6, 'medium': 0.3, 'large': 0.1},
            'normal': {'small': 0.4, 'medium': 0.5, 'large': 0.1},
            'dense': {'small': 0.3, 'medium': 0.5, 'large': 0.2},
            'very_dense': {'small': 0.2, 'medium': 0.5, 'large': 0.3}
        }
        return mixes.get(density, mixes['normal'])
    
    def _select_ilot_category(self, mix: Dict[str, float]) -> str:
        """Select îlot category based on probability mix"""
        rand_val = random.random()
        cumulative = 0
        
        for category, probability in mix.items():
            cumulative += probability
            if rand_val <= cumulative:
                return category
        
        return 'medium'  # Fallback
    
    def _find_optimal_position(self, available_zones: List[Polygon], ilot_config: Dict[str, Any],
                             existing_ilots: List[Dict[str, Any]], min_spacing: float) -> Optional[Tuple[float, float]]:
        """Find optimal position for îlot placement"""
        width = ilot_config['width']
        height = ilot_config['height']
        
        best_position = None
        best_score = -1
        
        for zone in available_zones:
            # Generate candidate positions within zone
            bounds = zone.bounds
            min_x, min_y, max_x, max_y = bounds
            
            # Try multiple positions within the zone
            for _ in range(20):  # 20 random attempts per zone
                x = random.uniform(min_x + width/2, max_x - width/2)
                y = random.uniform(min_y + height/2, max_y - height/2)
                
                # Create îlot rectangle
                ilot_rect = box(x - width/2, y - height/2, x + width/2, y + height/2)
                
                # Check if îlot fits entirely within zone
                if not zone.contains(ilot_rect):
                    continue
                
                # Check spacing from existing îlots
                valid_spacing = True
                for existing in existing_ilots:
                    existing_rect = box(
                        existing['x'] - existing['width']/2,
                        existing['y'] - existing['height']/2,
                        existing['x'] + existing['width']/2,
                        existing['y'] + existing['height']/2
                    )
                    
                    if ilot_rect.distance(existing_rect) < min_spacing:
                        valid_spacing = False
                        break
                
                if not valid_spacing:
                    continue
                
                # Calculate placement score (higher is better)
                score = self._calculate_placement_score(x, y, zone, existing_ilots)
                
                if score > best_score:
                    best_score = score
                    best_position = (x, y)
        
        return best_position
    
    def _calculate_placement_score(self, x: float, y: float, zone: Polygon, 
                                 existing_ilots: List[Dict[str, Any]]) -> float:
        """Calculate placement score for a position"""
        score = 0
        
        # Distance from zone centroid (prefer center)
        centroid = zone.centroid
        distance_to_center = Point(x, y).distance(centroid)
        score += max(0, 10 - distance_to_center)
        
        # Spacing from existing îlots (prefer even distribution)
        if existing_ilots:
            min_distance = min(
                Point(x, y).distance(Point(ilot['x'], ilot['y'])) 
                for ilot in existing_ilots
            )
            score += min_distance
        
        # Distance from zone edges (prefer not too close to edges)
        distance_to_edge = zone.boundary.distance(Point(x, y))
        score += distance_to_edge
        
        return score
    
    def _generate_corridor_network(self, ilots: List[Dict[str, Any]], corridor_width: float,
                                 building_geometry: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate corridor network using graph-based pathfinding and MST algorithms"""
        corridors = []
        
        if len(ilots) < 2:
            return corridors
        
        # Create graph of îlot positions
        G = nx.Graph()
        
        # Add îlots as nodes
        for i, ilot in enumerate(ilots):
            G.add_node(i, pos=(ilot['x'], ilot['y']), ilot=ilot)
        
        # Add edges based on visibility and distance
        for i in range(len(ilots)):
            for j in range(i + 1, len(ilots)):
                ilot1, ilot2 = ilots[i], ilots[j]
                
                # Check if direct connection is possible
                line = LineString([(ilot1['x'], ilot1['y']), (ilot2['x'], ilot2['y'])])
                
                # Check if line intersects walls or restricted areas
                valid_connection = True
                for wall in building_geometry.get('walls', []):
                    if hasattr(wall.get('geometry'), 'intersects') and line.intersects(wall['geometry']):
                        valid_connection = False
                        break
                
                if valid_connection:
                    distance = Point(ilot1['x'], ilot1['y']).distance(Point(ilot2['x'], ilot2['y']))
                    G.add_edge(i, j, weight=distance)
        
        # Generate minimum spanning tree for efficient corridor network
        if G.number_of_edges() > 0:
            mst = nx.minimum_spanning_tree(G)
            
            # Create corridors from MST edges
            for edge in mst.edges():
                i, j = edge
                ilot1, ilot2 = ilots[i], ilots[j]
                
                corridor = self._create_corridor(ilot1, ilot2, corridor_width)
                if corridor:
                    corridors.append(corridor)
        else:
            # Fallback: create grid-based corridors
            corridors = self._create_grid_corridors(ilots, corridor_width, building_geometry)
        
        return corridors
    
    def _create_grid_corridors(self, ilots: List[Dict[str, Any]], corridor_width: float,
                              building_geometry: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create grid-based corridor system when MST fails"""
        corridors = []
        
        if not ilots:
            return corridors
        
        # Group îlots by approximate rows and columns
        y_positions = sorted(set(ilot['y'] for ilot in ilots), key=lambda y: round(y))
        x_positions = sorted(set(ilot['x'] for ilot in ilots), key=lambda x: round(x))
        
        boundary = building_geometry.get('boundary')
        if boundary:
            bounds = boundary.bounds
        else:
            bounds = (
                min(x_positions) - 5, min(y_positions) - 5,
                max(x_positions) + 5, max(y_positions) + 5
            )
        
        # Create horizontal corridors
        for y_pos in y_positions:
            corridors.append({
                'type': 'horizontal',
                'start': {'x': bounds[0], 'y': y_pos},
                'end': {'x': bounds[2], 'y': y_pos},
                'width': corridor_width,
                'length': bounds[2] - bounds[0],
                'area': (bounds[2] - bounds[0]) * corridor_width,
                'color': self.corridor_config['color'],
                'id': f"h_corridor_{len(corridors)}"
            })
        
        # Create vertical corridors
        for x_pos in x_positions:
            corridors.append({
                'type': 'vertical',
                'start': {'x': x_pos, 'y': bounds[1]},
                'end': {'x': x_pos, 'y': bounds[3]},
                'width': corridor_width,
                'length': bounds[3] - bounds[1],
                'area': (bounds[3] - bounds[1]) * corridor_width,
                'color': self.corridor_config['color'],
                'id': f"v_corridor_{len(corridors)}"
            })
        
        return corridors
    
    def _create_corridor(self, ilot1: Dict[str, Any], ilot2: Dict[str, Any], 
                        width: float) -> Dict[str, Any]:
        """Create corridor between two îlots"""
        # Calculate corridor path
        start_x, start_y = ilot1['x'], ilot1['y']
        end_x, end_y = ilot2['x'], ilot2['y']
        
        # Calculate corridor length and area
        length = Point(start_x, start_y).distance(Point(end_x, end_y))
        area = length * width
        
        return {
            'start': {'x': start_x, 'y': start_y},
            'end': {'x': end_x, 'y': end_y},
            'width': width,
            'length': length,
            'area': area,
            'color': self.corridor_config['color'],
            'label': f"{area:.2f}m²",
            'id': f"corridor_{ilot1['id']}_{ilot2['id']}"
        }
    
    def _calculate_optimization_statistics(self, ilots: List[Dict[str, Any]], 
                                         corridors: List[Dict[str, Any]],
                                         building_geometry: Dict[str, Any],
                                         plan_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate comprehensive optimization statistics"""
        total_building_area = building_geometry.get('total_area', 1)
        
        # Calculate areas
        total_ilot_area = sum(ilot['area'] for ilot in ilots)
        total_corridor_area = sum(corridor['area'] for corridor in corridors)
        
        # Calculate utilization rates
        ilot_utilization = (total_ilot_area / total_building_area) * 100 if total_building_area > 0 else 0
        corridor_utilization = (total_corridor_area / total_building_area) * 100 if total_building_area > 0 else 0
        total_utilization = ilot_utilization + corridor_utilization
        
        # Calculate efficiency score
        efficiency_score = min(100, (len(ilots) * 2 + len(corridors)) * 5)  # Arbitrary scoring
        
        # Category breakdown
        category_stats = {}
        for category in self.ilot_categories.keys():
            category_ilots = [ilot for ilot in ilots if ilot.get('category') == category]
            category_stats[category] = {
                'count': len(category_ilots),
                'total_area': sum(ilot['area'] for ilot in category_ilots)
            }
        
        return {
            'total_boxes': len(ilots),
            'total_ilots': len(ilots),
            'total_corridors': len(corridors),
            'total_area': total_building_area,
            'total_ilot_area': total_ilot_area,
            'total_corridor_area': total_corridor_area,
            'utilization_rate': total_utilization,
            'ilot_utilization_rate': ilot_utilization,
            'corridor_utilization_rate': corridor_utilization,
            'efficiency_score': efficiency_score,
            'category_breakdown': category_stats,
            'average_corridor_length': sum(c['length'] for c in corridors) / len(corridors) if corridors else 0
        }
    
    def _validate_constraints(self, position: Dict[str, float], dimensions: Dict[str, float], plan_data: Dict[str, Any]) -> bool:
        """Validate position and dimensions against constraints"""
        try:
            # Check if position is within building bounds
            building_dims = plan_data.get('dimensions', {})
            if position['x'] < 0 or position['y'] < 0:
                return False
            if position['x'] + dimensions['width'] > building_dims.get('width', 100):
                return False
            if position['y'] + dimensions['height'] > building_dims.get('height', 100):
                return False
            
            # Check wall proximity (simplified)
            for wall in plan_data.get('walls', []):
                if wall.get('type') == 'line':
                    # Simple proximity check - would be more sophisticated in production
                    start = wall['start']
                    end = wall['end']
                    # Check if too close to walls (within 0.5m)
                    min_distance = 0.5
                    # This is a simplified check
                    if (abs(position['x'] - start['x']) < min_distance or 
                        abs(position['y'] - start['y']) < min_distance):
                        return False
            
            return True
        except Exception as e:
            logging.error(f"Error validating constraints: {e}")
            return False
    
    def _boxes_overlap(self, box1: Dict[str, Any], box2: Dict[str, Any]) -> bool:
        """Check if two boxes overlap"""
        try:
            # Get box coordinates
            b1_x1, b1_y1 = box1.get('x', 0), box1.get('y', 0)
            b1_x2 = b1_x1 + box1.get('width', 0)
            b1_y2 = b1_y1 + box1.get('height', 0)
            
            b2_x1, b2_y1 = box2.get('x', 0), box2.get('y', 0)
            b2_x2 = b2_x1 + box2.get('width', 0)
            b2_y2 = b2_y1 + box2.get('height', 0)
            
            # Check for overlap
            return not (b1_x2 <= b2_x1 or b2_x2 <= b1_x1 or b1_y2 <= b2_y1 or b2_y2 <= b1_y1)
        except Exception as e:
            logging.error(f"Error checking box overlap: {e}")
            return False
    
    def _generate_constraint_suggestions(self, violations: List[str]) -> List[str]:
        """Generate suggestions to fix constraint violations"""
        suggestions = []
        
        for violation in violations:
            if 'overlap' in violation.lower():
                suggestions.append("Try reducing box size or adjusting positions")
                suggestions.append("Consider using the 'spacious' layout profile")
            elif 'wall' in violation.lower():
                suggestions.append("Move boxes further from walls (minimum 0.5m clearance)")
                suggestions.append("Increase corridor width to improve accessibility")
            elif 'zone' in violation.lower():
                suggestions.append("Avoid placing boxes in restricted zones")
                suggestions.append("Use the zone indicators to identify valid placement areas")
        
        if not suggestions:
            suggestions = [
                "Try using a different layout profile",
                "Adjust box dimensions to better fit the space",
                "Check that your floor plan has valid dimensions"
            ]
        
        return suggestions
