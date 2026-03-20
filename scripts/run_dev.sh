#!/usr/bin/env bash
# ============================================================
# Author:        Jared Garcia
# Date Created:  2026-03-14
# Description:   Local dev runner — sets up the environment and starts the simulator
#
# Merge notes (branch 72-create-the-experiment-object):
#   1. os.add_dll_directory() in core/src/main.py is Windows-only and will
#      crash on Linux/WSL — that line must be removed before merging.
#   2. core/src/main.py hardcodes its own Pulse engine path via sys.path.insert().
#      This script also sets PYTHONPATH for Pulse, so there is overlap.
#      If main.py is updated to rely on PYTHONPATH instead, remove its
#      hardcoded path setup to avoid conflicts.
#   3. ./scripts/run_dev.sh
# ============================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENTRYPOINT="$PROJECT_ROOT/core/src/main.py"

cd "$PROJECT_ROOT"

# figure out where Pulse is installed — check a custom path first, then look in the usual spots
if [ -n "$PULSE_ENGINE_PATH" ]; then
    PULSE_HOME="$PULSE_ENGINE_PATH"
elif [ -d "$PROJECT_ROOT/pulse_engine" ]; then
    PULSE_HOME="$PROJECT_ROOT/pulse_engine"
elif [ -d "$HOME/Pulse/builds/release/install" ]; then
    PULSE_HOME="$HOME/Pulse/builds/release/install"
else
    echo "ERROR: Pulse engine not found."
    echo "  Either place it at: $PROJECT_ROOT/pulse_engine"
    echo "  Or set PULSE_ENGINE_PATH to its location."
    exit 1
fi

PULSE_BIN="$PULSE_HOME/bin"
PULSE_PYTHON="$PULSE_HOME/python"

# make sure the Pulse folders we actually need are in there
if [ ! -d "$PULSE_BIN" ]; then
    echo "ERROR: Pulse bin directory not found at: $PULSE_BIN"
    exit 1
fi

if [ ! -d "$PULSE_PYTHON" ]; then
    echo "ERROR: Pulse python directory not found at: $PULSE_PYTHON"
    exit 1
fi

# make sure main.py is actually there before we try to run it
if [ ! -f "$ENTRYPOINT" ]; then
    echo "ERROR: Entry point not found at: $ENTRYPOINT"
    exit 1
fi

# spin up a virtual environment if we don't already have one
if [ ! -d "$PROJECT_ROOT/.venv" ]; then
    echo "[1/3] Creating virtual environment..."
    python3 -m venv "$PROJECT_ROOT/.venv"
fi

# jump into the virtual environment
echo "[2/4] Activating virtual environment..."
source "$PROJECT_ROOT/.venv/bin/activate"

# install dependencies
echo "[3/4] Installing dependencies..."
pip install -r "$PROJECT_ROOT/requirements.txt"

# tell Python where to find Pulse and our own code
export PYTHONPATH="$PULSE_BIN:$PULSE_PYTHON:$PROJECT_ROOT/core/src:$PYTHONPATH"

echo "[4/4] Starting clinical-batch-trial-simulator..."
echo "  Project root : $PROJECT_ROOT"
echo "  Pulse home   : $PULSE_HOME"
echo "  Entry point  : $ENTRYPOINT"
echo ""

python3 "$ENTRYPOINT" "$@"
