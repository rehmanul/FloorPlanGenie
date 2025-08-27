
import random
from scipy.optimize import differential_evolution
import numpy as np

class SpaceOptimizer:
    def __init__(self):
        pass
    
    def optimize_placement(self, plan_data, box_dimensions, corridor_width):
        # Simple optimization algorithm for placing boxes
        width = plan_data['dimensions']['width']
        height = plan_data['dimensions']['height']
        
        # Calculate how many boxes can fit
        box_width = box_dimensions['width']
        box_height = box_dimensions['height']
        
        # Simple grid placement
        boxes_per_row = int((width - corridor_width) // (box_width + corridor_width))
        boxes_per_col = int((height - corridor_width) // (box_height + corridor_width))
        
        boxes = []
        corridors = []
        
        # Place boxes in grid pattern
        for row in range(boxes_per_col):
            for col in range(boxes_per_row):
                x = corridor_width + col * (box_width + corridor_width)
                y = corridor_width + row * (box_height + corridor_width)
                
                boxes.append({
                    'id': f'box_{row}_{col}',
                    'x': x,
                    'y': y,
                    'width': box_width,
                    'height': box_height
                })
        
        # Generate corridors
        # Horizontal corridors
        for row in range(boxes_per_col + 1):
            y = row * (box_height + corridor_width)
            corridors.append({
                'type': 'horizontal',
                'x': 0,
                'y': y,
                'width': width,
                'height': corridor_width
            })
        
        # Vertical corridors
        for col in range(boxes_per_row + 1):
            x = col * (box_width + corridor_width)
            corridors.append({
                'type': 'vertical',
                'x': x,
                'y': 0,
                'width': corridor_width,
                'height': height
            })
        
        # Calculate statistics
        total_box_area = len(boxes) * box_width * box_height
        total_area = width * height
        utilization_rate = (total_box_area / total_area) * 100
        
        statistics = {
            'total_boxes': len(boxes),
            'total_corridors': len(corridors),
            'utilization_rate': utilization_rate,
            'total_area': total_area
        }
        
        return {
            'boxes': boxes,
            'corridors': corridors,
            'statistics': statistics
        }
