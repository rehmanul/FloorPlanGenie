import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import os
from datetime import datetime
import numpy as np

class VisualGenerator:
    def __init__(self):
        self.output_dir = 'static/outputs'
        os.makedirs(self.output_dir, exist_ok=True)

    def generate(self, data, output_format='2d'):
        # Create a figure with better styling
        plt.style.use('default')
        fig, ax = plt.subplots(1, 1, figsize=(16, 12), facecolor='white')
        ax.set_facecolor('#f8f9fa')

        # Get dimensions - no defaults, must be real data
        if 'dimensions' not in data:
            raise ValueError("No dimensional data provided - cannot generate visualization")
        
        width = data['dimensions']['width']
        height = data['dimensions']['height']
        
        if width <= 0 or height <= 0:
            raise ValueError("Invalid dimensions detected - must be positive real values")

        # Draw walls with professional styling
        if 'walls' in data:
            for wall in data['walls']:
                start = wall['start']
                end = wall['end']
                ax.plot([start['x'], end['x']], [start['y'], end['y']], 
                       color='#2c3e50', linewidth=4, solid_capstyle='round')

        # Draw îlots (islands/boxes) with professional styling
        if 'boxes' in data:
            for i, box in enumerate(data['boxes']):
                # Use gradient-like colors for îlots
                colors = ['#90EE90', '#98FB98', '#9AFF9A', '#ADFF2F', '#B8EFB8']
                color = colors[i % len(colors)]
                
                rect = patches.Rectangle(
                    (box['x'], box['y']), box['width'], box['height'],
                    linewidth=2, edgecolor='#2d5a27', facecolor=color, alpha=0.8
                )
                ax.add_patch(rect)
                # Add îlot ID with better styling
                ax.text(box['x'] + box['width']/2, box['y'] + box['height']/2,
                       f"Îlot {i+1}", ha='center', va='center', 
                       fontsize=10, fontweight='bold', color='#2d5a27')

        # Draw corridors with professional styling
        if 'corridors' in data:
            for corridor in data['corridors']:
                rect = patches.Rectangle(
                    (corridor['x'], corridor['y']), corridor['width'], corridor['height'],
                    linewidth=1, edgecolor='#e74c3c', facecolor='#ffebee', 
                    alpha=0.6, linestyle='--'
                )
                ax.add_patch(rect)

        # Draw zones with color coding like in your examples
        if 'zones' in data:
            # Entry/Exit zones (ENTRÉE/SORTIE) - Red like in your examples
            if 'entry_exit' in data['zones']:
                for zone in data['zones']['entry_exit']:
                    rect = patches.Rectangle(
                        (zone['x'], zone['y']), zone['width'], zone['height'],
                        linewidth=2, edgecolor='#e74c3c', facecolor='#ffcdd2', alpha=0.7
                    )
                    ax.add_patch(rect)
                    # Add label
                    ax.text(zone['x'] + zone['width']/2, zone['y'] + zone['height']/2,
                           'ENTRÉE/SORTIE', ha='center', va='center', 
                           fontsize=8, fontweight='bold', color='#c62828')
            
            # No entry zones (NO ENTRÉE) - Blue like in your examples  
            if 'no_entry' in data['zones']:
                for zone in data['zones']['no_entry']:
                    rect = patches.Rectangle(
                        (zone['x'], zone['y']), zone['width'], zone['height'],
                        linewidth=2, edgecolor='#2196F3', facecolor='#bbdefb', alpha=0.7
                    )
                    ax.add_patch(rect)
                    # Add label
                    ax.text(zone['x'] + zone['width']/2, zone['y'] + zone['height']/2,
                           'NO ENTRÉE', ha='center', va='center', 
                           fontsize=8, fontweight='bold', color='#1565c0')

        # Set axis properties with professional styling
        margin = max(width, height) * 0.05
        ax.set_xlim(-margin, width + margin)
        ax.set_ylim(-margin, height + margin)
        ax.set_aspect('equal')
        
        # Professional grid and labels
        ax.grid(True, alpha=0.2, linestyle='-', linewidth=0.5)
        ax.set_xlabel('Largeur (mètres)', fontsize=12, fontweight='bold')
        ax.set_ylabel('Hauteur (mètres)', fontsize=12, fontweight='bold')
        ax.set_title('Plan d\'Optimisation avec Îlots', fontsize=16, fontweight='bold', pad=20)
        
        # Add dimension annotations
        if 'boxes' in data and data['boxes']:
            total_boxes = len(data['boxes'])
            if 'statistics' in data:
                stats = data['statistics']
                title_text = f"Plan d'Optimisation - {total_boxes} Îlots - Utilisation: {stats.get('utilization_rate', 0):.1f}%"
                ax.set_title(title_text, fontsize=16, fontweight='bold', pad=20)
        
        # Add scale indicator
        scale_length = width / 10
        scale_x = width - scale_length - margin/2
        scale_y = -margin/2
        ax.plot([scale_x, scale_x + scale_length], [scale_y, scale_y], 'k-', linewidth=3)
        ax.text(scale_x + scale_length/2, scale_y - margin/8, f'{scale_length:.1f}m', 
               ha='center', va='top', fontweight='bold')

        # Save the figure
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"floorplan_{timestamp}.png"
        filepath = os.path.join(self.output_dir, filename)

        plt.savefig(filepath, dpi=150, bbox_inches='tight')
        plt.close()

        return filepath