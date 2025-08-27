import matplotlib.pyplot as plt
import matplotlib.patches as patches
import os
from datetime import datetime

class VisualGenerator:
    def __init__(self):
        self.output_dir = 'static/outputs'
        os.makedirs(self.output_dir, exist_ok=True)

    def generate(self, data, output_format='2d'):
        # Create a figure
        fig, ax = plt.subplots(1, 1, figsize=(12, 8))

        # Get dimensions
        if 'dimensions' in data:
            width = data['dimensions']['width']
            height = data['dimensions']['height']
        else:
            width, height = 20, 15  # Default

        # Draw walls
        if 'walls' in data:
            for wall in data['walls']:
                start = wall['start']
                end = wall['end']
                ax.plot([start[0], end[0]], [start[1], end[1]], 'k-', linewidth=3)

        # Draw boxes if present
        if 'boxes' in data:
            for box in data['boxes']:
                rect = patches.Rectangle(
                    (box['x'], box['y']), box['width'], box['height'],
                    linewidth=1, edgecolor='blue', facecolor='lightblue', alpha=0.7
                )
                ax.add_patch(rect)
                # Add box ID
                ax.text(box['x'] + box['width']/2, box['y'] + box['height']/2,
                       box['id'], ha='center', va='center', fontsize=8)

        # Draw corridors if present
        if 'corridors' in data:
            for corridor in data['corridors']:
                rect = patches.Rectangle(
                    (corridor['x'], corridor['y']), corridor['width'], corridor['height'],
                    linewidth=1, edgecolor='red', facecolor='lightcoral', alpha=0.3
                )
                ax.add_patch(rect)

        # Draw zones if present
        if 'zones' in data:
            if 'entry_exit' in data['zones']:
                for zone in data['zones']['entry_exit']:
                    rect = patches.Rectangle(
                        (zone['x'], zone['y']), zone['width'], zone['height'],
                        linewidth=2, edgecolor='green', facecolor='lightgreen', alpha=0.5
                    )
                    ax.add_patch(rect)

        # Set axis properties
        ax.set_xlim(0, width)
        ax.set_ylim(0, height)
        ax.set_aspect('equal')
        ax.grid(True, alpha=0.3)
        ax.set_xlabel('Width (meters)')
        ax.set_ylabel('Height (meters)')
        ax.set_title('Floor Plan Layout')

        # Save the figure
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"floorplan_{timestamp}.png"
        filepath = os.path.join(self.output_dir, filename)

        plt.savefig(filepath, dpi=150, bbox_inches='tight')
        plt.close()

        return filepath