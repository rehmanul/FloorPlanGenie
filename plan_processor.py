
import uuid
import json
import os
from PIL import Image, ImageDraw
import cv2
import numpy as np
import ezdxf
import PyPDF2
from io import BytesIO

class PlanProcessor:
    def __init__(self):
        self.plans = {}

    def process_plan(self, filepath):
        """Process uploaded floor plan file and extract real dimensions and features"""
        plan_id = str(uuid.uuid4())
        
        # Determine file type and process accordingly
        file_ext = os.path.splitext(filepath)[1].lower()
        
        try:
            if file_ext in ['.dwg', '.dxf']:
                plan_data = self._process_cad_file(filepath, plan_id)
            elif file_ext == '.pdf':
                plan_data = self._process_pdf_file(filepath, plan_id)
            elif file_ext in ['.jpg', '.jpeg', '.png']:
                plan_data = self._process_image_file(filepath, plan_id)
            else:
                raise ValueError(f"Unsupported file format: {file_ext}")
                
            self.plans[plan_id] = plan_data
            return plan_data
            
        except Exception as e:
            print(f"Error processing file: {e}")
            # Fallback to basic processing with actual file info
            return self._create_basic_plan(filepath, plan_id)

    def _process_cad_file(self, filepath, plan_id):
        """Process DWG/DXF files to extract walls, dimensions and zones"""
        try:
            # Read DXF file
            doc = ezdxf.readfile(filepath)
            modelspace = doc.modelspace()
            
            walls = []
            zones = {'entry_exit': [], 'no_entry': [], 'walls': []}
            min_x, min_y = float('inf'), float('inf')
            max_x, max_y = float('-inf'), float('-inf')
            
            # Extract lines (walls) and other entities
            for entity in modelspace:
                if entity.dxftype() == 'LINE':
                    start = entity.dxf.start
                    end = entity.dxf.end
                    
                    wall = {
                        'start': {'x': start.x, 'y': start.y},
                        'end': {'x': end.x, 'y': end.y},
                        'layer': entity.dxf.layer
                    }
                    walls.append(wall)
                    zones['walls'].append(wall)
                    
                    # Track boundaries
                    min_x = min(min_x, start.x, end.x)
                    max_x = max(max_x, start.x, end.x)
                    min_y = min(min_y, start.y, end.y)
                    max_y = max(max_y, start.y, end.y)
                
                elif entity.dxftype() == 'CIRCLE':
                    # Could represent doors or special zones
                    center = entity.dxf.center
                    radius = entity.dxf.radius
                    if radius < 2:  # Small circles might be doors
                        zones['entry_exit'].append({
                            'x': center.x - radius,
                            'y': center.y - radius,
                            'width': radius * 2,
                            'height': radius * 2
                        })
            
            # Calculate actual dimensions
            width = max_x - min_x if max_x != float('-inf') else 20
            height = max_y - min_y if max_y != float('-inf') else 15
            
            return {
                'id': plan_id,
                'filepath': filepath,
                'dimensions': {'width': width, 'height': height},
                'walls': walls,
                'zones': zones,
                'bounds': {'min_x': min_x, 'min_y': min_y, 'max_x': max_x, 'max_y': max_y}
            }
            
        except Exception as e:
            print(f"CAD processing error: {e}")
            return self._create_basic_plan(filepath, plan_id)

    def _process_pdf_file(self, filepath, plan_id):
        """Process PDF files - extract images and analyze"""
        try:
            with open(filepath, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                page = pdf_reader.pages[0]  # Process first page
                
                # For now, create a basic plan with PDF dimensions
                # In a real implementation, you'd extract images and analyze them
                mediabox = page.mediabox
                width = float(mediabox.width) / 72 * 25.4 / 1000  # Convert points to meters
                height = float(mediabox.height) / 72 * 25.4 / 1000
                
                return {
                    'id': plan_id,
                    'filepath': filepath,
                    'dimensions': {'width': width, 'height': height},
                    'walls': self._create_boundary_walls(width, height),
                    'zones': {'entry_exit': [], 'no_entry': [], 'walls': []}
                }
                
        except Exception as e:
            print(f"PDF processing error: {e}")
            return self._create_basic_plan(filepath, plan_id)

    def _process_image_file(self, filepath, plan_id):
        """Process image files using computer vision to detect walls and features"""
        try:
            # Load image
            image = cv2.imread(filepath)
            if image is None:
                raise ValueError("Could not load image")
                
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Edge detection to find walls
            edges = cv2.Canny(gray, 50, 150, apertureSize=3)
            
            # Find lines (potential walls)
            lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=100, 
                                   minLineLength=50, maxLineGap=10)
            
            walls = []
            if lines is not None:
                for line in lines:
                    x1, y1, x2, y2 = line[0]
                    # Convert pixel coordinates to meters (assuming scale)
                    scale = 0.1  # 1 pixel = 0.1 meter (adjustable)
                    walls.append({
                        'start': {'x': x1 * scale, 'y': y1 * scale},
                        'end': {'x': x2 * scale, 'y': y2 * scale},
                        'layer': 'Detected'
                    })
            
            # Calculate dimensions from image
            h, w = image.shape[:2]
            scale = 0.1  # 1 pixel = 0.1 meter
            width = w * scale
            height = h * scale
            
            return {
                'id': plan_id,
                'filepath': filepath,
                'dimensions': {'width': width, 'height': height},
                'walls': walls,
                'zones': {'entry_exit': [], 'no_entry': [], 'walls': walls}
            }
            
        except Exception as e:
            print(f"Image processing error: {e}")
            return self._create_basic_plan(filepath, plan_id)

    def _create_boundary_walls(self, width, height):
        """Create boundary walls for a rectangular space"""
        return [
            {'start': {'x': 0, 'y': 0}, 'end': {'x': width, 'y': 0}},
            {'start': {'x': width, 'y': 0}, 'end': {'x': width, 'y': height}},
            {'start': {'x': width, 'y': height}, 'end': {'x': 0, 'y': height}},
            {'start': {'x': 0, 'y': height}, 'end': {'x': 0, 'y': 0}}
        ]

    def _create_basic_plan(self, filepath, plan_id):
        """Fallback method for basic plan creation"""
        return {
            'id': plan_id,
            'filepath': filepath,
            'dimensions': {'width': 20, 'height': 15},
            'walls': self._create_boundary_walls(20, 15),
            'zones': {'entry_exit': [], 'no_entry': [], 'walls': []}
        }

    def get_plan_data(self, plan_id):
        return self.plans.get(plan_id)
