"""
============================================================
Author:        Jared Garcia
Date Created:  2026-03-22
Description:   Patient table write and read operations.
============================================================
"""

import json
import uuid
from core.src.database.connection import transaction, execute, execute_one


def insert_patient(sex=None, age=None, height=None,
                   weight=None, json_file=None, additional_descriptors=None,
                   patient_id=None, demographic_group=None):
    """
    Insert a patient record. Returns the patient_id.
    Pass patient_id if you already have one, otherwise a UUID is generated.

    NOTE (branch 72 — cohort_builder.py):
        cohort_id has been removed from this function. Cohort membership
        is now managed via the patient_cohorts junction table.
        After inserting a patient, call:
            from database.cohort import add_patient_to_cohort
            add_patient_to_cohort(patient_id, cohort_id)
    """
    pid = patient_id or str(uuid.uuid4())
    descriptors = json.dumps(additional_descriptors) if additional_descriptors else None

    with transaction() as conn:
        conn.execute("""
            INSERT INTO patients
                (patient_id, sex, age, height, weight, json_file, additional_descriptors, demographic_group)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (pid, sex, age, height, weight, json_file, descriptors, demographic_group))

    return pid


def get_patient(patient_id):
    """Fetch one patient by ID. Returns a dict or None."""
    row = execute_one("SELECT * FROM patients WHERE patient_id = ?", (patient_id,))
    if row and row.get("additional_descriptors"):
        row["additional_descriptors"] = json.loads(row["additional_descriptors"])
    return row


def get_patients_by_cohort(cohort_id):
    """Fetch all patients in a cohort via the junction table. Returns a list of dicts."""
    rows = execute("""
        SELECT p.* FROM patients p
        JOIN patient_cohorts pc ON p.patient_id = pc.patient_id
        WHERE pc.cohort_id = ?
    """, (cohort_id,))
    for row in rows:
        if row.get("additional_descriptors"):
            row["additional_descriptors"] = json.loads(row["additional_descriptors"])
    return rows


def get_all_patients():
    """Fetch all patients. Returns a list of dicts."""
    rows = execute("SELECT * FROM patients")
    for row in rows:
        if row.get("additional_descriptors"):
            row["additional_descriptors"] = json.loads(row["additional_descriptors"])
    return rows


# Valid demographic groups
DEMOGRAPHIC_GROUPS = {"soldier", "adult"}

def get_patients_by_demographic(group, count=None):
    """
    Fetch patients belonging to a demographic group.

    Args:
        group  — one of: soldier, neonatal, pediatric, adult, geriatric
        count  — optional, max number of patients to return

    Returns a list of patient dicts.

    Usage:
        get_patients_by_demographic("soldier", count=5)
    """
    if group not in DEMOGRAPHIC_GROUPS:
        raise ValueError(f"Unknown demographic group '{group}'. "
                         f"Valid options: {sorted(DEMOGRAPHIC_GROUPS)}")

    if count is not None:
        sql = """
            SELECT p.* FROM patients p
            WHERE p.demographic_group = ?
            LIMIT ?
        """
        rows = execute(sql, (group, count))
    else:
        sql = """
            SELECT p.* FROM patients p
            WHERE p.demographic_group = ?
        """
        rows = execute(sql, (group,))

    for row in rows:
        if row.get("additional_descriptors"):
            row["additional_descriptors"] = json.loads(row["additional_descriptors"])
    return rows