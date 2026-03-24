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
from database.connection import transaction, execute, execute_one


def insert_experiment(experiment_id, name, target_metric=None,
                      custom_target_value=None, simulation_duration=None,
                      events=None, output_columns=None, status='pending'):
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
                 simulation_duration, events, output_columns, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (experiment_id, name, target_metric, custom_target_value,
              simulation_duration, events_json, output_columns_json, status))

    return experiment_id


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
