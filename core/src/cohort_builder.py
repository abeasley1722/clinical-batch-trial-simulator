"""
Soldier Cohort Generator for Digital Clinical Trials

Generates a population of virtual soldiers with physiologically plausible
parameter distributions, then batch-stabilizes them using Pulse.

Output: A folder of pre-stabilized patient states (.json) ready for
rapid loading in simulation scenarios.

Usage:
    python generate_soldier_cohort.py --count 200 --output ./soldier_cohort
    python generate_soldier_cohort.py --count 50 --output ./test_cohort --workers 4
    
Typical runtime: ~2-3 minutes per patient for stabilization
    - 50 patients with 4 workers: ~30-40 min
    - 200 patients with 8 workers: ~1-1.5 hours
"""

import os
import sys
import json
import argparse
import random
import hashlib
import uuid
from database.patient import insert_patient
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Optional
from multiprocessing import Pool, cpu_count

# === PATH SETUP (MUST be before importing local modules) ===
# Navigate up from core/src to project root, then into pulse_engine
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PULSE_HOME = os.path.join(PROJECT_ROOT, "pulse_engine")
PULSE_BIN = os.path.join(PULSE_HOME, "bin")
PULSE_PYTHON = os.path.join(PULSE_HOME, "python")

sys.path.insert(0, PULSE_PYTHON)
sys.path.insert(0, PULSE_BIN)
os.add_dll_directory(PULSE_BIN)

from vital_ranges import SOLDIER

@dataclass
class SoldierProfile:
    """A virtual soldier's baseline characteristics."""
    
    # Identity
    id : str
    name: str
    sex: str  # "Male" or "Female"
    
    # Demographics
    age_yr: int
    height_cm: float
    weight_kg: float
    
    # Derived
    bmi: float
    body_surface_area_m2: float  # Mosteller formula
    
    # Baseline vitals
    heart_rate_baseline: int
    systolic_bp_baseline: int
    diastolic_bp_baseline: int
    respiration_rate_baseline: int
    
    # Metadata
    seed: int
    generated_at: str
    
    def to_pulse_config(self) -> dict:
        """Convert to Pulse patient configuration format."""
        return {
            "Name": self.name,
            "Sex": self.sex,
            "Age": {"ScalarTime": {"Value": self.age_yr, "Unit": "yr"}},
            "Height": {"ScalarLength": {"Value": self.height_cm, "Unit": "cm"}},
            "Weight": {"ScalarMass": {"Value": self.weight_kg, "Unit": "kg"}},
            "HeartRateBaseline": {"ScalarFrequency": {"Value": self.heart_rate_baseline, "Unit": "1/min"}},
            "SystolicArterialPressureBaseline": {"ScalarPressure": {"Value": self.systolic_bp_baseline, "Unit": "mmHg"}},
            "DiastolicArterialPressureBaseline": {"ScalarPressure": {"Value": self.diastolic_bp_baseline, "Unit": "mmHg"}},
            "RespirationRateBaseline": {"ScalarFrequency": {"Value": self.respiration_rate_baseline, "Unit": "1/min"}},
        }

#TODO: extend to accept other demographic groups
class SoldierGenerator:
    """
    Generates physiologically plausible soldier profiles.
    
    Based on typical military demographics and fitness standards.
    """
    
    def __init__(self, seed: Optional[int] = None):
        """Initialize generator with optional seed for reproducibility."""
        self.base_seed = seed if seed is not None else random.randint(0, 2**32 - 1)
        self.rng = random.Random(self.base_seed)
        self.count = 0
    
    def _clamp(self, value: float, min_val: float, max_val: float) -> float:
        """Clamp value to range."""
        return max(min_val, min(max_val, value))
    
    def _normal(self, mean: float, std: float, min_val: float = 0, max_val: float = 0) -> float:
        """Sample from normal distribution, optionally clamped."""
        value = self.rng.gauss(mean, std)
        if min_val != 0 or max_val != 0:
            value = self._clamp(value, min_val or float('-inf'), max_val or float('inf'))
        return value
    
    def _calculate_bsa(self, height_cm: float, weight_kg: float) -> float:
        """Calculate body surface area using Mosteller formula."""
        return ((height_cm * weight_kg) / 3600) ** 0.5
    
    def generate_one(self) -> SoldierProfile:
        """Generate a single soldier profile."""
        self.count += 1
        
        # Deterministic seed for this soldier (reproducible)
        soldier_seed = self.base_seed + self.count
        self.rng.seed(soldier_seed)
        
        # Sex
        is_female = self.rng.random() < SOLDIER.female_proportion
        sex = "Female" if is_female else "Male"
        
        # Age (truncated normal)
        age = int(self._normal(SOLDIER.age_mean, SOLDIER.age_std, SOLDIER.age_min, SOLDIER.age_max))
        
        # Height based on sex
        if is_female:
            height = self._normal(SOLDIER.female_height_mean, SOLDIER.female_height_std)
        else:
            height = self._normal(SOLDIER.male_height_mean, SOLDIER.male_height_std)
        height = round(height, 1)
        
        # BMI -> Weight
        bmi = self._normal(SOLDIER.bmi_mean, SOLDIER.bmi_std, SOLDIER.bmi_min, SOLDIER.bmi_max)
        weight = bmi * (height / 100) ** 2
        weight = round(weight, 1)
        bmi = round(bmi, 1)
        
        # Body surface area
        bsa = round(self._calculate_bsa(height, weight), 2)
        
        # Heart rate (sex-dependent)
        if is_female:
            hr = int(self._normal(SOLDIER.female_hr_mean, SOLDIER.female_hr_std, SOLDIER.hr_min, SOLDIER.hr_max))
        else:
            hr = int(self._normal(SOLDIER.male_hr_mean, SOLDIER.male_hr_std, SOLDIER.hr_min, SOLDIER.hr_max))
        
        # Blood pressure (correlated - higher SBP tends to have higher DBP)
        sbp = int(self._normal(SOLDIER.sbp_mean, SOLDIER.sbp_std, SOLDIER.sbp_min, SOLDIER.sbp_max))
        # DBP correlates with SBP
        dbp_offset = (sbp - SOLDIER.sbp_mean) * 0.5  # Partial correlation
        dbp = int(self._normal(SOLDIER.dbp_mean + dbp_offset, SOLDIER.dbp_std * 0.7, SOLDIER.dbp_min, SOLDIER.dbp_max))
        
        # Respiration rate
        rr = int(self._normal(SOLDIER.rr_mean, SOLDIER.rr_std, SOLDIER.rr_min, SOLDIER.rr_max))
        
        # Generate name (Soldier_XXX where XXX is hash-based for reproducibility)
        name_hash = hashlib.md5(f"{soldier_seed}".encode()).hexdigest()[:8].upper()
        name = f"Soldier_{name_hash}"
        
        return SoldierProfile(
            id = name_hash,
            name=name,
            sex=sex,
            age_yr=age,
            height_cm=height,
            weight_kg=weight,
            bmi=bmi,
            body_surface_area_m2=bsa,
            heart_rate_baseline=hr,
            systolic_bp_baseline=sbp,
            diastolic_bp_baseline=dbp,
            respiration_rate_baseline=rr,
            seed=soldier_seed,
            generated_at=datetime.now().isoformat()
        )
    
    def generate_cohort(self, n: int) -> List[SoldierProfile]:
        """Generate n soldier profiles."""
        return [self.generate_one() for _ in range(n)]


def stabilize_patient(args) -> dict:
    """
    Stabilize a single patient using Pulse.
    
    This runs in a separate process, so must set up Pulse independently.
    Returns dict with status and path to stabilized state.
    """
    #TODO: change from taking args, need to change output dir to the proper location in the database
    profile_dict, output_dir, pulse_bin, pulse_python = args
    profile = SoldierProfile(**profile_dict)
    
    try:
        # Set up Pulse paths for this worker
        import sys
        if pulse_python not in sys.path:
            sys.path.insert(0, pulse_python)
        if pulse_bin not in sys.path:
            sys.path.insert(0, pulse_bin)
        
        if hasattr(os, 'add_dll_directory'):
            try:
                os.add_dll_directory(pulse_bin)
            except OSError:
                pass
        
        os.chdir(pulse_bin)
        
        # Import Pulse
        from pulse.engine.PulseEngine import PulseEngine
        from pulse.cdm.engine import SEDataRequestManager, SEDataRequest
        from pulse.cdm.patient import SEPatientConfiguration, eSex
        from pulse.cdm.scalars import FrequencyUnit, PressureUnit, TimeUnit, LengthUnit, MassUnit
        
        # Create engine
        pulse = PulseEngine()
        safe_name = profile.name.replace(' ', '_')
        pulse.set_log_filename(f"./test_results/stabilize_{safe_name}.log")
        pulse.log_to_console(False)
        
        # Configure patient
        pc = SEPatientConfiguration()
        p = pc.get_patient()
        
        p.set_name(profile.name)
        p.set_sex(eSex.Female if profile.sex == "Female" else eSex.Male)
        p.get_age().set_value(profile.age_yr, TimeUnit.yr)
        p.get_height().set_value(profile.height_cm, LengthUnit.cm)
        p.get_weight().set_value(profile.weight_kg, MassUnit.kg)
        p.get_heart_rate_baseline().set_value(profile.heart_rate_baseline, FrequencyUnit.Per_min)
        p.get_systolic_arterial_pressure_baseline().set_value(profile.systolic_bp_baseline, PressureUnit.mmHg)
        p.get_diastolic_arterial_pressure_baseline().set_value(profile.diastolic_bp_baseline, PressureUnit.mmHg)
        p.get_respiration_rate_baseline().set_value(profile.respiration_rate_baseline, FrequencyUnit.Per_min)
        
        pc.set_data_root_dir("./")
        
        # Minimal data requests for stabilization
        data_requests = [
            SEDataRequest.create_physiology_request("HeartRate", unit=FrequencyUnit.Per_min),
            SEDataRequest.create_physiology_request("OxygenSaturation"),
        ]
        data_mgr = SEDataRequestManager(data_requests)
        
        # Initialize (stabilize) - this takes ~2-3 minutes
        if not pulse.initialize_engine(pc, data_mgr):
            return {
                'status': 'error',
                'name': profile.name,
                'message': 'Stabilization failed'
            }
        
        # Save stabilized state
        #TODO: save to proper location in database
        output_path = os.path.join(output_dir, f"{profile.name}@0s.json")
        
        # Pulse saves state relative to its working directory
        # We need to use a relative path or handle this carefully
        rel_output = os.path.relpath(output_path, pulse_bin)
        
        # Serialize to file
        if not pulse.serialize_to_file(rel_output):
            return {
                'status': 'error',
                'name': profile.name,
                'message': 'Failed to save state'
            }
        
        insert_patient(
            cohort_id=None,
            sex=profile.sex,
            age=profile.age_yr,
            height=profile.height_cm,
            weight=profile.weight_kg,
            json_file=rel_output,
            additional_descriptors=None,
            patient_id=profile.id
        )

        return {
            'status': 'success',
            'name': profile.name,
            'id': profile.id,
            'state_path': rel_output  # Path to stabilized state file
        }
        
    except Exception as e:
        import traceback
        return {
            'status': 'error',
            'name': profile.name,
            'message': str(e),
            'traceback': traceback.format_exc()
        }