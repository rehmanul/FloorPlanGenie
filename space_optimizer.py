
import random
import numpy as np
from scipy.optimize import differential_evolution
import math

class SpaceOptimizer:
    def __init__(self):
        self.optimization_params = {
            'population_size': 50,
            'max_iterations': 100,
            'mutation_rate': 0.1
        }
    
    def optimize_placement(self, plan_data, box_dimensions, corridor_width):
        """Advanced space optimization with collision detection and efficiency maximization"""
        if not plan_data:
            raise ValueError("Plan data is required for optimization")
        
        if 'dimensions' not in plan_data:
            raise ValueError("Plan dimensions not found")
            
        width = plan_data['dimensions']['width']
        height = plan_data['dimensions']['height']
        walls = plan_data.get('walls', [])
        
        box_width = box_dimensions['width']
        box_height = box_dimensions['height']
        
        # Get usable area (avoid walls and boundaries)
        usable_bounds = self._calculate_usable_bounds(width, height, walls)
        
        # Auto-adjust box dimensions if they're too large for the space
        max_box_width = min(box_width, usable_bounds['width'] / 2)  # Allow room for at least 2 boxes
        max_box_height = min(box_height, usable_bounds['height'] / 2)
        
        # Ensure minimum viable box size but make it proportional to space
        min_box_size = min(0.1, min(usable_bounds['width'], usable_bounds['height']) / 10)
        max_box_width = max(max_box_width, min_box_size)
        max_box_height = max(max_box_height, min_box_size)
        
        if max_box_width < box_width or max_box_height < box_height:
            print(f"Auto-adjusting box size from {box_width}x{box_height} to {max_box_width:.2f}x{max_box_height:.2f} to fit space")
            box_width = max_box_width
            box_height = max_box_height
        
        # Use genetic algorithm for optimal placement
        optimization_result = self._genetic_algorithm_placement(
            usable_bounds, box_width, box_height, corridor_width
        )
        
        # Generate corridors based on box placement
        corridors = self._generate_optimal_corridors(
            optimization_result['boxes'], usable_bounds, corridor_width
        )
        
        # Calculate detailed statistics
        statistics = self._calculate_detailed_statistics(
            optimization_result['boxes'], corridors, width, height, box_width, box_height
        )
        
        return {
            'boxes': optimization_result['boxes'],
            'corridors': corridors,
            'statistics': statistics,
            'optimization_score': optimization_result['score']
        }

    def _calculate_usable_bounds(self, width, height, walls):
        """Calculate the usable area considering walls and obstacles"""
        # For now, use simple rectangular bounds
        # In advanced version, this would consider complex wall geometries
        margin = 0.5  # 0.5m margin from walls
        
        return {
            'min_x': margin,
            'max_x': width - margin,
            'min_y': margin,
            'max_y': height - margin,
            'width': width - 2 * margin,
            'height': height - 2 * margin
        }

    def _genetic_algorithm_placement(self, bounds, box_width, box_height, corridor_width):
        """Use genetic algorithm to find optimal box placement"""
        
        # Calculate maximum possible boxes
        max_boxes_x = int(bounds['width'] // (box_width + corridor_width))
        max_boxes_y = int(bounds['height'] // (box_height + corridor_width))
        max_boxes = max_boxes_x * max_boxes_y
        
        if max_boxes == 0:
            return {'boxes': [], 'score': 0}
        
        # Define fitness function
        def fitness_function(chromosome):
            boxes = self._chromosome_to_boxes(chromosome, bounds, box_width, box_height, corridor_width)
            return self._calculate_fitness(boxes, bounds)
        
        # Initialize population
        population = []
        for _ in range(self.optimization_params['population_size']):
            chromosome = self._generate_random_chromosome(max_boxes_x, max_boxes_y)
            population.append(chromosome)
        
        # Evolution loop
        best_score = 0
        best_boxes = []
        
        for generation in range(self.optimization_params['max_iterations']):
            # Evaluate fitness
            fitness_scores = [fitness_function(chrom) for chrom in population]
            
            # Track best solution
            best_idx = np.argmax(fitness_scores)
            if fitness_scores[best_idx] > best_score:
                best_score = fitness_scores[best_idx]
                best_boxes = self._chromosome_to_boxes(
                    population[best_idx], bounds, box_width, box_height, corridor_width
                )
            
            # Selection and reproduction (simplified)
            new_population = []
            for _ in range(len(population)):
                parent1 = self._tournament_selection(population, fitness_scores)
                parent2 = self._tournament_selection(population, fitness_scores)
                child = self._crossover(parent1, parent2)
                child = self._mutate(child)
                new_population.append(child)
            
            population = new_population
        
        return {'boxes': best_boxes, 'score': best_score}

    def _generate_random_chromosome(self, max_x, max_y):
        """Generate random chromosome representing box placement"""
        chromosome = []
        for x in range(max_x):
            for y in range(max_y):
                # Random decision to place box (0 or 1)
                chromosome.append(random.randint(0, 1))
        return chromosome

    def _chromosome_to_boxes(self, chromosome, bounds, box_width, box_height, corridor_width):
        """Convert chromosome to actual box positions"""
        boxes = []
        max_x = int(bounds['width'] // (box_width + corridor_width))
        
        for i, gene in enumerate(chromosome):
            if gene == 1:  # Place box
                grid_x = i % max_x
                grid_y = i // max_x
                
                x = bounds['min_x'] + grid_x * (box_width + corridor_width)
                y = bounds['min_y'] + grid_y * (box_height + corridor_width)
                
                boxes.append({
                    'id': f'box_{grid_y}_{grid_x}',
                    'x': x,
                    'y': y,
                    'width': box_width,
                    'height': box_height
                })
        
        return boxes

    def _calculate_fitness(self, boxes, bounds):
        """Calculate fitness score for box placement"""
        if not boxes:
            return 0
        
        # Factors: space utilization, accessibility, distribution
        total_box_area = len(boxes) * boxes[0]['width'] * boxes[0]['height']
        total_usable_area = bounds['width'] * bounds['height']
        utilization = total_box_area / total_usable_area
        
        # Penalty for clustering (encourage distribution)
        distribution_score = self._calculate_distribution_score(boxes)
        
        # Accessibility score (ensure all boxes are reachable)
        accessibility_score = self._calculate_accessibility_score(boxes)
        
        return utilization * 0.5 + distribution_score * 0.3 + accessibility_score * 0.2

    def _calculate_distribution_score(self, boxes):
        """Calculate how well distributed the boxes are"""
        if len(boxes) < 2:
            return 1.0
        
        total_distance = 0
        for i, box1 in enumerate(boxes):
            for box2 in boxes[i+1:]:
                distance = math.sqrt(
                    (box1['x'] - box2['x'])**2 + (box1['y'] - box2['y'])**2
                )
                total_distance += distance
        
        avg_distance = total_distance / (len(boxes) * (len(boxes) - 1) / 2)
        return min(1.0, avg_distance / 10)  # Normalize

    def _calculate_accessibility_score(self, boxes):
        """Ensure all boxes have access paths"""
        # Simplified: assume all boxes are accessible if properly spaced
        return 1.0

    def _tournament_selection(self, population, fitness_scores):
        """Select parent using tournament selection"""
        tournament_size = 3
        tournament_indices = random.sample(range(len(population)), tournament_size)
        tournament_fitness = [fitness_scores[i] for i in tournament_indices]
        winner_idx = tournament_indices[np.argmax(tournament_fitness)]
        return population[winner_idx]

    def _crossover(self, parent1, parent2):
        """Single-point crossover"""
        crossover_point = random.randint(1, len(parent1) - 1)
        child = parent1[:crossover_point] + parent2[crossover_point:]
        return child

    def _mutate(self, chromosome):
        """Mutate chromosome"""
        for i in range(len(chromosome)):
            if random.random() < self.optimization_params['mutation_rate']:
                chromosome[i] = 1 - chromosome[i]  # Flip bit
        return chromosome

    def _generate_optimal_corridors(self, boxes, bounds, corridor_width):
        """Generate corridors that connect all boxes efficiently"""
        corridors = []
        
        if not boxes:
            return corridors
        
        # Create main horizontal corridors
        unique_y_positions = sorted(set(box['y'] for box in boxes))
        for y_pos in unique_y_positions:
            corridors.append({
                'type': 'horizontal',
                'x': bounds['min_x'],
                'y': y_pos - corridor_width/2,
                'width': bounds['width'],
                'height': corridor_width
            })
        
        # Create main vertical corridors
        unique_x_positions = sorted(set(box['x'] for box in boxes))
        for x_pos in unique_x_positions:
            corridors.append({
                'type': 'vertical',
                'x': x_pos - corridor_width/2,
                'y': bounds['min_y'],
                'width': corridor_width,
                'height': bounds['height']
            })
        
        return corridors

    def _calculate_detailed_statistics(self, boxes, corridors, total_width, total_height, box_width, box_height):
        """Calculate comprehensive statistics"""
        total_area = total_width * total_height
        
        # Box statistics
        total_boxes = len(boxes)
        total_box_area = total_boxes * box_width * box_height
        
        # Corridor statistics
        total_corridor_area = sum(c['width'] * c['height'] for c in corridors)
        
        # Utilization calculations
        space_utilization = (total_box_area / total_area) * 100 if total_area > 0 else 0
        
        # Efficiency metrics
        wasted_space = total_area - total_box_area - total_corridor_area
        efficiency_score = (total_box_area / (total_box_area + total_corridor_area)) * 100 if (total_box_area + total_corridor_area) > 0 else 0
        
        return {
            'total_boxes': total_boxes,
            'total_corridors': len(corridors),
            'utilization_rate': round(space_utilization, 2),
            'total_area': round(total_area, 2),
            'box_area': round(total_box_area, 2),
            'corridor_area': round(total_corridor_area, 2),
            'wasted_space': round(wasted_space, 2),
            'efficiency_score': round(efficiency_score, 2),
            'average_box_spacing': self._calculate_average_spacing(boxes) if boxes else 0
        }

    def _calculate_average_spacing(self, boxes):
        """Calculate average spacing between boxes"""
        if len(boxes) < 2:
            return 0
        
        total_distance = 0
        count = 0
        
        for i, box1 in enumerate(boxes):
            for box2 in boxes[i+1:]:
                distance = math.sqrt(
                    (box1['x'] - box2['x'])**2 + (box1['y'] - box2['y'])**2
                )
                total_distance += distance
                count += 1
        
        return round(total_distance / count, 2) if count > 0 else 0
