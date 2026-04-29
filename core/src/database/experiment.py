"""
============================================================
Author:        Jared Garcia
Date Created:  2026-03-22
Description:   Database write and read operations for experiments.
               Kept separate from experiment.py (which holds the
               Experiment dataclass from branch 72) to avoid
               merge conflicts.

Usage:
    from database.experiment_db import insert_experiment, get_experiment

    insert_experiment(
        experiment_id=exp.experiment_id,
        name=exp.name,
        simulation_duration=exp.simulation_duration,
        events=exp.events,
        output_columns=exp.output_columns
    )

Merge note (branch 72):
    from_json() uses datetime.now() which should be
    datetime.datetime.now() — this will crash at runtime
    until fixed in branch 72.
============================================================
"""

import json
from core.src.database.connection import transaction, execute, execute_one
from core.src.data_classes import Experiment

def insert_experiment(experiment_id, name, target_metric=None,
                      custom_target_value=None, simulation_duration=None,
                      events=None, output_columns=None, mean_csv_path=None, status='pending'):
    """
    Insert an experiment record. Returns the experiment_id.
    events and output_columns should be lists — stored as JSON.
    """
    events_json = json.dumps(events) if events else None
    output_columns_json = json.dumps(output_columns) if output_columns else None

    with transaction() as conn:
        conn.execute("""
            INSERT INTO experiments
                (experiment_id, name, target_metric, custom_target_value,
                 simulation_duration, events, output_columns, mean_csv_path, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (experiment_id, name, target_metric, custom_target_value,
              simulation_duration, events_json, output_columns_json, mean_csv_path, status))

    return experiment_id

def insert_experiment_from_object(experiment: Experiment):
    """Helper to insert an Experiment dataclass instance."""
    return insert_experiment(
        experiment_id=experiment.experiment_id,
        name=experiment.name,
        simulation_duration=experiment.simulation_duration,
        events=experiment.events,
        output_columns=experiment.output_columns,
        mean_csv_path=experiment.mean_csv_path
    )

def update_experiment(experiment_id, name=None, target_metric=None,
                      custom_target_value=None, simulation_duration=None,
                      events=None, output_columns=None, mean_csv_path=None, status=None):
    """
    Update an experiment record. Only fields passed (non-None) will be updated.
    Returns the experiment_id.
    """
    fields = []
    params = []

    if name is not None:
        fields.append("name = ?")
        params.append(name)
    if target_metric is not None:
        fields.append("target_metric = ?")
        params.append(target_metric)
    if custom_target_value is not None:
        fields.append("custom_target_value = ?")
        params.append(custom_target_value)
    if simulation_duration is not None:
        fields.append("simulation_duration = ?")
        params.append(simulation_duration)
    if events is not None:
        fields.append("events = ?")
        params.append(json.dumps(events))
    if output_columns is not None:
        fields.append("output_columns = ?")
        params.append(json.dumps(output_columns))
    if mean_csv_path is not None:
        fields.append("mean_csv_path = ?")
        params.append(mean_csv_path)
    if status is not None:
        fields.append("status = ?")
        params.append(status)

    if not fields:
        return experiment_id  # nothing to update

    params.append(experiment_id)
    with transaction() as conn:
        conn.execute(f"""
            UPDATE experiments
            SET {', '.join(fields)}
            WHERE experiment_id = ?
        """, params)
    return experiment_id


def update_experiment_from_object(experiment: Experiment):
    """Helper to update an Experiment dataclass instance."""
    return update_experiment(
        experiment_id=experiment.experiment_id,
        name=experiment.name,
        simulation_duration=experiment.simulation_duration,
        events=experiment.events,
        output_columns=experiment.output_columns,
        mean_csv_path=experiment.mean_csv_path
    )

def get_experiment(experiment_id):
    """Fetch one experiment by ID. Returns a dict or None."""
    row = execute_one(
        "SELECT * FROM experiments WHERE experiment_id = ?", (experiment_id,)
    )
    if row:
        if row.get("events"):
            row["events"] = json.loads(row["events"])
        if row.get("output_columns"):
            row["output_columns"] = json.loads(row["output_columns"])
    return row


def get_all_experiments():
    """Fetch all experiments. Returns a list of dicts."""
    rows = execute("SELECT * FROM experiments ORDER BY created_at DESC")
    for row in rows:
        if row.get("events"):
            row["events"] = json.loads(row["events"])
        if row.get("output_columns"):
            row["output_columns"] = json.loads(row["output_columns"])
    return rows