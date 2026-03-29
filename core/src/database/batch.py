"""
============================================================
Author:        Jared Garcia
Date Created:  2026-03-22
Description:   Batch table write and read operations.
               A batch links an experiment to a patient
               and stores the path to the raw CSV output
               produced by ExperimentExecutor (branch 73).
============================================================
"""

import uuid
from database.connection import transaction, execute, execute_one


def insert_batch(experiment_id, patient_id, raw_csv_path=None, batch_id=None):
    """Insert a batch record. Returns the batch_id."""
    bid = batch_id or str(uuid.uuid4())

    with transaction() as conn:
        conn.execute("""
            INSERT INTO batches (batch_id, experiment_id, patient_id, raw_csv_path)
            VALUES (?, ?, ?, ?)
        """, (bid, experiment_id, patient_id, raw_csv_path))

    return bid


def get_batch(batch_id):
    """Fetch one batch by ID. Returns a dict or None."""
    return execute_one("SELECT * FROM batches WHERE batch_id = ?", (batch_id,))


def get_batches_by_experiment(experiment_id):
    """Fetch all batches for an experiment. Returns a list of dicts."""
    return execute(
        "SELECT * FROM batches WHERE experiment_id = ?", (experiment_id,)
    )


def get_batches_by_patient(patient_id):
    """Fetch all batches for a patient. Returns a list of dicts."""
    return execute(
        "SELECT * FROM batches WHERE patient_id = ?", (patient_id,)
    )