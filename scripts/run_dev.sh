#!/usr/bin/env bash
set -e

# ============================================================
# Local dev runner (WSL compatible)
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENTRYPOINT="$PROJECT_ROOT/core/src/run.py"
INIT_DB="$PROJECT_ROOT/core/src/init_db.py"

# ✅ Set Pulse path (WSL format)
export PULSE_ENGINE_PATH="/mnt/c/Users/badas/Pulse/builds/debug/install"

cd "$PROJECT_ROOT"

# ------------------------------------------------------------
# Locate Pulse
# ------------------------------------------------------------
if [ -n "$PULSE_ENGINE_PATH" ]; then
    PULSE_HOME="$PULSE_ENGINE_PATH"
elif [ -d "$PROJECT_ROOT/pulse_engine" ]; then
    PULSE_HOME="$PROJECT_ROOT/pulse_engine"
elif [ -d "$HOME/Pulse/builds/release/install" ]; then
    PULSE_HOME="$HOME/Pulse/builds/release/install"
else
    echo "ERROR: Pulse engine not found."
    exit 1
fi

PULSE_BIN="$PULSE_HOME/bin"
PULSE_PYTHON="$PULSE_HOME/python"

# ------------------------------------------------------------
# Validate Pulse install
# ------------------------------------------------------------
if [ ! -d "$PULSE_BIN" ]; then
    echo "ERROR: Pulse bin directory not found at: $PULSE_BIN"
    exit 1
fi

if [ ! -d "$PULSE_PYTHON" ]; then
    echo "ERROR: Pulse python directory not found at: $PULSE_PYTHON"
    exit 1
fi

# ------------------------------------------------------------
# Validate entrypoint
# ------------------------------------------------------------
if [ ! -f "$ENTRYPOINT" ]; then
    echo "ERROR: Entry point not found at: $ENTRYPOINT"
    exit 1
fi

# ------------------------------------------------------------
# Virtual environment
# ------------------------------------------------------------
if [ ! -d "$PROJECT_ROOT/.venv" ]; then
    echo "[1/5] Creating virtual environment..."
    python3 -m venv "$PROJECT_ROOT/.venv"
fi

echo "[2/5] Activating virtual environment..."
source "$PROJECT_ROOT/.venv/bin/activate"

echo "[3/5] Installing dependencies..."
pip install -r "$PROJECT_ROOT/requirements.txt"

# ------------------------------------------------------------
# Python path setup
# ------------------------------------------------------------
export PYTHONPATH="$PULSE_BIN:$PULSE_PYTHON:$PROJECT_ROOT/core/src:$PYTHONPATH"

# ------------------------------------------------------------
# INIT DATABASE (🔥 THIS IS THE FIX)----------------------------------------------
echo "[4/5] Initializing database..."

if [ ! -f "$INIT_DB" ]; then
    echo "ERROR: init_db.py not found at $INIT_DB"
    exit 1
fi

python3 "$INIT_DB"

# ------------------------------------------------------------
# Run app
# ------------------------------------------------------------
echo "[5/5] Starting clinical-batch-trial-simulator..."
echo "  Project root : $PROJECT_ROOT"
echo "  Pulse home   : $PULSE_HOME"
echo "  Entry point  : $ENTRYPOINT"
echo ""

python3 "$ENTRYPOINT" "$@"