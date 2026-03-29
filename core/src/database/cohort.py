"""
============================================================
Author:        Jared Garcia
Date Created:  2026-03-22
Description:   Cohort table write and read operations.
               A cohort defines a demographic group.
               Patients can belong to multiple cohorts via
               the patient_cohorts junction table.

NOTE (branch 72 — cohort_builder.py):
    Two changes needed to use this:
    1. Before inserting patients, create a cohort:
           cohort_id = insert_cohort("soldier")
    2. After inserting each patient, link them:
           add_patient_to_cohort(patient_id, cohort_id)
    cohort_id should no longer be passed to insert_patient().

Usage:
    from database.cohort import insert_cohort, add_patient_to_cohort

    cohort_id = insert_cohort("soldier", description="Military cohort")
    add_patient_to_cohort(patient_id, cohort_id)
============================================================
"""

import uuid
from database.connection import transaction, execute, execute_one

VALID_COHORT_TYPES = {"soldier", "neonatal", "pediatric", "adult", "geriatric"}


def insert_cohort(cohort_type, description=None, cohort_id=None):
    """
    Create a cohort. Returns the cohort_id.
    cohort_type must be one of: soldier, neonatal, pediatric, adult, geriatric
    """
    if cohort_type not in VALID_COHORT_TYPES:
        raise ValueError(f"Invalid cohort type '{cohort_type}'. "
                         f"Valid options: {sorted(VALID_COHORT_TYPES)}")

    cid = cohort_id or str(uuid.uuid4())
    with transaction() as conn:
        conn.execute("""
            INSERT INTO cohorts (cohort_id, cohort_type, description)
            VALUES (?, ?, ?)
        """, (cid, cohort_type, description))
    return cid


def add_patient_to_cohort(patient_id, cohort_id):
    """Link a patient to a cohort. Safe to call multiple times — ignores duplicates."""
    with transaction() as conn:
        conn.execute("""
            INSERT OR IGNORE INTO patient_cohorts (patient_id, cohort_id)
            VALUES (?, ?)
        """, (patient_id, cohort_id))


def get_cohort(cohort_id):
    """Fetch one cohort by ID. Returns a dict or None."""
    return execute_one("SELECT * FROM cohorts WHERE cohort_id = ?", (cohort_id,))


def get_cohorts_by_type(cohort_type):
    """Fetch all cohorts of a given demographic type."""
    return execute("SELECT * FROM cohorts WHERE cohort_type = ?", (cohort_type,))


def get_patient_cohorts(patient_id):
    """Fetch all cohorts a patient belongs to."""
    return execute("""
        SELECT c.* FROM cohorts c
        JOIN patient_cohorts pc ON c.cohort_id = pc.cohort_id
        WHERE pc.patient_id = ?
    """, (patient_id,))
