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


def insert_patient(sex=None, age=None, height=None, weight=None,
                   json_file=None, demographic_group=None,
                   additional_descriptors=None, patient_id=None):
    """
    Insert a patient record. Returns the patient_id.
    Pass patient_id if you already have one, otherwise a UUID is generated.
    """
    pid = patient_id or str(uuid.uuid4())
    descriptors = json.dumps(additional_descriptors) if additional_descriptors else None

    with transaction() as conn:
        conn.execute("""
            INSERT INTO patients
                (patient_id, sex, age, height, weight, json_file,
                 demographic_group, additional_descriptors)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (pid, sex, age, height, weight, json_file,
              demographic_group, descriptors))

    return pid


def get_patient(patient_id):
    """Fetch one patient by ID. Returns a dict or None."""
    row = execute_one("SELECT * FROM patients WHERE patient_id = ?", (patient_id,))
    if row and row.get("additional_descriptors"):
        row["additional_descriptors"] = json.loads(row["additional_descriptors"])
    return row


def get_all_patients(randomize=False):
    """
    Fetch all patients. Returns a list of dicts.
    Pass randomize=True to return them in random order.
    """
    sql = "SELECT * FROM patients"
    if randomize:
        sql += " ORDER BY RANDOM()"
    rows = execute(sql)
    for row in rows:
        if row.get("additional_descriptors"):
            row["additional_descriptors"] = json.loads(row["additional_descriptors"])
    return rows


DEMOGRAPHIC_GROUPS = {"soldier", "adult"}


def get_patients_by_demographic(group, count=None):
    """
    Fetch patients by demographic group. Pass randomize via get_all_patients
    or add ORDER BY RANDOM() here if needed.
    """
    if group not in DEMOGRAPHIC_GROUPS:
        raise ValueError(f"Unknown demographic group '{group}'. "
                         f"Valid options: {sorted(DEMOGRAPHIC_GROUPS)}")

    sql = "SELECT * FROM patients WHERE demographic_group = ?"
    params = (group,)
    if count is not None:
        sql += " LIMIT ?"
        params = (group, count)

    rows = execute(sql, params)
    for row in rows:
        if row.get("additional_descriptors"):
            row["additional_descriptors"] = json.loads(row["additional_descriptors"])
    return rows
