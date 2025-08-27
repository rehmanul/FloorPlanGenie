
import cv2
import numpy as np
import PyPDF2
import ezdxf
from PIL import Image
import uuid
import json
import os

class PlanProcessor:
    def __init__(self):
        self.plans_data = {}
        
    def process_plan(self, filepath):
        """Process uploaded plan file and extract geometry"""
        file_ext = os.path.splitext(filepath)[1].lower()
        
        if file_ext == '.pdf':
            return self._process_pdf(filepath)
        elif file_ext in ['.dwg', '.dxf']:
            return self._process_cad(filepath)
        elif file_ext in ['.jpg', '.jpeg', '.png']:
            return self._process_image(filepath)
        else:
            raise ValueError(f"Unsupported file format: {file_ext}")
    
    def _process_pdf(self, filepath):
        """Extract plan from PDF using OCR and image processing"""
        plan_id = str(uuid.uuid4())
        
        # Convert PDF to image for processing
        # In production, use pdf2image library
        # For now, assume we extract the plan geometry
        
        plan_data = {
            'id': plan_id,
            'source_file': filepath,
            'dimensions': {'width': 20.0, 'height': 15.0},  # meters
            'walls': self._detect_walls_from_pdf(filepath),
            'zones': {
                'no_entry': [],  # Blue zones
                'entry_exit': [],  # Red zones
                'walls': []  # Black walls
            }
        }
        
        self.plans_data[plan_id] = plan_data
        return plan_data
    
    def _process_cad(self, filepath):
        """Process DWG/DXF files"""
        plan_id = str(uuid.uuid4())
        
        try:
            doc = ezdxf.readfile(filepath)
            modelspace = doc.modelspace()
            
            walls = []
            zones = {'no_entry': [], 'entry_exit': [], 'walls': []}
            
            # Extract lines (walls) and areas (zones)
            for entity in modelspace:
                if entity.dxftype() == 'LINE':
                    start = entity.dxf.start
                    end = entity.dxf.end
                    walls.append({
                        'start': {'x': start.x, 'y': start.y},
                        'end': {'x': end.x, 'y': end.y},
                        'layer': entity.dxf.layer
                    })
                elif entity.dxftype() in ['LWPOLYLINE', 'POLYLINE']:
                    # Process zones based on color/layer
                    self._classify_zone(entity, zones)
            
            plan_data = {
                'id': plan_id,
                'source_file': filepath,
                'dimensions': self._calculate_plan_dimensions(walls),
                'walls': walls,
                'zones': zones
            }
            
            self.plans_data[plan_id] = plan_data
            return plan_data
            
        except Exception as e:
            raise ValueError(f"Error processing CAD file: {str(e)}")
    
    def _process_image(self, filepath):
        """Process image files using computer vision"""
        plan_id = str(uuid.uuid4())
        
        # Load image
        image = cv2.imread(filepath)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Detect walls using edge detection
        walls = self._detect_walls_from_image(gray)
        
        # Detect colored zones
        zones = self._detect_zones_from_image(image)
        
        plan_data = {
            'id': plan_id,
            'source_file': filepath,
            'dimensions': {'width': gray.shape[1] * 0.1, 'height': gray.shape[0] * 0.1},  # Assume 10px = 1m
            'walls': walls,
            'zones': zones
        }
        
        self.plans_data[plan_id] = plan_data
        return plan_data
    
    def _detect_walls_from_image(self, gray_image):
        """Detect walls using computer vision"""
        # Apply edge detection
        edges = cv2.Canny(gray_image, 50, 150, apertureSize=3)
        
        # Detect lines using Hough transform
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=100, minLineLength=50, maxLineGap=10)
        
        walls = []
        if lines is not None:
            for line in lines:
                x1, y1, x2, y2 = line[0]
                walls.append({
                    'start': {'x': x1 * 0.1, 'y': y1 * 0.1},  # Convert pixels to meters
                    'end': {'x': x2 * 0.1, 'y': y2 * 0.1},
                    'thickness': 0.2
                })
        
        return walls
    
    def _detect_zones_from_image(self, image):
        """Detect colored zones in the image"""
        # Convert to HSV for better color detection
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        zones = {'no_entry': [], 'entry_exit': [], 'walls': []}
        
        # Define color ranges
        blue_range = [(100, 50, 50), (130, 255, 255)]  # Blue (no entry)
        red_range = [(0, 50, 50), (10, 255, 255)]      # Red (entry/exit)
        
        # Detect blue zones
        blue_mask = cv2.inRange(hsv, np.array(blue_range[0]), np.array(blue_range[1]))
        blue_contours, _ = cv2.findContours(blue_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in blue_contours:
            x, y, w, h = cv2.boundingRect(contour)
            zones['no_entry'].append({
                'x': x * 0.1, 'y': y * 0.1,
                'width': w * 0.1, 'height': h * 0.1
            })
        
        # Detect red zones
        red_mask = cv2.inRange(hsv, np.array(red_range[0]), np.array(red_range[1]))
        red_contours, _ = cv2.findContours(red_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in red_contours:
            x, y, w, h = cv2.boundingRect(contour)
            zones['entry_exit'].append({
                'x': x * 0.1, 'y': y * 0.1,
                'width': w * 0.1, 'height': h * 0.1
            })
        
        return zones
    
    def _detect_walls_from_pdf(self, filepath):
        """Extract walls from PDF (simplified)"""
        # This would require more sophisticated PDF processing
        # For now, return sample walls
        return [
            {'start': {'x': 0, 'y': 0}, 'end': {'x': 20, 'y': 0}, 'thickness': 0.2},
            {'start': {'x': 20, 'y': 0}, 'end': {'x': 20, 'y': 15}, 'thickness': 0.2},
            {'start': {'x': 20, 'y': 15}, 'end': {'x': 0, 'y': 15}, 'thickness': 0.2},
            {'start': {'x': 0, 'y': 15}, 'end': {'x': 0, 'y': 0}, 'thickness': 0.2}
        ]
    
    def _calculate_plan_dimensions(self, walls):
        """Calculate overall plan dimensions from walls"""
        if not walls:
            return {'width': 10.0, 'height': 10.0}
        
        all_x = []
        all_y = []
        
        for wall in walls:
            all_x.extend([wall['start']['x'], wall['end']['x']])
            all_y.extend([wall['start']['y'], wall['end']['y']])
        
        return {
            'width': max(all_x) - min(all_x),
            'height': max(all_y) - min(all_y)
        }
    
    def _classify_zone(self, entity, zones):
        """Classify CAD entity into zone types based on layer/color"""
        layer = entity.dxf.layer.lower()
        
        if 'no_entry' in layer or 'blue' in layer:
            # Add to no_entry zones
            pass
        elif 'entry' in layer or 'exit' in layer or 'red' in layer:
            # Add to entry_exit zones
            pass
    
    def get_plan_data(self, plan_id):
        """Retrieve stored plan data"""
        if plan_id not in self.plans_data:
            raise ValueError(f"Plan {plan_id} not found")
        return self.plans_data[plan_id]
