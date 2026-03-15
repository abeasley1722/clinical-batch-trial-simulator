""" 
============================================================
Author:        Zachary Kao
Date Created:  2026-03-15
Description:   Storing vital sign ranges for various demographics.
============================================================ 
"""

from dataclasses import dataclass

@dataclass(frozen=True)
class Demographic:
    age_min: int
    age_max: int
    age_mean: int
    age_std: int

    female_proportion: float

    male_height_mean: float
    male_height_std: float
    female_height_mean: float
    female_height_std: float

    bmi_mean: float
    bmi_std: float
    bmi_min: float
    bmi_max: float

    male_hr_mean: int
    male_hr_std: int
    female_hr_mean: int 
    female_hr_std: int
    hr_min: int
    hr_max: int

    sbp_mean: int
    sbp_std: int
    sbp_min: int
    sbp_max: int

    dbp_mean: int
    dbp_std: int
    dbp_min: int
    dbp_max: int

    rr_mean: int
    rr_std: int
    rr_min: int
    rr_max: int

SOLDIER = Demographic(
    age_min=18,
    age_max=45,
    age_mean=28,
    age_std=6,

    female_proportion=0.17,
    
    male_height_mean=177.0,
    male_height_std=7.0,
    female_height_mean=163.0,
    female_height_std=6.5,

    bmi_mean=24.5,
    bmi_std=2.5,
    bmi_min=18.5,
    bmi_max=30.0,
    
    male_hr_mean=65,
    male_hr_std=8,
    female_hr_mean=70,
    female_hr_std=8,
    hr_min=50,
    hr_max=85,

    sbp_mean=112,
    sbp_std=5,
    sbp_min=100,
    sbp_max=119,

    dbp_mean=72,
    dbp_std=6,
    dbp_min=60,
    dbp_max=85,

    rr_mean=14,
    rr_std=2,
    rr_min=10,
    rr_max=18
)