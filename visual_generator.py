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
        """Generate 3-step professional visualization: Empty Plan → Îlots → Corridors"""
        try:
            if not data.get('dimensions'):
                raise ValueError("No dimensional data provided - cannot generate visualization")
            
            # Get dimensions
            dimensions = data['dimensions']
            width = dimensions['width']
            height = dimensions['height']
            
            # Create 3-step visualization
            if output_format == '3d':
                return self._generate_single_step(data, width, height)
            else:
                return self._generate_3_step_2d(data, width, height)
        
        except Exception as e:
            print(f"Visual generation error: {e}")
            raise
    
    def _generate_3_step_2d(self, data, width, height):
        """Generate 3-step 2D visualization matching user's examples"""
        
        # Create figure with 3 subplots for the 3 steps
        fig, axes = plt.subplots(1, 3, figsize=(18, 6))
        
        # Step 1: Empty Floor Plan with Color Coding
        ax1 = axes[0]
        self._draw_step1_empty_plan(ax1, data, width, height)
        ax1.set_title('1. Plan Vide\n(Zones d\'Entrée)', fontsize=12, fontweight='bold')
        
        # Step 2: Place Îlots  
        ax2 = axes[1]
        self._draw_step2_with_ilots(ax2, data, width, height)
        ax2.set_title('2. Placement des Îlots\n(Zones Optimisées)', fontsize=12, fontweight='bold')
        
        # Step 3: Add Corridors
        ax3 = axes[2]
        self._draw_step3_with_corridors(ax3, data, width, height)
        ax3.set_title('3. Corridors & Calculs\n(Résultat Final)', fontsize=12, fontweight='bold')
        
        # Apply professional styling to all subplots
        for ax in axes:
            ax.set_xlim(0, width)
            ax.set_ylim(0, height)
            ax.set_aspect('equal')
            ax.grid(True, alpha=0.2)
            ax.set_xlabel('Largeur (m)')
            ax.set_ylabel('Hauteur (m)')
        
        plt.suptitle('FloorPlanGenie - Optimisation Architecturale', fontsize=16, fontweight='bold')
        plt.tight_layout()
        
        # Save the output
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"optimization_3steps_{timestamp}.png"
        filepath = os.path.join(self.output_dir, filename)
        
        plt.savefig(filepath, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        
        return filepath
    
    def _generate_single_step(self, data, width, height):
        """Generate single comprehensive view for 3D format"""
        plt.clf()
        fig, ax = plt.subplots(1, 1, figsize=(12, 10))
        
        # Draw all elements together
        self._draw_walls(ax, data.get('walls', []))
        self._draw_zones_with_colors(ax, data, width, height)
        if data.get('boxes'):
            self._draw_boxes(ax, data['boxes'])
        if data.get('corridors'):
            self._draw_corridors(ax, data['corridors'])
        
        # Professional styling
        ax.set_xlim(0, width)
        ax.set_ylim(0, height)
        ax.set_aspect('equal')
        ax.grid(True, alpha=0.3)
        ax.set_xlabel('Largeur (metres)')
        ax.set_ylabel('Hauteur (metres)')
        
        stats = data.get('statistics', {})
        total_boxes = stats.get('total_boxes', 0)
        utilization = stats.get('utilization_rate', 0)
        ax.set_title(f'Plan d\'Optimisation - {total_boxes} Îlots - Utilisation: {utilization:.1f}%', 
                    fontsize=14, fontweight='bold')
        
        # Add scale bar
        scale_length = min(width, height) * 0.1
        ax.plot([0.02 * width, 0.02 * width + scale_length], 
               [0.02 * height, 0.02 * height], 'k-', linewidth=3)
        ax.text(0.02 * width, 0.05 * height, f'{scale_length:.1f}m', fontsize=8)
        
        plt.tight_layout()
        
        # Save the output
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"optimization_{timestamp}.png"
        filepath = os.path.join(self.output_dir, filename)
        
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        
        return filepath
    
    def _draw_step1_empty_plan(self, ax, data, width, height):
        """Step 1: Draw empty floor plan with entry/exit zones"""
        # Draw walls (gray MUR)
        self._draw_walls(ax, data.get('walls', []), color='#6c757d')
        
        # Draw entry/exit zones (red ENTRÉE/SORTIE) and no-entry zones (blue NO ENTRÉE)
        self._draw_zones_with_colors(ax, data, width, height)
        
        # Add legend
        legend_elements = [
            patches.Patch(color='#bbdefb', label='NO ENTRÉE'),
            patches.Patch(color='#ffcdd2', label='ENTRÉE/SORTIE'),
            patches.Patch(color='#6c757d', label='MUR')
        ]
        ax.legend(handles=legend_elements, loc='upper right', fontsize=8)
    
    def _draw_step2_with_ilots(self, ax, data, width, height):
        """Step 2: Add green îlots to the plan"""
        # Draw walls and zones from step 1
        self._draw_walls(ax, data.get('walls', []), color='#6c757d')
        self._draw_zones_with_colors(ax, data, width, height)
        
        # Draw îlots (green boxes)
        if data.get('boxes'):
            self._draw_boxes(ax, data['boxes'])
        
        # Add legend
        legend_elements = [
            patches.Patch(color='#90EE90', label='ÎLOTS'),
            patches.Patch(color='#bbdefb', label='NO ENTRÉE'),
            patches.Patch(color='#ffcdd2', label='ENTRÉE/SORTIE'),
            patches.Patch(color='#6c757d', label='MUR')
        ]
        ax.legend(handles=legend_elements, loc='upper right', fontsize=8)
    
    def _draw_step3_with_corridors(self, ax, data, width, height):
        """Step 3: Add red corridors and calculations"""
        # Draw walls, zones, and îlots from previous steps
        self._draw_walls(ax, data.get('walls', []), color='#6c757d')
        self._draw_zones_with_colors(ax, data, width, height)
        
        if data.get('boxes'):
            self._draw_boxes_with_calculations(ax, data['boxes'])
        
        # Draw corridors (red pathways)
        if data.get('corridors'):
            self._draw_corridors(ax, data['corridors'])
        
        # Add statistics text
        stats = data.get('statistics', {})
        stats_text = (
            f"Total Îlots: {stats.get('total_boxes', 0)}\n"
            f"Utilisation: {stats.get('utilization_rate', 0):.1f}%\n"
            f"Surface Îlots: {stats.get('box_area', 0):.1f}m²\n"
            f"Surface Corridors: {stats.get('corridor_area', 0):.1f}m²"
        )
        ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, fontsize=8,
               verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    def _draw_walls(self, ax, walls, color='#2c3e50'):
        """Draw walls with professional styling"""
        for wall in walls:
            start = wall['start']
            end = wall['end']
            ax.plot([start['x'], end['x']], [start['y'], end['y']], 
                   color=color, linewidth=3, solid_capstyle='round')
    
    def _draw_zones_with_colors(self, ax, data, width, height):
        """Draw entry/exit zones with proper color coding"""
        # Simulate entry/exit zones near building perimeter (red)
        perimeter_margin = min(width, height) * 0.1
        
        # Entry zones (red - ENTRÉE/SORTIE)
        entry_zones = [
            {'x': 0, 'y': 0, 'width': perimeter_margin, 'height': perimeter_margin},
            {'x': width-perimeter_margin, 'y': height-perimeter_margin, 'width': perimeter_margin, 'height': perimeter_margin}
        ]
        
        for zone in entry_zones:
            rect = patches.Rectangle(
                (zone['x'], zone['y']), zone['width'], zone['height'],
                linewidth=2, edgecolor='#e74c3c', facecolor='#ffcdd2', alpha=0.7
            )
            ax.add_patch(rect)
        
        # No entry zones (blue - NO ENTRÉE)
        no_entry_zones = [
            {'x': 0, 'y': height-perimeter_margin, 'width': perimeter_margin, 'height': perimeter_margin},
            {'x': width-perimeter_margin, 'y': 0, 'width': perimeter_margin, 'height': perimeter_margin}
        ]
        
        for zone in no_entry_zones:
            rect = patches.Rectangle(
                (zone['x'], zone['y']), zone['width'], zone['height'],
                linewidth=2, edgecolor='#2196F3', facecolor='#bbdefb', alpha=0.7
            )
            ax.add_patch(rect)
    
    def _draw_boxes(self, ax, boxes):
        """Draw green îlots"""
        for i, box in enumerate(boxes):
            rect = patches.Rectangle(
                (box['x'], box['y']), box['width'], box['height'],
                linewidth=2, edgecolor='#2d5a27', facecolor='#90EE90', alpha=0.8
            )
            ax.add_patch(rect)
            
            # Add îlot number
            ax.text(box['x'] + box['width']/2, box['y'] + box['height']/2,
                   f"{i+1}", ha='center', va='center', 
                   fontsize=10, fontweight='bold', color='#2d5a27')
    
    def _draw_boxes_with_calculations(self, ax, boxes):
        """Draw green îlots with area calculations"""
        for i, box in enumerate(boxes):
            rect = patches.Rectangle(
                (box['x'], box['y']), box['width'], box['height'],
                linewidth=2, edgecolor='#2d5a27', facecolor='#90EE90', alpha=0.8
            )
            ax.add_patch(rect)
            
            # Calculate area
            area = box['width'] * box['height']
            
            # Add îlot number and area
            ax.text(box['x'] + box['width']/2, box['y'] + box['height']/2,
                   f"{i+1}\n{area:.1f}m²", ha='center', va='center', 
                   fontsize=9, fontweight='bold', color='#2d5a27')
    
    def _draw_corridors(self, ax, corridors):
        """Draw red corridor pathways"""
        for corridor in corridors:
            rect = patches.Rectangle(
                (corridor['x'], corridor['y']), corridor['width'], corridor['height'],
                linewidth=2, edgecolor='#e74c3c', facecolor='#ffebee', 
                alpha=0.6, linestyle='-'
            )
            ax.add_patch(rect)