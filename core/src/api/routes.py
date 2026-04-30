""" 
============================================================
Author:        Zachary Kao
Date Created:  2026-03-14
Description:   API endpoints for the Pulse server
============================================================ 
"""

import glob
import os
import sys
import threading
import uuid
import zipfile
import requests as http_requests
from datetime import datetime
from pathlib import Path
import numpy as np
from flask import Flask, request, jsonify, send_file, Blueprint
from flask_cors import CORS
from flask_socketio import SocketIO, emit

from core.src.experiment_executor import AVAILABLE_VARIABLES, run_batch_thread, set_batch_cancel_flag
from core.src.controllers import UNIT_MAP, DATA_REQUEST_FACTORIES

# === DATABASE ROUTES ===
from core.src.database.batch import get_batch, get_batches_by_experiment, get_batches_by_patient
from core.src.database.experiment import get_experiment, get_all_experiments
from core.src.database.metric import get_metrics_by_experiment
from core.src.database.patient import get_patient, get_patients_by_cohort, get_all_patients
from core.src.database.retrieval import get_metrics_dataframe, get_raw_csv_paths, get_raw_csv_dataframe

from core.src import socketio

api_bp = Blueprint('api', __name__)

@api_bp.after_request
def add_no_cache_headers(response):
    """Prevent browser caching during development."""
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    return response

@api_bp.route('/api/available_variables')
def api_available_variables():
    """Return the list of available CSV output variables for the GUI."""
    return jsonify(AVAILABLE_VARIABLES)

@api_bp.route('/api/test_http_controller', methods=['POST'])
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

@api_bp.route('/api/submit_batch', methods=['POST'])
def submit_batch():
    batch = request.json
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    id = str(uuid.uuid4())[:8]
    batch_id = f"{timestamp}_{id}"
    
    print(f"[BATCH] Received batch submission: {batch_id}")
    
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


@api_bp.route('/api/batch_status/<batch_id>')
def batch_status(batch_id):
    with batch_lock:
        if batch_id not in batches:
            return jsonify({'status': 'not_found'}), 404
        return jsonify(batches[batch_id])


@api_bp.route('/api/cancel_batch/<batch_id>', methods=['POST'])
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


@api_bp.route('/api/download_batch/<experiment_id>')
def download_batch(experiment_id):
    experiment = get_experiment(experiment_id)
    if not experiment:
        return "Experiment not found", 404

    if experiment.get('status') not in ('complete', 'cancelled'):
        return "Experiment not complete", 400

    output_dir = experiment.get('output_dir')
    if not output_dir or not os.path.exists(output_dir):
        return "Output directory not found", 404

    # Use cached zip if already created
    zip_path = os.path.join(output_dir, f"experiment_{experiment_id}.zip")
    if not os.path.exists(zip_path):
        try:
            import zipfile
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                for csv_file in glob.glob(os.path.join(output_dir, '*.csv')):
                    zf.write(csv_file, os.path.basename(csv_file))
        except Exception as e:
            return f"Failed to create zip: {e}", 500

    return send_file(zip_path, as_attachment=True, download_name=f"experiment_{experiment_id}.zip")

@api_bp.route('/api/shutdown', methods=['POST'])
def shutdown():
    os._exit(0)

@socketio.on('connect')
def handle_connect():
    print(f"[WebSocket] Client connected")


@socketio.on('disconnect')
def handle_disconnect():
    print(f"[WebSocket] Client disconnected")

# === DATABASE ROUTES ===

# --- Batch ---

@api_bp.route('/api/batches/<batch_id>')
def api_get_batch(batch_id):
    result = get_batch(batch_id)
    if result is None:
        return jsonify({'error': 'Batch not found'}), 404
    return jsonify(result)

@api_bp.route('/api/batches/by_experiment/<experiment_id>')
def api_get_batches_by_experiment(experiment_id):
    return jsonify(get_batches_by_experiment(experiment_id))

@api_bp.route('/api/batches/by_patient/<patient_id>')
def api_get_batches_by_patient(patient_id):
    return jsonify(get_batches_by_patient(patient_id))

# --- Experiment ---

@api_bp.route('/api/experiments')
def api_get_all_experiments():
    return jsonify(get_all_experiments())

@api_bp.route('/api/experiments/<experiment_id>')
def api_get_experiment(experiment_id):
    result = get_experiment(experiment_id)
    if result is None:
        return jsonify({'error': 'Experiment not found'}), 404
    return jsonify(result)

# --- Metrics ---

@api_bp.route('/api/metrics/by_experiment/<experiment_id>')
def api_get_metrics_by_experiment(experiment_id):
    return jsonify(get_metrics_by_experiment(experiment_id))

# --- Patient ---

@api_bp.route('/api/patients')
def api_get_all_patients():
    return jsonify(get_all_patients())

@api_bp.route('/api/patients/<patient_id>')
def api_get_patient(patient_id):
    result = get_patient(patient_id)
    if result is None:
        return jsonify({'error': 'Patient not found'}), 404
    return jsonify(result)

@api_bp.route('/api/patients/by_cohort/<cohort_id>')
def api_get_patients_by_cohort(cohort_id):
    return jsonify(get_patients_by_cohort(cohort_id))

# --- Retrieval ---

@api_bp.route('/api/retrieval/metrics/<experiment_id>')
def api_get_metrics_dataframe(experiment_id):
    df = get_metrics_dataframe(experiment_id)
    return jsonify(df.to_dict(orient='records'))

@api_bp.route('/api/retrieval/raw_csv_paths/<experiment_id>')
def api_get_raw_csv_paths(experiment_id):
    return jsonify(get_raw_csv_paths(experiment_id))

@api_bp.route('/api/retrieval/raw_csv/<experiment_id>')
def api_get_raw_csv_dataframe(experiment_id):
    """
    Query params:
        ?selection=gases,ventilator
        ?selection=all
        ?selection=hr_bpm,spo2_pct
    """
    print(f"Received request for raw CSV data of experiment {experiment_id} with query params: {request.args}")   
    # 🔥 Get selection from query params
    selection_param = request.args.get("selection")
    print(f"Parsed selection param: {selection_param}")
    if selection_param:
        selection = selection_param.split(",")
    else:
        selection = None  # default → core vitals

    # 🔥 Fetch filtered dataframe
    df = get_raw_csv_dataframe(experiment_id, selection)

    # 🔥 Convert NaN → None (JSON safe)
    df = df.replace({np.nan: None})

    # 🔥 Debug (corrected)
    print("Columns returned:", df.columns.tolist())
    print(df.head())

    return jsonify(df.to_dict(orient='records'))
