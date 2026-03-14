import os
import sys
import threading
import uuid
import zipfile
import requests as http_requests
from datetime import datetime
from pathlib import Path

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flask_socketio import SocketIO, emit

#TODO: change if single patient functions are removed
from ..main import AVAILABLE_VARIABLES, run_batch_thread, set_batch_cancel_flag
from ..controllers import UNIT_MAP, DATA_REQUEST_FACTORIES

# === PATH SETUP ===
PULSE_HOME = os.path.join(os.path.dirname(os.path.abspath(__file__)),"pulse_engine")
PULSE_BIN = os.path.join(PULSE_HOME, "bin")
PULSE_PYTHON = os.path.join(PULSE_HOME, "python")

sys.path.insert(0, PULSE_PYTHON)
sys.path.insert(0, PULSE_BIN)
os.add_dll_directory(PULSE_BIN)

#TODO: refactor using FastAPI instead of Flask
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

jobs = {}
job_lock = threading.Lock()
cancel_flags = {}  # job_id -> True if should cancel
pulse_config_lock = threading.Lock()

# Use absolute paths so they work even after os.chdir()
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(SCRIPT_DIR, 'uploads')
RESULTS_FOLDER = os.path.join(SCRIPT_DIR, 'results')
Path(UPLOAD_FOLDER).mkdir(exist_ok=True)
Path(RESULTS_FOLDER).mkdir(exist_ok=True)

#TODO: refactor using FastAPI instead of Flask
#TODO: figure out which functions can be removed if single patient functionality is removed

@app.after_request
def add_no_cache_headers(response):
    """Prevent browser caching during development."""
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    return response

@app.after_request
def add_no_cache_headers(response):
    """Prevent browser caching during development."""
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    return response

@app.route('/')
def serve_gui():
    """Serve the GUI HTML file."""
    gui_path = os.path.join(SCRIPT_DIR, 'pulse_gui.html')
    
    if not os.path.exists(gui_path):
        return """
        <html><body style="font-family: sans-serif; padding: 40px;">
        <h1>Pulse Server Running</h1>
        <p>API is available at <code>/api/</code></p>
        <p>To use the GUI, place <code>pulse_gui.html</code> in the same directory as <code>pulse_server.py</code></p>
        <p>Or open <code>pulse_gui.html</code> directly in a browser and connect to this server.</p>
        </body></html>
        """, 200
    
    # Read the GUI HTML
    with open(gui_path, 'r', encoding='utf-8') as f:
        html = f.read()
    
    # Auto-set the server URL to this server's address
    # Replace the default localhost:8080 with empty string so it uses relative URLs
    html = html.replace('value="http://localhost:8080"', 'value=""')
    
    return html


@app.route('/api/available_variables')
def api_available_variables():
    """Return the list of available CSV output variables for the GUI."""
    return jsonify(AVAILABLE_VARIABLES)

@app.route('/api/test_http_controller', methods=['POST'])
def test_http_controller():
    """Test connection to an HTTP controller."""
    data = request.json
    url = data.get('url', '').strip()
    
    if not url:
        return jsonify({'success': False, 'error': 'No URL provided'})
    
    try:
        payload = {
            "patient": "TestPatient",
            "vent_settings": {"mode": "VC-AC", "fio2": 0.4, "peep_cmh2o": 5, "vt_ml": 420, "rr": 14},
            "config": {}
        }
        
        resp = http_requests.post(
            f"{url.rstrip('/')}/init",
            json=payload,
            timeout=5.0
        )
        resp.raise_for_status()
        result = resp.json()
        
        if result.get("status") != "ok":
            return jsonify({'success': False, 'error': f"Controller returned: {result.get('error', 'unknown error')}"})
        
        data_requests = result.get("data_requests", [])
        
        for req in data_requests:
            category = req.get("category")
            name = req.get("name")
            unit_str = req.get("unit")
            
            if category not in DATA_REQUEST_FACTORIES:
                return jsonify({
                    'success': False, 
                    'error': f"Invalid category '{category}' for {name}"
                })
            
            if unit_str and unit_str not in UNIT_MAP:
                return jsonify({
                    'success': False,
                    'error': f"Invalid unit '{unit_str}' for {category}:{name}"
                })
        
        return jsonify({
            'success': True,
            'data_requests': len(data_requests),
            'next_update_s': result.get("next_update_s", 1.0)
        })
        
    except http_requests.exceptions.Timeout:
        return jsonify({'success': False, 'error': f'Connection timed out after 5s'})
    except http_requests.exceptions.ConnectionError as e:
        return jsonify({'success': False, 'error': f'Cannot connect to {url}'})
    except http_requests.exceptions.RequestException as e:
        return jsonify({'success': False, 'error': f'HTTP error: {e}'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
    
# === BATCH MODE SUPPORT ===
batches = {}
batch_lock = threading.Lock()
batch_cancel_flags = {}  # batch_id -> True if should cancel (for thread-level check)

@app.route('/api/submit_batch', methods=['POST'])
def submit_batch():
    batch = request.json
    batch_id = str(uuid.uuid4())[:8]
    
    print(f"[BATCH] Received batch submission: {batch_id}")
    print(f"[BATCH] Patients: {batch.get('patients', [])}")
    print(f"[BATCH] Custom patients: {len(batch.get('custom_patients', []))}")
    
    with batch_lock:
        batches[batch_id] = {
            'status': 'running',
            'batch': batch,
            'patients': {},
            'started': datetime.now().isoformat()
        }
    
    thread = threading.Thread(target=run_batch_thread, args=(batch_id, batch), daemon=True)
    thread.start()
    
    print(f"[BATCH] Thread started for {batch_id}")
    return jsonify({'batch_id': batch_id})


@app.route('/api/batch_status/<batch_id>')
def batch_status(batch_id):
    with batch_lock:
        if batch_id not in batches:
            return jsonify({'status': 'not_found'}), 404
        return jsonify(batches[batch_id])


@app.route('/api/cancel_batch/<batch_id>', methods=['POST'])
def cancel_batch(batch_id):
    """Cancel a running batch."""
    with batch_lock:
        if batch_id not in batches:
            return jsonify({'success': False, 'error': 'Batch not found'}), 404

        status = batches[batch_id].get('status')
        if status != 'running':
            return jsonify({'success': False, 'error': f'Batch is {status}, cannot cancel'})

        # Set both the thread-level flag and the file-based cross-process flag
        batch_cancel_flags[batch_id] = True
        set_batch_cancel_flag(batch_id)  # File-based for worker processes

        batches[batch_id]['status'] = 'cancelling'
        return jsonify({'success': True, 'message': 'Cancellation requested'})


@app.route('/api/download_batch/<batch_id>')
def download_batch(batch_id):
    with batch_lock:
        if batch_id not in batches:
            return "Not found", 404
        batch_info = batches[batch_id]

    if 'zip_path' not in batch_info:
        return "Not ready", 400

    return send_file(batch_info['zip_path'], as_attachment=True)

@app.route('/api/shutdown', methods=['POST'])
def shutdown():
    os._exit(0)

@socketio.on('connect')
def handle_connect():
    print(f"[WebSocket] Client connected")


@socketio.on('disconnect')
def handle_disconnect():
    print(f"[WebSocket] Client disconnected")