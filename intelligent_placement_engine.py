"""
Intelligent Îlot Placement Engine - Production Grade
Graph-based pathfinding and optimization algorithms
"""
import numpy as np
import networkx as nx
from shapely.geometry import Point, Polygon, LineString, box
from shapely.ops import unary_union
import matplotlib.path as mpath
from scipy.spatial.distance import pdist, squareform
from scipy.optimize import differential_evolution
import random
import math

class IntelligentPlacementEngine:
    def __init__(self):
        self.layout_profiles = {
            '10%': {'coverage': 0.10, 'box_size_factor': 0.8, 'spacing_factor': 1.5},
            '25%': {'coverage': 0.25, 'box_size_factor': 1.0, 'spacing_factor': 1.2},
            '30%': {'coverage': 0.30, 'box_size_factor': 1.1, 'spacing_factor': 1.0},
            '35%': {'coverage': 0.35, 'box_size_factor': 1.2, 'spacing_factor': 0.8}
        }
        
    def optimize_placement(self, plan_data, box_dimensions, corridor_width, layout_profile='25%'):
        """Main optimization method using advanced algorithms"""
        
        # Extract and prepare data
        dimensions = plan_data['dimensions']
        walls = plan_data.get('walls', [])
        zones = plan_data.get('zones', {})
        
        # Create spatial analysis framework
        spatial_framework = self._create_spatial_framework(dimensions, walls, zones)
        
        # Apply layout profile
        profile = self.layout_profiles.get(layout_profile, self.layout_profiles['25%'])
        adjusted_box_dims = self._adjust_box_dimensions(box_dimensions, profile, dimensions)
        
        # Generate optimal placement using multi-objective optimization
        placement_result = self._multi_objective_optimization(
            spatial_framework, adjusted_box_dims, corridor_width, profile
        )
        
        # Generate corridor network using graph algorithms
        corridor_network = self._generate_corridor_network(
            placement_result['boxes'], spatial_framework, corridor_width
        )
        
        # Calculate comprehensive statistics
        statistics = self._calculate_advanced_statistics(
            placement_result, corridor_network, dimensions, profile
        )
        
        return {
            'boxes': placement_result['boxes'],
            'corridors': corridor_network['corridors'],
            'statistics': statistics,
            'spatial_analysis': spatial_framework,
            'optimization_metadata': {
                'layout_profile': layout_profile,
                'algorithm': 'multi_objective_genetic_with_graph_pathfinding',
                'generations': placement_result.get('generations', 100),
                'final_score': placement_result.get('score', 0)
            }
        }
    
    def _create_spatial_framework(self, dimensions, walls, zones):
        """Create comprehensive spatial analysis framework"""
        width, height = dimensions['width'], dimensions['height']
        
        # Create grid for spatial analysis
        grid_resolution = min(width, height) / 50  # High resolution grid
        x_coords = np.arange(0, width, grid_resolution)
        y_coords = np.arange(0, height, grid_resolution)
        
        # Create spatial zones
        available_zones = []
        restricted_zones = []
        
        # Process walls to create obstacle geometries
        wall_obstacles = []
        for wall in walls:
            wall_line = LineString([
                (wall['start']['x'], wall['start']['y']),
                (wall['end']['x'], wall['end']['y'])
            ])
            # Create buffer around walls
            wall_obstacles.append(wall_line.buffer(0.15))  # 15cm wall thickness
        
        # Process restricted zones
        for zone in zones.get('no_entry', []):
            restricted_poly = box(zone['x'], zone['y'], 
                                zone['x'] + zone['width'], 
                                zone['y'] + zone['height'])
            restricted_zones.append(restricted_poly)
        
        # Process entry/exit zones (also restricted for placement)
        for zone in zones.get('entry_exit', []):
            entry_poly = box(zone['x'], zone['y'], 
                           zone['x'] + zone['width'], 
                           zone['y'] + zone['height'])
            restricted_zones.append(entry_poly)
        
        # Combine all obstacles
        all_obstacles = wall_obstacles + restricted_zones
        if all_obstacles:
            obstacle_union = unary_union(all_obstacles)
        else:
            obstacle_union = None
        
        # Create available space grid
        available_grid = []
        for x in x_coords:
            for y in y_coords:
                point = Point(x, y)
                
                # Check if point is inside building bounds
                if 0 <= x <= width and 0 <= y <= height:
                    # Check if point is not in obstacle zones
                    if obstacle_union is None or not obstacle_union.contains(point):
                        # Add margin from walls
                        min_wall_distance = float('inf')
                        for wall_obstacle in wall_obstacles:
                            distance = point.distance(wall_obstacle)
                            min_wall_distance = min(min_wall_distance, distance)
                        
                        if min_wall_distance > 0.5:  # 50cm minimum from walls
                            available_grid.append({
                                'x': x, 'y': y, 
                                'wall_distance': min_wall_distance,
                                'accessibility_score': self._calculate_accessibility_score(point, wall_obstacles, restricted_zones)
                            })
        
        return {
            'dimensions': dimensions,
            'available_grid': available_grid,
            'obstacles': all_obstacles,
            'wall_obstacles': wall_obstacles,
            'restricted_zones': restricted_zones,
            'grid_resolution': grid_resolution
        }
    
    def _calculate_accessibility_score(self, point, wall_obstacles, restricted_zones):
        """Calculate accessibility score for a point"""
        score = 1.0
        
        # Penalize points too close to walls
        for wall in wall_obstacles:
            distance = point.distance(wall)
            if distance < 1.0:  # Within 1 meter of wall
                score *= (distance / 1.0)
        
        # Penalize points near restricted zones
        for zone in restricted_zones:
            distance = point.distance(zone)
            if distance < 2.0:  # Within 2 meters of restricted zone
                score *= (distance / 2.0)
        
        return max(score, 0.1)  # Minimum score
    
    def _adjust_box_dimensions(self, box_dimensions, profile, building_dimensions):
        """Adjust box dimensions based on layout profile and building size"""
        base_width = box_dimensions['width']
        base_height = box_dimensions['height']
        
        # Apply profile size factor
        size_factor = profile['box_size_factor']
        
        # Scale based on building size
        building_area = building_dimensions['width'] * building_dimensions['height']
        scale_factor = min(1.0, math.sqrt(building_area / 100))  # Normalize to 100m² reference
        
        adjusted_width = base_width * size_factor * scale_factor
        adjusted_height = base_height * size_factor * scale_factor
        
        # Ensure minimum viable size
        min_size = 0.5  # 50cm minimum
        adjusted_width = max(adjusted_width, min_size)
        adjusted_height = max(adjusted_height, min_size)
        
        # Ensure boxes fit in the building
        max_width = building_dimensions['width'] / 3
        max_height = building_dimensions['height'] / 3
        
        return {
            'width': min(adjusted_width, max_width),
            'height': min(adjusted_height, max_height)
        }
    
    def _multi_objective_optimization(self, spatial_framework, box_dims, corridor_width, profile):
        """Multi-objective optimization using genetic algorithms"""
        
        available_points = spatial_framework['available_grid']
        if not available_points:
            return {'boxes': [], 'score': 0, 'generations': 0}
        
        # Estimate target number of boxes based on coverage
        total_area = spatial_framework['dimensions']['width'] * spatial_framework['dimensions']['height']
        box_area = box_dims['width'] * box_dims['height']
        target_coverage = profile['coverage']
        max_boxes = int((total_area * target_coverage) / box_area)
        max_boxes = min(max_boxes, len(available_points) // 4)  # Practical limit
        
        if max_boxes <= 0:
            return {'boxes': [], 'score': 0, 'generations': 0}
        
        # Use scipy's differential evolution for robust optimization
        bounds = []
        for i in range(max_boxes):
            bounds.extend([
                (0, len(available_points) - 1),  # Point index
                (0, 1)  # Use/don't use this box (will be thresholded)
            ])
        
        def objective_function(params):
            return -self._evaluate_placement(params, available_points, box_dims, 
                                           spatial_framework, corridor_width, profile)
        
        # Run optimization
        result = differential_evolution(
            objective_function,
            bounds,
            maxiter=50,  # Reduced for practical performance
            popsize=15,
            atol=1e-6,
            seed=42
        )
        
        # Convert result to box placements
        boxes = self._params_to_boxes(result.x, available_points, box_dims, spatial_framework)
        
        return {
            'boxes': boxes,
            'score': -result.fun,
            'generations': result.nit
        }
    
    def _evaluate_placement(self, params, available_points, box_dims, spatial_framework, corridor_width, profile):
        """Evaluate placement quality using multiple objectives"""
        
        # Convert parameters to box placements
        boxes = self._params_to_boxes(params, available_points, box_dims, spatial_framework)
        
        if not boxes:
            return 0
        
        score = 0
        
        # Objective 1: Maximize number of placed boxes
        score += len(boxes) * 10
        
        # Objective 2: Minimize overlaps (critical constraint)
        overlap_penalty = self._calculate_overlap_penalty(boxes)
        score -= overlap_penalty * 100
        
        # Objective 3: Optimize spacing and accessibility
        spacing_score = self._calculate_spacing_score(boxes, profile['spacing_factor'])
        score += spacing_score * 5
        
        # Objective 4: Maximize wall proximity (but not too close)
        wall_proximity_score = self._calculate_wall_proximity_score(boxes, spatial_framework)
        score += wall_proximity_score * 3
        
        # Objective 5: Ensure corridor connectivity potential
        connectivity_score = self._calculate_connectivity_score(boxes, corridor_width)
        score += connectivity_score * 8
        
        return score
    
    def _params_to_boxes(self, params, available_points, box_dims, spatial_framework):
        """Convert optimization parameters to box placements"""
        boxes = []
        box_width, box_height = box_dims['width'], box_dims['height']
        
        # Process parameters in pairs (point_index, use_flag)
        for i in range(0, len(params), 2):
            if i + 1 < len(params):
                point_idx = int(params[i]) % len(available_points)
                use_flag = params[i + 1]
                
                if use_flag > 0.5:  # Threshold for using this box
                    point = available_points[point_idx]
                    
                    # Create box centered on the point
                    box = {
                        'x': point['x'] - box_width / 2,
                        'y': point['y'] - box_height / 2,
                        'width': box_width,
                        'height': box_height,
                        'center': {'x': point['x'], 'y': point['y']},
                        'accessibility_score': point['accessibility_score']
                    }
                    
                    # Ensure box is within building bounds
                    building_dims = spatial_framework['dimensions']
                    if (box['x'] >= 0 and box['y'] >= 0 and 
                        box['x'] + box['width'] <= building_dims['width'] and
                        box['y'] + box['height'] <= building_dims['height']):
                        
                        # Check for overlap with existing boxes
                        overlaps = False
                        for existing_box in boxes:
                            if self._boxes_overlap(box, existing_box):
                                overlaps = True
                                break
                        
                        if not overlaps:
                            boxes.append(box)
        
        return boxes
    
    def _boxes_overlap(self, box1, box2):
        """Check if two boxes overlap"""
        return not (box1['x'] + box1['width'] <= box2['x'] or
                   box2['x'] + box2['width'] <= box1['x'] or
                   box1['y'] + box1['height'] <= box2['y'] or
                   box2['y'] + box2['height'] <= box1['y'])
    
    def _calculate_overlap_penalty(self, boxes):
        """Calculate penalty for overlapping boxes"""
        penalty = 0
        for i, box1 in enumerate(boxes):
            for j, box2 in enumerate(boxes[i+1:], i+1):
                if self._boxes_overlap(box1, box2):
                    penalty += 1
        return penalty
    
    def _calculate_spacing_score(self, boxes, spacing_factor):
        """Calculate score based on box spacing"""
        if len(boxes) < 2:
            return 1.0
        
        centers = [(box['center']['x'], box['center']['y']) for box in boxes]
        distances = pdist(centers)
        
        target_distance = 2.0 * spacing_factor  # Target spacing in meters
        score = 0
        
        for distance in distances:
            if distance > target_distance * 0.5:  # Not too close
                if distance <= target_distance * 2:  # Not too far
                    score += 1
                else:
                    score += 0.5  # Penalty for being too far
            else:
                score -= 0.5  # Penalty for being too close
        
        return score / len(distances) if distances.size > 0 else 0
    
    def _calculate_wall_proximity_score(self, boxes, spatial_framework):
        """Calculate score based on proximity to walls"""
        wall_obstacles = spatial_framework['wall_obstacles']
        if not wall_obstacles:
            return 0
        
        score = 0
        for box in boxes:
            box_center = Point(box['center']['x'], box['center']['y'])
            
            min_distance = float('inf')
            for wall in wall_obstacles:
                distance = box_center.distance(wall)
                min_distance = min(min_distance, distance)
            
            # Optimal distance: close to walls but not too close
            optimal_distance = 1.0  # 1 meter
            if 0.5 <= min_distance <= 2.0:
                score += 1.0 - abs(min_distance - optimal_distance) / optimal_distance
        
        return score / len(boxes) if boxes else 0
    
    def _calculate_connectivity_score(self, boxes, corridor_width):
        """Calculate score based on potential corridor connectivity"""
        if len(boxes) < 2:
            return 1.0
        
        # Create adjacency graph based on corridor potential
        connectivity_score = 0
        
        for i, box1 in enumerate(boxes):
            for j, box2 in enumerate(boxes[i+1:], i+1):
                distance = math.sqrt(
                    (box1['center']['x'] - box2['center']['x'])**2 + 
                    (box1['center']['y'] - box2['center']['y'])**2
                )
                
                # Score based on reasonable corridor distance
                if corridor_width * 2 <= distance <= corridor_width * 10:
                    connectivity_score += 1
        
        return connectivity_score / (len(boxes) * (len(boxes) - 1) / 2) if len(boxes) > 1 else 0
    
    def _generate_corridor_network(self, boxes, spatial_framework, corridor_width):
        """Generate corridor network using graph-based pathfinding"""
        if len(boxes) < 2:
            return {'corridors': [], 'network_graph': None}
        
        # Create graph with boxes as nodes
        G = nx.Graph()
        
        # Add nodes (box centers)
        for i, box in enumerate(boxes):
            G.add_node(i, pos=(box['center']['x'], box['center']['y']))
        
        # Calculate minimum spanning tree for efficient connectivity
        box_centers = [(box['center']['x'], box['center']['y']) for box in boxes]
        mst_graph = self._create_minimum_spanning_tree(box_centers)
        
        # Generate corridors based on MST
        corridors = []
        for edge in mst_graph.edges():
            box1, box2 = boxes[edge[0]], boxes[edge[1]]
            corridor = self._create_corridor_between_boxes(box1, box2, corridor_width)
            if corridor:
                corridors.append(corridor)
        
        return {
            'corridors': corridors,
            'network_graph': mst_graph,
            'connectivity_matrix': nx.adjacency_matrix(mst_graph).todense()
        }
    
    def _create_minimum_spanning_tree(self, points):
        """Create minimum spanning tree from points"""
        G = nx.Graph()
        
        # Add all points as nodes
        for i, point in enumerate(points):
            G.add_node(i, pos=point)
        
        # Add edges with weights as distances
        for i in range(len(points)):
            for j in range(i + 1, len(points)):
                distance = math.sqrt(
                    (points[i][0] - points[j][0])**2 + 
                    (points[i][1] - points[j][1])**2
                )
                G.add_edge(i, j, weight=distance)
        
        # Return minimum spanning tree
        return nx.minimum_spanning_tree(G)
    
    def _create_corridor_between_boxes(self, box1, box2, corridor_width):
        """Create corridor connecting two boxes"""
        # Calculate corridor path (simplified - straight line)
        center1 = (box1['center']['x'], box1['center']['y'])
        center2 = (box2['center']['x'], box2['center']['y'])
        
        # Calculate corridor dimensions
        dx = center2[0] - center1[0]
        dy = center2[1] - center1[1]
        distance = math.sqrt(dx**2 + dy**2)
        
        if distance == 0:
            return None
        
        # Create corridor rectangle
        corridor_length = distance
        
        # Position corridor
        corridor_x = min(center1[0], center2[0]) - corridor_width / 2
        corridor_y = min(center1[1], center2[1]) - corridor_width / 2
        
        # For simplicity, create horizontal/vertical corridors
        if abs(dx) > abs(dy):  # More horizontal
            corridor = {
                'x': min(center1[0], center2[0]),
                'y': center1[1] - corridor_width / 2,
                'width': abs(dx),
                'height': corridor_width,
                'type': 'horizontal'
            }
        else:  # More vertical
            corridor = {
                'x': center1[0] - corridor_width / 2,
                'y': min(center1[1], center2[1]),
                'width': corridor_width,
                'height': abs(dy),
                'type': 'vertical'
            }
        
        return corridor
    
    def _calculate_advanced_statistics(self, placement_result, corridor_network, dimensions, profile):
        """Calculate comprehensive statistics"""
        boxes = placement_result['boxes']
        corridors = corridor_network['corridors']
        
        total_area = dimensions['width'] * dimensions['height']
        box_area = sum(box['width'] * box['height'] for box in boxes)
        corridor_area = sum(corridor['width'] * corridor['height'] for corridor in corridors)
        
        # Calculate various metrics
        utilization_rate = (box_area / total_area) * 100 if total_area > 0 else 0
        corridor_efficiency = (corridor_area / (box_area + corridor_area)) * 100 if (box_area + corridor_area) > 0 else 0
        
        # Calculate spacing metrics
        if len(boxes) > 1:
            centers = [(box['center']['x'], box['center']['y']) for box in boxes]
            distances = pdist(centers)
            avg_spacing = np.mean(distances)
            min_spacing = np.min(distances)
            max_spacing = np.max(distances)
        else:
            avg_spacing = min_spacing = max_spacing = 0
        
        return {
            'total_boxes': len(boxes),
            'total_corridors': len(corridors),
            'total_area': total_area,
            'box_area': box_area,
            'corridor_area': corridor_area,
            'utilization_rate': utilization_rate,
            'corridor_efficiency': corridor_efficiency,
            'efficiency_score': placement_result.get('score', 0),
            'average_box_spacing': avg_spacing,
            'min_box_spacing': min_spacing,
            'max_box_spacing': max_spacing,
            'wasted_space': total_area - box_area - corridor_area,
            'layout_profile': profile,
            'connectivity_ratio': len(corridors) / len(boxes) if len(boxes) > 0 else 0
        }
    
    def _validate_constraints(self, new_position, new_dimensions, plan_data):
        """Advanced real-time constraint validation"""
        violations = []
        
        # Create the new box geometry
        new_box = {
            'x': new_position['x'],
            'y': new_position['y'],
            'width': new_dimensions['width'],
            'height': new_dimensions['height']
        }
        
        # Check wall proximity constraints
        walls = plan_data.get('walls', [])
        min_wall_distance = 0.5  # minimum distance from walls
        
        for wall in walls:
            wall_line = LineString([(wall['start']['x'], wall['start']['y']), 
                                   (wall['end']['x'], wall['end']['y'])])
            box_polygon = Polygon([
                (new_box['x'], new_box['y']),
                (new_box['x'] + new_box['width'], new_box['y']),
                (new_box['x'] + new_box['width'], new_box['y'] + new_box['height']),
                (new_box['x'], new_box['y'] + new_box['height'])
            ])
            
            distance = wall_line.distance(box_polygon)
            if distance < min_wall_distance:
                violations.append(f"Too close to wall (distance: {distance:.2f}m)")
        
        # Check boundary constraints
        dimensions = plan_data['dimensions']
        margin = 0.3
        
        if new_box['x'] < margin:
            violations.append("Too close to left boundary")
        if new_box['y'] < margin:
            violations.append("Too close to bottom boundary")
        if new_box['x'] + new_box['width'] > dimensions['width'] - margin:
            violations.append("Too close to right boundary")
        if new_box['y'] + new_box['height'] > dimensions['height'] - margin:
            violations.append("Too close to top boundary")
        
        # Check restricted zones
        zones = plan_data.get('zones', {})
        restricted_zones = zones.get('no_entry', [])
        
        for zone in restricted_zones:
            if 'polygon' in zone:
                zone_polygon = Polygon(zone['polygon'])
                box_polygon = Polygon([
                    (new_box['x'], new_box['y']),
                    (new_box['x'] + new_box['width'], new_box['y']),
                    (new_box['x'] + new_box['width'], new_box['y'] + new_box['height']),
                    (new_box['x'], new_box['y'] + new_box['height'])
                ])
                
                if zone_polygon.intersects(box_polygon):
                    violations.append("Intersects with restricted zone")
        
        return len(violations) == 0
    
    def _boxes_overlap(self, box1, box2):
        """Check if two boxes overlap"""
        return not (box1['x'] + box1['width'] <= box2['x'] or
                   box2['x'] + box2['width'] <= box1['x'] or
                   box1['y'] + box1['height'] <= box2['y'] or
                   box2['y'] + box2['height'] <= box1['y'])
    
    def _generate_constraint_suggestions(self, violations):
        """Generate intelligent suggestions for constraint violations"""
        suggestions = []
        
        for violation in violations:
            if "too close to wall" in violation.lower():
                suggestions.append("Move the îlot further from the nearest wall (minimum 0.5m distance)")
            elif "boundary" in violation.lower():
                suggestions.append("Keep îlots within the safety margin (0.3m from boundaries)")
            elif "overlap" in violation.lower():
                suggestions.append("Ensure minimum spacing between îlots (1.0m recommended)")
            elif "restricted zone" in violation.lower():
                suggestions.append("Move îlot away from no-entry zones or architectural constraints")
            else:
                suggestions.append("Adjust îlot position to meet placement requirements")
        
        # Add general optimization suggestions
        if len(violations) > 0:
            suggestions.append("Consider using auto-optimization to find the best placement")
            suggestions.append("Check the constraint visualization overlay for detailed guidance")
        
        return suggestions