
from flask import Flask, render_template, request, jsonify, send_file
import json
import os
from werkzeug.utils import secure_filename
from plan_processor import PlanProcessor
from space_optimizer import SpaceOptimizer
from visual_generator import VisualGenerator

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

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
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Process the plan
        try:
            plan_data = plan_processor.process_plan(filepath)
            return jsonify({
                'success': True,
                'plan_id': plan_data['id'],
                'dimensions': plan_data['dimensions'],
                'walls': plan_data['walls'],
                'zones': plan_data['zones']
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

@app.route('/optimize', methods=['POST'])
def optimize_space():
    data = request.json
    plan_id = data.get('plan_id')
    box_dimensions = data.get('box_dimensions', {'width': 3.0, 'height': 4.0})  # Default room size
    corridor_width = data.get('corridor_width', 1.2)  # Default 1.2m corridors
    
    try:
        # Get plan data
        plan_data = plan_processor.get_plan_data(plan_id)
        
        # Optimize space placement
        optimization_result = space_optimizer.optimize_placement(
            plan_data, box_dimensions, corridor_width
        )
        
        return jsonify({
            'success': True,
            'boxes': optimization_result['boxes'],
            'corridors': optimization_result['corridors'],
            'statistics': optimization_result['statistics']
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/generate_visual', methods=['POST'])
def generate_visual():
    data = request.json
    output_format = data.get('format', '2d')  # 2d, 3d, pdf
    
    try:
        visual_path = visual_generator.generate(data, output_format)
        return send_file(visual_path, as_attachment=True)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
