
import os
import json
from flask import Flask, render_template, request, jsonify, send_file, render_template_string
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.utils import secure_filename
from plan_processor import PlanProcessor
from space_optimizer import SpaceOptimizer
from visual_generator import VisualGenerator

# Import production-grade components
try:
    from advanced_cad_processor import AdvancedCADProcessor
    from intelligent_placement_engine import IntelligentPlacementEngine
    from interactive_canvas import InteractiveCanvasRenderer
    from modern_ui_controller import ModernUIController
    PRODUCTION_MODE = True
except ImportError as e:
    print(f"Production components not available: {e}")
    PRODUCTION_MODE = False

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///floorplan.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size

# initialize the app with the extension
db.init_app(app)

with app.app_context():
    try:
        import models
        db.create_all()
    except Exception as e:
        print(f"Database initialization warning: {e}")

@app.errorhandler(413)
def too_large(e):
    return jsonify({'error': 'File too large. Maximum size is 100MB.'}), 413

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('static/outputs', exist_ok=True)

# Initialize processors
plan_processor = PlanProcessor()
space_optimizer = SpaceOptimizer()
visual_generator = VisualGenerator()

# Initialize production-grade components if available
if PRODUCTION_MODE:
    try:
        advanced_cad_processor = AdvancedCADProcessor()
        intelligent_placement_engine = IntelligentPlacementEngine()
        interactive_canvas_renderer = InteractiveCanvasRenderer()
        modern_ui_controller = ModernUIController()
        print("✅ Production-grade components initialized successfully")
    except Exception as e:
        print(f"❌ Error initializing production components: {e}")
        PRODUCTION_MODE = False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/professional')
def professional():
    """Serve the professional interface"""
    if not PRODUCTION_MODE:
        return render_template('professional.html')
    
    try:
        # Generate modern interface with default data
        default_data = {
            'dimensions': {'width': 50, 'height': 40},
            'statistics': {
                'total_boxes': 0,
                'utilization_rate': 0,
                'total_corridors': 0,
                'efficiency_score': 0
            }
        }
        
        html_content = modern_ui_controller.generate_modern_interface_html(default_data)
        return render_template_string(html_content)
        
    except Exception as e:
        print(f"Error serving professional interface: {e}")
        return render_template('professional.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if not file.filename:
            return jsonify({'error': 'Invalid filename'}), 400

        # Check file extension
        allowed_extensions = {'dxf', 'dwg', 'pdf', 'png', 'jpg', 'jpeg'}
        file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
        if file_ext not in allowed_extensions:
            return jsonify({'error': f'File type .{file_ext} not supported. Please upload DXF, DWG, PDF, or image files.'}), 400

        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Ensure the file is actually saved
        try:
            file.save(filepath)
            if not os.path.exists(filepath):
                return jsonify({'error': 'Failed to save uploaded file'}), 500
        except Exception as e:
            return jsonify({'error': f'Error saving file: {str(e)}'}), 500

        # Process the plan with timeout protection
        try:
            print(f"Processing file: {filename} at path: {filepath}")
            file_size = os.path.getsize(filepath)
            print(f"File size: {file_size} bytes")
            
            # Try production-grade processor first
            if PRODUCTION_MODE:
                try:
                    plan_data = advanced_cad_processor.process_plan(filepath)
                    print(f"File processed with advanced processor. Plan ID: {plan_data['id']}")
                except Exception as advanced_error:
                    print(f"Advanced processor failed: {advanced_error}")
                    # Fallback to standard processor
                    plan_data = plan_processor.process_plan(filepath)
                    print(f"File processed with standard processor. Plan ID: {plan_data['id']}")
            else:
                plan_data = plan_processor.process_plan(filepath)
                print(f"File processed with standard processor. Plan ID: {plan_data['id']}")

            # Generate initial visual of the processed plan
            initial_visual_data = {
                'walls': plan_data.get('walls', []),
                'zones': plan_data.get('zones', []),
                'dimensions': plan_data.get('dimensions', {}),
                'doors': plan_data.get('doors', []),
                'windows': plan_data.get('windows', [])
            }

            # Generate visual representation
            try:
                if PRODUCTION_MODE:
                    # Generate interactive SVG
                    interactive_result = interactive_canvas_renderer.generate_interactive_svg(initial_visual_data)
                    visual_path = interactive_result.get('svg_path')
                else:
                    # Use standard visual generator
                    visual_path = visual_generator.generate(initial_visual_data, '2d')
            except Exception as visual_error:
                print(f"Visual generation failed: {visual_error}")
                visual_path = None

            return jsonify({
                'success': True,
                'plan_id': plan_data['id'],
                'dimensions': plan_data.get('dimensions', {}),
                'walls': plan_data.get('walls', []),
                'zones': plan_data.get('zones', []),
                'doors': plan_data.get('doors', []),
                'windows': plan_data.get('windows', []),
                'visual_path': visual_path.replace('static/', '/static/') if visual_path else None,
                'file_type': plan_data.get('file_type', file_ext),
                'production_mode': PRODUCTION_MODE
            })
            
        except Exception as e:
            print(f"Upload processing error: {e}")
            return jsonify({'error': f'Error processing file: {str(e)}'}), 500
            
    except Exception as e:
        print(f"Upload error: {e}")
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

@app.route('/optimize', methods=['POST'])
def optimize_space():
    data = request.json or {}
    plan_id = data.get('plan_id')
    box_dimensions = data.get('box_dimensions', {'width': 3.0, 'height': 4.0})
    corridor_width = data.get('corridor_width', 1.2)
    layout_profile = data.get('layout_profile', '25%')

    print(f"Optimization request - Plan ID: {plan_id}, Profile: {layout_profile}")
    
    try:
        # Get plan data - try advanced processor first if available
        plan_data = None
        if PRODUCTION_MODE:
            try:
                plan_data = advanced_cad_processor.get_plan_data(plan_id)
            except:
                pass
        
        if not plan_data:
            plan_data = plan_processor.get_plan_data(plan_id)
        
        if not plan_data:
            # If no plan found, try reprocessing the most recent file
            import glob
            upload_files = glob.glob('uploads/*.dxf') + glob.glob('uploads/*.dwg') + glob.glob('uploads/*.pdf')
            if upload_files:
                latest_file = max(upload_files, key=os.path.getctime)
                print(f"Reprocessing latest file: {latest_file}")
                
                if PRODUCTION_MODE:
                    try:
                        plan_data = advanced_cad_processor.process_plan(latest_file)
                    except:
                        plan_data = plan_processor.process_plan(latest_file)
                else:
                    plan_data = plan_processor.process_plan(latest_file)
                
                plan_id = plan_data['id']
            else:
                return jsonify({'error': 'No architectural file found. Please upload a DXF, DWG, or PDF file first.'}), 404

        # Optimize space placement using appropriate engine
        try:
            if PRODUCTION_MODE:
                optimization_result = intelligent_placement_engine.optimize_placement(
                    plan_data, box_dimensions, corridor_width, layout_profile
                )
            else:
                optimization_result = space_optimizer.optimize_placement(
                    plan_data, box_dimensions, corridor_width
                )
        except Exception as opt_error:
            print(f"Optimization error: {opt_error}")
            # Fallback to basic optimization
            optimization_result = space_optimizer.optimize_placement(
                plan_data, box_dimensions, corridor_width
            )

        # Include dimensional data for visualization
        result_data = {
            'success': True,
            'boxes': optimization_result.get('boxes', []),  # For compatibility
            'ilots': optimization_result.get('ilots', optimization_result.get('boxes', [])),
            'corridors': optimization_result.get('corridors', []),
            'statistics': optimization_result.get('statistics', {}),
            'dimensions': plan_data.get('dimensions', {}),
            'walls': plan_data.get('walls', []),
            'zones': plan_data.get('zones', []),
            'doors': plan_data.get('doors', []),
            'windows': plan_data.get('windows', []),
            'layout_profile': layout_profile,
            'production_mode': PRODUCTION_MODE,
            'optimization_metadata': optimization_result.get('optimization_metadata', {})
        }

        return jsonify(result_data)
        
    except Exception as e:
        print(f"Optimization error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/generate_visual', methods=['POST'])
def generate_visual():
    data = request.json or {}
    output_format = data.get('format', '2d')
    visual_type = data.get('visual_type', 'standard')

    print(f"Generating visual with format: {output_format}, type: {visual_type}")

    try:
        if not data or ('boxes' not in data and 'ilots' not in data):
            return jsonify({'error': 'No optimization data provided for visualization'}), 400

        # Use production-grade renderer if available and requested
        if PRODUCTION_MODE and visual_type == 'interactive':
            try:
                if output_format == 'svg':
                    result = interactive_canvas_renderer.generate_interactive_svg(data)
                    return send_file(result['svg_path'], as_attachment=True)
                elif output_format == 'canvas':
                    html_content = interactive_canvas_renderer.generate_canvas_html(data)
                    return html_content
            except Exception as e:
                print(f"Interactive visual generation error: {e}")
                # Fallback to standard visual generator

        # Use standard visual generator
        visual_path = visual_generator.generate(data, output_format)
        return send_file(visual_path, as_attachment=True)
        
    except Exception as e:
        print(f"Visual generation error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/interactive_visual', methods=['POST'])
def interactive_visual():
    """Generate interactive visual using production-grade renderer"""
    if not PRODUCTION_MODE:
        return jsonify({'error': 'Interactive visuals require production mode'}), 400
    
    try:
        data = request.json or {}
        
        # Generate interactive SVG
        result = interactive_canvas_renderer.generate_interactive_svg(data)
        
        return jsonify({
            'success': True,
            'visual_path': result['svg_path'].replace('static/', '/static/'),
            'interactive': True,
            'svg_string': result.get('svg_string', '')
        })

    except Exception as e:
        print(f"Error in interactive_visual: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/advanced_optimize', methods=['POST'])
def advanced_optimize():
    """Advanced optimization with production-grade algorithms"""
    if not PRODUCTION_MODE:
        return optimize_space()  # Fallback to standard optimization
    
    try:
        data = request.json or {}
        plan_id = data.get('plan_id')
        layout_profile = data.get('layout_profile', '25%')

        box_dimensions = {
            'width': float(data.get('box_width', 3.0)),
            'height': float(data.get('box_height', 4.0))
        }
        corridor_width = float(data.get('corridor_width', 1.2))

        # Get plan data
        plan_data = advanced_cad_processor.get_plan_data(plan_id)
        if not plan_data:
            plan_data = plan_processor.get_plan_data(plan_id)
            
        if not plan_data:
            return jsonify({'error': 'Plan not found'}), 404

        # Use production-grade optimization
        optimization_result = intelligent_placement_engine.optimize_placement(
            plan_data, box_dimensions, corridor_width, layout_profile
        )

        result_data = {
            'success': True,
            'boxes': optimization_result.get('boxes', []),
            'ilots': optimization_result.get('ilots', optimization_result.get('boxes', [])),
            'corridors': optimization_result.get('corridors', []),
            'statistics': optimization_result.get('statistics', {}),
            'dimensions': plan_data.get('dimensions', {}),
            'walls': plan_data.get('walls', []),
            'zones': plan_data.get('zones', []),
            'doors': plan_data.get('doors', []),
            'windows': plan_data.get('windows', []),
            'layout_profile': layout_profile,
            'production_mode': True,
            'optimization_metadata': optimization_result.get('optimization_metadata', {})
        }

        return jsonify(result_data)

    except Exception as e:
        print(f"Advanced optimization error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/export_plan', methods=['POST'])
def export_plan():
    """Export floor plan in multiple formats"""
    if not PRODUCTION_MODE:
        return jsonify({'error': 'Export functionality requires production mode'}), 400
    
    try:
        data = request.json or {}
        export_format = data.get('format', 'svg')  # svg, pdf, png
        plan_data = data.get('plan_data')
        
        if not plan_data:
            return jsonify({'error': 'No plan data provided'}), 400
        
        if export_format == 'svg':
            result = interactive_canvas_renderer.generate_interactive_svg(plan_data)
            return send_file(result['svg_path'], as_attachment=True, as_attachment_filename='floorplan.svg')
        elif export_format == 'canvas':
            html_content = interactive_canvas_renderer.generate_canvas_html(plan_data)
            return html_content, 200, {'Content-Type': 'text/html'}
        else:
            return jsonify({'error': f'Export format {export_format} not supported yet'}), 400
            
    except Exception as e:
        print(f"Export error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/status')
def status():
    """System status endpoint"""
    return jsonify({
        'status': 'running',
        'production_mode': PRODUCTION_MODE,
        'features': {
            'advanced_cad_processing': PRODUCTION_MODE,
            'intelligent_placement': PRODUCTION_MODE,
            'interactive_canvas': PRODUCTION_MODE,
            'modern_ui': PRODUCTION_MODE,
            'basic_functionality': True
        },
        'upload_folder': app.config['UPLOAD_FOLDER'],
        'max_file_size': app.config['MAX_CONTENT_LENGTH']
    })

if __name__ == '__main__':
    print("🏗️  FloorPlanGenie Server Starting...")
    print("📊 Standard Interface: http://0.0.0.0:5000/")
    print("🚀 Professional Interface: http://0.0.0.0:5000/professional")
    
    if PRODUCTION_MODE:
        print("✅ Production-grade features: ENABLED")
        print("   - Advanced CAD Processing")
        print("   - Intelligent Placement Engine")
        print("   - Interactive Canvas Rendering")
        print("   - Modern UI Controller")
    else:
        print("⚠️  Production-grade features: DISABLED (fallback mode)")
        print("   - Using basic implementations")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
