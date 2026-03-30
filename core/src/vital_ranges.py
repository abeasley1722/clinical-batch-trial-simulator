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
    dbp_max=85,

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
    bmi_min=14.1,
    bmi_max=74.8,
    
    male_hr_mean=71,
    male_hr_std=12,
    female_hr_mean=74,
    female_hr_std=11,
    hr_min=38,
    hr_max=129,

    male_sbp_mean=123,
    male_sbp_std=15,
    female_sbp_mean=116,
    female_sbp_std=16,
    sbp_min=74,
    sbp_max=232,

    male_dbp_mean=76,
    male_dbp_std=11,
    female_dbp_mean=74,
    female_dbp_std=11,
    dbp_min=32,
    dbp_max=137,

    rr_mean=18,
    rr_std=3,
    rr_min=12,
    rr_max=20
)

PEDIATRIC = Demographic(
    demo_name="pediatric",
    
    age_min=8,
    age_max=18,
    age_mean=13,
    age_std=3,

    female_proportion=0.5,

    male_height_mean=156.9,
    male_height_std=17.4,
    female_height_mean=152.4,
    female_height_std=11.9,

    male_bmi_mean=22.4,
    female_bmi_mean=22.7,
    male_bmi_std=6.5,
    female_bmi_std=6.3,
    bmi_min=12.5,
    bmi_max=66.6,

    male_hr_mean=78,
    male_hr_std=13,
    female_hr_mean=80,
    female_hr_std=11,
    hr_min=50,
    hr_max=151,

    male_sbp_mean=106,
    male_sbp_std=10,
    female_sbp_mean=102,
    female_sbp_std=9,
    sbp_min=68,
    sbp_max=143,

    male_dbp_mean=62,
    male_dbp_std=9,
    female_dbp_mean=62,
    female_dbp_std=8,
    dbp_min=35,
    dbp_max=94,

    rr_mean=22,
    rr_std=6,
    rr_min=12,
    rr_max=40
)

GERIATRIC = Demographic(
    demo_name="geriatric",
    
    age_min=65,
    age_max=80,
    age_mean=72,
    age_std=5,

    female_proportion=0.54,
    
    male_height_mean=172.5,
    male_height_std=7.3,
    female_height_mean=158.5,
    female_height_std=6.8,

    male_bmi_mean=29.0,
    female_bmi_mean=29.6,
    male_bmi_std=5.6,
    female_bmi_std=6.8,
    bmi_min=11.1,
    bmi_max=62.9,
    
    male_hr_mean=68,
    male_hr_std=13,
    female_hr_mean=71,
    female_hr_std=12,
    hr_min=34,
    hr_max=129,

    male_sbp_mean=129,
    male_sbp_std=20,
    female_sbp_mean=131,
    female_sbp_std=20,
    sbp_min=65,
    sbp_max=215,

    male_dbp_mean=72,
    male_dbp_std=11,
    female_dbp_mean=72,
    female_dbp_std=11,
    dbp_min=37,
    dbp_max=124,

    rr_mean=20,
    rr_std=4,
    rr_min=12,
    rr_max=28
)