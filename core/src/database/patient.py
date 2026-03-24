"""
============================================================
Author:        Jared Garcia
Date Created:  2026-03-22
Description:   Patient table write and read operations.
============================================================
"""

import json
import uuid
from database.connection import transaction, execute, execute_one


def insert_patient(cohort_id=None, sex=None, age=None, height=None,
                   weight=None, json_file=None, additional_descriptors=None,
                   patient_id=None):
    """
    Insert a patient record. Returns the patient_id.
    Pass patient_id if you already have one, otherwise a UUID is generated.
    """
    pid = patient_id or str(uuid.uuid4())
    descriptors = json.dumps(additional_descriptors) if additional_descriptors else None

    with transaction() as conn:
        conn.execute("""
            INSERT INTO patients
                (patient_id, cohort_id, sex, age, height, weight, json_file, additional_descriptors)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (pid, cohort_id, sex, age, height, weight, json_file, descriptors))

    return pid


def get_patient(patient_id):
    """Fetch one patient by ID. Returns a dict or None."""
    row = execute_one("SELECT * FROM patients WHERE patient_id = ?", (patient_id,))
    if row and row.get("additional_descriptors"):
        row["additional_descriptors"] = json.loads(row["additional_descriptors"])
    return row


def get_patients_by_cohort(cohort_id):
    """Fetch all patients in a cohort. Returns a list of dicts."""
    rows = execute("SELECT * FROM patients WHERE cohort_id = ?", (cohort_id,))
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
