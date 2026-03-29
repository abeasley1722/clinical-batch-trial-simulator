"""
============================================================
Author:        Jared Garcia
Date Created:  2026-03-22
Description:   Scenario table write and read operations.
============================================================
"""

import uuid
from database.connection import transaction, execute, execute_one


def insert_scenario(experiment_id, scenario_type=None, scenario_time=None,
                    scenario_id=None):
    """Insert a scenario. Returns the scenario_id."""
    sid = scenario_id or str(uuid.uuid4())

    with transaction() as conn:
        conn.execute("""
            INSERT INTO scenarios (scenario_id, experiment_id, scenario_type, scenario_time)
            VALUES (?, ?, ?, ?)
        """, (sid, experiment_id, scenario_type, scenario_time))

    return sid


def get_scenario(scenario_id):
    """Fetch one scenario by ID. Returns a dict or None."""
    return execute_one("SELECT * FROM scenarios WHERE scenario_id = ?", (scenario_id,))


def get_scenarios_by_experiment(experiment_id):
    """Fetch all scenarios for an experiment. Returns a list of dicts."""
    return execute(
        "SELECT * FROM scenarios WHERE experiment_id = ?", (experiment_id,)
    )