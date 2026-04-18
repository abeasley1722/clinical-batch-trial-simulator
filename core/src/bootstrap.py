""" 
============================================================
Author:         Zachary Kao
Date Created:   2026-04-18
Description:    Bootstrap to initialize Pulse paths
============================================================ 
"""

import sys
import os
from pathlib import Path

def _bootstrap():
    if getattr(sys, "frozen", False):
        base = Path(sys.executable).resolve().parent
    else:
        # bootstrap.py is at core/src/bootstrap.py → parents[2] = project root
        base = Path(__file__).resolve().parents[2]

    pulse_python = base / "pulse_engine" / "python"
    pulse_bin    = base / "pulse_engine" / "bin"

    # Add both to sys.path — pulse_bin contains PyPulse.pyd/.so compiled extension
    sys.path.insert(0, str(pulse_bin))
    sys.path.insert(0, str(pulse_python))

    if sys.platform == "win32":
        if pulse_bin.exists():
            os.add_dll_directory(str(pulse_bin))
        else:
            print(f"[bootstrap] WARNING: pulse_bin not found at {pulse_bin}", file=sys.stderr)

_bootstrap()