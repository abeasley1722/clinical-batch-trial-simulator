# ============================================================
# Author:        Jared Garcia
# Date Created:  2026-03-14
# Description:   Local dev runner — sets up the environment and starts the simulator
#
# Merge notes (branch 72-create-the-experiment-object):
#   2. core/src/main.py hardcodes its own Pulse engine path via sys.path.insert().
#      This script also sets PYTHONPATH for Pulse, so there is overlap.
#      If main.py is updated to rely on PYTHONPATH instead, remove its
#      hardcoded path setup to avoid conflicts.
#   3. Run this script from PowerShell: .\scripts\run_dev.ps1
# ============================================================

$ErrorActionPreference = "Stop"

$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$PROJECT_ROOT = Split-Path -Parent $SCRIPT_DIR
$ENTRYPOINT = Join-Path $PROJECT_ROOT "core\src\run.py"
$env:PULSE_ENGINE_PATH="C:\Users\badas\Pulse\builds\debug\install"
Set-Location $PROJECT_ROOT

# figure out where Pulse is installed — check a custom path first, then look in the usual spots
if ($env:PULSE_ENGINE_PATH) {
    $PULSE_HOME = $env:PULSE_ENGINE_PATH
} elseif (Test-Path (Join-Path $PROJECT_ROOT "\pulse_engine")) {
    $PULSE_HOME = Join-Path $PROJECT_ROOT "\pulse_engine"
} elseif (Test-Path (Join-Path $PROJECT_ROOT "core\src\pulse_engine")) {
    $PULSE_HOME = Join-Path $PROJECT_ROOT "core\src\pulse_engine"
} elseif (Test-Path "$env:USERPROFILE\Pulse\builds\release\install") {
    $PULSE_HOME = "$env:USERPROFILE\Pulse\builds\release\install"
} else {
    Write-Host "ERROR: Pulse engine not found."
    Write-Host "  Either place it at: $PROJECT_ROOT\core\src\pulse_engine"
    Write-Host "  Or set PULSE_ENGINE_PATH to its location."
    exit 1
}

$PULSE_BIN = Join-Path $PULSE_HOME "bin"
$PULSE_PYTHON = Join-Path $PULSE_HOME "python"

# make sure the Pulse folders we actually need are in there
if (-not (Test-Path $PULSE_BIN)) {
    Write-Host "ERROR: Pulse bin directory not found at: $PULSE_BIN"
    exit 1
}

if (-not (Test-Path $PULSE_PYTHON)) {
    Write-Host "ERROR: Pulse python directory not found at: $PULSE_PYTHON"
    exit 1
}

# make sure main.py is actually there before we try to run it
if (-not (Test-Path $ENTRYPOINT)) {
    Write-Host "ERROR: Entry point not found at: $ENTRYPOINT"
    exit 1
}

# spin up a virtual environment if we don't already have one
if (-not (Test-Path (Join-Path $PROJECT_ROOT ".venv"))) {
    Write-Host "[1/4] Creating virtual environment..."
    python -m venv "$PROJECT_ROOT\.venv"
}

# jump into the virtual environment
Write-Host "[2/4] Activating virtual environment..."
& "$PROJECT_ROOT\.venv\Scripts\Activate.ps1"

# install dependencies
Write-Host "[3/4] Installing dependencies..."
pip install -r "$PROJECT_ROOT\requirements.txt"

# tell Python where to find Pulse and our own code
$env:PYTHONPATH = "$PULSE_BIN;$PULSE_PYTHON;$PROJECT_ROOT\core\src;$env:PYTHONPATH"

Write-Host "[4/4] Starting clinical-batch-trial-simulator..."
Write-Host "  Project root : $PROJECT_ROOT"
Write-Host "  Pulse home   : $PULSE_HOME"
Write-Host "  Entry point  : $ENTRYPOINT"
Write-Host ""

python $ENTRYPOINT $args