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
    demo_name: str

    age_min: int
    age_max: int
    age_mean: int
    age_std: int

    female_proportion: float

    male_height_mean: float
    male_height_std: float
    female_height_mean: float
    female_height_std: float

    male_bmi_mean: float
    female_bmi_mean: float
    male_bmi_std: float
    female_bmi_std: float
    bmi_min: float
    bmi_max: float

    male_hr_mean: int
    male_hr_std: int
    female_hr_mean: int 
    female_hr_std: int
    hr_min: int
    hr_max: int

    male_sbp_mean: int
    male_sbp_std: int
    female_sbp_mean: int
    female_sbp_std: int
    sbp_min: int
    sbp_max: int

    male_dbp_mean: int
    male_dbp_std: int
    female_dbp_mean: int
    female_dbp_std: int
    dbp_min: int
    dbp_max: int

    rr_mean: int
    rr_std: int
    rr_min: int
    rr_max: int

SOLDIER = Demographic(
    demo_name="soldier",

    age_min=18,
    age_max=45,
    age_mean=28,
    age_std=14,

    female_proportion=0.55,
    
    male_height_mean=177.0,
    male_height_std=7.0,
    female_height_mean=163.0,
    female_height_std=6.5,

    male_bmi_mean=24.5,
    female_bmi_mean=24.5,
    male_bmi_std=2.5,
    female_bmi_std=2.5,
    bmi_min=18.5,
    bmi_max=30.0,
    
    male_hr_mean=65,
    male_hr_std=8,
    female_hr_mean=70,
    female_hr_std=8,
    hr_min=50,
    hr_max=85,

    male_sbp_mean=112,
    male_sbp_std=5,
    female_sbp_mean=112,
    female_sbp_std=5,
    sbp_min=100,
    sbp_max=119,

    male_dbp_mean=72,
    male_dbp_std=6,
    female_dbp_mean=72,
    female_dbp_std=6,
    dbp_min=60,
    dbp_max=80,

    rr_mean=14,
    rr_std=2,
    rr_min=10,
    rr_max=18
)

ADULT = Demographic(
    demo_name="adult",

    age_min=18,
    age_max=64,
    age_mean=43,
    age_std=14,

    female_proportion=0.55,
    
    male_height_mean=175.4,
    male_height_std=7.7,
    female_height_mean=161.8,
    female_height_std=6.9,

    male_bmi_mean=29.1,
    female_bmi_mean=30.4,
    male_bmi_std=6.9,
    female_bmi_std=8.5,
    bmi_min=17.0,
    bmi_max=29.0,
    
    male_hr_mean=71,
    male_hr_std=12,
    female_hr_mean=74,
    female_hr_std=11,
    hr_min=50,
    hr_max=129,

    male_sbp_mean=123,
    male_sbp_std=15,
    female_sbp_mean=116,
    female_sbp_std=16,
    sbp_min=100,
    sbp_max=120,

    male_dbp_mean=76,
    male_dbp_std=11,
    female_dbp_mean=74,
    female_dbp_std=11,
    dbp_min=60,
    dbp_max=80,

    rr_mean=18,
    rr_std=3,
    rr_min=12,
    rr_max=20
)