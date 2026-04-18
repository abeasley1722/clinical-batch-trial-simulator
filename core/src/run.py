""" 
============================================================
Author:         Zachary Kao
Date Created:   2026-04-15
Description:    Main entrypoint for the Clinical Batch Trial Simulator server. 
                Initializes the Flask app and SocketIO, and starts the server.
============================================================ 
"""

import core.src.bootstrap

import argparse
import os
import sys

from core.src import create_app, socketio
from core.src.runtime_paths import PULSE_HOME, init_native_paths, init_runtime_dirs

init_runtime_dirs()
app = create_app()

if __name__ == '__main__':
    from multiprocessing import freeze_support
    freeze_support()
    
    parser = argparse.ArgumentParser(description='Clinical Batch Trial Simulator Server')
    parser.add_argument('--port', type=int, default=8080, help='Port to run on (default: 8080)')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to (default: 0.0.0.0)')
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print("  CLINICAL BATCH TRIAL SIMULATOR SERVER")
    print("="*60)
    print(f"  API running at http://{args.host}:{args.port}")
    print(f"  WebSocket enabled for live data streaming")
    print(f"  Pulse Home: {PULSE_HOME}")
    print(f"  CPUs: {os.cpu_count()}")
    print("="*60)
    print("  Connect with Clinical Batch Trial Simulator Client")
    print("="*60 + "\n")

    #TODO: remove this test code
    from datetime import datetime
    from core.src.experiment_executor import run_batch_thread
    import uuid
    print("Running test of batch simulation")
    #batch id should be in the form of timestamp_uuid for uniqueness and traceability
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    id = str(uuid.uuid4())[:8]
    batch_id = f"{timestamp}_{id}"
    run_batch_thread(batch_id, {
        'name': 'Test Batch',
        'patient_count' : 8,
        'demographics': [
        {'name': 'soldier', 'percent': 50},
        {'name': 'adult', 'percent': 50}
        ],
        'target_metrics': {
            'hr_bpm': {
                'target_value': 75,
                'tolerance': 5,
                'matching_function' :  'log(x)'
            },
            'spo2_pct': {
                'target_value': 98,
                'tolerance': 2,
                'matching_function' : ''
            },
            'etco2_mmhg': {
                'target_value': 40,
                'tolerance': 5,
                'matching_function' : ''
            },
            'rr_patient': {
                'target_value': 16,
                'tolerance': 3,
                'matching_function' : ''
            }
        },
        'duration_s': 300,
        'sample_rate_hz': 50,
        'start_intubated': False,
        'vent_settings': {},
        'events': [],
        'workers': 4,
        'replicates': 1
    })

    socketio.run(app, host=args.host, port=args.port, debug=False)
