"""
============================================================
Author:        Jared Garcia
Date Created:  2026-03-22
Description:   Basic DB tests — creates a temp SQLite DB,
               writes an experiment + patient + run + metrics,
               reads them back, and asserts correctness.
============================================================
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "core", "src"))


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    """Use a temporary DB file for every test."""
    db_file = str(tmp_path / "test.db")
    monkeypatch.setenv("DB_PATH", db_file)

    import importlib
    import database.connection as conn_mod
    conn_mod.DB_PATH = db_file
    importlib.reload(conn_mod)

    from init_db import init_db
    init_db()

    yield db_file


def test_insert_and_get_experiment():
    from database.experiment import insert_experiment, get_experiment

    eid = insert_experiment(
        experiment_id="20260322_120000",
        name="Test Experiment",
        target_metric="SpO2",
        simulation_duration=300,
        events=[{"time": 60, "action": "hemorrhage"}],
        output_dir="results/20260322_120000"
    )

    row = get_experiment(eid)
    assert row is not None
    assert row["experiment_id"] == "20260322_120000"
    assert row["name"] == "Test Experiment"
    assert row["events"][0]["action"] == "hemorrhage"
    assert row["output_dir"] == "results/20260322_120000"
    assert row["status"] == "pending"


def test_insert_and_get_patient():
    from database.patient import insert_patient, get_patient

    pid = insert_patient(
        sex="M",
        age=25,
        height=175.0,
        weight=80.0,
        json_file="patients/soldier_001.json",
        demographic_group="soldier",
        additional_descriptors={"fitness": "high"}
    )

    row = get_patient(pid)
    assert row is not None
    assert row["sex"] == "M"
    assert row["age"] == 25
    assert row["demographic_group"] == "soldier"
    assert row["additional_descriptors"]["fitness"] == "high"


def test_insert_run_and_update_status():
    from database.experiment import insert_experiment
    from database.metric import insert_run, update_run_status, get_run

    insert_experiment(experiment_id="exp-001", name="Run Test")
    rid = insert_run(experiment_id="exp-001", controller_type="PID", status="pending")

    row = get_run(rid)
    assert row["status"] == "pending"

    update_run_status(rid, "complete")
    row = get_run(rid)
    assert row["status"] == "complete"


def test_insert_and_get_metrics():
    from database.experiment import insert_experiment
    from database.metric import insert_run, insert_metric, get_metrics_by_run

    insert_experiment(experiment_id="exp-002", name="Metrics Test")
    rid = insert_run(experiment_id="exp-002", controller_type="builtin")
    insert_metric(
        experiment_id="exp-002",
        run_id=rid,
        mean_absolute_error=2.5,
        controller_start_time=30.0,
        mean=98.0,
        std_dev=0.5,
        time_within_target_range=85.0,
        percent_time_within_target_range=92.0
    )

    metrics = get_metrics_by_run(rid)
    assert len(metrics) == 1
    assert metrics[0]["mean_absolute_error"] == 2.5
    assert metrics[0]["time_within_target_range"] == 85.0
    assert metrics[0]["percent_time_within_target_range"] == 92.0


def test_batch_links_experiment_and_patient():
    from database.experiment import insert_experiment
    from database.patient import insert_patient
    from database.batch import insert_batch, get_batches_by_experiment

    insert_experiment(experiment_id="exp-003", name="Batch Test")
    pid = insert_patient(sex="F", age=30, height=165.0, weight=65.0,
                         json_file="patients/soldier_002.json")
    insert_batch(experiment_id="exp-003", patient_id=pid,
                 raw_csv_path="results/run1.csv")

    batches = get_batches_by_experiment("exp-003")
    assert len(batches) == 1
    assert batches[0]["patient_id"] == pid
    assert batches[0]["raw_csv_path"] == "results/run1.csv"
