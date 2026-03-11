# clinical-batch-trial-simulator

Requirements:
- VS_Code
- git
- WSL Ubuntu

-----------------------------------------------------------
Pulse Implementation
-----------------------------------------------------------

- Open VS Code
- Move to the folder you would like to keep Pulse in
- Open the terminal and clone the repo: git clone https://gitlab.kitware.com/physiology/engine.git

Set up virtual enviornment
- Move to the engine folder
- sudo apt update
- sudo apt install -y build-essential cmake git python3 python3-venv python3-pip
- python3 -m venv .venv
- source .venv/bin/activate
- pip install -U pip
- pip install -r requirements.txt

PulseC++ engine compiled
- Create a new folder for the pulse build
- Enter it
- cmake -DCMAKE_BUILD_TYPE=Release ../engine
- make -j4
- After it finishes you should have: ~/Pulse/builds/release/install/bin
- Test it:
  - cd ~/Pulse/builds/release/install/bin
   - ./PulseScenarioDriver VitalsMonitor.json

 Enable the python API
- Look for the python module: cd ~/Pulse/builds/release/install/bin
ls | grep -i pypulse
- source ~/Pulse/engine/.venv/bin/activate
- export PYTHONPATH=~/Pulse/builds/release/install/bin:$PYTHONPATH
- python -c "import PyPulse; print('PyPulse import OK')"
  
