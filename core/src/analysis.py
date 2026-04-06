"""
============================================================
Author:        Jared Garcia
Date Created:  2026-03-22
Description:   Analysis functions that compute metrics from
               raw simulation CSV data after a run completes.
               Called by ExperimentExecutor (branch 73) after
               each run, then results are stored in the DB.

Usage:
    from analysis import compute_metrics
    from database.metric import insert_metric

    metric = compute_metrics(
        experiment_id=exp.experiment_id,
        csv_path="results/run1.csv",
        target_value=98.0,
        controller_start_time=30.0
    )
    insert_metric(
        experiment_id=metric.experiment_id,
        run_id=run_id,
        mean_absolute_error=metric.mean_absolute_error,
        controller_start_time=metric.controller_start_time,
        mean=metric.mean,
        std_dev=metric.std_dev,
        time_within_target_range=metric.time_within_target_range,
        percent_time_within_target_range=metric.percent_time_within_target_range
    )
============================================================
"""

import pandas as pd
from data_classes import Metric


def compute_metrics(experiment_id: str, csv_path: str, target_value: float,
                    controller_start_time: float = 0.0,
                    target_column: str = "spo2_pct",
                    tolerance: float = 2.0) -> Metric:
    """
    Compute postprocessed metrics from a raw simulation CSV.

    Args:
        experiment_id         — ID of the experiment this run belongs to
        csv_path              — path to the raw CSV produced by ExperimentExecutor
        target_value          — the value the controller is trying to hit (user defined)
        controller_start_time — when the controller started (seconds into simulation)
        target_column         — which column to analyze (default: spo2_pct)
        tolerance             — how far from target_value is still "within range"

    Returns a Metric dataclass ready to store in the DB.

    TODO (branch 73): hook this into ExperimentExecutor after each run completes.
    """
    df = pd.read_csv(csv_path)
    values = df[target_column].dropna()

    errors = (values - target_value).abs()
    in_range = errors <= tolerance
    seconds_in_range = float(in_range.sum())
    percent_in_range = float(in_range.mean() * 100)

    return Metric(
        experiment_id=experiment_id,
        mean_absolute_error=float(errors.mean()),
        controller_start_time=controller_start_time,
        mean=float(values.mean()),
        std_dev=float(values.std()),
        time_within_target_range=seconds_in_range,
        percent_time_within_target_range=percent_in_range
    )
