"""
Advanced CAD File Processor - Production Grade
Layer-aware extraction with element classification
"""
import uuid
import json
import os
import math
import ezdxf
import fitz  # PyMuPDF for PDF processing
import cv2
import numpy as np
from PIL import Image
from typing import Dict, List, Tuple, Optional, Any
import logging
from shapely.geometry import LineString, Polygon, Point
from shapely.ops import unary_union
import networkx as nx
from collections import defaultdict
import io # Import io for BytesIO

# Ensure logging is configured if not already done elsewhere
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class AdvancedCADProcessor:
    """Production-grade CAD file processor with layer-aware extraction and element classification"""

    def __init__(self):
        self.supported_formats = {'.dxf', '.dwg', '.pdf', '.png', '.jpg', '.jpeg'}
        self.color_mapping = {
            'walls': {'color': '#000000', 'render_color': '#6B7280', 'thickness': 3},
            'restricted_zones': {'color': '#ADD8E6', 'render_color': '#3B82F6', 'alpha': 0.3},
            'entrances_exits': {'color': '#FF0000', 'render_color': '#EF4444', 'thickness': 2},
            'doors': {'color': '#FF0000', 'render_color': '#EF4444', 'swing': True},
            'windows': {'color': '#0000FF', 'render_color': '#60A5FA', 'thickness': 1}
        }
        self.plans = {} # Keep this from original for potential future use or compatibility
        self.layer_mapping = { # Keep original layer mapping for fallback or if needed
            'walls': ['walls', 'wall', 'mur', 'murs', '0', 'outline'],
            'doors': ['doors', 'door', 'porte', 'portes', 'opening'],
            'windows': ['windows', 'window', 'fenetre', 'fenetres'],
            'restricted': ['restricted', 'no_entry', 'blocked'],
            'entry_exit': ['entry', 'exit', 'entrance', 'sortie', 'entree']
        }


    def process_plan(self, filepath: str) -> Dict[str, Any]:
        """Process uploaded architectural file with full layer-aware extraction"""
        plan_id = str(uuid.uuid4())
        file_ext = os.path.splitext(filepath)[1].lower()

        try:
            if file_ext == '.dxf':
                return self._process_dxf_file(filepath, plan_id)
            elif file_ext == '.dwg':
                # Placeholder for DWG processing (requires external libraries like ODA File Converter)
                logging.warning("DWG processing is not fully implemented. Returning a basic structure.")
                return {
                    'id': plan_id,
                    'filename': os.path.basename(filepath),
                    'file_type': 'dwg',
                    'error': 'DWG processing not implemented'
                }
            elif file_ext == '.pdf':
                return self._process_pdf_file(filepath, plan_id)
            elif file_ext in ['.png', '.jpg', '.jpeg']:
                return self._process_image_file(filepath, plan_id)
            else:
                raise ValueError(f"Unsupported file format: {file_ext}")
        except Exception as e:
            logging.error(f"Error processing CAD file {filepath}: {e}")
            raise

    def _process_dxf_file(self, filepath: str, plan_id: str) -> Dict[str, Any]:
        """Advanced DXF processing with layer-aware element classification"""
        try:
            doc = ezdxf.readfile(filepath)
            plan_data = {
                'id': plan_id,
                'filename': os.path.basename(filepath),
                'file_type': 'dxf',
                'walls': [],
                'zones': [],
                'doors': [],
                'windows': [],
                'dimensions': {'width': 0, 'height': 0},
                'layers': {},
                'scale_factor': 1.0,
                'units': 'meters'
            }

            # Extract all layers and their contents
            for layer_name in doc.layers:
                layer = doc.layers.get(layer_name)
                plan_data['layers'][layer_name] = {
                    'color': layer.color,
                    'elements': [],
                    'classification': self._classify_layer(layer_name, layer.color)
                }

            # Process all entities in model space
            msp = doc.modelspace()
            min_x, min_y = float('inf'), float('inf')
            max_x, max_y = float('-inf'), float('-inf')

            # Store all elements from all layers for later processing
            all_elements = []

            for entity in msp:
                element_data = self._extract_entity_data(entity)
                if element_data:
                    layer_name = entity.dxf.layer
                    if layer_name in plan_data['layers']:
                        plan_data['layers'][layer_name]['elements'].append(element_data)
                    all_elements.append(element_data)

                    # Update bounding box based on geometric entities with start/end points
                    if hasattr(entity, 'dxf'):
                        if hasattr(entity.dxf, 'start') and hasattr(entity.dxf, 'end'):
                            min_x = min(min_x, entity.dxf.start.x, entity.dxf.end.x)
                            max_x = max(max_x, entity.dxf.start.x, entity.dxf.end.x)
                            min_y = min(min_y, entity.dxf.start.y, entity.dxf.end.y)
                            max_y = max(max_y, entity.dxf.start.y, entity.dxf.end.y)
                        elif hasattr(entity.dxf, 'center') and hasattr(entity.dxf, 'radius'): # For circles
                            min_x = min(min_x, entity.dxf.center.x - entity.dxf.radius)
                            max_x = max(max_x, entity.dxf.center.x + entity.dxf.radius)
                            min_y = min(min_y, entity.dxf.center.y - entity.dxf.radius)
                            max_y = max(max_y, entity.dxf.center.y + entity.dxf.radius)
                        elif hasattr(entity.dxf, 'insert'): # For text
                            min_x = min(min_x, entity.dxf.insert.x)
                            max_x = max(max_x, entity.dxf.insert.x)
                            min_y = min(min_y, entity.dxf.insert.y)
                            max_y = max(max_y, entity.dxf.insert.y)

            # Handle cases where no entities were processed or bounding box is invalid
            if not all(math.isfinite(val) for val in [min_x, min_y, max_x, max_y]):
                logging.warning("Could not determine valid bounds for DXF. Using default.")
                min_x, min_y, max_x, max_y = 0, 0, 100, 100 # Default bounds

            plan_data['dimensions'] = {
                'width': max_x - min_x,
                'height': max_y - min_y,
                'min_x': min_x,
                'min_y': min_y,
                'max_x': max_x,
                'max_y': max_y
            }

            # Classify and organize elements based on layer classification
            self._classify_elements(plan_data)

            # Assign original code's processing methods if needed, or integrate their logic
            # For now, we rely on the new _classify_elements and _extract_entity_data

            return plan_data

        except FileNotFoundError:
            logging.error(f"DXF file not found: {filepath}")
            raise FileNotFoundError(f"DXF file not found at {filepath}")
        except ezdxf.DXFStructureError as e:
            logging.error(f"Invalid DXF file structure: {e}")
            raise ValueError(f"Invalid DXF file structure: {e}")
        except Exception as e:
            logging.error(f"Error processing DXF file: {e}")
            raise


    def _classify_layer(self, layer_name: str, color: int) -> str:
        """Classify layer type based on name and color"""
        layer_name_lower = layer_name.lower()

        if any(keyword in layer_name_lower for keyword in ['wall', 'mur', 'walls']):
            return 'walls'
        elif any(keyword in layer_name_lower for keyword in ['door', 'porte', 'doors']):
            return 'doors'
        elif any(keyword in layer_name_lower for keyword in ['window', 'fenetre', 'windows']):
            return 'windows'
        elif any(keyword in layer_name_lower for keyword in ['zone', 'area', 'region']):
            return 'zones'
        elif color == 4:  # Cyan - often used for restricted areas
            return 'restricted_zones'
        elif color == 1:  # Red - often used for entrances/exits
            return 'entrances_exits'
        else:
            # Fallback to original layer mapping if new classifications don't match
            for element_type, keywords in self.layer_mapping.items():
                if any(keyword in layer_name_lower for keyword in keywords):
                    return element_type if element_type in ['walls', 'doors', 'windows'] else 'walls'
            return 'general'

    def _extract_entity_data(self, entity) -> Optional[Dict[str, Any]]:
        """Extract geometric data from DXF entity"""
        entity_type = entity.dxftype()

        if entity_type == 'LINE':
            return {
                'type': 'line',
                'start': {'x': float(entity.dxf.start.x), 'y': float(entity.dxf.start.y)},
                'end': {'x': float(entity.dxf.end.x), 'y': float(entity.dxf.end.y)},
                'layer': entity.dxf.layer,
                'color': entity.dxf.color,
                'length': math.sqrt((entity.dxf.end.x - entity.dxf.start.x)**2 + (entity.dxf.end.y - entity.dxf.start.y)**2)
            }
        elif entity_type == 'POLYLINE' or entity_type == 'LWPOLYLINE':
            points = []
            try:
                # Use get_points for newer ezdxf versions, fallback if needed
                if hasattr(entity, 'get_points'):
                    vertices = entity.get_points()
                else:
                    vertices = entity.vertices # Older ezdxf versions

                for vertex in vertices:
                    # Ensure vertex is a tuple/list of coordinates, handle potential data variations
                    if isinstance(vertex, (list, tuple)) and len(vertex) >= 2:
                         points.append({'x': float(vertex[0]), 'y': float(vertex[1])})
                    elif hasattr(vertex, 'dxf') and hasattr(vertex.dxf, 'location'): # For older Vertex objects
                         points.append({'x': float(vertex.dxf.location.x), 'y': float(vertex.dxf.location.y)})
            except Exception as e:
                logging.error(f"Error processing polyline vertices: {e}")
                return None # Skip if polyline processing fails

            return {
                'type': 'polyline',
                'points': points,
                'closed': entity.closed,
                'layer': entity.dxf.layer,
                'color': entity.dxf.color
            }
        elif entity_type == 'CIRCLE':
            # Filter for reasonable door/window sizes based on original code
            radius = entity.dxf.radius
            if 0.3 < radius < 3.0:
                return {
                    'type': 'circle',
                    'center': {'x': float(entity.dxf.center.x), 'y': float(entity.dxf.center.y)},
                    'radius': float(radius),
                    'layer': entity.dxf.layer,
                    'color': entity.dxf.color
                }
            return None
        elif entity_type == 'ARC':
            # Filter for reasonable door swing size based on original code
            radius = entity.dxf.radius
            if 0.5 < radius < 2.5:
                return {
                    'type': 'arc',
                    'center': {'x': float(entity.dxf.center.x), 'y': float(entity.dxf.center.y)},
                    'radius': float(radius),
                    'start_angle': float(entity.dxf.start_angle),
                    'end_angle': float(entity.dxf.end_angle),
                    'layer': entity.dxf.layer,
                    'color': entity.dxf.color
                }
            return None
        elif entity_type == 'TEXT' or entity_type == 'MTEXT':
            return {
                'type': 'text',
                'text': entity.dxf.text,
                'position': {'x': float(entity.dxf.insert.x), 'y': float(entity.dxf.insert.y)},
                'height': float(entity.dxf.height),
                'layer': entity.dxf.layer,
                'color': entity.dxf.color
            }

        return None

    def _classify_elements(self, plan_data: Dict[str, Any]):
        """Classify and organize elements by type"""
        for layer_name, layer_data in plan_data['layers'].items():
            classification = layer_data['classification']

            for element in layer_data['elements']:
                # Add render styles based on classification
                render_style = self.color_mapping.get(classification, self.color_mapping['walls']) # Default to walls style

                if classification == 'walls':
                    plan_data['walls'].append({
                        **element,
                        'render_style': render_style
                    })
                elif classification == 'doors':
                    plan_data['doors'].append({
                        **element,
                        'render_style': render_style
                    })
                elif classification == 'windows':
                    plan_data['windows'].append({
                        **element,
                        'render_style': render_style
                    })
                elif classification in ['zones', 'restricted_zones', 'entrances_exits']:
                    zone_type = 'restricted' if 'restricted' in classification else 'entrance' if 'entrance' in classification else 'general'
                    plan_data['zones'].append({
                        **element,
                        'zone_type': zone_type,
                        'render_style': render_style
                    })

    def _process_pdf_file(self, filepath: str, plan_id: str) -> Dict[str, Any]:
        """Advanced PDF processing with page analysis"""
        try:
            doc = fitz.open(filepath)
            plan_data = {
                'id': plan_id,
                'filename': os.path.basename(filepath),
                'file_type': 'pdf',
                'walls': [],
                'zones': [],
                'doors': [],
                'windows': [],
                'dimensions': {'width': 0, 'height': 0},
                'pages': len(doc),
                'scale_factor': 1.0,
                'units': 'points' # PDF units are typically points
            }

            # Find the main floor plan page (assuming the first page with most paths is the plan)
            main_page_idx = self._identify_main_floor_plan_page(doc)
            page = doc[main_page_idx]

            # Extract vector graphics (paths)
            paths = page.get_drawings()

            # Process vector paths
            for path in paths:
                self._process_pdf_path(path, plan_data)

            # Process images if any (e.g., scanned plans) - basic handling
            images = page.get_images(full=True)
            for img_index, img_info in enumerate(images):
                 xref = img_info[0]
                 base_image = doc.extract_image(xref)
                 image_bytes = base_image["image"]
                 # Convert to PIL Image for potential further processing (e.g., OCR, vectorization)
                 img = Image.open(io.BytesIO(image_bytes))
                 plan_data.setdefault('images', []).append({
                     'index': img_index,
                     'bbox': img_info[7], # Bounding box of the image on the page
                     'width': img.width,
                     'height': img.height
                 })


            # Calculate page dimensions
            rect = page.rect
            plan_data['dimensions'] = {
                'width': rect.width,
                'height': rect.height,
                'min_x': rect.x0,
                'min_y': rect.y0,
                'max_x': rect.x1,
                'max_y': rect.y1
            }

            doc.close()
            return plan_data

        except FileNotFoundError:
            logging.error(f"PDF file not found: {filepath}")
            raise FileNotFoundError(f"PDF file not found at {filepath}")
        except Exception as e:
            logging.error(f"Error processing PDF file: {e}")
            raise

    def _identify_main_floor_plan_page(self, doc) -> int:
        """Identify the main floor plan page from multi-page PDF"""
        max_significant_paths = 0
        main_page_index = 0

        for page_num in range(len(doc)):
            page = doc[page_num]
            paths = page.get_drawings()

            # Count paths that have actual drawing items (lines, curves, etc.)
            significant_paths_count = sum(len(p.get('items', [])) for p in paths)

            if significant_paths_count > max_significant_paths:
                max_significant_paths = significant_paths_count
                main_page_index = page_num

        return main_page_index

    def _process_pdf_path(self, path: Dict, plan_data: Dict[str, Any]):
        """Process PDF vector path and classify as architectural element"""
        items = path.get('items', [])
        stroke_color_rgba = path.get('stroke', {}).get('color') # RGBA tuple
        fill_color_rgba = path.get('fill', {}).get('color')
        width = path.get('width', 1.0)

        # Determine element type based on stroke color and original layer mapping logic
        element_type = 'general'
        if stroke_color_rgba:
            r, g, b = stroke_color_rgba[:3] # Use RGB part

            # Use a tolerance for color matching
            tolerance = 0.1 

            # Black or very dark colors for walls
            if all(c < tolerance for c in [r, g, b]):
                element_type = 'walls'
            # Reddish colors for entrances/exits
            elif r > 1 - tolerance and g < 0.2 and b < 0.2:
                element_type = 'entrances_exits'
            # Bluish colors for windows
            elif b > 1 - tolerance and r < 0.2 and g < 0.2:
                element_type = 'windows'
            # Other specific colors or fallback to general
            else:
                # Try matching with original layer mapping keywords if color is not distinctive
                # This part is complex without direct access to original layer names from PDF paths
                # For now, rely on color-based classification or default to general
                pass 

        # Process geometric items within the path
        for item in items:
            item_type = item[0]

            if item_type == 'l':  # Line to
                # item[1] is (x1, y1), item[2] is (x2, y2)
                line_data = {
                    'type': 'line',
                    'start': {'x': item[1], 'y': item[2]},
                    'end': {'x': item[3], 'y': item[4]},
                    'width': width,
                    'color': stroke_color_rgba # Store RGBA color
                }
                if element_type == 'walls':
                    plan_data['walls'].append(line_data)
                elif element_type == 'doors': # Assuming red lines can be doors
                    plan_data['doors'].append(line_data)
                elif element_type == 'windows':
                    plan_data['windows'].append(line_data)
                elif element_type == 'entrances_exits':
                    plan_data['zones'].append({
                        **line_data,
                        'zone_type': 'entrance',
                        'render_style': self.color_mapping.get('entrances_exits', {})
                    })

            elif item_type == 'm': # Move to (start of a new subpath)
                pass # Ignore move to commands for now
            elif item_type == 'c': # Curve to (Bézier curve)
                # Extracting curves into lines or arcs is more complex and might require approximation
                # For simplicity, we'll skip processing curves as distinct architectural elements for now
                pass
            elif item_type == 're': # Rectangle
                x0, y0, x1, y1 = item[1], item[2], item[3], item[4]
                rect_data = {
                    'type': 'rectangle',
                    'x0': x0, 'y0': y0, 'x1': x1, 'y1': y1,
                    'width': abs(x1 - x0), 'height': abs(y1 - y0),
                    'color': stroke_color_rgba
                }
                # Rectangles could represent various elements, e.g., zones or openings
                if element_type == 'restricted_zones': # Example: use for restricted zones
                     plan_data['zones'].append({
                        **rect_data,
                        'zone_type': 'restricted',
                        'render_style': self.color_mapping.get('restricted_zones', {})
                     })


    def _process_image_file(self, filepath: str, plan_id: str) -> Dict[str, Any]:
        """Process image files (PNG, JPG) using OCR and basic shape detection"""
        try:
            img = Image.open(filepath).convert('RGB')
            width, height = img.size

            plan_data = {
                'id': plan_id,
                'filename': os.path.basename(filepath),
                'file_type': 'image',
                'walls': [],
                'zones': [],
                'doors': [],
                'windows': [],
                'dimensions': {'width': width, 'height': height},
                'scale_factor': 1.0, # Placeholder, real scale needs calibration
                'units': 'pixels' # Default units for images
            }

            # Basic image processing using OpenCV for shape detection (simplified)
            img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2GRAY)
            # Apply thresholding to get binary image
            _, thresh = cv2.threshold(img_cv, 200, 255, cv2.THRESH_BINARY_INV) # Adjust threshold as needed

            # Find contours
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            for contour in contours:
                # Approximate contour to simplify shapes
                perimeter = cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, 0.02 * perimeter, True)

                x, y, w, h = cv2.boundingRect(contour)

                # Classify based on shape properties (e.g., aspect ratio, area) - very basic
                if len(approx) == 4: # Potential rectangles/walls
                    # Check aspect ratio and size to guess if it's a wall segment or room boundary
                    aspect_ratio = float(w) / h if h > 0 else 0
                    if 0.8 < aspect_ratio < 1.2 and w > 5 and h > 5: # Likely square/rect, could be wall segment
                         plan_data['walls'].append({
                             'type': 'rectangle', # Represent as bounding box for now
                             'x0': x, 'y0': y, 'x1': x+w, 'y1': y+h,
                             'width': w, 'height': h,
                             'render_style': self.color_mapping['walls']
                         })
                    # More sophisticated logic needed here for complex shapes and OCR for text

            # Placeholder for OCR if text detection is needed
            # Example: using pytesseract if installed
            # try:
            #     import pytesseract
            #     text = pytesseract.image_to_string(img)
            #     plan_data['text_content'] = text
            # except ImportError:
            #     logging.warning("pytesseract not installed, skipping OCR.")
            # except Exception as e:
            #     logging.warning(f"OCR failed: {e}")


            return plan_data

        except FileNotFoundError:
            logging.error(f"Image file not found: {filepath}")
            raise FileNotFoundError(f"Image file not found at {filepath}")
        except Exception as e:
            logging.error(f"Error processing image file: {e}")
            raise


    def get_plan_data(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve processed plan data by ID"""
        # This would typically query a database or cache
        # Returning from self.plans for direct access if it was populated
        return self.plans.get(plan_id)

    # Original methods from the initial code that might still be relevant or need integration:

    def _identify_main_floor_plan(self, doc):
        """Identify the main floor plan among multiple layouts (from original code)"""
        layouts = [doc.modelspace()]

        for layout_name in doc.layout_names():
            if layout_name.lower() != 'model':
                try:
                    layouts.append(doc.layouts.get(layout_name))
                except:
                    continue

        best_layout = None
        best_score = 0

        for layout in layouts:
            score = self._score_layout_for_floor_plan(layout)
            if score > best_score:
                best_score = score
                best_layout = layout

        return best_layout or doc.modelspace()

    def _score_layout_for_floor_plan(self, layout):
        """Score layout based on typical floor plan characteristics (from original code)"""
        score = 0
        line_count = 0
        total_length = 0

        for entity in layout:
            if entity.dxftype() in ['LINE', 'POLYLINE', 'LWPOLYLINE']:
                line_count += 1
                if hasattr(entity, 'dxf'):
                    layer = getattr(entity.dxf, 'layer', '').lower()
                    if any(wall_keyword in layer for wall_keyword in self.layer_mapping['walls']):
                        score += 10

                if entity.dxftype() == 'LINE':
                    start, end = entity.dxf.start, entity.dxf.end
                    length = math.sqrt((end.x - start.x)**2 + (end.y - start.y)**2)
                    total_length += length

        score += min(line_count * 2, 100)
        score += min(total_length / 1000, 50)

        return score

    def _extract_architectural_elements(self, layout):
        """Extract and classify architectural elements by layer (from original code)"""
        elements = {
            'walls': [],
            'doors': [],
            'windows': [],
            'annotations': [],
            'layers': defaultdict(list)
        }

        bounds = {'min_x': float('inf'), 'min_y': float('inf'),
                  'max_x': float('-inf'), 'max_y': float('-inf')}

        for entity in layout:
            layer_name = getattr(entity.dxf, 'layer', 'Default').lower()
            element_type = self._classify_element_by_layer(layer_name)

            if entity.dxftype() == 'LINE':
                element = self._process_line_entity(entity, element_type, bounds)
                elements[element_type].append(element)
                elements['layers'][layer_name].append(element)

            elif entity.dxftype() in ['POLYLINE', 'LWPOLYLINE']:
                polyline_elements = self._process_polyline_entity(entity, element_type, bounds)
                elements[element_type].extend(polyline_elements)
                elements['layers'][layer_name].extend(polyline_elements)

            elif entity.dxftype() == 'CIRCLE':
                element = self._process_circle_entity(entity, bounds)
                if element:
                    elements['doors'].append(element)
                    elements['layers'][layer_name].append(element)

            elif entity.dxftype() == 'ARC':
                element = self._process_arc_entity(entity, bounds)
                if element:
                    elements['doors'].append(element)
                    elements['layers'][layer_name].append(element)

        elements['bounds'] = bounds
        return elements

    def _classify_element_by_layer(self, layer_name):
        """Classify architectural elements based on layer names (from original code)"""
        layer_lower = layer_name.lower()

        for element_type, keywords in self.layer_mapping.items():
            if any(keyword in layer_lower for keyword in keywords):
                return element_type if element_type in ['walls', 'doors', 'windows'] else 'walls'

        if any(term in layer_lower for term in ['door', 'porte', 'opening']):
            return 'doors'
        elif any(term in layer_lower for term in ['window', 'fenetre']):
            return 'windows'
        else:
            return 'walls'

    def _process_line_entity(self, entity, element_type, bounds):
        """Process LINE entities (from original code)"""
        start, end = entity.dxf.start, entity.dxf.end

        bounds['min_x'] = min(bounds['min_x'], start.x, end.x)
        bounds['max_x'] = max(bounds['max_x'], start.x, end.x)
        bounds['min_y'] = min(bounds['min_y'], start.y, end.y)
        bounds['max_y'] = max(bounds['max_y'], start.y, end.y)

        length = math.sqrt((end.x - start.x)**2 + (end.y - start.y)**2)

        return {
            'start': {'x': float(start.x), 'y': float(start.y)},
            'end': {'x': float(end.x), 'y': float(end.y)},
            'layer': getattr(entity.dxf, 'layer', 'Default'),
            'length': length,
            'type': 'line',
            'element_type': element_type
        }

    def _process_polyline_entity(self, entity, element_type, bounds):
        """Process POLYLINE/LWPOLYLINE entities (from original code)"""
        elements = []
        try:
            points = list(entity.get_points())
            for i in range(len(points) - 1):
                start, end = points[i], points[i + 1]

                bounds['min_x'] = min(bounds['min_x'], start[0], end[0])
                bounds['max_x'] = max(bounds['max_x'], start[0], end[0])
                bounds['min_y'] = min(bounds['min_y'], start[1], end[1])
                bounds['max_y'] = max(bounds['max_y'], start[1], end[1])

                element = {
                    'start': {'x': float(start[0]), 'y': float(start[1])},
                    'end': {'x': float(end[0]), 'y': float(end[1])},
                    'layer': getattr(entity.dxf, 'layer', 'Default'),
                    'type': 'polyline',
                    'element_type': element_type
                }
                elements.append(element)
        except:
            pass

        return elements

    def _process_circle_entity(self, entity, bounds):
        """Process CIRCLE entities (often doors) (from original code)"""
        center = entity.dxf.center
        radius = entity.dxf.radius

        if 0.3 < radius < 3.0:
            bounds['min_x'] = min(bounds['min_x'], center.x - radius)
            bounds['max_x'] = max(bounds['max_x'], center.x + radius)
            bounds['min_y'] = min(bounds['min_y'], center.y - radius)
            bounds['max_y'] = max(bounds['max_y'], center.y + radius)

            return {
                'center': {'x': float(center.x), 'y': float(center.y)},
                'radius': float(radius),
                'type': 'circle',
                'element_type': 'door'
            }
        return None

    def _process_arc_entity(self, entity, bounds):
        """Process ARC entities (door swings) (from original code)"""
        try:
            center = entity.dxf.center
            radius = entity.dxf.radius
            start_angle = entity.dxf.start_angle
            end_angle = entity.dxf.end_angle

            if 0.5 < radius < 2.5:
                bounds['min_x'] = min(bounds['min_x'], center.x - radius)
                bounds['max_x'] = max(bounds['max_x'], center.x + radius)
                bounds['min_y'] = min(bounds['min_y'], center.y - radius)
                bounds['max_y'] = max(bounds['max_y'], center.y + radius)

                return {
                    'center': {'x': float(center.x), 'y': float(center.y)},
                    'radius': float(radius),
                    'start_angle': float(start_angle),
                    'end_angle': float(end_angle),
                    'type': 'arc',
                    'element_type': 'door'
                }
        except:
            pass
        return None

    def _analyze_geometry(self, elements):
        """Perform geometric analysis of architectural elements (from original code)"""
        bounds = elements['bounds']

        wall_lines = []
        for wall in elements['walls']:
            line = LineString([
                (wall['start']['x'], wall['start']['y']),
                (wall['end']['x'], wall['end']['y'])
            ])
            wall_lines.append(line)

        outline = self._create_building_outline(wall_lines, bounds)
        interior_spaces = self._identify_interior_spaces(wall_lines, outline)

        return {
            'bounds': bounds,
            'wall_lines': wall_lines,
            'outline': outline,
            'interior_spaces': interior_spaces,
            'total_area': self._calculate_area(outline)
        }

    def _create_building_outline(self, wall_lines, bounds):
        """Create building outline from wall network (from original code)"""
        try:
            buffered_walls = [line.buffer(0.1) for line in wall_lines]
            union_walls = unary_union(buffered_walls)

            if hasattr(union_walls, 'exterior'):
                return union_walls.exterior
            else:
                return Polygon([
                    (bounds['min_x'], bounds['min_y']),
                    (bounds['max_x'], bounds['min_y']),
                    (bounds['max_x'], bounds['max_y']),
                    (bounds['min_x'], bounds['max_y'])
                ])
        except:
            return Polygon([
                (bounds['min_x'], bounds['min_y']),
                (bounds['max_x'], bounds['min_y']),
                (bounds['max_x'], bounds['max_y']),
                (bounds['min_x'], bounds['max_y'])
            ])

    def _identify_interior_spaces(self, wall_lines, outline):
        """Identify interior spaces using wall network analysis (from original code)"""
        spaces = []

        try:
            bounds = outline.bounds
            grid_resolution = min((bounds[2] - bounds[0]), (bounds[3] - bounds[1])) / 20

            x_coords = np.arange(bounds[0], bounds[2], grid_resolution)
            y_coords = np.arange(bounds[1], bounds[3], grid_resolution)

            for x in x_coords:
                for y in y_coords:
                    point = Point(x, y)
                    if outline.contains(point):
                        min_wall_distance = min([point.distance(wall) for wall in wall_lines] or [float('inf')])
                        if min_wall_distance > 1.0:
                            spaces.append({'center': (x, y), 'type': 'available'})
        except:
            pass

        return spaces

    def _generate_intelligent_zones(self, elements, geometry):
        """Generate zones using architectural intelligence (from original code)"""
        zones = {
            'entry_exit': [],
            'no_entry': [],
            'available': [],
            'restricted': []
        }

        bounds = geometry['bounds']

        for door in elements['doors']:
            if door['type'] in ['circle', 'arc']:
                center = door['center']
                radius = door.get('radius', 1.0)

                zone = {
                    'x': center['x'] - radius * 1.5,
                    'y': center['y'] - radius * 1.5,
                    'width': radius * 3,
                    'height': radius * 3,
                    'type': 'entry_exit'
                }
                zones['entry_exit'].append(zone)

        margin = min(bounds['max_x'] - bounds['min_x'], bounds['max_y'] - bounds['min_y']) * 0.1

        perimeter_zones = [
            {'x': bounds['min_x'], 'y': bounds['min_y'], 'width': margin, 'height': margin},
            {'x': bounds['max_x'] - margin, 'y': bounds['max_y'] - margin, 'width': margin, 'height': margin}
        ]

        for zone in perimeter_zones:
            zone['type'] = 'no_entry'
            zones['no_entry'].append(zone)

        return zones

    def _calculate_precise_dimensions(self, geometry):
        """Calculate precise building dimensions (from original code)"""
        bounds = geometry['bounds']

        width = bounds['max_x'] - bounds['min_x']
        height = bounds['max_y'] - bounds['min_y']

        normalized_bounds = {
            'min_x': 0,
            'min_y': 0,
            'max_x': width,
            'max_y': height
        }

        return {
            'width': float(width),
            'height': float(height),
            'area': float(width * height),
            'bounds': normalized_bounds,
            'units': 'meters'
        }

    def _calculate_area(self, polygon):
        """Calculate area of a polygon (from original code)"""
        try:
            return polygon.area
        except:
            return 0.0

    def normalize_coordinates(self, elements, bounds):
        """Normalize coordinates to start from origin (from original code)"""
        offset_x = bounds['min_x']
        offset_y = bounds['min_y']

        normalized_elements = []
        for element in elements:
            if 'start' in element and 'end' in element:
                normalized = element.copy()
                normalized['start'] = {
                    'x': element['start']['x'] - offset_x,
                    'y': element['start']['y'] - offset_y
                }
                normalized['end'] = {
                    'x': element['end']['x'] - offset_x,
                    'y': element['end']['y'] - offset_y
                }
                normalized_elements.append(normalized)

        return normalized_elements