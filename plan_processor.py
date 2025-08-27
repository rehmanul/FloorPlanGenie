
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
            if file_ext in ['.dxf']:
                plan_data = self._process_cad_file(filepath, plan_id)
            elif file_ext in ['.dwg']:
                # For DWG files, provide clear guidance
                raise ValueError(f"DWG files need to be converted to DXF format first. Please convert {filepath} to DXF using AutoCAD or a free converter, then upload the DXF file.")
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
        """Process DWG/DXF files to extract walls, dimensions and zones with real architectural data"""
        try:
            # Read DXF file
            doc = ezdxf.readfile(filepath)
            modelspace = doc.modelspace()
            
            walls = []
            zones = {'entry_exit': [], 'no_entry': [], 'walls': []}
            min_x, min_y = float('inf'), float('inf')
            max_x, max_y = float('-inf'), float('-inf')
            doors = []
            
            # Extract different types of entities
            for entity in modelspace:
                if entity.dxftype() == 'LINE':
                    start = entity.dxf.start
                    end = entity.dxf.end
                    
                    # Only consider significant lines (walls)
                    line_length = ((end.x - start.x)**2 + (end.y - start.y)**2)**0.5
                    if line_length > 0.1:  # Filter very small lines
                        wall = {
                            'start': {'x': float(start.x), 'y': float(start.y)},
                            'end': {'x': float(end.x), 'y': float(end.y)},
                            'layer': getattr(entity.dxf, 'layer', 'Default'),
                            'length': line_length
                        }
                        walls.append(wall)
                        
                        # Track boundaries
                        min_x = min(min_x, start.x, end.x)
                        max_x = max(max_x, start.x, end.x)
                        min_y = min(min_y, start.y, end.y)
                        max_y = max(max_y, start.y, end.y)
                
                elif entity.dxftype() == 'POLYLINE' or entity.dxftype() == 'LWPOLYLINE':
                    # Handle polylines as connected walls
                    try:
                        points = list(entity.get_points())
                        for i in range(len(points) - 1):
                            start = points[i]
                            end = points[i + 1]
                            wall = {
                                'start': {'x': float(start[0]), 'y': float(start[1])},
                                'end': {'x': float(end[0]), 'y': float(end[1])},
                                'layer': getattr(entity.dxf, 'layer', 'Default'),
                                'type': 'polyline'
                            }
                            walls.append(wall)
                            
                            min_x = min(min_x, start[0], end[0])
                            max_x = max(max_x, start[0], end[0])
                            min_y = min(min_y, start[1], end[1])
                            max_y = max(max_y, start[1], end[1])
                    except:
                        pass
                
                elif entity.dxftype() == 'CIRCLE':
                    # Identify doors or special zones
                    center = entity.dxf.center
                    radius = entity.dxf.radius
                    if 0.3 < radius < 3:  # Reasonable door size range
                        door = {
                            'x': float(center.x - radius),
                            'y': float(center.y - radius),
                            'width': float(radius * 2),
                            'height': float(radius * 2),
                            'type': 'door'
                        }
                        doors.append(door)
                        zones['entry_exit'].append(door)
                
                elif entity.dxftype() == 'ARC':
                    # Handle arcs (often doors)
                    try:
                        center = entity.dxf.center
                        radius = entity.dxf.radius
                        if 0.5 < radius < 2:  # Door size
                            arc_door = {
                                'x': float(center.x - radius),
                                'y': float(center.y - radius),
                                'width': float(radius * 2),
                                'height': float(radius * 2),
                                'type': 'arc_door'
                            }
                            zones['entry_exit'].append(arc_door)
                    except:
                        pass
            
            # Calculate dimensions with proper scaling
            if max_x == float('-inf'):
                raise ValueError("No valid geometric data found in CAD file. Please ensure the file contains actual architectural drawings.")
            else:
                width = float(max_x - min_x)
                height = float(max_y - min_y)
                
                # Apply reasonable scaling if dimensions seem too large/small
                if width > 1000 or height > 1000:  # Likely in mm, convert to meters
                    width /= 1000
                    height /= 1000
                    # Scale all coordinates
                    for wall in walls:
                        wall['start']['x'] /= 1000
                        wall['start']['y'] /= 1000
                        wall['end']['x'] /= 1000
                        wall['end']['y'] /= 1000
                    for zone in zones['entry_exit']:
                        zone['x'] /= 1000
                        zone['y'] /= 1000
                        zone['width'] /= 1000
                        zone['height'] /= 1000
                    min_x /= 1000
                    min_y /= 1000
                    max_x /= 1000
                    max_y /= 1000
            
            # Filter walls and create zones array
            zones['walls'] = walls
            
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
        """Only called when file processing completely fails - no fake data"""
        raise ValueError(f"Unable to process architectural file: {filepath}. Please ensure you're uploading a valid DWG, DXF, PDF, or image file with actual floor plan data.")

    def get_plan_data(self, plan_id):
        return self.plans.get(plan_id)
