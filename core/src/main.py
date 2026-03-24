# ============================================================
# Author:        Zachary Kao
# Date Created:  2026-03-12
# Description:   Starts the Pulse Simulation API server
# ============================================================ 

from dataclasses import asdict
import os
import argparse
from pathlib import Path
from api.routes import app, socketio


# Use absolute paths so they work even after os.chdir()
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(SCRIPT_DIR, 'uploads')
RESULTS_FOLDER = os.path.join(SCRIPT_DIR, 'results')
Path(UPLOAD_FOLDER).mkdir(exist_ok=True)
Path(RESULTS_FOLDER).mkdir(exist_ok=True)

if __name__ == '__main__':
    from multiprocessing import freeze_support
    freeze_support()
    
    parser = argparse.ArgumentParser(description='Pulse Simulation Server')
    parser.add_argument('--port', type=int, default=8080, help='Port to run on (default: 8080)')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to (default: 0.0.0.0)')
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print("  PULSE SIMULATION SERVER v6")
    print("="*60)
    print(f"  API running at http://{args.host}:{args.port}")
    print("="*60 + "\n")

    socketio.run(app, host=args.host, port=args.port,  debug=False, allow_unsafe_werkzeug=True)
