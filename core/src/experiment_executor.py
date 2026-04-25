""" 
============================================================
Author:        Zachary Kao
Date Created:  2026-03-12
Description:   Business logic for the core simulation server.
============================================================ 
"""

from dataclasses import asdict
import os
import sys
import json
import threading
import random
import queue
import uuid
import time
import io
import csv
import tempfile
import argparse
import uuid
import requests as http_requests
import pandas as pd
import numpy as np
import math
from datetime import datetime
from pathlib import Path

import sympy as sp
import numpy as np
from sympy.utilities.lambdify import lambdify
ALLOWED_SYMPY_MODULES = ["numpy"]  # safe numpy-backed math

from core.src.runtime_paths import APP_DATA_DIR, PULSE_BIN, PULSE_PYTHON

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flask_socketio import SocketIO, emit

from core.src.controllers import HTTPController, HTTPFluidController, BuiltinController, BuiltinFluidController, PULSE_UNIT_MAP
from core.src.cohort_builder import PatientGenerator, stabilize_patient
from core.src.vital_ranges import SOLDIER, ADULT, Demographic
from core.src.analysis import compute_wobble_divergence
from core.src.data_classes import Experiment, Patient, Scenario, Metric

from core.src.database.patient import get_patients_by_demographic
from core.src.database.batch import insert_batch
from core.src.database.metric import insert_metric, insert_metric_from_object, insert_run
from core.src.database.experiment import insert_experiment_from_object, update_experiment_from_object

# === PULSE IMPORTS ===
from pulse.engine.PulseEngine import PulseEngine, eModelType
from pulse.engine.PulseEnginePool import PulseEnginePool
from pulse.cdm.engine import SEDataRequest, SEDataRequestManager, SEAdvanceTime, IEventHandler, SEEventChange, eEvent
from multiprocessing import Pool as ProcessPool, TimeoutError as MPTimeoutError
from pulse.cdm.patient_actions import (
    SEIntubation, eIntubationType, 
    SEAcuteRespiratoryDistressSyndromeExacerbation,
    SESubstanceBolus, eSubstance_Administration,
    SESubstanceInfusion,
    SESubstanceCompoundInfusion,
    SEExercise,
    SEAcuteStress,
    SEHemorrhage, eHemorrhage_Compartment,
    SEAirwayObstruction,
    SERespiratoryMechanicsConfiguration
)
from pulse.cdm.physiology import eLungCompartment
from pulse.cdm.mechanical_ventilator_actions import (
    SEMechanicalVentilatorVolumeControl,
    SEMechanicalVentilatorPressureControl,
    eMechanicalVentilator_VolumeControlMode,
    eMechanicalVentilator_PressureControlMode
)
from pulse.cdm.mechanical_ventilator import eSwitch
from pulse.cdm.scalars import (
    FrequencyUnit, PressureUnit, TimeUnit,
    VolumeUnit, VolumePerTimeUnit, MassPerVolumeUnit,
    LengthUnit, MassUnit, PressureTimePerVolumeUnit, VolumePerPressureUnit,
    AmountPerVolumeUnit
)
from pulse.cdm.patient import eSex, SEPatient, SEPatientConfiguration
from pulse.cdm.io.patient import serialize_patient_from_file

from core.src.runtime_paths import APP_DATA_DIR    
PATIENTS_FOLDER = APP_DATA_DIR / "patients"
EXPERIMENT_RESULTS_FOLDER = APP_DATA_DIR / "experiment_results"
ANALYSIS_RESULTS_FOLDER = APP_DATA_DIR / "analysis_results"

for folder in [PATIENTS_FOLDER, EXPERIMENT_RESULTS_FOLDER, ANALYSIS_RESULTS_FOLDER,
]:
    folder.mkdir(parents=True, exist_ok=True)

jobs = {}
job_lock = threading.Lock()
cancel_flags = {}  # job_id -> True if should cancel
pulse_config_lock = threading.Lock()

# === AVAILABLE CSV OUTPUT VARIABLES ===
# Each entry defines a Pulse data request that can be selected for CSV output.
# "key" = CSV column name, "pulse_name" = Pulse engine variable name
# "request_type": "physiology", "mechanical_ventilator", or "compartment_substance"
# "transform": post-processing applied to raw Pulse value before CSV output
# Variables with "default": True match the original hardcoded set.

AVAILABLE_VARIABLES = [
    # --- Vital Signs ---
    {"key": "hr_bpm", "label": "Heart Rate", "unit": "bpm", "category": "Vital Signs",
     "default": True, "request_type": "physiology", "pulse_name": "HeartRate",
     "pulse_unit": "FrequencyUnit.Per_min", "transform": None},
    {"key": "spo2_pct", "label": "SpO2", "unit": "%", "category": "Vital Signs",
     "default": True, "request_type": "physiology", "pulse_name": "OxygenSaturation",
     "pulse_unit": None, "transform": "multiply_100"},
    {"key": "etco2_mmhg", "label": "EtCO2", "unit": "mmHg", "category": "Vital Signs",
     "default": True, "request_type": "physiology", "pulse_name": "EndTidalCarbonDioxidePressure",
     "pulse_unit": "PressureUnit.mmHg", "transform": None},
    {"key": "rr_patient", "label": "Resp Rate (patient)", "unit": "bpm", "category": "Vital Signs",
     "default": True, "request_type": "physiology", "pulse_name": "RespirationRate",
     "pulse_unit": "FrequencyUnit.Per_min", "transform": None},
    {"key": "sbp_mmhg", "label": "Systolic BP", "unit": "mmHg", "category": "Vital Signs",
     "default": True, "request_type": "physiology", "pulse_name": "SystolicArterialPressure",
     "pulse_unit": "PressureUnit.mmHg", "transform": None},
    {"key": "dbp_mmhg", "label": "Diastolic BP", "unit": "mmHg", "category": "Vital Signs",
     "default": True, "request_type": "physiology", "pulse_name": "DiastolicArterialPressure",
     "pulse_unit": "PressureUnit.mmHg", "transform": None},
    {"key": "map_mmhg", "label": "Mean Arterial Pressure", "unit": "mmHg", "category": "Vital Signs",
     "default": True, "request_type": "physiology", "pulse_name": "MeanArterialPressure",
     "pulse_unit": "PressureUnit.mmHg", "transform": None},

    # --- Blood Gas ---
    {"key": "pao2_mmhg", "label": "PaO2", "unit": "mmHg", "category": "Blood Gas",
     "default": True, "request_type": "physiology", "pulse_name": "ArterialOxygenPressure",
     "pulse_unit": "PressureUnit.mmHg", "transform": None},
    {"key": "paco2_mmhg", "label": "PaCO2", "unit": "mmHg", "category": "Blood Gas",
     "default": True, "request_type": "physiology", "pulse_name": "ArterialCarbonDioxidePressure",
     "pulse_unit": "PressureUnit.mmHg", "transform": None},
    {"key": "ph", "label": "Blood pH", "unit": "", "category": "Blood Gas",
     "default": True, "request_type": "physiology", "pulse_name": "BloodPH",
     "pulse_unit": None, "transform": None},

    # --- Cardiac ---
    {"key": "vt_patient_ml", "label": "Tidal Volume (patient)", "unit": "mL", "category": "Cardiac",
     "default": True, "request_type": "physiology", "pulse_name": "TidalVolume",
     "pulse_unit": "VolumeUnit.mL", "transform": None},
    {"key": "co_lpm", "label": "Cardiac Output", "unit": "L/min", "category": "Cardiac",
     "default": True, "request_type": "physiology", "pulse_name": "CardiacOutput",
     "pulse_unit": "VolumePerTimeUnit.L_Per_min", "transform": None},

    # --- Hematology (DEFAULT in PSB for shock/resuscitation monitoring) ---
    {"key": "lactate_mmol_L", "label": "Lactate", "unit": "mmol/L", "category": "Hematology",
     "default": True, "request_type": "compartment_substance",
     "pulse_name": "Lactate", "pulse_unit": "MassPerVolumeUnit.g_Per_L",
     "compartment": "Aorta", "property": "Concentration",
     "transform": "lactate_g_to_mmol"},
    {"key": "blood_volume_ml", "label": "Blood Volume", "unit": "mL", "category": "Hematology",
     "default": True, "request_type": "physiology", "pulse_name": "BloodVolume",
     "pulse_unit": "VolumeUnit.mL", "transform": None},
    {"key": "hematocrit_pct", "label": "Hematocrit", "unit": "%", "category": "Hematology",
     "default": False, "request_type": "physiology", "pulse_name": "Hematocrit",
     "pulse_unit": None, "transform": None},

    # --- Ventilator (measured) ---
    {"key": "rr_vent", "label": "Resp Rate (vent)", "unit": "bpm", "category": "Ventilator",
     "default": True, "request_type": "mechanical_ventilator", "pulse_name": "RespirationRate",
     "pulse_unit": "FrequencyUnit.Per_min", "transform": None},
    {"key": "vt_vent_ml", "label": "Tidal Volume (vent)", "unit": "mL", "category": "Ventilator",
     "default": True, "request_type": "mechanical_ventilator", "pulse_name": "TidalVolume",
     "pulse_unit": "VolumeUnit.mL", "transform": None},
    {"key": "pip_cmh2o", "label": "Peak Insp Pressure", "unit": "cmH2O", "category": "Ventilator",
     "default": True, "request_type": "mechanical_ventilator", "pulse_name": "PeakInspiratoryPressure",
     "pulse_unit": "PressureUnit.cmH2O", "transform": None},
    {"key": "pplat_cmh2o", "label": "Plateau Pressure", "unit": "cmH2O", "category": "Ventilator",
     "default": True, "request_type": "mechanical_ventilator", "pulse_name": "PlateauPressure",
     "pulse_unit": "PressureUnit.cmH2O", "transform": None},
    {"key": "paw_mean_cmh2o", "label": "Mean Airway Pressure", "unit": "cmH2O", "category": "Ventilator",
     "default": True, "request_type": "mechanical_ventilator", "pulse_name": "MeanAirwayPressure",
     "pulse_unit": "PressureUnit.cmH2O", "transform": None},
    {"key": "insp_flow_lpm", "label": "Inspiratory Flow", "unit": "L/min", "category": "Ventilator",
     "default": True, "request_type": "mechanical_ventilator", "pulse_name": "InspiratoryFlow",
     "pulse_unit": "VolumePerTimeUnit.L_Per_min", "transform": None},
    {"key": "exp_flow_lpm", "label": "Expiratory Flow", "unit": "L/min", "category": "Ventilator",
     "default": True, "request_type": "mechanical_ventilator", "pulse_name": "ExpiratoryFlow",
     "pulse_unit": "VolumePerTimeUnit.L_Per_min", "transform": None},

    # --- Respiratory Mechanics (non-default) ---
    {"key": "resp_compliance_ml_cmh2o", "label": "Respiratory Compliance", "unit": "mL/cmH2O",
     "category": "Respiratory Mechanics", "default": False, "request_type": "mechanical_ventilator",
     "pulse_name": "DynamicRespiratoryCompliance",
     "pulse_unit": "VolumePerPressureUnit.mL_Per_cmH2O", "transform": None},
    {"key": "static_compliance_ml_cmh2o", "label": "Static Compliance", "unit": "mL/cmH2O",
     "category": "Respiratory Mechanics", "default": False, "request_type": "mechanical_ventilator",
     "pulse_name": "StaticRespiratoryCompliance",
     "pulse_unit": "VolumePerPressureUnit.mL_Per_cmH2O", "transform": None},

    # --- Additional Ventilator (non-default) ---
    {"key": "airway_pressure_cmh2o", "label": "Airway Pressure", "unit": "cmH2O",
     "category": "Additional Ventilator", "default": False, "request_type": "mechanical_ventilator",
     "pulse_name": "AirwayPressure", "pulse_unit": "PressureUnit.cmH2O", "transform": None},
    {"key": "total_peep_cmh2o", "label": "Total PEEP", "unit": "cmH2O",
     "category": "Additional Ventilator", "default": False, "request_type": "mechanical_ventilator",
     "pulse_name": "TotalPositiveEndExpiratoryPressure",
     "pulse_unit": "PressureUnit.cmH2O", "transform": None},
    {"key": "ie_ratio", "label": "I:E Ratio", "unit": "",
     "category": "Additional Ventilator", "default": False, "request_type": "mechanical_ventilator",
     "pulse_name": "InspiratoryExpiratoryRatio", "pulse_unit": None, "transform": None},
    {"key": "insp_vt_ml", "label": "Inspiratory Vt", "unit": "mL",
     "category": "Additional Ventilator", "default": False, "request_type": "mechanical_ventilator",
     "pulse_name": "InspiratoryTidalVolume", "pulse_unit": "VolumeUnit.mL", "transform": None},
    {"key": "exp_vt_ml", "label": "Expiratory Vt", "unit": "mL",
     "category": "Additional Ventilator", "default": False, "request_type": "mechanical_ventilator",
     "pulse_name": "ExpiratoryTidalVolume", "pulse_unit": "VolumeUnit.mL", "transform": None},
    {"key": "peak_insp_flow_lpm", "label": "Peak Insp Flow", "unit": "L/min",
     "category": "Additional Ventilator", "default": False, "request_type": "mechanical_ventilator",
     "pulse_name": "PeakInspiratoryFlow", "pulse_unit": "VolumePerTimeUnit.L_Per_min", "transform": None},

    # --- Temperature (non-default) ---
    {"key": "skin_temp_c", "label": "Skin Temperature", "unit": "C",
     "category": "Temperature", "default": False, "request_type": "physiology",
     "pulse_name": "SkinTemperature", "pulse_unit": None, "transform": None},

    # --- Advanced Respiratory (non-default) ---
    {"key": "total_lung_volume_ml", "label": "Total Lung Volume", "unit": "mL",
     "category": "Advanced Respiratory", "default": False, "request_type": "physiology",
     "pulse_name": "TotalLungVolume", "pulse_unit": "VolumeUnit.mL", "transform": None},
    {"key": "total_pulm_ventilation_lpm", "label": "Total Pulmonary Ventilation", "unit": "L/min",
     "category": "Advanced Respiratory", "default": False, "request_type": "physiology",
     "pulse_name": "TotalPulmonaryVentilation", "pulse_unit": "VolumePerTimeUnit.L_Per_min", "transform": None},
]

# Columns always included in CSV (not Pulse data requests - internally tracked state)
# PSB includes fluid controller columns
ALWAYS_INCLUDED_COLUMNS = [
    "cmd_mode", "cmd_vt_ml", "cmd_rr", "cmd_fio2",
    "cmd_peep_cmh2o", "cmd_pinsp_cmh2o", "cmd_itime_s",
    "is_intubated", "vent_active", "controller_active", "fluid_controller_active",
    "blood_loss_ml", "blood_infused_ml", "crystalloid_infused_ml",
    "cmd_crystalloid_rate", "cmd_blood_rate",
    "event", "controller_cmd", "fluid_cmd"
]

# Default variable keys (for backward compatibility when no output_columns specified)
DEFAULT_OUTPUT_KEYS = [v["key"] for v in AVAILABLE_VARIABLES if v["default"]]

def resolve_selected_vars(output_columns=None):
    """Return the list of AVAILABLE_VARIABLES entries matching the selected keys.
    If output_columns is None, returns the default set. Preserves registry order."""
    if output_columns is None:
        return [v for v in AVAILABLE_VARIABLES if v["default"]]
    selected_set = set(output_columns)
    return [v for v in AVAILABLE_VARIABLES if v["key"] in selected_set]


def build_data_requests(selected_vars):
    """Build Pulse SEDataRequest list from selected variable definitions."""
    data_requests = []
    for var in selected_vars:
        unit = PULSE_UNIT_MAP.get(var.get("pulse_unit")) if var.get("pulse_unit") else None
        kwargs = {}
        if unit is not None:
            kwargs["unit"] = unit

        if var["request_type"] == "physiology":
            data_requests.append(SEDataRequest.create_physiology_request(var["pulse_name"], **kwargs))
        elif var["request_type"] == "mechanical_ventilator":
            data_requests.append(SEDataRequest.create_mechanical_ventilator_request(var["pulse_name"], **kwargs))
        elif var["request_type"] == "compartment_substance":
            data_requests.append(
                SEDataRequest.create_liquid_compartment_substance_request(
                    var["compartment"], var["pulse_name"], var["property"], **kwargs
                )
            )
    return data_requests


def build_vitals_dict(results, selected_vars):
    """Convert Pulse results array to a named vitals dict based on selected variables.
    results[0] is always sim_time, results[1..N] correspond to selected_vars in order."""
    vitals = {"t": results[0]}
    for i, var in enumerate(selected_vars):
        val = results[i + 1]
        transform = var.get("transform")
        if transform == "multiply_100":
            val = val * 100
        elif transform == "lactate_g_to_mmol":
            val = val * 11.1  # g/L to mmol/L (MW lactate ~90.08)
        vitals[var["key"]] = val
    return vitals


def build_csv_columns(selected_vars):
    """Build the CSV column header list from selected variables plus always-included columns."""
    cols = ["sim_time_s"]
    cols.extend([v["key"] for v in selected_vars])
    cols.extend(ALWAYS_INCLUDED_COLUMNS)
    return cols

def parse_matching_function(expr_str: str):
    """
    Parses a user-defined math string into a callable numpy function.
    
    Supports: log, exp, sin, cos, sqrt, abs, x (the simulation value), t (sim time)
    Returns: callable(x, t=None) -> np.ndarray
    Raises: ValueError on invalid/unsafe input
    """
    if not expr_str or not isinstance(expr_str, str):
        return None
    
    # Whitelist: only allow safe characters
    import re
    if re.search(r'[^a-zA-Z0-9\s\+\-\*\/\(\)\.\,\_\^]', expr_str):
        raise ValueError(f"Invalid characters in matching function: '{expr_str}'")
    
    # Replace ^ with ** for power operator
    expr_str = expr_str.replace("^", "**")

    try:
        x, t = sp.symbols('x t')
        expr = sp.sympify(expr_str, locals={'x': x, 't': t})
        
        # Check for disallowed sympy types (e.g. relational, boolean)
        if not isinstance(expr, sp.Basic):
            raise ValueError("Expression must be a scalar math expression.")
        
        # Lambdify with numpy backend
        free = expr.free_symbols
        if t in free:
            func = lambdify((x, t), expr, modules=ALLOWED_SYMPY_MODULES)
            return lambda x_arr, t_arr: func(x_arr, t_arr)
        else:
            func = lambdify(x, expr, modules=ALLOWED_SYMPY_MODULES)
            return lambda x_arr, t_arr=None: func(x_arr)

    except (sp.SympifyError, TypeError, AttributeError) as e:
        raise ValueError(f"Could not parse matching function '{expr_str}': {e}")
    
def allocate_counts(total, demographics):
    #extract percentages
    percents = [d.get('percent', 0.0) for d in demographics]

    total_percent = sum(percents)
    if total_percent == 0:
        return [0] * len(demographics)
    
    #normalize to fractions
    exact = [(p / total_percent) * total for p in percents]

    #floor to get base counts, then distribute remainder by largest fractional part
    base = [math.floor(x) for x in exact]
    remainder = total - sum(base)

    #sort by fractional part descending
    fractions = sorted(
        [(i, exact[i] - base[i]) for i in range(len(demographics))],
        key=lambda x: x[1],
        reverse=True
    )

    for i in range(remainder):
        idx = fractions[i][0]
        base[idx] += 1

    return base

# === BATCH MODE SUPPORT ===
batches = {}
batch_lock = threading.Lock()
batch_cancel_flags = {}  # batch_id -> True if should cancel (for thread-level check)

# File-based cancellation for cross-process communication
# Using files instead of multiprocessing.Manager because Manager proxies
# don't reliably propagate updates to already-running worker processes

def get_cancel_flag_path(batch_id):
    """Get the path to the cancel flag file for a batch.

    Uses os.path.realpath() to normalize the temp directory path,
    ensuring consistency between main process and worker processes
    (Windows can return short 8.3 paths vs long paths depending on context).
    """
    temp_dir = os.path.realpath(tempfile.gettempdir())
    return os.path.join(temp_dir, f"pulse_batch_cancel_{batch_id}.flag")

def set_batch_cancel_flag(batch_id):
    """Set the cancel flag for a batch by creating a flag file."""
    flag_path = get_cancel_flag_path(batch_id)
    try:
        with open(flag_path, 'w') as f:
            f.write('cancel')
        # Also get the absolute/real path to verify
        real_path = os.path.realpath(flag_path)
        print(f"[BATCH] Cancel flag file created: {flag_path}")
        if real_path != flag_path:
            print(f"[BATCH] Real path: {real_path}")
        return True
    except Exception as e:
        print(f"[BATCH] Failed to create cancel flag file: {e}")
        return False

def check_batch_cancel_flag(batch_id):
    """Check if the cancel flag is set for a batch."""
    flag_path = get_cancel_flag_path(batch_id)
    return os.path.exists(flag_path)

def clear_batch_cancel_flag(batch_id):
    """Clear the cancel flag for a batch by removing the flag file."""
    flag_path = get_cancel_flag_path(batch_id)
    try:
        if os.path.exists(flag_path):
            os.remove(flag_path)
    except Exception:
        pass  # Ignore errors during cleanup


def _extract_batch_patient_weight(patient_json, patient_name, initial_blood_volume_ml):
    """Extract patient weight in kg for batch worker.

    Tries in order:
    1. patient_json state file (CurrentPatient.Weight)
    2. patient_json patient definition (Weight)
    3. Read from state file on disk
    4. Fallback: estimate from blood volume
    """
    weight_kg = None

    # 1. Patient JSON (state file or patient definition)
    if patient_json:
        # State file format: CurrentPatient.Weight.ScalarMass
        if "CurrentPatient" in patient_json:
            weight_data = patient_json.get("CurrentPatient", {}).get("Weight", {}).get("ScalarMass", {})
        else:
            # Patient definition format: Weight.ScalarMass
            weight_data = patient_json.get("Weight", {}).get("ScalarMass", {})

        if weight_data:
            value = weight_data.get("Value")
            unit = weight_data.get("Unit", "lb")
            if value:
                if unit == "kg":
                    weight_kg = value
                else:  # Default to lb
                    weight_kg = value * 0.453592

    # 2. Read from state file on disk
    elif patient_name:
        try:
            import json as json_module
            state_path = f"./states/{patient_name}" if not os.path.isabs(patient_name) else patient_name
            if os.path.exists(state_path):
                with open(state_path, 'r') as f:
                    state_data = json_module.load(f)
                weight_data = state_data.get("CurrentPatient", {}).get("Weight", {}).get("ScalarMass", {})
                if weight_data:
                    value = weight_data.get("Value")
                    unit = weight_data.get("Unit", "lb")
                    if value:
                        if unit == "kg":
                            weight_kg = value
                        else:
                            weight_kg = value * 0.453592
        except Exception:
            pass  # Fall through to estimation

    # 3. Fallback: estimate from blood volume
    if weight_kg is None or weight_kg < 20:
        weight_kg = initial_blood_volume_ml / 70.0
        if weight_kg < 20:
            weight_kg = 70.0  # Default adult weight

    return weight_kg


def run_single_patient(args):
    """
    Run a single patient simulation in a separate process.

    This function must be completely self-contained with no shared state,
    since it runs in a separate process (multiprocessing.Pool).

    Args can contain either:
    - patient: filename of pre-stabilized state (e.g., "Carol@0s.json")
    - patient_json: dict with 'name' and 'json' for custom patient

    Args tuple: (patient_info, batch_config, output_dir, job_id)
    - job_id is the unique identifier including replicate suffix (e.g., "Carol@0s.json_r1")
    - Cancellation is checked via file-based flag (check_batch_cancel_flag)
    """
    # Support various tuple formats for backwards compatibility
    if len(args) == 5:
        # Legacy format with shared_cancel dict (ignored now, we use file-based)
        patient_info, batch_config, output_dir, job_id, _ = args
    elif len(args) == 4:
        patient_info, batch_config, output_dir, job_id = args
    else:
        patient_info, batch_config, output_dir = args
        job_id = None  # Will be set below

    # Get batch_id for cancellation check (file-based)
    batch_id = batch_config.get('batch_id', '')
    
    duration_s = batch_config['duration_s']
    sample_rate_hz = batch_config.get('sample_rate_hz', 50)
    vent_settings = batch_config['vent_settings']
    events = sorted(batch_config.get('events', []), key=lambda e: e.get('time', 0))
    pulse_bin = batch_config['pulse_bin']
    pulse_python = batch_config.get('pulse_python', pulse_bin)
    
    timestep = 1.0 / sample_rate_hz
    
    # Get replicate suffix if present
    replicate_suffix = batch_config.get('replicate_suffix', '')

    # Determine if this is a pre-stabilized or custom patient
    if isinstance(patient_info, dict):
        patient_name = patient_info['name']
        patient_json = patient_info['json']
        is_custom = True
    else:
        patient_name = patient_info
        patient_json = None
        is_custom = False

    # Set job_id if not provided (legacy support)
    if job_id is None:
        if is_custom:
            job_id = f"custom_{patient_name}{replicate_suffix}"
        else:
            job_id = f"{patient_name}{replicate_suffix}"
    
    try:
        # Set up paths for this worker process (Windows spawn doesn't inherit sys.path)
        import sys
        for path in [pulse_python, pulse_bin]:
            if path not in sys.path:
                sys.path.insert(0, path)
        
        # Add DLL directory on Windows
        if hasattr(os, 'add_dll_directory'):
            try:
                os.add_dll_directory(pulse_bin)
            except OSError:
                pass  # Already added or doesn't exist
        
        os.chdir(pulse_bin)
        
        # Import Pulse in the worker process
        from pulse.engine.PulseEngine import PulseEngine
        from pulse.cdm.engine import SEDataRequest, SEDataRequestManager, IEventHandler, SEEventChange, eEvent
        from pulse.cdm.scalars import FrequencyUnit, PressureUnit, TimeUnit, VolumeUnit, VolumePerTimeUnit, LengthUnit, MassUnit, MassPerVolumeUnit, AmountPerVolumeUnit, VolumePerPressureUnit, PressureTimePerVolumeUnit
        from pulse.cdm.patient_actions import (
            SEIntubation, eIntubationType, SEExercise,
            SEAcuteRespiratoryDistressSyndromeExacerbation,
            SEAirwayObstruction, SEAcuteStress,
            SEHemorrhage, eHemorrhage_Compartment,
            SESubstanceBolus, SESubstanceInfusion,
            SESubstanceCompoundInfusion
        )
        from pulse.cdm.physiology import eLungCompartment
        from pulse.cdm.mechanical_ventilator_actions import (
            SEMechanicalVentilatorVolumeControl,
            SEMechanicalVentilatorPressureControl,
            eMechanicalVentilator_VolumeControlMode,
            eMechanicalVentilator_PressureControlMode
        )
        from pulse.cdm.mechanical_ventilator import eSwitch
        from pulse.cdm.patient import SEPatientConfiguration, eSex
        from pulse.cdm.io.patient import serialize_patient_from_file
        import tempfile
        
        from core.src.controllers import BatchBuiltinController, BatchBuiltinFluidController, BatchHTTPController, BatchHTTPFluidController

        # Local event handler for batch simulation (can't use main class due to multiprocessing)
        class BatchEventHandler(IEventHandler):
            DEATH_EVENTS = {eEvent.IrreversibleState, eEvent.CardiacArrest}
            CRITICAL_EVENTS = {
                eEvent.IrreversibleState: "Irreversible State (Death)",
                eEvent.CardiacArrest: "Cardiac Arrest",
                eEvent.CardiovascularCollapse: "Cardiovascular Collapse",
                eEvent.HypovolemicShock: "Hypovolemic Shock",
            }

            def __init__(self):
                super().__init__(active_events_only=False)
                self.is_dead = False
                self.death_time_s = None
                self.death_cause = None
                self.event_log = []

            def handle_event(self, change):
                event = change.event
                time_s = change.sim_time.get_value(TimeUnit.s) if change.sim_time.is_valid() else 0
                if event in self.DEATH_EVENTS and change.active and not self.is_dead:
                    self.is_dead = True
                    self.death_time_s = time_s
                    self.death_cause = self.CRITICAL_EVENTS.get(event, str(event))
                if event in self.CRITICAL_EVENTS:
                    self.event_log.append((time_s, self.CRITICAL_EVENTS[event], change.active))

        # Create engine for this patient
        pulse = PulseEngine()
        safe_name = patient_name.replace('@', '_').replace('.', '_').replace(' ', '_')
        pulse.set_log_filename(f"./test_results/batch_{safe_name}.log")
        pulse.log_to_console(False)

        # Set up event handler for death detection
        event_handler = BatchEventHandler()
        pulse.set_event_handler(event_handler)
        
        # Build data requests using ALL available variables
        selected_vars = batch_config.get('available_variables', [])

        # Unit string -> Pulse unit object mapping (needed in worker process)
        worker_unit_map = {
            "FrequencyUnit.Per_min": FrequencyUnit.Per_min,
            "PressureUnit.mmHg": PressureUnit.mmHg,
            "PressureUnit.cmH2O": PressureUnit.cmH2O,
            "VolumeUnit.mL": VolumeUnit.mL,
            "VolumePerTimeUnit.L_Per_min": VolumePerTimeUnit.L_Per_min,
            "VolumePerTimeUnit.mL_Per_min": VolumePerTimeUnit.mL_Per_min,
            "MassPerVolumeUnit.g_Per_L": MassPerVolumeUnit.g_Per_L,
            "VolumePerPressureUnit.mL_Per_cmH2O": VolumePerPressureUnit.mL_Per_cmH2O,
            "PressureTimePerVolumeUnit.cmH2O_s_Per_L": PressureTimePerVolumeUnit.cmH2O_s_Per_L,
        }

        data_requests = []
        for var in selected_vars:
            unit = worker_unit_map.get(var.get("pulse_unit")) if var.get("pulse_unit") else None
            kwargs = {}
            if unit is not None:
                kwargs["unit"] = unit
            if var["request_type"] == "physiology":
                data_requests.append(SEDataRequest.create_physiology_request(var["pulse_name"], **kwargs))
            elif var["request_type"] == "mechanical_ventilator":
                data_requests.append(SEDataRequest.create_mechanical_ventilator_request(var["pulse_name"], **kwargs))
            elif var["request_type"] == "compartment_substance":
                data_requests.append(
                    SEDataRequest.create_liquid_compartment_substance_request(
                        var["compartment"], var["pulse_name"], var["property"], **kwargs
                    )
                )
        data_mgr = SEDataRequestManager(data_requests)
        
        if is_custom:
            # Check if this is a pre-stabilized state file or a patient definition
            is_state_file = patient_json and any(key in patient_json for key in ['SimulationTime', 'InitialPatient', 'Compartments', 'CurrentPatient'])
            
            if is_state_file:
                # Pre-stabilized state file - load directly
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, dir=PULSE_BIN) as f:
                    import json as json_module
                    json_module.dump(patient_json, f)
                    temp_path = f.name
                
                try:
                    rel_path = os.path.basename(temp_path)
                    if not pulse.serialize_from_file(rel_path, data_mgr):
                        raise RuntimeError(f"Failed to load pre-stabilized state: {patient_name}")
                finally:
                    try:
                        os.unlink(temp_path)
                    except:
                        pass
            elif patient_json is None:
                # Newly stabilized patient - look for state file in patients folder
                state_file_path = os.path.join(PATIENTS_FOLDER, f"{patient_name}@0s.json")
                if os.path.exists(state_file_path):
                    if not pulse.serialize_from_file(state_file_path, data_mgr):
                        raise RuntimeError(f"Failed to load stabilized patient state: {patient_name}")
                else:
                    raise RuntimeError(f"Stabilized patient state file not found: {state_file_path}")
            else:
                # Patient definition - needs stabilization
                pc = SEPatientConfiguration()
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                    import json as json_module
                    json_module.dump(patient_json, f)
                    temp_path = f.name
                
                try:
                    serialize_patient_from_file(temp_path, pc.get_patient())
                    pc.set_data_root_dir("./")
                    if not pulse.initialize_engine(pc, data_mgr):
                        raise RuntimeError(f"Failed to stabilize custom patient: {patient_name}")
                finally:
                    os.unlink(temp_path)
        else:
            # Pre-stabilized patient - load state directly
            patient_path = f"./states/{patient_name}"
            if not pulse.serialize_from_file(patient_path, data_mgr):
                raise RuntimeError(f"Failed to load patient: {patient_name} at path: {patient_path}")

        # Capture initial blood volume for relative hemorrhage rates
        # Advance time slightly to ensure engine has computed state values
        pulse.advance_time_s(0.1)
        initial_results = pulse.pull_data()
        # Use dynamic vitals dict to get blood volume by key (index depends on selected columns)
        initial_vitals = {"t": initial_results[0]}
        for vi, var in enumerate(selected_vars):
            val = initial_results[vi + 1]
            transform = var.get("transform")
            if transform == "multiply_100":
                val = val * 100
            elif transform == "lactate_g_to_mmol":
                val = val * 11.1
            initial_vitals[var["key"]] = val
        initial_blood_volume_ml = initial_vitals.get("blood_volume_ml", 5000.0)
        if initial_blood_volume_ml <= 0:
            initial_blood_volume_ml = 5000.0

        # Extract patient weight for weight-based drug dosing
        patient_weight_kg = _extract_batch_patient_weight(patient_json, patient_name, initial_blood_volume_ml)

        # Track intubation and vent state
        is_intubated = False
        vent_active = False
        # v6: start_intubated defaults to False - use events for intubation/ventilation
        start_intubated = batch_config.get('start_intubated', False)

        if start_intubated:
            # Legacy support: intubate at t=0 if start_intubated is True
            intubation = SEIntubation()
            intubation.set_type(eIntubationType.Tracheal)
            pulse.process_action(intubation)
            pulse.advance_time_s(2)
            is_intubated = True

            # Start ventilator with job-level settings
            vent = SEMechanicalVentilatorVolumeControl()
            vent.set_connection(eSwitch.On)
            vent.set_mode(eMechanicalVentilator_VolumeControlMode.AssistedControl)
            vent.get_tidal_volume().set_value(vent_settings.get('vt_ml', 420), VolumeUnit.mL)
            vent.get_respiration_rate().set_value(vent_settings.get('rr', 14), FrequencyUnit.Per_min)
            vent.get_fraction_inspired_oxygen().set_value(vent_settings.get('fio2', 0.4))
            vent.get_positive_end_expired_pressure().set_value(vent_settings.get('peep_cmh2o', 5), PressureUnit.cmH2O)
            vent.get_inspiratory_period().set_value(vent_settings.get('itime_s', 1.0), TimeUnit.s)
            vent.get_flow().set_value(vent_settings.get('flow_lpm', 50), VolumePerTimeUnit.L_Per_min)
            pulse.process_action(vent)
            pulse.advance_time_s(3)
            vent_active = True
        
        # CSV output - build columns dynamically from selected variables
        csv_buffer = io.StringIO()
        writer = csv.writer(csv_buffer)
        csv_columns = ["sim_time_s"]
        csv_columns.extend([v["key"] for v in selected_vars])
        csv_columns.extend([
            "cmd_mode", "cmd_vt_ml", "cmd_rr", "cmd_fio2",
            "cmd_peep_cmh2o", "cmd_pinsp_cmh2o", "cmd_itime_s",
            "is_intubated", "vent_active", "controller_active", "fluid_controller_active",
            "blood_loss_ml", "blood_infused_ml", "crystalloid_infused_ml",
            "cmd_crystalloid_rate", "cmd_blood_rate",
            "event", "controller_cmd", "fluid_cmd"
        ])
        writer.writerow(csv_columns)
        
        # Run simulation
        sim_time = 0.0
        event_idx = 0
        patient_dead = False

        # Track hemorrhage conditions (for conditional stop feature)
        hemorrhage_stop_conditions = {}  # compartment -> {vital, operator, value, maxDurationSec, startTime}
        hemorrhage_flow_rates = {}  # compartment -> current flow rate

        # Ventilator controller state
        controller = None
        controller_active = False
        last_control_time = 0.0
        control_interval_s = 1.0
        controller_cmd = ""  # For CSV output

        # Fluid controller state
        fluid_controller = None
        fluid_controller_active = False
        last_fluid_control_time = 0.0
        fluid_control_interval_s = 10.0
        fluid_controller_cmd = ""  # For CSV output
        fluid_settings = {
            'crystalloid_rate_ml_min': 0,
            'blood_rate_ml_min': 0,
            'crystalloid_compound': 'Saline',
            'blood_compound': 'Blood'
        }

        # Fluid infusion tracking
        cumulative_blood_loss_ml = 0.0
        cumulative_blood_infused_ml = 0.0
        cumulative_crystalloid_infused_ml = 0.0
        active_infusions = {}  # compound -> {rate, remaining_ml, is_blood}

        # Separate trigger-based events from time-based events
        time_events = [e for e in events if "trigger" not in e]
        triggered_events = [e for e in events if "trigger" in e]
        fired_trigger_ids = set()
        fired_event_names = set()  # Track event names for after_event triggers
        pending_delayed_triggers = {}  # event_id -> fire_time for triggers waiting on delay

        # Use time_events for the main loop
        events = time_events

        # Track if we were cancelled
        was_cancelled = False
        last_cancel_check = 0  # Check cancellation every 5 seconds of sim time
        cancel_check_count = 0


        last_heartbeat = 0
        while sim_time < duration_s:
            # Check for cancellation periodically (every 5 seconds of sim time)
            if (sim_time - last_cancel_check) >= 5.0:
                last_cancel_check = sim_time

                # Check for cancellation using file-based flag
                # Use os.path.realpath() to normalize path (Windows short vs long path issue)
                if batch_id:
                    temp_dir = os.path.realpath(tempfile.gettempdir())
                    cancel_flag_path = os.path.join(temp_dir, f"pulse_batch_cancel_{batch_id}.flag")
                    if os.path.exists(cancel_flag_path):
                        print(f"[Batch {job_id}] Cancelled at t={sim_time:.1f}s")
                        was_cancelled = True
                        break

            # Process events at this time - collect all that fire now
            current_events = []
            while event_idx < len(events) and events[event_idx].get('time', 0) <= sim_time:
                event = events[event_idx]
                etype = event.get('type', '')
                event_name = ""
                
                if etype == 'pathology':
                    pathology = event.get('pathology', 'ARDS')
                    severity = event.get('severity', 0.5)
                    
                    if pathology == 'ARDS':
                        action = SEAcuteRespiratoryDistressSyndromeExacerbation()
                        action.get_severity(eLungCompartment.LeftLung).set_value(severity)
                        action.get_severity(eLungCompartment.RightLung).set_value(severity)
                        pulse.process_action(action)
                        event_name = f"ARDS({severity})"
                    elif pathology == 'AirwayObstruction':
                        action = SEAirwayObstruction()
                        action.get_severity().set_value(severity)
                        pulse.process_action(action)
                        event_name = f"AirwayObs({severity})"
                    elif pathology == 'AcuteStress':
                        action = SEAcuteStress()
                        action.get_severity().set_value(severity)
                        pulse.process_action(action)
                        event_name = f"Stress({severity})"
                    elif pathology == 'Hemorrhage':
                        compartment = event.get('compartment', 'VenaCava')
                        flow_rate = event.get('flowRate', event.get('flow_rate', 100))
                        flow_rate_mode = event.get('flowRateMode', 'absolute')
                        is_auto_stop = event.get('isAutoStop', False)

                        # Convert percentage of blood volume to absolute mL/min if needed
                        if flow_rate_mode == "percent_bv" and initial_blood_volume_ml > 0:
                            absolute_rate = (flow_rate / 100.0) * initial_blood_volume_ml
                            flow_rate = absolute_rate

                        # Map compartment string to enum
                        compartment_map = {
                            "RightLeg": eHemorrhage_Compartment.RightLeg,
                            "LeftLeg": eHemorrhage_Compartment.LeftLeg,
                            "RightArm": eHemorrhage_Compartment.RightArm,
                            "LeftArm": eHemorrhage_Compartment.LeftArm,
                            "Aorta": eHemorrhage_Compartment.Aorta,
                            "VenaCava": eHemorrhage_Compartment.VenaCava,
                        }

                        action = SEHemorrhage()
                        action.set_compartment(compartment_map.get(compartment, eHemorrhage_Compartment.VenaCava))
                        action.get_flow_rate().set_value(flow_rate, VolumePerTimeUnit.mL_Per_min)
                        pulse.process_action(action)

                        hemorrhage_flow_rates[compartment] = flow_rate

                        # Register stop condition if this is a conditional hemorrhage
                        stop_condition = event.get('stopCondition')
                        if stop_condition and flow_rate > 0:
                            hemorrhage_stop_conditions[compartment] = {
                                "vital": stop_condition.get("vital", "hr_bpm"),
                                "operator": stop_condition.get("operator", ">="),
                                "value": stop_condition.get("value", 120),
                                "maxDurationSec": event.get("maxDurationSec", 600),
                                "startTime": sim_time
                            }

                        if flow_rate == 0 or is_auto_stop:
                            if compartment in hemorrhage_stop_conditions:
                                del hemorrhage_stop_conditions[compartment]
                            event_name = f"StopHemorrhage({compartment})"
                        else:
                            event_name = f"Hemorrhage({compartment},{flow_rate:.1f}mL/min)"
                
                # Legacy pathology event types for backwards compatibility
                elif etype == 'pathology_ards':
                    severity = event.get('severity', 0.5)
                    action = SEAcuteRespiratoryDistressSyndromeExacerbation()
                    action.get_severity(eLungCompartment.LeftLung).set_value(severity)
                    action.get_severity(eLungCompartment.RightLung).set_value(severity)
                    pulse.process_action(action)
                    event_name = f"ARDS({severity})"
                elif etype == 'pathology_airway':
                    severity = event.get('severity', 0.5)
                    action = SEAirwayObstruction()
                    action.get_severity().set_value(severity)
                    pulse.process_action(action)
                    event_name = f"AirwayObs({severity})"
                elif etype == 'pathology_stress':
                    severity = event.get('severity', 0.5)
                    action = SEAcuteStress()
                    action.get_severity().set_value(severity)
                    pulse.process_action(action)
                    event_name = f"Stress({severity})"
                
                elif etype == 'intubate':
                    intubation_type = event.get('intubationType', 'Tracheal')
                    type_map = {
                        'Tracheal': eIntubationType.Tracheal,
                        'RightMainstem': eIntubationType.RightMainstem,
                        'LeftMainstem': eIntubationType.LeftMainstem,
                        'Esophageal': eIntubationType.Esophageal,
                        'Oropharyngeal': eIntubationType.Oropharyngeal,
                        'Nasopharyngeal': eIntubationType.Nasopharyngeal,
                    }
                    intubation = SEIntubation()
                    intubation.set_type(type_map.get(intubation_type, eIntubationType.Tracheal))
                    pulse.process_action(intubation)
                    is_intubated = (intubation_type != 'Off')
                    event_name = f"Intubate({intubation_type})"
                
                elif etype == 'start_vent':
                    # v6: vent_settings can be embedded in the event
                    evt_vent_settings = event.get('vent_settings', vent_settings)
                    vent = SEMechanicalVentilatorVolumeControl()
                    vent.set_connection(eSwitch.On)
                    vent.set_mode(eMechanicalVentilator_VolumeControlMode.AssistedControl)
                    vent.get_tidal_volume().set_value(evt_vent_settings.get('vt_ml', 420), VolumeUnit.mL)
                    vent.get_respiration_rate().set_value(evt_vent_settings.get('rr', 14), FrequencyUnit.Per_min)
                    vent.get_fraction_inspired_oxygen().set_value(evt_vent_settings.get('fio2', 0.4))
                    vent.get_positive_end_expired_pressure().set_value(evt_vent_settings.get('peep_cmh2o', 5), PressureUnit.cmH2O)
                    vent.get_inspiratory_period().set_value(evt_vent_settings.get('itime_s', 1.0), TimeUnit.s)
                    vent.get_flow().set_value(evt_vent_settings.get('flow_lpm', 50), VolumePerTimeUnit.L_Per_min)
                    pulse.process_action(vent)
                    vent_active = True
                    # Update job-level settings for CSV output
                    vent_settings.update(evt_vent_settings)
                    event_name = "StartVent"

                elif etype == 'change_vent':
                    # v6: Change ventilator settings mid-simulation
                    evt_vent_settings = event.get('vent_settings', {})
                    if evt_vent_settings:
                        vent = SEMechanicalVentilatorVolumeControl()
                        vent.set_connection(eSwitch.On)
                        vent.set_mode(eMechanicalVentilator_VolumeControlMode.AssistedControl)
                        vent.get_tidal_volume().set_value(evt_vent_settings.get('vt_ml', 420), VolumeUnit.mL)
                        vent.get_respiration_rate().set_value(evt_vent_settings.get('rr', 14), FrequencyUnit.Per_min)
                        vent.get_fraction_inspired_oxygen().set_value(evt_vent_settings.get('fio2', 0.4))
                        vent.get_positive_end_expired_pressure().set_value(evt_vent_settings.get('peep_cmh2o', 5), PressureUnit.cmH2O)
                        vent.get_inspiratory_period().set_value(evt_vent_settings.get('itime_s', 1.0), TimeUnit.s)
                        vent.get_flow().set_value(evt_vent_settings.get('flow_lpm', 50), VolumePerTimeUnit.L_Per_min)
                        pulse.process_action(vent)
                        # Update job-level settings for CSV output
                        vent_settings.update(evt_vent_settings)
                        event_name = "ChangeVent"

                elif etype == 'exercise':
                    intensity = event.get('intensity', event.get('severity', 0.5))
                    action = SEExercise()
                    action.get_intensity().set_value(intensity)
                    pulse.process_action(action)
                    event_name = f"Exercise({intensity})"
                
                elif etype == 'bolus':
                    drug = event.get('drug', 'Rocuronium')
                    dose_mode = event.get('dose_mode', 'fixed')
                    concentration = float(event.get('concentration', 10))
                    conc_unit = event.get('concentration_unit', 'mg/mL')

                    # Calculate dose based on mode
                    if dose_mode == 'weight':
                        dose_per_kg = float(event.get('dose_per_kg', 0.5))
                        dose_per_kg_unit = event.get('dose_per_kg_unit', 'mg/kg')

                        # Calculate total mass in mg based on patient weight
                        if dose_per_kg_unit in ('ug/kg', 'mcg/kg'):
                            total_mass_mg = (dose_per_kg / 1000.0) * patient_weight_kg
                        else:  # mg/kg
                            total_mass_mg = dose_per_kg * patient_weight_kg

                        # Calculate volume from total mass and concentration
                        if conc_unit == 'mg/mL':
                            conc_mg_per_mL = concentration
                        elif conc_unit == 'ug/mL':
                            conc_mg_per_mL = concentration / 1000.0
                        elif conc_unit == 'g/L':
                            conc_mg_per_mL = concentration
                        else:
                            conc_mg_per_mL = concentration

                        dose_mL = total_mass_mg / conc_mg_per_mL if conc_mg_per_mL > 0 else 1.0
                        dose_desc = f"{dose_per_kg}{dose_per_kg_unit} ({patient_weight_kg:.1f}kg)"
                    else:
                        # Fixed dose
                        dose_mL = float(event.get('dose_mL', 5))
                        if conc_unit == 'mg/mL':
                            total_mass_mg = dose_mL * concentration
                        elif conc_unit == 'ug/mL':
                            total_mass_mg = dose_mL * concentration / 1000.0
                        elif conc_unit == 'g/L':
                            total_mass_mg = dose_mL * concentration
                        else:
                            total_mass_mg = dose_mL * concentration
                        dose_desc = f"{total_mass_mg:.1f}mg"

                    # Convert concentration to g/L for Pulse
                    if conc_unit == 'mg/mL':
                        conc_g_L = concentration
                    elif conc_unit == 'ug/mL':
                        conc_g_L = concentration / 1000.0
                    elif conc_unit == 'g/L':
                        conc_g_L = concentration
                    else:
                        conc_g_L = concentration

                    try:
                        infusion = SESubstanceInfusion()
                        infusion.set_comment(f"Bolus delivery of {drug}")
                        infusion.set_substance(drug)
                        infusion.get_rate().set_value(dose_mL * 60.0, VolumePerTimeUnit.mL_Per_min)
                        infusion.get_concentration().set_value(conc_g_L, MassPerVolumeUnit.from_string("g/L"))
                        pulse.process_action(infusion)
                        event_name = f"Bolus({drug},{dose_desc})"
                    except Exception as e:
                        event_name = f"Bolus FAILED ({e})"
                
                elif etype == 'infusion':
                    drug = event.get('drug', 'Norepinephrine')
                    conc = event.get('concentration', 0.016)
                    rate = event.get('rate_ml_per_hr', 10)
                    substance = pulse.get_substance_manager().get_substance(drug)
                    if substance:
                        infusion = SESubstanceInfusion()
                        infusion.set_substance(substance)
                        infusion.get_concentration().set_value(conc, MassPerVolumeUnit.from_string("mg/mL"))
                        infusion.get_rate().set_value(rate / 60.0, VolumePerTimeUnit.mL_Per_min)
                        pulse.process_action(infusion)
                        event_name = f"Infusion({drug},{rate}mL/hr)"
                
                elif etype == 'compound_infusion':
                    compound = event.get('compound', 'Saline')
                    rate = event.get('rate_mL_per_min', event.get('rate_ml_per_min', 100))
                    bag_volume = event.get('bag_volume_mL', 1000)
                    try:
                        infusion = SESubstanceCompoundInfusion()
                        infusion.set_compound(compound)  # Pass string directly, not compound object
                        infusion.get_rate().set_value(rate, VolumePerTimeUnit.mL_Per_min)
                        infusion.get_bag_volume().set_value(bag_volume, VolumeUnit.mL)
                        pulse.process_action(infusion)
                        event_name = f"Compound({compound},{bag_volume}mL@{rate}mL/min)"
                    except Exception as e:
                        print(f"[Batch] Compound infusion error: {e}")

                elif etype == 'start_controller':
                    controller_name = event.get('controller', 'default_controller')

                    if controller_name == 'http_controller':
                        url = event.get('http_url', 'http://localhost:5001')
                        config = event.get('http_config', {})
                        timeout = event.get('http_timeout', 10.0)

                        # Build simulation context for concurrent batch identification
                        batch_id_for_controller = batch_config.get('batch_id', '')
                        simulation_context = {
                            'simulation_id': f"{batch_id_for_controller}_{job_id}" if batch_id_for_controller else job_id,
                            'batch_id': batch_id_for_controller,
                            'job_id': job_id
                        }

                        try:
                            controller = BatchHTTPController(url, config=config, timeout=timeout, simulation_context=simulation_context)
                            controller.send_init(patient_name, vent_settings)
                            controller_active = True
                            control_interval_s = controller.next_update_s
                            event_name = f"HTTPController({url})"
                        except Exception as e:
                            print(f"[Batch] HTTP Controller init failed: {e}")
                            event_name = f"HTTPController FAILED ({e})"
                    else:
                        # Built-in controller
                        controller = BatchBuiltinController(controller_name)
                        controller.send_init(patient_name, vent_settings)
                        controller_active = True
                        event_name = f"Controller({controller_name})"

                elif etype == 'stop_controller':
                    if controller_active:
                        controller_active = False
                        if controller:
                            controller.shutdown()
                        event_name = "Controller stopped"

                elif etype == 'start_fluid_controller':
                    fluid_controller_name = event.get('controller', 'default_fluid_controller')

                    if fluid_controller_name == 'http_fluid_controller':
                        # HTTP fluid controller
                        url = event.get('http_url', 'http://localhost:5001/fluid')
                        config = event.get('config', {})
                        timeout = event.get('timeout', 5.0)
                        batch_id_for_controller = batch_config.get('batch_id', '')
                        simulation_context = {
                            'simulation_id': f"{batch_id_for_controller}_{job_id}" if batch_id_for_controller else job_id,
                            'batch_id': batch_id_for_controller,
                            'job_id': job_id
                        }
                        try:
                            fluid_controller = BatchHTTPFluidController(url, config=config, timeout=timeout, simulation_context=simulation_context)
                            fluid_controller.send_init(patient_name, fluid_settings)
                            fluid_controller_active = True
                            fluid_control_interval_s = 10.0
                            event_name = f"HTTPFluidController({url})"
                        except Exception as e:
                            print(f"[Batch] HTTP Fluid Controller init failed: {e}")
                            event_name = f"HTTPFluidController FAILED ({e})"
                    else:
                        # Built-in fluid controller
                        fluid_controller = BatchBuiltinFluidController(fluid_controller_name)
                        fluid_controller.send_init(patient_name, fluid_settings)
                        fluid_controller_active = True
                        fluid_control_interval_s = 10.0
                        event_name = f"FluidController({fluid_controller_name})"

                elif etype == 'stop_fluid_controller':
                    if fluid_controller_active:
                        fluid_controller_active = False
                        # Stop any active infusions
                        fluid_settings['crystalloid_rate_ml_min'] = 0
                        fluid_settings['blood_rate_ml_min'] = 0
                        # Apply zero rates to stop infusions
                        for compound in ['Saline', 'Blood']:
                            try:
                                infusion = SESubstanceCompoundInfusion()
                                infusion.set_compound(compound)
                                infusion.get_rate().set_value(0, VolumePerTimeUnit.mL_Per_min)
                                infusion.get_bag_volume().set_value(0, VolumeUnit.mL)
                                pulse.process_action(infusion)
                            except:
                                pass
                        active_infusions.clear()
                        event_name = "FluidController stopped"

                if event_name:
                    current_events.append(event_name)
                    # Track event type for after_event triggers
                    if etype:
                        fired_event_names.add(etype)
                event_idx += 1

            # Join multiple events with semicolon
            event_annotation = "; ".join(current_events) if current_events else ""
            
            # Advance time
            pulse.advance_time_s(timestep)
            sim_time += timestep
            
            # Pull data
            results = pulse.pull_data()

            # Build vitals dict dynamically from selected variables
            batch_vitals = {"t": results[0]}
            for vi, var in enumerate(selected_vars):
                val = results[vi + 1]
                transform = var.get("transform")
                if transform == "multiply_100":
                    val = val * 100
                elif transform == "lactate_g_to_mmol":
                    val = val * 11.1
                batch_vitals[var["key"]] = val

            # Controller step - run PCLC if active
            controller_cmd = ""
            if controller_active and controller and (sim_time - last_control_time) >= control_interval_s:
                # Build data payload for controller
                controller_data = {"sim_time_s": sim_time}
                controller_data.update(batch_vitals)

                response = controller.step(controller_data, vent_settings)

                if response:
                    changes = []
                    for key in ['mode', 'vt_ml', 'rr', 'fio2', 'peep_cmh2o', 'pinsp_cmh2o', 'itime_s']:
                        if key in response:
                            old_val = vent_settings.get(key)
                            new_val = response[key]
                            if old_val != new_val:
                                if key == 'fio2':
                                    changes.append(f"FiO2:{old_val:.0%}->{new_val:.0%}")
                                elif key == 'mode':
                                    changes.append(f"Mode:{new_val}")
                                else:
                                    key_short = key.replace('_cmh2o', '').replace('_ml', '').replace('_s', '')
                                    changes.append(f"{key_short}:{old_val}->{new_val}")
                            vent_settings[key] = new_val

                    if changes:
                        controller_cmd = "; ".join(changes)

                    # Apply ventilator changes if vent is active
                    if vent_active:
                        vent = SEMechanicalVentilatorVolumeControl()
                        vent.set_connection(eSwitch.On)
                        vent.set_mode(eMechanicalVentilator_VolumeControlMode.AssistedControl)
                        vent.get_tidal_volume().set_value(vent_settings.get('vt_ml', 420), VolumeUnit.mL)
                        vent.get_respiration_rate().set_value(vent_settings.get('rr', 14), FrequencyUnit.Per_min)
                        vent.get_fraction_inspired_oxygen().set_value(vent_settings.get('fio2', 0.4))
                        vent.get_positive_end_expired_pressure().set_value(vent_settings.get('peep_cmh2o', 5), PressureUnit.cmH2O)
                        vent.get_inspiratory_period().set_value(vent_settings.get('itime_s', 1.0), TimeUnit.s)
                        vent.get_flow().set_value(vent_settings.get('flow_lpm', 50), VolumePerTimeUnit.L_Per_min)
                        pulse.process_action(vent)

                    # Update control interval from response
                    if 'next_interval_s' in response:
                        control_interval_s = max(0.1, response['next_interval_s'])

                last_control_time = sim_time

            # Fluid controller step - run if active
            fluid_controller_cmd = ""
            if fluid_controller_active and fluid_controller and (sim_time - last_fluid_control_time) >= fluid_control_interval_s:
                # Build vitals for fluid controller - HTTP controllers need sim_time
                if isinstance(fluid_controller, BatchHTTPFluidController):
                    fluid_vitals = {
                        "sim_time_s": sim_time,
                        "hr_bpm": batch_vitals.get("hr_bpm", 0),
                        "map_mmhg": batch_vitals.get("map_mmhg", 0),
                        "sbp_mmhg": batch_vitals.get("sbp_mmhg", 0),
                        "dbp_mmhg": batch_vitals.get("dbp_mmhg", 0),
                        "spo2_pct": batch_vitals.get("spo2_pct", 0),
                        "lactate_mmol_l": batch_vitals.get("lactate_mmol_l", 0),
                    }
                else:
                    fluid_vitals = batch_vitals

                fluid_response = fluid_controller.step(
                    fluid_vitals,
                    fluid_settings,
                    blood_loss_ml=cumulative_blood_loss_ml,
                    blood_infused_ml=cumulative_blood_infused_ml,
                    crystalloid_infused_ml=cumulative_crystalloid_infused_ml
                )

                if fluid_response:
                    changes = []

                    # Helper to check cancellation before potentially-blocking Pulse calls
                    def check_cancel_before_pulse():
                        if batch_id:
                            temp_dir = os.path.realpath(tempfile.gettempdir())
                            cancel_flag_path = os.path.join(temp_dir, f"pulse_batch_cancel_{batch_id}.flag")
                            return os.path.exists(cancel_flag_path)
                        return False

                    # Quick cancel check before applying infusions (which may block)
                    if check_cancel_before_pulse():
                        was_cancelled = True
                        break

                    # Apply crystalloid rate changes
                    new_crystalloid_rate = fluid_response.get('crystalloid_rate_ml_min', 0)
                    old_crystalloid_rate = fluid_settings.get('crystalloid_rate_ml_min', 0)
                    if new_crystalloid_rate != old_crystalloid_rate:
                        changes.append(f"Cryst:{old_crystalloid_rate}->{new_crystalloid_rate}mL/min")
                        # Apply crystalloid infusion
                        compound = fluid_settings.get('crystalloid_compound', 'Saline')
                        try:
                            infusion = SESubstanceCompoundInfusion()
                            infusion.set_compound(compound)
                            infusion.get_rate().set_value(new_crystalloid_rate, VolumePerTimeUnit.mL_Per_min)
                            infusion.get_bag_volume().set_value(10000, VolumeUnit.mL)
                            pulse.process_action(infusion)
                            if new_crystalloid_rate > 0:
                                active_infusions[compound] = {'rate': new_crystalloid_rate, 'remaining_ml': 10000, 'is_blood': False}
                            elif compound in active_infusions:
                                del active_infusions[compound]
                        except Exception as e:
                            print(f"[Batch] Crystalloid infusion error: {e}")

                    # Cancel check between infusions (before blood which may hang)
                    if check_cancel_before_pulse():
                        was_cancelled = True
                        break

                    # Apply blood rate changes
                    new_blood_rate = fluid_response.get('blood_rate_ml_min', 0)
                    old_blood_rate = fluid_settings.get('blood_rate_ml_min', 0)
                    if new_blood_rate != old_blood_rate:
                        changes.append(f"Blood:{old_blood_rate}->{new_blood_rate}mL/min")
                        # Apply blood infusion
                        compound = fluid_settings.get('blood_compound', 'Blood')
                        try:
                            infusion = SESubstanceCompoundInfusion()
                            infusion.set_compound(compound)
                            infusion.get_rate().set_value(new_blood_rate, VolumePerTimeUnit.mL_Per_min)
                            infusion.get_bag_volume().set_value(10000, VolumeUnit.mL)
                            pulse.process_action(infusion)
                            if new_blood_rate > 0:
                                active_infusions[compound] = {'rate': new_blood_rate, 'remaining_ml': 10000, 'is_blood': True}
                            elif compound in active_infusions:
                                del active_infusions[compound]
                        except Exception as e:
                            print(f"[Batch] Blood infusion error: {e}")

                    if changes:
                        fluid_controller_cmd = "; ".join(changes)

                    fluid_settings.update(fluid_response)
                    if 'next_interval_s' in fluid_response:
                        fluid_control_interval_s = max(1.0, fluid_response['next_interval_s'])

                last_fluid_control_time = sim_time

            # Blood loss tracking (from hemorrhage)
            total_flow_rate = sum(hemorrhage_flow_rates.values())
            blood_loss_this_step = total_flow_rate * (timestep / 60.0)
            cumulative_blood_loss_ml += blood_loss_this_step

            # Infusion tracking (for cumulative totals)
            for compound, info in list(active_infusions.items()):
                if info['remaining_ml'] > 0:
                    volume_this_step = info['rate'] * (timestep / 60.0)
                    actual_volume = min(volume_this_step, info['remaining_ml'])
                    info['remaining_ml'] -= actual_volume

                    if info['is_blood']:
                        cumulative_blood_infused_ml += actual_volume
                    else:
                        cumulative_crystalloid_infused_ml += actual_volume

                    if info['remaining_ml'] <= 0:
                        del active_infusions[compound]

            # Check conditional hemorrhage stops
            compartments_to_stop = []
            for compartment, condition in hemorrhage_stop_conditions.items():
                vital_name = condition["vital"]
                operator = condition["operator"]
                threshold = condition["value"]
                max_duration = condition["maxDurationSec"]
                start_time = condition["startTime"]

                current_value = batch_vitals.get(vital_name, 0)
                condition_met = False
                if operator == ">=" and current_value >= threshold:
                    condition_met = True
                elif operator == "<=" and current_value <= threshold:
                    condition_met = True
                elif operator == ">" and current_value > threshold:
                    condition_met = True
                elif operator == "<" and current_value < threshold:
                    condition_met = True

                # Also check max duration
                elapsed = sim_time - start_time
                if elapsed >= max_duration:
                    condition_met = True

                if condition_met:
                    compartments_to_stop.append((compartment, f"{vital_name} {operator} {threshold}"))

            # Stop hemorrhages that met their conditions
            for compartment, reason in compartments_to_stop:
                compartment_map = {
                    "RightLeg": eHemorrhage_Compartment.RightLeg,
                    "LeftLeg": eHemorrhage_Compartment.LeftLeg,
                    "RightArm": eHemorrhage_Compartment.RightArm,
                    "LeftArm": eHemorrhage_Compartment.LeftArm,
                    "Aorta": eHemorrhage_Compartment.Aorta,
                    "VenaCava": eHemorrhage_Compartment.VenaCava,
                }
                action = SEHemorrhage()
                action.set_compartment(compartment_map.get(compartment, eHemorrhage_Compartment.VenaCava))
                action.get_flow_rate().set_value(0, VolumePerTimeUnit.mL_Per_min)
                pulse.process_action(action)
                del hemorrhage_stop_conditions[compartment]
                stop_annotation = f"StopHemorrhage({compartment}, {reason})"
                if event_annotation:
                    event_annotation += "; " + stop_annotation
                else:
                    event_annotation = stop_annotation

            # Check triggered events (condition-based interventions)
            # First, check for any pending delayed triggers that are ready to fire
            events_ready_from_delay = []
            for event_id, fire_time in list(pending_delayed_triggers.items()):
                if sim_time >= fire_time:
                    # Find the event with this id
                    for event in triggered_events:
                        eid = event.get("id", id(event))
                        if eid == event_id:
                            events_ready_from_delay.append(event)
                            fired_trigger_ids.add(event_id)
                            break
                    del pending_delayed_triggers[event_id]

            # Now check all triggered events for new condition matches
            for event in triggered_events:
                event_id = event.get("id", id(event))

                # Skip if already fired or already pending delay
                if event_id in fired_trigger_ids:
                    continue
                if event_id in pending_delayed_triggers:
                    continue

                trigger = event.get("trigger")
                if not trigger:
                    continue

                condition_met = False

                # Check for after_event trigger (event-based)
                after_event = trigger.get("after_event")
                if after_event:
                    if after_event in fired_event_names:
                        condition_met = True
                else:
                    # Vital-based trigger
                    vital_name = trigger.get("vital")
                    operator = trigger.get("operator")
                    threshold = trigger.get("value")

                    if vital_name and operator and threshold is not None:
                        current_value = batch_vitals.get(vital_name, 0)
                        if operator == ">=" and current_value >= threshold:
                            condition_met = True
                        elif operator == "<=" and current_value <= threshold:
                            condition_met = True
                        elif operator == ">" and current_value > threshold:
                            condition_met = True
                        elif operator == "<" and current_value < threshold:
                            condition_met = True

                if condition_met:
                    delay_s = trigger.get("delay_s", 0)
                    if delay_s > 0:
                        # Schedule for later firing
                        pending_delayed_triggers[event_id] = sim_time + delay_s
                    else:
                        # Fire immediately
                        events_ready_from_delay.append(event)
                        fired_trigger_ids.add(event_id)

            # Process all events that are ready to fire (from delay or immediate)
            for event in events_ready_from_delay:
                event_id = event.get("id", id(event))
                trigger = event.get("trigger", {})

                # Build trigger description based on trigger type
                after_event = trigger.get("after_event")
                delay_s = trigger.get("delay_s", 0)
                if after_event:
                    trigger_desc = f"after:{after_event}"
                    if delay_s > 0:
                        trigger_desc += f"+{delay_s}s"
                else:
                    vital_name = trigger.get("vital")
                    operator = trigger.get("operator")
                    threshold = trigger.get("value")
                    trigger_desc = f"{vital_name} {operator} {threshold}"
                    if delay_s > 0:
                        trigger_desc += f"+{delay_s}s delay"

                    # Process the triggered event - same logic as time-based events
                    etype = event.get('type', '')
                    triggered_event_name = ""

                    if etype == 'start_controller':
                        controller_name = event.get('controller', 'default_controller')
                        if controller_name == 'http_controller':
                            url = event.get('http_url', 'http://localhost:5001')
                            config = event.get('config', {})
                            timeout = event.get('timeout', 5.0)
                            batch_id_for_controller = batch_config.get('batch_id', '')
                            simulation_context = {
                                'simulation_id': f"{batch_id_for_controller}_{job_id}" if batch_id_for_controller else job_id,
                                'batch_id': batch_id_for_controller,
                                'job_id': job_id
                            }
                            try:
                                controller = BatchHTTPController(url, config=config, timeout=timeout, simulation_context=simulation_context)
                                controller.send_init(patient_name, vent_settings)
                                controller_active = True
                                control_interval_s = 10.0
                                triggered_event_name = f"HTTPController({url})"
                            except Exception as e:
                                print(f"[Batch] HTTP Controller init failed: {e}")
                                triggered_event_name = f"HTTPController FAILED ({e})"
                        else:
                            controller = BatchBuiltinController(controller_name)
                            controller_active = True
                            control_interval_s = 10.0
                            triggered_event_name = f"Controller({controller_name})"

                    elif etype == 'start_fluid_controller':
                        fluid_controller_name = event.get('controller', 'default_fluid_controller')
                        if fluid_controller_name == 'http_fluid_controller':
                            url = event.get('http_url', 'http://localhost:5001/fluid')
                            config = event.get('config', {})
                            timeout = event.get('timeout', 5.0)
                            batch_id_for_controller = batch_config.get('batch_id', '')
                            simulation_context = {
                                'simulation_id': f"{batch_id_for_controller}_{job_id}" if batch_id_for_controller else job_id,
                                'batch_id': batch_id_for_controller,
                                'job_id': job_id
                            }
                            try:
                                fluid_controller = BatchHTTPFluidController(url, config=config, timeout=timeout, simulation_context=simulation_context)
                                fluid_controller.send_init(patient_name, fluid_settings)
                                fluid_controller_active = True
                                fluid_control_interval_s = 10.0
                                triggered_event_name = f"HTTPFluidController({url})"
                            except Exception as e:
                                print(f"[Batch] HTTP Fluid Controller init failed: {e}")
                                triggered_event_name = f"HTTPFluidController FAILED ({e})"
                        else:
                            fluid_controller = BatchBuiltinFluidController(fluid_controller_name)
                            fluid_controller.send_init(patient_name, fluid_settings)
                            fluid_controller_active = True
                            fluid_control_interval_s = 10.0
                            triggered_event_name = f"FluidController({fluid_controller_name})"

                    elif etype == 'stop_fluid_controller':
                        if fluid_controller_active:
                            fluid_controller_active = False
                            fluid_settings['crystalloid_rate_ml_min'] = 0
                            fluid_settings['blood_rate_ml_min'] = 0
                            for compound in ['Saline', 'Blood']:
                                try:
                                    infusion = SESubstanceCompoundInfusion()
                                    infusion.set_compound(compound)
                                    infusion.get_rate().set_value(0, VolumePerTimeUnit.mL_Per_min)
                                    infusion.get_bag_volume().set_value(0, VolumeUnit.mL)
                                    pulse.process_action(infusion)
                                except:
                                    pass
                            triggered_event_name = "StopFluidController"

                    elif etype == 'intubate':
                        intubation_type = event.get('intubationType', 'Tracheal')
                        type_map = {
                            'Tracheal': eIntubationType.Tracheal,
                            'RightMainstem': eIntubationType.RightMainstem,
                            'LeftMainstem': eIntubationType.LeftMainstem,
                            'Esophageal': eIntubationType.Esophageal,
                            'Oropharyngeal': eIntubationType.Oropharyngeal,
                            'Nasopharyngeal': eIntubationType.Nasopharyngeal,
                        }
                        intubation = SEIntubation()
                        intubation.set_type(type_map.get(intubation_type, eIntubationType.Tracheal))
                        pulse.process_action(intubation)
                        is_intubated = (intubation_type != 'Off')
                        triggered_event_name = f"Intubate({intubation_type})"

                    elif etype == 'start_vent':
                        evt_vent_settings = event.get('vent_settings', vent_settings)
                        vent = SEMechanicalVentilatorVolumeControl()
                        vent.set_connection(eSwitch.On)
                        vent.set_mode(eMechanicalVentilator_VolumeControlMode.AssistedControl)
                        vent.get_tidal_volume().set_value(evt_vent_settings.get('vt_ml', 420), VolumeUnit.mL)
                        vent.get_respiration_rate().set_value(evt_vent_settings.get('rr', 14), FrequencyUnit.Per_min)
                        vent.get_fraction_inspired_oxygen().set_value(evt_vent_settings.get('fio2', 0.4))
                        vent.get_positive_end_expired_pressure().set_value(evt_vent_settings.get('peep_cmh2o', 5), PressureUnit.cmH2O)
                        vent.get_inspiratory_period().set_value(evt_vent_settings.get('itime_s', 1.0), TimeUnit.s)
                        vent.get_flow().set_value(evt_vent_settings.get('flow_lpm', 50), VolumePerTimeUnit.L_Per_min)
                        pulse.process_action(vent)
                        vent_active = True
                        vent_settings.update(evt_vent_settings)
                        triggered_event_name = "StartVent"

                    elif etype == 'change_vent':
                        evt_vent_settings = event.get('vent_settings', {})
                        if evt_vent_settings:
                            vent = SEMechanicalVentilatorVolumeControl()
                            vent.set_connection(eSwitch.On)
                            vent.set_mode(eMechanicalVentilator_VolumeControlMode.AssistedControl)
                            vent.get_tidal_volume().set_value(evt_vent_settings.get('vt_ml', 420), VolumeUnit.mL)
                            vent.get_respiration_rate().set_value(evt_vent_settings.get('rr', 14), FrequencyUnit.Per_min)
                            vent.get_fraction_inspired_oxygen().set_value(evt_vent_settings.get('fio2', 0.4))
                            vent.get_positive_end_expired_pressure().set_value(evt_vent_settings.get('peep_cmh2o', 5), PressureUnit.cmH2O)
                            vent.get_inspiratory_period().set_value(evt_vent_settings.get('itime_s', 1.0), TimeUnit.s)
                            vent.get_flow().set_value(evt_vent_settings.get('flow_lpm', 50), VolumePerTimeUnit.L_Per_min)
                            pulse.process_action(vent)
                            vent_settings.update(evt_vent_settings)
                            triggered_event_name = "ChangeVent"

                    elif etype == 'bolus':
                        drug_name = event.get('drug', 'Rocuronium')
                        dose_mode = event.get('dose_mode', 'fixed')
                        concentration = float(event.get('concentration', 10))
                        conc_unit = event.get('concentration_unit', 'mg/mL')

                        # Calculate dose based on mode
                        if dose_mode == 'weight':
                            dose_per_kg = float(event.get('dose_per_kg', 0.5))
                            dose_per_kg_unit = event.get('dose_per_kg_unit', 'mg/kg')

                            if dose_per_kg_unit in ('ug/kg', 'mcg/kg'):
                                total_mass_mg = (dose_per_kg / 1000.0) * patient_weight_kg
                            else:
                                total_mass_mg = dose_per_kg * patient_weight_kg

                            if conc_unit == 'mg/mL':
                                conc_mg_per_mL = concentration
                            elif conc_unit == 'ug/mL':
                                conc_mg_per_mL = concentration / 1000.0
                            elif conc_unit == 'g/L':
                                conc_mg_per_mL = concentration
                            else:
                                conc_mg_per_mL = concentration

                            dose_mL = total_mass_mg / conc_mg_per_mL if conc_mg_per_mL > 0 else 1.0
                            dose_desc = f"{dose_per_kg}{dose_per_kg_unit} ({patient_weight_kg:.1f}kg)"
                        else:
                            dose_mL = float(event.get('dose_mL', 5))
                            if conc_unit == 'mg/mL':
                                total_mass_mg = dose_mL * concentration
                            elif conc_unit == 'ug/mL':
                                total_mass_mg = dose_mL * concentration / 1000.0
                            elif conc_unit == 'g/L':
                                total_mass_mg = dose_mL * concentration
                            else:
                                total_mass_mg = dose_mL * concentration
                            dose_desc = f"{total_mass_mg:.1f}mg"

                        if conc_unit == 'mg/mL':
                            conc_g_L = concentration
                        elif conc_unit == 'ug/mL':
                            conc_g_L = concentration / 1000.0
                        elif conc_unit == 'g/L':
                            conc_g_L = concentration
                        else:
                            conc_g_L = concentration

                        try:
                            infusion = SESubstanceInfusion()
                            infusion.set_comment(f"Bolus delivery of {drug_name}")
                            infusion.set_substance(drug_name)
                            infusion.get_rate().set_value(dose_mL * 60.0, VolumePerTimeUnit.mL_Per_min)
                            infusion.get_concentration().set_value(conc_g_L, MassPerVolumeUnit.from_string("g/L"))
                            pulse.process_action(infusion)
                            triggered_event_name = f"Bolus({drug_name},{dose_desc})"
                        except Exception as e:
                            triggered_event_name = f"Bolus FAILED ({e})"

                    elif etype == 'infusion':
                        drug_name = event.get('drug', 'Norepinephrine')
                        concentration = event.get('concentration', 0.004)
                        rate_ml_per_hr = event.get('rate_ml_per_hr', 10)
                        try:
                            infusion = SESubstanceInfusion()
                            infusion.set_substance(drug_name)
                            infusion.get_concentration().set_value(concentration, MassPerVolumeUnit.mg_Per_mL)
                            infusion.get_rate().set_value(rate_ml_per_hr, VolumePerTimeUnit.mL_Per_hr)
                            pulse.process_action(infusion)
                            triggered_event_name = f"Infusion({drug_name},{rate_ml_per_hr}mL/hr)"
                        except Exception as e:
                            triggered_event_name = f"Infusion FAILED ({e})"

                    elif etype == 'compound_infusion':
                        compound = event.get('compound', 'Saline')
                        rate_ml_per_min = event.get('rate_ml_per_min', 10)
                        try:
                            infusion = SESubstanceCompoundInfusion()
                            infusion.set_compound(compound)
                            infusion.get_rate().set_value(rate_ml_per_min, VolumePerTimeUnit.mL_Per_min)
                            infusion.get_bag_volume().set_value(500, VolumeUnit.mL)
                            pulse.process_action(infusion)
                            triggered_event_name = f"CompoundInfusion({compound},{rate_ml_per_min}mL/min)"
                        except Exception as e:
                            triggered_event_name = f"CompoundInfusion FAILED ({e})"

                    else:
                        triggered_event_name = f"{etype}"

                    # Build the full triggered annotation
                    trigger_annotation = f"TRIGGERED[{trigger_desc}]: {triggered_event_name}"
                    if event_annotation:
                        event_annotation += "; " + trigger_annotation
                    else:
                        event_annotation = trigger_annotation

                    # Track event type for after_event triggers (enables chaining)
                    if etype:
                        fired_event_names.add(etype)

            # Check for patient death via event handler
            if event_handler.is_dead and not patient_dead:
                patient_dead = True
                death_msg = f"PATIENT_DEATH ({event_handler.death_cause})"
                if event_annotation:
                    event_annotation += "; " + death_msg
                else:
                    event_annotation = death_msg

            # Fallback: also check vitals for death (HR=0, MAP<10, or CO=0)
            if not patient_dead:
                hr = batch_vitals.get("hr_bpm", 60)
                map_val = batch_vitals.get("map_mmhg", 70)
                co = batch_vitals.get("co_lpm", 5)
                if hr < 1 or map_val < 5 or co < 0.1:
                    patient_dead = True
                    if event_annotation:
                        event_annotation += "; PATIENT_DEATH (vitals)"
                    else:
                        event_annotation = "PATIENT_DEATH (vitals)"

            # Build CSV row dynamically
            row = [batch_vitals["t"]]
            row.extend([batch_vitals.get(v["key"], "") for v in selected_vars])
            row.extend([
                vent_settings.get('mode', 'VC-AC'),
                vent_settings.get('vt_ml', 420),
                vent_settings.get('rr', 14),
                vent_settings.get('fio2', 0.4),
                vent_settings.get('peep_cmh2o', 5),
                vent_settings.get('pinsp_cmh2o', ''),
                vent_settings.get('itime_s', 1.0),
                1 if is_intubated else 0,
                1 if vent_active else 0,
                1 if controller_active else 0,
                1 if fluid_controller_active else 0,
                round(cumulative_blood_loss_ml, 1),
                round(cumulative_blood_infused_ml, 1),
                round(cumulative_crystalloid_infused_ml, 1),
                fluid_settings.get('crystalloid_rate_ml_min', 0),
                fluid_settings.get('blood_rate_ml_min', 0),
                event_annotation,
                controller_cmd,
                fluid_controller_cmd
            ])
            writer.writerow(row)
        
        # Add summary note at end of CSV if patient died
        if patient_dead and event_handler:
            writer.writerow([])  # Empty row
            writer.writerow(["# SIMULATION SUMMARY"])
            if event_handler.is_dead:
                writer.writerow([f"# Patient Status: DECEASED - {event_handler.death_cause}"])
                writer.writerow([f"# Time of Death: {event_handler.death_time_s:.1f}s"])
            else:
                writer.writerow(["# Patient Status: DECEASED (vitals-based detection)"])
            if event_handler.event_log:
                writer.writerow(["# Critical Events:"])
                for time_s, event_name, active in event_handler.event_log:
                    status = "ONSET" if active else "RESOLVED"
                    writer.writerow([f"#   {time_s:.1f}s - {event_name} ({status})"])

        # Log end of simulation loop
        # Shutdown controllers if active
        if controller:
            controller.shutdown()
        if fluid_controller:
            fluid_controller.shutdown()

        # Save CSV - use safe name for file with replicate suffix
        safe_csv_name = patient_name.replace('@0s.json', '').replace(' ', '_')
        csv_path = os.path.join(output_dir, f"{safe_csv_name}{replicate_suffix}.csv")
        with open(csv_path, 'w', newline='') as f:
            f.write(csv_buffer.getvalue())

        pulse.clear()

        #strip patient id from patient name
        patient_id = patient_name.split('_', 1)[1]

        #save to database
        insert_batch(experiment_id=batch_config['experiment_id'], patient_id=patient_id, raw_csv_path=csv_path)

        # Return cancelled status if we were cancelled
        if was_cancelled:
            return {
                'job_id': job_id,
                'patient': job_id,
                'patient_name': patient_name,
                'is_custom': is_custom,
                'status': 'cancelled',
                'csv_path': csv_path,  # Still provide partial CSV
                'duration': sim_time,  # Actual time completed
                'message': f'Cancelled at {sim_time:.1f}s of {duration_s}s'
            }

        return {
            'job_id': job_id,  # Unique ID including replicate suffix
            'patient': job_id,  # Legacy compatibility
            'patient_name': patient_name,
            'is_custom': is_custom,
            'status': 'complete',
            'csv_path': csv_path,
            'duration': duration_s
        }

    except Exception as e:
        import traceback
        return {
            'job_id': job_id,
            'patient': job_id,  # Legacy compatibility
            'patient_name': patient_name,
            'is_custom': is_custom,
            'status': 'error',
            'message': str(e),
            'traceback': traceback.format_exc()
        }


def run_batch_thread(batch_id, batch):
    """
    Run a batch of patients in parallel using multiprocessing.Pool.

    Uses imap_unordered for better progress visibility - results are
    yielded as each patient completes rather than waiting for all.

    Supports replicates: if replicates > 1, each patient is run multiple times
    with output files suffixed _r1, _r2, etc.
    """
    print(f"[BATCH] run_batch_thread started for {batch_id}")

    # Initialize batch status in global dictionary to avoid KeyError during update
    with batch_lock:
        batches[batch_id] = {
            'status': 'running',
            'message': 'Batch started',
            'patients': {},
            'created_at': datetime.now().isoformat(),
            'started_at': datetime.now().isoformat(),
            'completed_count': 0,
            'total_count': 0,
            'batch_dir': None,
            'zip_path': None,
        }

    # extract demographic info from batch config
    demographics = batch.get('demographics', [])
    demographic_map = {
        'soldier': SOLDIER,
        'adult': ADULT
    }
    patients = []

    #convert percentages to counts
    total_patients = batch.get('patient_count', 0)
    counts = allocate_counts(total_patients, demographics)

    #add count to demographic specs
    for demo_spec, count in zip(demographics, counts):
        demo_spec['count'] = count

    #draw patients from database
    for demo_spec in demographics:
        demo_obj = demographic_map.get(demo_spec['name'])
        if demo_obj is None:
            print(f"[Batch] Warning: Unknown demographic '{demo_spec['name']}' - skipping database draw for this group")
            continue
        
        drawn = get_patients_by_demographic(demo_obj.demo_name, demo_spec.get('count', 0))
        for row in drawn:
            patients.append({
                'name': f"{row['demographic_group']}_{row['patient_id']}",
                'json': None,
                'id': row['patient_id']
            })
        demo_spec['count'] -= len(drawn)

    #generate patients if not enough patients in database match criteria
    generator = PatientGenerator(random.seed())
    generated_patients = []
    for demo_spec in demographics:
        demo_name = demo_spec.get('name')
        count = demo_spec.get('count', 0)
        demo_obj = demographic_map.get(demo_name)
        if demo_obj and count > 0:
            generated_patients += generator.generate_cohort(count, demo_obj)
        elif not demo_obj:
            print(f"[Batch] Warning: Unknown demographic '{demo_name}' - skipping generation for this group")

    # Stabilize patients in parallel
    if generated_patients:
        num_workers = batch.get('workers', None)
        if num_workers is None:
            num_workers = max(1, (os.cpu_count() or 4) - 1)
        print(f"\nStabilizing {len(generated_patients)} patients with {num_workers} workers...")
        print(f"Estimated time: {len(generated_patients) * 2.5 / num_workers:.0f}-{len(generated_patients) * 3.5 / num_workers:.0f} minutes\n")
        
        # Prepare arguments for worker processes
        output_dir = PATIENTS_FOLDER
        work_items = [
            (asdict(profile), output_dir, PULSE_BIN, PULSE_PYTHON, profile.demographic.demo_name)
            for profile in generated_patients
        ]
        
        # Run stabilization
        from multiprocessing import freeze_support
        freeze_support()
        
        results = []
        completed = 0
        failed = 0
        
        with ProcessPool(num_workers) as pool:
            for result in pool.imap_unordered(stabilize_patient, work_items):
                completed += 1
                if result['status'] == 'success':
                    print(f"  [{completed}/{len(generated_patients)}] OK {result['name']}")
                else:
                    failed += 1
                    print(f"  [{completed}/{len(generated_patients)}] FAIL {result['name']}: {result.get('message', 'Unknown error')}")
                results.append(result)

        #add generated patients to cohort
        for r in results:
            if r['status'] == 'success':
                patients.append({
                    'name': r['name'],
                    'json': None,  # Stable state is on disk under PATIENTS_FOLDER (e.g. name@0s.json)
                    'id': r.get('id')
                })

    # Create output directory
    batch_dir = os.path.join(EXPERIMENT_RESULTS_FOLDER, f"batch_{batch_id}")
    os.makedirs(batch_dir, exist_ok=True)

    #create experiment and insert into database
    experiment = Experiment.from_json(batch, patients, batch_dir, batch_id)
    insert_experiment_from_object(experiment)

    workers = batch.get('workers', max(1, (os.cpu_count() or 4) - 1))
    total_jobs = len(patients)
    
    if len(patients) == 0:
        with batch_lock:
            batches[batch_id]['status'] = 'error'
            batches[batch_id]['message'] = 'No patients selected'
        print(f"[BATCH] {batch_id}: No patients selected!")
        return

    # Cap workers at CPU count and total job count
    max_workers = os.cpu_count() or 4
    workers = min(workers, max_workers, len(patients)) if len(patients) > 0 else 1

    # Initialize job progress tracking (patient x replicate combinations)
    with batch_lock:
        #batches[batch_id]['replicates'] = replicates
        batches[batch_id]['patient_count'] = len(patients)
        batches[batch_id]['total_jobs'] = len(patients)

        for p in patients:
            patient_name = p['name'] if isinstance(p, dict) else p
            job_id = patient_name
            batches[batch_id]['patients'][job_id] = {
                'status': 'queued',
                'sim_time': 0,
                'duration': experiment.simulation_duration,
                'is_custom': True,  # Newly generated patients are pre-stabilized (custom=state file)
                'base_patient': patient_name
            }
    
    try:
        # Prepare batch config (without patients list)
        # Include PULSE_BIN and PULSE_PYTHON so worker processes know where to chdir and import from
        # v6: start_intubated defaults to False - use events for intubation/ventilation
        batch_config = {
            'batch_id': batch_id,  # For HTTP controller concurrent identification
            'duration_s': experiment.simulation_duration,
            'sample_rate_hz': batch.get('sample_rate_hz', 50),
            'start_intubated': batch.get('start_intubated', False),
            'vent_settings': batch.get('vent_settings', {}),
            'events': experiment.events,
            'pulse_bin': PULSE_BIN,
            'pulse_python': PULSE_PYTHON,
            'output_columns': experiment.output_columns,
            'available_variables': AVAILABLE_VARIABLES,
            'experiment_id': experiment.experiment_id,
        }

        # Clear any stale cancel flag for this batch (file-based)
        clear_batch_cancel_flag(batch_id)

        # Create argument tuples for each patient x replicate combination
        # Pre-stabilized: pass filename string
        # Custom: pass dict with {name, json}
        # Include replicate info for file naming
        # Cancellation is checked via file-based flag, not passed in args
        patient_args = []
        for p in patients:
            # p is now a dict with name, state_path, id
            patient_name = p['name'] if isinstance(p, dict) else p
            job_id = patient_name
            config = batch_config.copy()
            patient_args.append((p, config, batch_dir, job_id))

        # Run with ProcessPool using apply_async for non-blocking cancellation support
        print(f"Starting batch {batch_id} with {workers} workers for {total_jobs} jobs")

        csv_paths = {}
        completed = 0
        cancelled = False

        with ProcessPool(processes=workers) as pool:
            # Submit all jobs asynchronously
            async_results = []
            for args in patient_args:
                async_results.append(pool.apply_async(run_single_patient, (args,)))

            # Poll for results with periodic cancel checks
            pending_results = list(enumerate(async_results))
            cancel_grace_period_start = None
            CANCEL_GRACE_PERIOD_S = 15  # Give workers 15 seconds to save partial results

            while pending_results:
                # Check for cancellation every iteration (roughly every 0.5s)
                if batch_cancel_flags.get(batch_id):
                    if cancel_grace_period_start is None:
                        # First time noticing cancellation - start grace period
                        cancel_grace_period_start = time.time()
                        print(f"[BATCH] Cancellation requested for {batch_id}, waiting up to {CANCEL_GRACE_PERIOD_S}s for {len(pending_results)} jobs to save partial results...")
                    elif time.time() - cancel_grace_period_start > CANCEL_GRACE_PERIOD_S:
                        # Grace period expired - force terminate
                        print(f"[BATCH] Grace period expired, terminating {len(pending_results)} remaining jobs...")
                        pool.terminate()
                        cancelled = True
                        break

                # Check each pending result with a short timeout
                still_pending = []
                for idx, async_result in pending_results:
                    try:
                        # Try to get result with short timeout
                        result = async_result.get(timeout=0.1)

                        # Process the result
                        job_id = result['job_id']
                        status = result['status']

                        with batch_lock:
                            if job_id in batches[batch_id]['patients']:
                                batches[batch_id]['patients'][job_id]['status'] = status
                                if status == 'complete':
                                    batches[batch_id]['patients'][job_id]['csv_path'] = result['csv_path']
                                    batches[batch_id]['patients'][job_id]['sim_time'] = result['duration']
                                    csv_paths[job_id] = result['csv_path']
                                elif status == 'cancelled':
                                    batches[batch_id]['patients'][job_id]['message'] = result.get('message', 'Cancelled')
                                    if result.get('csv_path'):
                                        csv_paths[job_id] = result['csv_path']
                                    print(f"[BATCH] Job {job_id} saved partial results: {result.get('message', '')}")
                                else:
                                    batches[batch_id]['patients'][job_id]['message'] = result.get('message', 'Unknown error')
                                    print(f"[ERROR] Job {job_id} failed:")
                                    print(f"  Message: {result.get('message', 'Unknown')}")
                                    if 'traceback' in result:
                                        print(f"  Traceback:\n{result['traceback']}")

                        completed += 1
                        print(f"Batch {batch_id}: {result.get('patient_name', job_id)} {status} ({completed}/{total_jobs})")

                    except MPTimeoutError:
                        # Result not ready yet, keep it in pending list
                        still_pending.append((idx, async_result))
                    except Exception as e:
                        # Job raised an exception
                        completed += 1
                        import traceback
                        print(f"[ERROR] Job raised exception: {e}")
                        print(f"[ERROR] Traceback: {traceback.format_exc()}")

                pending_results = still_pending

                # If we're in grace period and all jobs have finished, we're done
                if cancel_grace_period_start is not None and not pending_results:
                    cancelled = True
                    print(f"[BATCH] All jobs saved partial results")
                    break

                # Small sleep to prevent busy-waiting
                if pending_results:
                    time.sleep(0.1)

        # Clean up cancel flags (both thread-level and file-based)
        if batch_id in batch_cancel_flags:
            del batch_cancel_flags[batch_id]
        clear_batch_cancel_flag(batch_id)

    except Exception as e:
        import traceback
        with batch_lock:
            batches[batch_id]['status'] = 'error'
            batches[batch_id]['message'] = str(e)
            batches[batch_id]['traceback'] = traceback.format_exc()
        print(f"Batch {batch_id} failed: {e}")

    # --- ANALYSIS PHASE ---

    #get a list of all completed csv paths
    completed_csv_paths = [p for job, p in csv_paths.items() 
                            if batches[batch_id]['patients'][job]['status'] == 'complete']
    
    #build dataframes for analysis
    dfs = []
    for path in completed_csv_paths:
        df = pd.read_csv(path)

        #round timestamps to nearest millisecond
        df['sim_time_s'] = df['sim_time_s'].round(3)

        dfs.append(df)

    #concatenate all dataframes into one
    all_data = pd.DataFrame()
    if dfs:
        all_data = pd.concat(dfs, ignore_index=True)

    mean_df = all_data.groupby('sim_time_s').mean(numeric_only=True).reset_index()

    #save mean csv to database and filesystem
    mean_df.to_csv(str(ANALYSIS_RESULTS_FOLDER / f"batch_{batch_id}_mean.csv"),index=False)
    experiment.mean_csv_path = str(ANALYSIS_RESULTS_FOLDER / f"batch_{batch_id}_mean.csv")

    #update experiment in database with mean csv path
    update_experiment_from_object(experiment)

    #get controller start time
    start_time_df = pd.read_csv(completed_csv_paths[0])
    start_time_df['sim_time_s'] = start_time_df['sim_time_s'].round(3)

    #find first activation timestamp
    active_mask = (start_time_df['controller_active'] == 1) | (start_time_df['fluid_controller_active'] == 1)

    if active_mask.any():
        controller_start_time = float(start_time_df.loc[active_mask, 'sim_time_s'].iloc[0])
    else:
        controller_start_time = 0.0

    #do analysis of each desired metric
    metrics_list = []

    target_metrics = batch.get('target_metrics', {})
    metric_keys = [k for k in target_metrics.keys() if k in mean_df.columns]

    if not metric_keys:
        return []

    # Extract matrix of values (N timesteps x M metrics)
    values_matrix = mean_df[metric_keys].to_numpy(dtype=float)  # shape: (N, M)
    sim_time = mean_df['sim_time_s'].to_numpy(dtype=float)

    dt = sim_time[1] - sim_time[0]

    # Build target + tolerance arrays aligned with columns
    target_values = np.array([target_metrics[k]['target_value'] for k in metric_keys])
    tolerances = np.array([target_metrics[k]['tolerance'] for k in metric_keys])

    lower_bounds = target_values - tolerances
    upper_bounds = target_values + tolerances

    # --- Vectorized calculations ---

    # Mean & std (per column)
    means = values_matrix.mean(axis=0)
    stds = values_matrix.std(axis=0)

    # Mean absolute error (broadcast target_values across rows)
    mae = np.abs(values_matrix - target_values).mean(axis=0)

    # Masks
    within_target = (values_matrix >= lower_bounds) & (values_matrix <= upper_bounds)

    after_start = sim_time >= controller_start_time
    after_start_mask = after_start[:, None]  # reshape for broadcasting

    valid_mask = within_target & after_start_mask

    # Time calculations
    time_within_target = valid_mask.sum(axis=0) * dt
    percent_time_within_target = valid_mask.sum(axis=0) / after_start.sum() * 100

    # --- Build Metric objects ---
    for i, vital_sign in enumerate(metric_keys):
        col = values_matrix[:, i]
        col_after = col[after_start]
        time_after = sim_time[after_start]

        wobble, divergence = compute_wobble_divergence(time_after, col_after, target_values[i])

        metric_obj = Metric(
            experiment_id=experiment.experiment_id,
            vital_sign_measured=vital_sign,
            mean_absolute_error=mae[i],
            controller_start_time=controller_start_time,
            mean=means[i],
            std_dev=stds[i],
            target_value=target_values[i],
            tolerance=tolerances[i],
            time_within_target_range=time_within_target[i],
            percent_time_within_target_range=percent_time_within_target[i],
            wobble=wobble,
            divergence=divergence
        )

        #check matching function
        expr_str = target_metrics[vital_sign].get('matching_function', None)
        if expr_str:
            try:
                func = parse_matching_function(expr_str)
                transformed = func(col, sim_time)
                #only analyze data after controller start time
                transformed_after = transformed[after_start]
                matching_mae = float(np.abs(col_after - transformed_after).mean())
                metric_obj.matching_function = expr_str
                metric_obj.matching_function_mae = matching_mae
            except ValueError as e:
                # Log and continue — don't let a bad expression break analysis
                print(f"Warning: could not evaluate matching_function for {vital_sign}: {e}")

        metrics_list.append(metric_obj)

    # Insert metrics into database
    for metric in metrics_list:
        insert_metric_from_object(metric)

