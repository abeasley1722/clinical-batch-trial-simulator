"""
============================================================
Author:        Jared Garcia
Date Created:  2026-03-22
Description:   Run and Metric table write and read operations.
               Runs track each simulation execution.
               Metrics store postprocessed results per run.
============================================================
"""

import uuid
from core.src.database.connection import transaction, execute, execute_one
from core.src.data_classes import Metric

# ── Runs ──────────────────────────────────────────────────────────────────────

def insert_run(experiment_id, patient_id=None, scenario_id=None,
               controller_type=None, status="pending", run_id=None):
    """Insert a run record. Returns the run_id."""
    rid = run_id or str(uuid.uuid4())

    with transaction() as conn:
        conn.execute("""
            INSERT INTO runs
                (run_id, experiment_id, patient_id, scenario_id, controller_type, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (rid, experiment_id, patient_id, scenario_id, controller_type, status))

    return rid


def update_run_status(run_id, status):
    """Update the status of a run (e.g. 'running', 'complete', 'failed')."""
    with transaction() as conn:
        conn.execute(
            "UPDATE runs SET status = ? WHERE run_id = ?", (status, run_id)
        )


def get_run(run_id):
    """Fetch one run by ID. Returns a dict or None."""
    return execute_one("SELECT * FROM runs WHERE run_id = ?", (run_id,))


def get_runs_by_experiment(experiment_id):
    """Fetch all runs for an experiment. Returns a list of dicts."""
    return execute(
        "SELECT * FROM runs WHERE experiment_id = ? ORDER BY created_at DESC",
        (experiment_id,)
    )


def get_runs_by_controller(experiment_id, controller_type):
    """Fetch runs filtered by controller type. Returns a list of dicts."""
    return execute(
        """SELECT * FROM runs
           WHERE experiment_id = ? AND controller_type = ?
           ORDER BY created_at DESC""",
        (experiment_id, controller_type)
    )


def get_latest_run_per_controller(experiment_id):
    """Return the most recent run for each controller type in an experiment."""
    return execute(
        """SELECT * FROM runs
           WHERE experiment_id = ?
           GROUP BY controller_type
           HAVING created_at = MAX(created_at)""",
        (experiment_id,)
    )


# ── Metrics ───────────────────────────────────────────────────────────────────

def insert_metric(experiment_id, vital_sign=None, target_value=None, mae=None, median=None,
                  std_dev=None, time_within_target_range=None, percent_time_within_target_range=None,
                  wobble=None, divergence=None,
                  matching_function=None, matching_function_mae=None, metric_id=None):
    """Insert a metric record after a run completes. Returns the metric_id."""
    mid = metric_id or str(uuid.uuid4())

    with transaction() as conn:
        conn.execute("""
            INSERT INTO metrics
                (metric_id, experiment_id, vital_sign, target_value, mae, median,
                 std_dev, time_within_target_range, percent_time_within_target_range, wobble, divergence, matching_function, matching_function_mae)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (mid, experiment_id, vital_sign, target_value, mae, median, std_dev,
              time_within_target_range, percent_time_within_target_range, wobble, divergence, matching_function, matching_function_mae))

    return mid

def insert_metric_from_object(metric: Metric):
    """Helper to insert a Metric dataclass instance."""
    return insert_metric(
        experiment_id=metric.experiment_id,
        vital_sign=metric.vital_sign_measured,
        target_value=metric.target_value,
        mae=metric.mean_absolute_error,
        median=metric.mean,
        std_dev=metric.std_dev,
        time_within_target_range=metric.time_within_target_range,
        percent_time_within_target_range=metric.percent_time_within_target_range,
        wobble=metric.wobble,
        divergence=metric.divergence,
        matching_function=metric.matching_function,
        matching_function_mae=metric.matching_function_mae
    )

def get_metrics_by_experiment(experiment_id):
    """Fetch all metrics for an experiment. Returns a list of dicts."""
    return execute(
        "SELECT * FROM metrics WHERE experiment_id = ?", (experiment_id,)
    )


def get_metrics_by_run(run_id):
    """Fetch all metrics for a specific run. Returns a list of dicts."""
    return execute(
        "SELECT * FROM metrics WHERE run_id = ?", (run_id,)
    )