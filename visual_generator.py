
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import io
import os

class VisualGenerator:
    def __init__(self):
        self.colors = {
            'wall': '#333333',
            'box': '#90EE90',
            'corridor': '#FFE4B5',
            'no_entry': '#FF6B6B',
            'entry_exit': '#4ECDC4',
            'background': '#F8F8F8'
        }
    
    def generate(self, data: dict, output_format: str = '2d') -> str:
        """Generate visual output in specified format"""
        if output_format == '2d':
            return self._generate_2d_plan(data)
        elif output_format == '3d':
            return self._generate_3d_visualization(data)
        elif output_format == 'pdf':
            return self._generate_pdf_report(data)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")
    
    def _generate_2d_plan(self, data: dict) -> str:
        """Generate 2D floor plan visualization"""
        fig, ax = plt.subplots(1, 1, figsize=(16, 12))
        ax.set_aspect('equal')
        
        # Set background
        ax.set_facecolor(self.colors['background'])
        
        # Draw walls if available
        if 'walls' in data:
            self._draw_walls(ax, data['walls'])
        
        # Draw zones if available
        if 'zones' in data:
            self._draw_zones(ax, data['zones'])
        
        # Draw boxes (islands)
        if 'boxes' in data:
            self._draw_boxes(ax, data['boxes'])
        
        # Draw corridors
        if 'corridors' in data:
            self._draw_corridors(ax, data['corridors'])
        
        # Add grid
        self._add_grid(ax)
        
        # Add dimensions and labels
        self._add_dimensions(ax, data.get('boxes', []), data.get('corridors', []))
        
        # Style the plot
        ax.set_title('FloorPlanGenie - Optimized Layout', fontsize=16, fontweight='bold', pad=20)
        ax.set_xlabel('Distance (meters)', fontsize=12)
        ax.set_ylabel('Distance (meters)', fontsize=12)
        
        # Add legend
        self._add_legend(ax)
        
        # Save to file
        output_path = 'static/generated_plan_2d.png'
        os.makedirs('static', exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        
        return output_path
    
    def _draw_walls(self, ax, walls):
        """Draw walls on the plot"""
        for wall in walls:
            x_coords = [wall['start']['x'], wall['end']['x']]
            y_coords = [wall['start']['y'], wall['end']['y']]
            ax.plot(x_coords, y_coords, color=self.colors['wall'], linewidth=3, solid_capstyle='round')
    
    def _draw_zones(self, ax, zones):
        """Draw colored zones"""
        # Draw no-entry zones (blue)
        for zone in zones.get('no_entry', []):
            rect = patches.Rectangle(
                (zone['x'], zone['y']), zone['width'], zone['height'],
                linewidth=2, edgecolor=self.colors['no_entry'], 
                facecolor=self.colors['no_entry'], alpha=0.3
            )
            ax.add_patch(rect)
        
        # Draw entry/exit zones (teal)
        for zone in zones.get('entry_exit', []):
            rect = patches.Rectangle(
                (zone['x'], zone['y']), zone['width'], zone['height'],
                linewidth=2, edgecolor=self.colors['entry_exit'], 
                facecolor=self.colors['entry_exit'], alpha=0.3
            )
            ax.add_patch(rect)
    
    def _draw_boxes(self, ax, boxes):
        """Draw island boxes"""
        for i, box in enumerate(boxes):
            # Default box dimensions if not provided
            width = box.get('width', 3.0)
            height = box.get('height', 4.0)
            
            rect = patches.Rectangle(
                (box['x'], box['y']), width, height,
                linewidth=2, edgecolor='#2E8B57', 
                facecolor=self.colors['box'], alpha=0.8
            )
            ax.add_patch(rect)
            
            # Add box number
            center_x = box['x'] + width / 2
            center_y = box['y'] + height / 2
            ax.text(center_x, center_y, f'B{i+1}', 
                   ha='center', va='center', fontsize=10, fontweight='bold')
    
    def _draw_corridors(self, ax, corridors):
        """Draw corridors"""
        for i, corridor in enumerate(corridors):
            rect = patches.Rectangle(
                (corridor['x'], corridor['y']), corridor['width'], corridor['height'],
                linewidth=1, edgecolor='#DAA520', 
                facecolor=self.colors['corridor'], alpha=0.6
            )
            ax.add_patch(rect)
            
            # Add corridor label
            center_x = corridor['x'] + corridor['width'] / 2
            center_y = corridor['y'] + corridor['height'] / 2
            ax.text(center_x, center_y, f'C{i+1}', 
                   ha='center', va='center', fontsize=8, style='italic')
    
    def _add_grid(self, ax):
        """Add grid to the plot"""
        ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
        ax.set_axisbelow(True)
    
    def _add_dimensions(self, ax, boxes, corridors):
        """Add dimension annotations"""
        # Add dimension arrows and text for key measurements
        # This is a simplified version - could be expanded
        pass
    
    def _add_legend(self, ax):
        """Add legend to the plot"""
        legend_elements = [
            patches.Patch(color=self.colors['box'], label='Island Boxes'),
            patches.Patch(color=self.colors['corridor'], label='Corridors'),
            patches.Patch(color=self.colors['no_entry'], alpha=0.3, label='No Entry Zones'),
            patches.Patch(color=self.colors['entry_exit'], alpha=0.3, label='Entry/Exit Zones'),
            plt.Line2D([0], [0], color=self.colors['wall'], linewidth=3, label='Walls')
        ]
        ax.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(1, 1))
    
    def _generate_3d_visualization(self, data: dict) -> str:
        """Generate 3D visualization (simplified version)"""
        # For now, create an enhanced 2D view with 3D-like effects
        fig, ax = plt.subplots(1, 1, figsize=(16, 12))
        ax.set_aspect('equal')
        
        # Similar to 2D but with shadow effects and perspective
        self._generate_2d_plan(data)
        
        output_path = 'static/generated_plan_3d.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        
        return output_path
    
    def _generate_pdf_report(self, data: dict) -> str:
        """Generate comprehensive PDF report"""
        output_path = 'static/generated_plan_report.pdf'
        
        with PdfPages(output_path) as pdf:
            # Page 1: 2D Plan
            fig, ax = plt.subplots(1, 1, figsize=(11, 8.5))
            self._generate_2d_plan(data)
            pdf.savefig(fig, bbox_inches='tight')
            plt.close()
            
            # Page 2: Statistics and Data
            fig, ax = plt.subplots(1, 1, figsize=(11, 8.5))
            self._create_statistics_page(ax, data.get('statistics', {}))
            pdf.savefig(fig, bbox_inches='tight')
            plt.close()
        
        return output_path
    
    def _create_statistics_page(self, ax, statistics):
        """Create statistics page for PDF report"""
        ax.axis('off')
        ax.text(0.5, 0.9, 'FloorPlanGenie - Optimization Report', 
               ha='center', va='top', fontsize=20, fontweight='bold', transform=ax.transAxes)
        
        # Add statistics
        stats_text = f"""
        Total Island Boxes: {statistics.get('total_boxes', 0)}
        Total Corridors: {statistics.get('total_corridors', 0)}
        Box Area: {statistics.get('box_area', 0):.2f} m²
        Corridor Area: {statistics.get('corridor_area', 0):.2f} m²
        Space Utilization: {statistics.get('utilization_rate', 0):.1f}%
        Average Box Size: {statistics.get('average_box_size', 'N/A')}
        """
        
        ax.text(0.1, 0.7, stats_text, ha='left', va='top', fontsize=12, 
               transform=ax.transAxes, bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray"))
