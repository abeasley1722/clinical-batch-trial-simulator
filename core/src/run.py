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
from core.src.init_db import init_db

if __name__ == '__main__':
    init_db()
    init_runtime_dirs()
    app = create_app()

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

    socketio.run(app, host=args.host, port=args.port, debug=False, allow_unsafe_werkzeug=True)
