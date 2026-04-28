"""
============================================================
Author:        Jared Garcia
Date Created:  2026-03-22
Description:   SQL schema definitions for all tables.
               Run init_db.py to create the database.
============================================================
"""

# Experiments — one per clinical trial run
CREATE_EXPERIMENTS = """
CREATE TABLE IF NOT EXISTS experiments (
    experiment_id       TEXT PRIMARY KEY,
    name                TEXT NOT NULL,
    target_metric       TEXT,
    custom_target_value TEXT,
    simulation_duration INTEGER,
    events              TEXT,           -- JSON blob
    output_columns      TEXT,           -- JSON blob
    mean_csv_path       TEXT,
    status              TEXT NOT NULL DEFAULT 'pending',
    created_at          TEXT NOT NULL DEFAULT (datetime('now'))
);
"""

# Scenarios — what clinical situation is being simulated
CREATE_SCENARIOS = """
CREATE TABLE IF NOT EXISTS scenarios (
    scenario_id     TEXT PRIMARY KEY,
    experiment_id   TEXT NOT NULL,
    scenario_type   TEXT,
    scenario_time   INTEGER,
    FOREIGN KEY (experiment_id) REFERENCES experiments(experiment_id)
);
"""

# Patients — demographic info and reference to their Pulse JSON file
CREATE_PATIENTS = """
CREATE TABLE IF NOT EXISTS patients (
    patient_id              TEXT PRIMARY KEY,
    sex                     TEXT,
    age                     REAL,
    height                  REAL,
    weight                  REAL,
    json_file               TEXT,
    demographic_group       TEXT,
    additional_descriptors  TEXT    -- JSON blob
);
"""

# Batches — links experiments to patients, stores raw CSV output path
CREATE_BATCHES = """
CREATE TABLE IF NOT EXISTS batches (
    batch_id        TEXT PRIMARY KEY,
    experiment_id   TEXT NOT NULL,
    patient_id      TEXT NOT NULL,
    raw_csv_path    TEXT,
    FOREIGN KEY (experiment_id) REFERENCES experiments(experiment_id),
    FOREIGN KEY (patient_id)    REFERENCES patients(patient_id)
);
"""

# Runs — one simulation execution per patient per experiment
CREATE_RUNS = """
CREATE TABLE IF NOT EXISTS runs (
    run_id          TEXT PRIMARY KEY,
    experiment_id   TEXT NOT NULL,
    patient_id      TEXT,
    scenario_id     TEXT,
    controller_type TEXT,
    status          TEXT NOT NULL DEFAULT 'pending',
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (experiment_id) REFERENCES experiments(experiment_id),
    FOREIGN KEY (patient_id)    REFERENCES patients(patient_id),
    FOREIGN KEY (scenario_id)   REFERENCES scenarios(scenario_id)
);
"""

# Metrics — postprocessed results per run
CREATE_METRICS = """
CREATE TABLE IF NOT EXISTS metrics (
    metric_id               TEXT PRIMARY KEY,
    experiment_id           TEXT NOT NULL,
    vital_sign              TEXT,
    target_value              REAL,
    mae                     REAL,
    median                  REAL,
    std_dev                 REAL,
    time_within_target_range REAL,
    percent_time_within_target_range REAL,
    wobble                  REAL,
    divergence              REAL,
    matching_function       TEXT,
    matching_function_mae   REAL,
    FOREIGN KEY (experiment_id) REFERENCES experiments(experiment_id)
);
"""

ALL_TABLES = [
    CREATE_EXPERIMENTS,
    CREATE_PATIENTS,
    CREATE_SCENARIOS,
    CREATE_BATCHES,
    CREATE_RUNS,
    CREATE_METRICS,
]