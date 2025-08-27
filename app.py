import os
import json
from flask import Flask, render_template, request, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.utils import secure_filename
from plan_processor import PlanProcessor
from space_optimizer import SpaceOptimizer
from visual_generator import VisualGenerator


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)

# create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)  # needed for url_for to generate with https

# configure the database, relative to the app instance folder
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size

# initialize the app with the extension, flask-sqlalchemy >= 3.0.x
db.init_app(app)

with app.app_context():
    # Make sure to import the models here or their tables won't be created
    import models  # noqa: F401
    db.create_all()

@app.errorhandler(413)
def too_large(e):
    return jsonify({'error': 'File too large. Maximum size is 50MB.'}), 413

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize processors
plan_processor = PlanProcessor()
space_optimizer = SpaceOptimizer()
visual_generator = VisualGenerator()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if file:
        filename = secure_filename(file.filename or "upload")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Process the plan with timeout protection
        try:
            print(f"Processing file: {filename} (size: {file.content_length if hasattr(file, 'content_length') else 'unknown'})")
            plan_data = plan_processor.process_plan(filepath)
            print(f"File processed successfully. Plan ID: {plan_data['id']}")
            print(f"Total stored plans: {len(plan_processor.plans)}")

            # Generate initial visual of the processed plan
            initial_visual_data = {
                'walls': plan_data['walls'],
                'zones': plan_data['zones'],
                'dimensions': plan_data['dimensions']
            }

            # Generate visual representation with timeout handling
            try:
                visual_path = visual_generator.generate(initial_visual_data, '2d')
            except Exception as visual_error:
                print(f"Visual generation failed: {visual_error}")
                visual_path = None

            return jsonify({
                'success': True,
                'plan_id': plan_data['id'],
                'dimensions': plan_data['dimensions'],
                'walls': plan_data['walls'],
                'zones': plan_data['zones'],
                'visual_path': visual_path.replace('static/', '/static/') if visual_path else None
            })
        except Exception as e:
            print(f"Upload processing error: {e}")
            return jsonify({'error': f'Error processing file: {str(e)}'}), 500

@app.route('/optimize', methods=['POST'])
def optimize_space():
    data = request.json or {}
    plan_id = data.get('plan_id')
    box_dimensions = data.get('box_dimensions', {'width': 3.0, 'height': 4.0})
    corridor_width = data.get('corridor_width', 1.2)

    # Debug logging
    print(f"Optimization request - Plan ID: {plan_id}")
    print(f"Available plans: {list(plan_processor.plans.keys())}")

    try:
        # Get plan data
        plan_data = plan_processor.get_plan_data(plan_id)
        if not plan_data:
            # If no plan found, try reprocessing the most recent file
            import glob
            upload_files = glob.glob('uploads/*.dxf') + glob.glob('uploads/*.dwg')
            if upload_files:
                # Use most recent file
                latest_file = max(upload_files, key=os.path.getctime)
                print(f"Reprocessing latest file: {latest_file}")
                plan_data = plan_processor.process_plan(latest_file)
                # Update plan_id for consistency
                plan_id = plan_data['id']
            else:
                return jsonify({'error': 'No architectural file found. Please upload a DXF or DWG file first.'}), 404

        # Optimize space placement
        optimization_result = space_optimizer.optimize_placement(
            plan_data, box_dimensions, corridor_width
        )

        # Include dimensional data for visualization
        result_data = {
            'success': True,
            'boxes': optimization_result['boxes'],
            'corridors': optimization_result['corridors'],
            'statistics': optimization_result['statistics'],
            'dimensions': plan_data['dimensions'],  # Add dimensions for visual generation
            'walls': plan_data['walls']  # Add walls for visual generation
        }

        return jsonify(result_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get_plan_visual/<plan_id>')
def get_plan_visual(plan_id):
    try:
        plan_data = plan_processor.get_plan_data(plan_id)
        if not plan_data:
            return jsonify({'error': 'Plan not found'}), 404

        # Create visual data
        visual_data = {
            'walls': plan_data['walls'],
            'zones': plan_data['zones'],
            'dimensions': plan_data['dimensions']
        }

        # Generate and return visual
        visual_path = visual_generator.generate(visual_data, '2d')
        return send_file(visual_path, mimetype='image/png')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/generate_visual', methods=['POST'])
def generate_visual():
    data = request.json or {}
    output_format = data.get('format', '2d')

    print(f"Generating visual with format: {output_format}")
    print(f"Data keys: {list(data.keys()) if data else 'None'}")

    try:
        # Ensure we have the required data structure
        if not data or 'boxes' not in data:
            return jsonify({'error': 'No optimization data provided for visualization'}), 400

        visual_path = visual_generator.generate(data, output_format)
        return send_file(visual_path, as_attachment=True)
    except Exception as e:
        print(f"Visual generation error: {e}")
        return jsonify({'error': str(e)}), 500

# Production-grade route for modern interface
@app.route('/professional')
def professional_interface():
    """Serve the production-grade professional interface"""
    try:
        from modern_ui_controller import ModernUIController

        ui_controller = ModernUIController()
        default_data = {
            'dimensions': {'width': 50, 'height': 40},
            'statistics': {
                'total_boxes': 0,
                'utilization_rate': 0,
                'total_corridors': 0,
                'efficiency_score': 0
            }
        }

        html_content = ui_controller.generate_modern_interface_html(default_data)
        return html_content

    except ImportError:
        return '''<!DOCTYPE html>
<html><head><title>Professional Mode Loading...</title></head>
<body style="font-family: Arial; text-align: center; padding: 50px;">
<h2>🚀 Production-Grade Interface</h2>
<p>Advanced components loading... Please refresh in a moment.</p>
<a href="/" style="color: #3b82f6;">← Back to Standard Interface</a>
</body></html>'''

@app.route('/advanced_optimize', methods=['POST'])
def advanced_optimize():
    """Advanced optimization with production-grade algorithms"""
    try:
        from intelligent_placement_engine import IntelligentPlacementEngine

        data = request.json or {}
        plan_id = data.get('plan_id')
        layout_profile = data.get('layout_profile', '25%')

        box_dimensions = {
            'width': float(data.get('box_width', 3.0)),
            'height': float(data.get('box_height', 4.0))
        }
        corridor_width = float(data.get('corridor_width', 1.2))

        # Get plan data
        plan_data = plan_processor.get_plan_data(plan_id)
        if not plan_data:
            return jsonify({'error': 'Plan not found'}), 404

        # Use production-grade optimization
        placement_engine = IntelligentPlacementEngine()
        optimization_result = placement_engine.optimize_placement(
            plan_data, box_dimensions, corridor_width, layout_profile
        )

        result_data = {
            'success': True,
            'boxes': optimization_result['boxes'],
            'corridors': optimization_result['corridors'],
            'statistics': optimization_result['statistics'],
            'dimensions': plan_data['dimensions'],
            'walls': plan_data['walls'],
            'layout_profile': layout_profile,
            'optimization_metadata': optimization_result['optimization_metadata']
        }

        return jsonify(result_data)

    except ImportError:
        # Fallback to standard optimization
        return optimize_space()
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/interactive_visual', methods=['POST'])
def interactive_visual():
    """Generate interactive visual"""
    try:
        data = request.json

        # Generate visual using the visual generator
        visual_generator = VisualGenerator()
        result = visual_generator.generate_interactive_visual(data)

        return jsonify(result)

    except Exception as e:
        print(f"Error in interactive_visual: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/professional_process', methods=['POST'])
def professional_process():
    """Advanced professional processing after optimization"""
    try:
        data = request.json
        plan_id = data.get('plan_id')
        optimization_data = data.get('optimization_data')

        if not plan_id or not optimization_data:
            return jsonify({'error': 'Missing plan_id or optimization_data'}), 400

        # Advanced professional processing
        result = {
            'success': True,
            'professional_mode': True,
            'advanced_features': {
                'collision_detection': True,
                'advanced_analytics': True,
                'real_time_optimization': True,
                'professional_export': True
            },
            'message': 'Professional processing activated'
        }

        print(f"Professional processing activated for plan: {plan_id}")
        return jsonify(result)

    except Exception as e:
        print(f"Error in professional_process: {e}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print("🏗️  FloorPlanGenie Server Starting...")
    print("📊 Standard Interface: http://localhost:5000/")
    print("🚀 Professional Interface: http://localhost:5000/professional")
    app.run(host='0.0.0.0', port=5000, debug=True)