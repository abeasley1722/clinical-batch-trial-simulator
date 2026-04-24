"""
============================================================
Author:        Jared Garcia
Date Created:  2026-03-22
Description:   Retrieval API for querying experiment results.
               Returns structured dicts or pandas DataFrames.
               Covers issue #46 query requirements:
                 - All runs for an experiment
                 - Runs filtered by controller/scenario
                 - CSVs for raw data and metrics
                 - Latest run per controller
============================================================
"""

import pandas as pd
from database.metric import (
    get_runs_by_experiment,
    get_runs_by_controller,
    get_latest_run_per_controller,
    get_metrics_by_experiment,
    get_metrics_by_run,
)
from database.batch import get_batches_by_experiment
from database.experiment import get_experiment


def get_all_runs(experiment_id):
    """Return all runs for an experiment as a DataFrame."""
    rows = get_runs_by_experiment(experiment_id)
    return pd.DataFrame(rows) if rows else pd.DataFrame()


def get_runs_filtered(experiment_id, controller_type=None, scenario_id=None):
    """Return runs filtered by controller type and/or scenario."""
    if controller_type:
        rows = get_runs_by_controller(experiment_id, controller_type)
    else:
        rows = get_runs_by_experiment(experiment_id)

    if scenario_id:
        rows = [r for r in rows if r.get("scenario_id") == scenario_id]

    return pd.DataFrame(rows) if rows else pd.DataFrame()


def get_latest_runs(experiment_id):
    """Return the most recent run per controller as a DataFrame."""
    rows = get_latest_run_per_controller(experiment_id)
    return pd.DataFrame(rows) if rows else pd.DataFrame()


def get_metrics_dataframe(experiment_id):
    """Return all postprocessed metrics for an experiment as a DataFrame."""
    rows = get_metrics_by_experiment(experiment_id)
    return pd.DataFrame(rows) if rows else pd.DataFrame()


def get_raw_csv_paths(experiment_id):
    """Return a list of raw CSV file paths for an experiment."""
    batches = get_batches_by_experiment(experiment_id)
    return [b["raw_csv_path"] for b in batches if b.get("raw_csv_path")]


def get_raw_csv_dataframe(experiment_id):
    """
    Load and concatenate all raw CSVs for an experiment into one DataFrame.
    Adds a 'patient_id' column from the batch record.
    """
    batches = get_batches_by_experiment(experiment_id)
    frames = []
    for batch in batches:
        path = batch.get("raw_csv_path")
        if path:
            try:
                df = pd.read_csv(path)
                df["patient_id"] = batch["patient_id"]
                frames.append(df)
            except FileNotFoundError:
                pass  # CSV not yet written or moved
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
