""" 
============================================================
Author:         Zachary Kao
Date Created:   2026-04-15
Description:    Defines the shared runtime and Pulse filepaths used by the
                Clinical Batch Trial Simulator server and other components.
============================================================ 
"""

import sys
import os
from pathlib import Path

def get_base_dir():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


BASE_DIR = get_base_dir()

# -----------------------------
# Data directories (runtime data)
# -----------------------------
APP_DATA_DIR = BASE_DIR / "data"

PATIENTS_DIR = APP_DATA_DIR / "patients"
EXPERIMENT_RESULTS_DIR = APP_DATA_DIR / "experiment_results"
ANALYSIS_RESULTS_DIR = APP_DATA_DIR / "analysis_results"

# -----------------------------
# External engine (pulse_engine)
# -----------------------------
PULSE_HOME = BASE_DIR / "pulse_engine"
PULSE_BIN = PULSE_HOME / "bin"
PULSE_PYTHON = PULSE_HOME / "python"


def init_runtime_dirs():
    for d in [
        PATIENTS_DIR,
        EXPERIMENT_RESULTS_DIR,
        ANALYSIS_RESULTS_DIR,
    ]:
        d.mkdir(parents=True, exist_ok=True)


def init_native_paths():
    pulse_python_str = str(PULSE_PYTHON)
    if pulse_python_str not in sys.path:
        sys.path.insert(0, pulse_python_str)
    if sys.platform == "win32":
        os.add_dll_directory(str(PULSE_BIN))