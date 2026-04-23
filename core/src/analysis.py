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

import numpy as np
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


def compute_wobble_divergence(times, measured_values, target_value):
    """
    Compute Wobble and Divergence per Varvel 1992.

    Args:
        times           — array-like of time points in seconds
        measured_values — array-like of measured vital sign values at each time point
        target_value    — the target (predicted/desired) value the controller aims for

    Returns:
        (wobble, divergence) as floats
        wobble     — intra-subject variability of PE, in % (Eq. 5)
        divergence — trend of |PE| over time, in %/hr (Eq. 3)

    PE_j = (measured_j - target) / target * 100
    MDPE  = median(PE)
    Wobble    = median(|PE_j - MDPE|)
    Divergence = slope of linear regression of |PE_j| vs time, converted to %/hr
    """
    times = np.asarray(times, dtype=float)
    measured = np.asarray(measured_values, dtype=float)

    pe = (measured - target_value) / target_value * 100.0  # Eq. 1

    mdpe = float(np.median(pe))
    wobble = float(np.median(np.abs(pe - mdpe)))           # Eq. 5

    # Linear regression of |PE| vs time (seconds), slope * 60 = %/hr
    abs_pe = np.abs(pe)
    slope = float(np.polyfit(times, abs_pe, 1)[0])
    divergence = slope * 60.0                              # Eq. 3

    return wobble, divergence
