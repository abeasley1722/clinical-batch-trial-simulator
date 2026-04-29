
"""
============================================================
Author:        Jared Garcia
Updated By:    Anointiyae Beasley
Description:   Retrieval API for querying experiment results.
               Optimized to support:
                 - Core vitals by default
                 - Group-based column selection
                 - "all" keyword for full dataset
============================================================
"""

import pandas as pd
from core.src.database.metric import (
    get_runs_by_experiment,
    get_runs_by_controller,
    get_latest_run_per_controller,
    get_metrics_by_experiment,
    get_metrics_by_run,
)
from core.src.database.batch import get_batches_by_experiment
from core.src.database.experiment import get_experiment, get_experiment_csv


# ========================
# COLUMN GROUPS
# ========================

CORE_VITALS = [
    "sim_time_s",
    "hr_bpm",
    "spo2_pct",
    "rr_patient",
    "sbp_mmhg",
    "dbp_mmhg",
    "map_mmhg",
    "skin_temp_c"
]

COLUMN_GROUPS = {
    "vitals": CORE_VITALS,

    "gases": [
        "pao2_mmhg",
        "paco2_mmhg",
        "etco2_mmhg",
        "ph",
        "lactate_mmol_L",
        "hematocrit_pct"
    ],

    "circulation": [
        "co_lpm",
        "blood_volume_ml",
        "blood_loss_ml",
        "blood_infused_ml",
        "crystalloid_infused_ml"
    ],

    "respiratory": [
        "vt_patient_ml",
        "total_lung_volume_ml",
        "total_pulm_ventilation_lpm"
    ],

    "ventilator": [
        "rr_vent",
        "vt_vent_ml",
        "pip_cmh2o",
        "pplat_cmh2o",
        "paw_mean_cmh2o",
        "total_peep_cmh2o",
        "ie_ratio"
    ],

    "airflow": [
        "insp_flow_lpm",
        "exp_flow_lpm",
        "peak_insp_flow_lpm",
        "airway_pressure_cmh2o"
    ],

    "compliance": [
        "resp_compliance_ml_cmh2o",
        "static_compliance_ml_cmh2o"
    ],

    "tidal": [
        "insp_vt_ml",
        "exp_vt_ml"
    ],

    "controller": [
        "cmd_vt_ml",
        "cmd_rr",
        "cmd_fio2",
        "cmd_peep_cmh2o",
        "cmd_pinsp_cmh2o",
        "cmd_itime_s",
        "cmd_crystalloid_rate",
        "cmd_blood_rate",
        "controller_cmd",
        "fluid_cmd"
    ],

    "states": [
        "is_intubated",
        "vent_active",
        "controller_active",
        "fluid_controller_active"
    ]
}


# ========================
# HELPER: RESOLVE COLUMNS
# ========================

def resolve_columns(selection=None):
    """
    selection:
        - None → core vitals only
        - ["gases", "ventilator"] → specific groups
        - ["all"] → everything
        - ["hr_bpm", "spo2_pct"] → specific columns
    """

    # Always include time
    selected = set(["sim_time_s"])

    # Default → core vitals
    if not selection:
        selected.update(CORE_VITALS)
        return list(selected)

    # Normalize
    if isinstance(selection, str):
        selection = [selection]

    # Handle "all"
    if "all" in selection:
        all_cols = set()
        for group in COLUMN_GROUPS.values():
            all_cols.update(group)
        all_cols.update(CORE_VITALS)
        return list(all_cols)

    # Otherwise resolve groups + individual columns
    selected.update(CORE_VITALS)

    for item in selection:
        if item in COLUMN_GROUPS:
            selected.update(COLUMN_GROUPS[item])
        else:
            # assume it's a column name
            selected.add(item)

    return list(selected)


# ========================
# DATAFRAME RETRIEVAL
# ========================

def get_raw_csv_dataframe(experiment_id, selection=None):
    """
    Load CSV and return filtered DataFrame.

    selection:
        None → core vitals
        ["gases"] → group
        ["hr_bpm"] → column
        ["all"] → everything
    """

    csv_path = get_experiment_csv(experiment_id)

    if not csv_path:
        print(f"No CSV found for experiment {experiment_id}")
        return pd.DataFrame()

    try:
        df = pd.read_csv(csv_path)

        selected_columns = resolve_columns(selection)

        # Only keep columns that exist
        selected_columns = [c for c in selected_columns if c in df.columns]

        df = df[selected_columns]

        return df

    except Exception as e:
        print(f"Error loading CSV: {e}")
        return pd.DataFrame()

def get_all_runs(experiment_id):
    rows = get_runs_by_experiment(experiment_id)
    return pd.DataFrame(rows) if rows else pd.DataFrame()


def get_runs_filtered(experiment_id, controller_type=None, scenario_id=None):
    if controller_type:
        rows = get_runs_by_controller(experiment_id, controller_type)
    else:
        rows = get_runs_by_experiment(experiment_id)

    if scenario_id:
        rows = [r for r in rows if r.get("scenario_id") == scenario_id]

    return pd.DataFrame(rows) if rows else pd.DataFrame()


def get_latest_runs(experiment_id):
    rows = get_latest_run_per_controller(experiment_id)
    return pd.DataFrame(rows) if rows else pd.DataFrame()


def get_metrics_dataframe(experiment_id):
    rows = get_metrics_by_experiment(experiment_id)
    return pd.DataFrame(rows) if rows else pd.DataFrame()


def get_raw_csv_paths(experiment_id):
    batches = get_batches_by_experiment(experiment_id)
    return [b["raw_csv_path"] for b in batches if b.get("raw_csv_path")]

