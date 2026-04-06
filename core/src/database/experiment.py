"""
============================================================
Author:        Jared Garcia
Date Created:  2026-03-22
Description:   Database write and read operations for experiments.
               Kept separate from data_classes.py to avoid
               merge conflicts with branch 72's Experiment dataclass.

Usage:
    from database.experiment import insert_experiment, insert_experiment_from_object

    # From individual fields
    insert_experiment(
        experiment_id=exp.experiment_id,
        name=exp.name,
        simulation_duration=exp.simulation_duration,
        events=exp.events,
        output_columns=exp.output_columns,
        output_dir=exp.output_dir
    )

    # Directly from Experiment object
    insert_experiment_from_object(exp)
============================================================
"""

import json
from data_classes import Experiment
from database.connection import transaction, execute, execute_one


def insert_experiment(experiment_id, name, target_metric=None,
                      custom_target_value=None, simulation_duration=None,
                      events=None, output_columns=None, output_dir=None,
                      status='pending'):
    """
    Insert an experiment record before the run starts. Returns the experiment_id.
    events and output_columns should be lists — stored as JSON.
    """
    events_json = json.dumps(events) if events else None
    output_columns_json = json.dumps(output_columns) if output_columns else None

    with transaction() as conn:
        conn.execute("""
            INSERT INTO experiments
                (experiment_id, name, target_metric, custom_target_value,
                 simulation_duration, events, output_columns, output_dir, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (experiment_id, name, target_metric, custom_target_value,
              simulation_duration, events_json, output_columns_json,
              output_dir, status))

    return experiment_id


def insert_experiment_from_object(experiment: Experiment):
    """Helper to insert directly from an Experiment dataclass instance."""
    return insert_experiment(
        experiment_id=experiment.experiment_id,
        name=experiment.name,
        simulation_duration=experiment.simulation_duration,
        events=experiment.events,
        output_columns=experiment.output_columns,
        output_dir=experiment.output_dir
    )


def update_experiment(experiment_id, target_metric=None, custom_target_value=None,
                      output_dir=None, status=None):
    """Update an experiment record after it runs."""
    with transaction() as conn:
        conn.execute("""
            UPDATE experiments
            SET target_metric       = COALESCE(?, target_metric),
                custom_target_value = COALESCE(?, custom_target_value),
                output_dir          = COALESCE(?, output_dir),
                status              = COALESCE(?, status)
            WHERE experiment_id = ?
        """, (target_metric, custom_target_value, output_dir, status, experiment_id))


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
