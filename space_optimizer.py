
import numpy as np
from scipy.spatial.distance import cdist
from typing import List, Dict, Tuple
import random

class SpaceOptimizer:
    def __init__(self):
        self.corridor_width = 1.2  # Default corridor width in meters
        
    def optimize_placement(self, plan_data: Dict, box_dimensions: Dict, corridor_width: float) -> Dict:
        """
        Optimize placement of island boxes with automatic corridor generation
        """
        self.corridor_width = corridor_width
        
        # Extract plan boundaries and constraints
        plan_bounds = self._get_plan_boundaries(plan_data)
        obstacles = self._get_obstacles(plan_data)
        
        # Generate potential box positions
        potential_positions = self._generate_potential_positions(
            plan_bounds, box_dimensions, obstacles
        )
        
        # Use genetic algorithm to find optimal placement
        best_solution = self._genetic_algorithm_placement(
            potential_positions, box_dimensions, plan_bounds, obstacles
        )
        
        # Generate corridors for the solution
        corridors = self._generate_corridors(best_solution, box_dimensions)
        
        # Calculate statistics
        statistics = self._calculate_statistics(
            best_solution, corridors, plan_bounds, box_dimensions
        )
        
        return {
            'boxes': best_solution,
            'corridors': corridors,
            'statistics': statistics
        }
    
    def _get_plan_boundaries(self, plan_data: Dict) -> Dict:
        """Extract plan boundaries from wall data"""
        walls = plan_data['walls']
        
        if not walls:
            return {
                'min_x': 0, 'max_x': plan_data['dimensions']['width'],
                'min_y': 0, 'max_y': plan_data['dimensions']['height']
            }
        
        all_x = []
        all_y = []
        
        for wall in walls:
            all_x.extend([wall['start']['x'], wall['end']['x']])
            all_y.extend([wall['start']['y'], wall['end']['y']])
        
        return {
            'min_x': min(all_x),
            'max_x': max(all_x),
            'min_y': min(all_y),
            'max_y': max(all_y)
        }
    
    def _get_obstacles(self, plan_data: Dict) -> List[Dict]:
        """Extract obstacles (no-entry zones, walls, etc.)"""
        obstacles = []
        
        # Add no-entry zones
        for zone in plan_data['zones']['no_entry']:
            obstacles.append({
                'type': 'no_entry',
                'x': zone['x'],
                'y': zone['y'],
                'width': zone['width'],
                'height': zone['height']
            })
        
        # Add wall obstacles (simplified)
        for wall in plan_data['walls']:
            # Convert lines to rectangular obstacles
            wall_thickness = wall.get('thickness', 0.2)
            obstacles.append({
                'type': 'wall',
                'x': min(wall['start']['x'], wall['end']['x']) - wall_thickness/2,
                'y': min(wall['start']['y'], wall['end']['y']) - wall_thickness/2,
                'width': abs(wall['end']['x'] - wall['start']['x']) + wall_thickness,
                'height': abs(wall['end']['y'] - wall['start']['y']) + wall_thickness
            })
        
        return obstacles
    
    def _generate_potential_positions(self, plan_bounds: Dict, box_dimensions: Dict, obstacles: List[Dict]) -> List[Dict]:
        """Generate grid of potential box positions"""
        positions = []
        
        step_size = 0.5  # 50cm grid
        box_width = box_dimensions['width']
        box_height = box_dimensions['height']
        
        x = plan_bounds['min_x']
        while x + box_width <= plan_bounds['max_x']:
            y = plan_bounds['min_y']
            while y + box_height <= plan_bounds['max_y']:
                # Check if position conflicts with obstacles
                if not self._position_conflicts_with_obstacles(x, y, box_width, box_height, obstacles):
                    positions.append({'x': x, 'y': y})
                y += step_size
            x += step_size
        
        return positions
    
    def _position_conflicts_with_obstacles(self, x: float, y: float, width: float, height: float, obstacles: List[Dict]) -> bool:
        """Check if a position conflicts with any obstacles"""
        for obstacle in obstacles:
            if self._rectangles_overlap(
                x, y, width, height,
                obstacle['x'], obstacle['y'], obstacle['width'], obstacle['height']
            ):
                return True
        return False
    
    def _rectangles_overlap(self, x1: float, y1: float, w1: float, h1: float,
                          x2: float, y2: float, w2: float, h2: float) -> bool:
        """Check if two rectangles overlap"""
        return not (x1 >= x2 + w2 or x2 >= x1 + w1 or y1 >= y2 + h2 or y2 >= y1 + h1)
    
    def _genetic_algorithm_placement(self, potential_positions: List[Dict], box_dimensions: Dict,
                                   plan_bounds: Dict, obstacles: List[Dict]) -> List[Dict]:
        """Use genetic algorithm to find optimal box placement"""
        
        population_size = 50
        generations = 100
        mutation_rate = 0.1
        
        # Initialize population
        population = []
        for _ in range(population_size):
            individual = self._create_random_individual(potential_positions, box_dimensions)
            population.append(individual)
        
        # Evolution loop
        for generation in range(generations):
            # Evaluate fitness
            fitness_scores = [self._evaluate_fitness(individual, box_dimensions) for individual in population]
            
            # Selection and reproduction
            new_population = []
            for _ in range(population_size):
                parent1 = self._tournament_selection(population, fitness_scores)
                parent2 = self._tournament_selection(population, fitness_scores)
                
                child = self._crossover(parent1, parent2)
                if random.random() < mutation_rate:
                    child = self._mutate(child, potential_positions)
                
                new_population.append(child)
            
            population = new_population
        
        # Return best solution
        final_fitness = [self._evaluate_fitness(individual, box_dimensions) for individual in population]
        best_index = np.argmax(final_fitness)
        return population[best_index]
    
    def _create_random_individual(self, potential_positions: List[Dict], box_dimensions: Dict) -> List[Dict]:
        """Create a random individual (solution)"""
        # Randomly select positions ensuring no overlaps
        selected_positions = []
        available_positions = potential_positions.copy()
        
        while available_positions and len(selected_positions) < 50:  # Max 50 boxes
            pos = random.choice(available_positions)
            selected_positions.append(pos)
            
            # Remove conflicting positions
            available_positions = [
                p for p in available_positions
                if not self._rectangles_overlap(
                    pos['x'], pos['y'], box_dimensions['width'], box_dimensions['height'],
                    p['x'], p['y'], box_dimensions['width'], box_dimensions['height']
                )
            ]
        
        return selected_positions
    
    def _evaluate_fitness(self, individual: List[Dict], box_dimensions: Dict) -> float:
        """Evaluate fitness of a solution"""
        if not individual:
            return 0
        
        score = 0
        
        # Reward number of boxes placed
        score += len(individual) * 100
        
        # Reward compact arrangements
        if len(individual) > 1:
            centers = [(pos['x'] + box_dimensions['width']/2, pos['y'] + box_dimensions['height']/2) 
                      for pos in individual]
            distances = cdist(centers, centers)
            avg_distance = np.mean(distances[distances > 0])
            score += max(0, 1000 - avg_distance * 10)  # Prefer closer arrangements
        
        # Reward alignment (grid-like patterns)
        alignment_score = self._calculate_alignment_score(individual)
        score += alignment_score * 50
        
        return score
    
    def _calculate_alignment_score(self, individual: List[Dict]) -> float:
        """Calculate how well-aligned the boxes are"""
        if len(individual) < 2:
            return 0
        
        x_coords = [pos['x'] for pos in individual]
        y_coords = [pos['y'] for pos in individual]
        
        # Count aligned positions
        alignment_score = 0
        tolerance = 0.1  # 10cm tolerance
        
        for x in x_coords:
            aligned_count = sum(1 for other_x in x_coords if abs(x - other_x) < tolerance)
            if aligned_count > 1:
                alignment_score += aligned_count - 1
        
        for y in y_coords:
            aligned_count = sum(1 for other_y in y_coords if abs(y - other_y) < tolerance)
            if aligned_count > 1:
                alignment_score += aligned_count - 1
        
        return alignment_score
    
    def _tournament_selection(self, population: List, fitness_scores: List[float]) -> List[Dict]:
        """Tournament selection for genetic algorithm"""
        tournament_size = 3
        tournament_indices = random.sample(range(len(population)), tournament_size)
        tournament_fitness = [fitness_scores[i] for i in tournament_indices]
        winner_index = tournament_indices[np.argmax(tournament_fitness)]
        return population[winner_index]
    
    def _crossover(self, parent1: List[Dict], parent2: List[Dict]) -> List[Dict]:
        """Crossover operation for genetic algorithm"""
        # Simple crossover: take random subset from each parent
        all_positions = parent1 + parent2
        # Remove duplicates and overlaps (simplified)
        return random.sample(all_positions, min(len(all_positions), random.randint(1, 30)))
    
    def _mutate(self, individual: List[Dict], potential_positions: List[Dict]) -> List[Dict]:
        """Mutation operation for genetic algorithm"""
        if not individual or not potential_positions:
            return individual
        
        # Randomly add or remove a position
        if random.random() < 0.5 and len(individual) > 1:
            # Remove random position
            individual.pop(random.randint(0, len(individual) - 1))
        else:
            # Add random position if no conflict
            new_pos = random.choice(potential_positions)
            if new_pos not in individual:
                individual.append(new_pos)
        
        return individual
    
    def _generate_corridors(self, boxes: List[Dict], box_dimensions: Dict) -> List[Dict]:
        """Generate corridors between facing rows of boxes"""
        corridors = []
        
        if len(boxes) < 2:
            return corridors
        
        # Group boxes by rows (similar y coordinates)
        tolerance = box_dimensions['height'] + 0.5  # Allow for some spacing
        rows = self._group_boxes_into_rows(boxes, tolerance)
        
        # Generate corridors between adjacent rows
        for i in range(len(rows) - 1):
            row1 = rows[i]
            row2 = rows[i + 1]
            
            # Calculate corridor between these rows
            corridor = self._create_corridor_between_rows(row1, row2, box_dimensions)
            if corridor:
                corridors.append(corridor)
        
        return corridors
    
    def _group_boxes_into_rows(self, boxes: List[Dict], tolerance: float) -> List[List[Dict]]:
        """Group boxes into rows based on y-coordinates"""
        if not boxes:
            return []
        
        # Sort boxes by y-coordinate
        sorted_boxes = sorted(boxes, key=lambda b: b['y'])
        
        rows = []
        current_row = [sorted_boxes[0]]
        
        for box in sorted_boxes[1:]:
            if abs(box['y'] - current_row[-1]['y']) <= tolerance:
                current_row.append(box)
            else:
                rows.append(current_row)
                current_row = [box]
        
        rows.append(current_row)
        return rows
    
    def _create_corridor_between_rows(self, row1: List[Dict], row2: List[Dict], box_dimensions: Dict) -> Dict:
        """Create a corridor between two rows of boxes"""
        if not row1 or not row2:
            return None
        
        # Calculate corridor bounds
        row1_max_y = max(box['y'] + box_dimensions['height'] for box in row1)
        row2_min_y = min(box['y'] for box in row2)
        
        # Check if there's space for a corridor
        available_space = row2_min_y - row1_max_y
        if available_space < self.corridor_width:
            return None
        
        # Calculate corridor dimensions
        all_x_coords = [box['x'] for box in row1 + row2]
        corridor_start_x = min(all_x_coords)
        corridor_end_x = max(box['x'] + box_dimensions['width'] for box in row1 + row2)
        
        corridor_y = row1_max_y + (available_space - self.corridor_width) / 2
        
        return {
            'x': corridor_start_x,
            'y': corridor_y,
            'width': corridor_end_x - corridor_start_x,
            'height': self.corridor_width,
            'type': 'corridor'
        }
    
    def _calculate_statistics(self, boxes: List[Dict], corridors: List[Dict], 
                            plan_bounds: Dict, box_dimensions: Dict) -> Dict:
        """Calculate statistics for the optimization result"""
        total_area = (plan_bounds['max_x'] - plan_bounds['min_x']) * (plan_bounds['max_y'] - plan_bounds['min_y'])
        
        box_area = len(boxes) * box_dimensions['width'] * box_dimensions['height']
        corridor_area = sum(c['width'] * c['height'] for c in corridors)
        
        return {
            'total_boxes': len(boxes),
            'total_corridors': len(corridors),
            'box_area': box_area,
            'corridor_area': corridor_area,
            'total_area': total_area,
            'utilization_rate': (box_area / total_area) * 100 if total_area > 0 else 0,
            'average_box_size': f"{box_dimensions['width']}m × {box_dimensions['height']}m"
        }
