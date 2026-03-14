
import requests as http_requests

from pulse.cdm.scalars import (
    FrequencyUnit, PressureUnit, TimeUnit,
    VolumeUnit, VolumePerTimeUnit, MassPerVolumeUnit,
    LengthUnit, MassUnit, PressureTimePerVolumeUnit, VolumePerPressureUnit,
    AmountPerVolumeUnit
)
from pulse.cdm.engine import SEDataRequest

# === UNIT MAPPING FOR HTTP CONTROLLERS ===
UNIT_MAP = {
    # Pressure units
    "mmHg": PressureUnit.mmHg,
    "cmH2O": PressureUnit.cmH2O,
    "Pa": PressureUnit.Pa,
    "atm": PressureUnit.atm,
    # Volume units
    "mL": VolumeUnit.mL,
    "L": VolumeUnit.L,
    # Flow units
    "mL/min": VolumePerTimeUnit.mL_Per_min,
    "L/min": VolumePerTimeUnit.L_Per_min,
    "L/s": VolumePerTimeUnit.L_Per_s,
    # Frequency units
    "1/min": FrequencyUnit.Per_min,
    "/min": FrequencyUnit.Per_min,
    "Per_min": FrequencyUnit.Per_min,
    "Hz": FrequencyUnit.Hz,
    "1/s": FrequencyUnit.Per_s,
    # Time units
    "s": TimeUnit.s,
    "min": TimeUnit.min,
    "hr": TimeUnit.hr,
    # Mass units
    "kg": MassUnit.kg,
    "g": MassUnit.g,
    "mg": MassUnit.mg,
    "ug": MassUnit.ug,
    # Length units
    "m": LengthUnit.m,
    "cm": LengthUnit.cm,
    "mm": LengthUnit.mm,
    "inch": LengthUnit.inch,
    # Concentration units
    "g/L": MassPerVolumeUnit.g_Per_L,
    "mg/mL": MassPerVolumeUnit.g_Per_L,
    "ug/mL": MassPerVolumeUnit.ug_Per_mL,
    # Compliance units
    "mL/cmH2O": VolumePerPressureUnit.mL_Per_cmH2O,
    "L/cmH2O": VolumePerPressureUnit.L_Per_cmH2O,
    # Resistance units
    "cmH2O*s/L": PressureTimePerVolumeUnit.cmH2O_s_Per_L,
}

DATA_REQUEST_FACTORIES = {
    "Physiology": SEDataRequest.create_physiology_request,
    "MechanicalVentilator": SEDataRequest.create_mechanical_ventilator_request,
}

# Unit string -> actual Pulse unit object mapping
PULSE_UNIT_MAP = {
    "FrequencyUnit.Per_min": FrequencyUnit.Per_min,
    "PressureUnit.mmHg": PressureUnit.mmHg,
    "PressureUnit.cmH2O": PressureUnit.cmH2O,
    "VolumeUnit.mL": VolumeUnit.mL,
    "VolumePerTimeUnit.L_Per_min": VolumePerTimeUnit.L_Per_min,
    "VolumePerTimeUnit.mL_Per_min": VolumePerTimeUnit.mL_Per_min,
    "MassPerVolumeUnit.g_Per_L": MassPerVolumeUnit.g_Per_L,
    "VolumePerPressureUnit.mL_Per_cmH2O": VolumePerPressureUnit.mL_Per_cmH2O,
    "PressureTimePerVolumeUnit.cmH2O_s_Per_L": PressureTimePerVolumeUnit.cmH2O_s_Per_L,
}

class HTTPController:
    """HTTP-based controller that communicates with an external controller service."""

    def __init__(self, base_url, config=None, timeout=10.0, simulation_context=None):
        self.base_url = base_url.rstrip('/')
        self.config = config or {}
        self.timeout = timeout
        self.data_requests = []
        self.next_update_s = 1.0
        self.initialized = False
        self.last_error = None
        # Simulation context for identification (single-patient mode uses job_id)
        self.simulation_context = simulation_context or {}
        self.simulation_id = self.simulation_context.get('simulation_id', '')
        self.job_id = self.simulation_context.get('job_id', '')

    def send_init(self, patient, vent_settings):
        payload = {
            "patient": patient,
            "vent_settings": vent_settings,
            "config": self.config,
            # Simulation identifiers for consistency with batch mode
            "simulation_id": self.simulation_id,
            "job_id": self.job_id
        }
        
        try:
            resp = http_requests.post(
                f"{self.base_url}/init",
                json=payload,
                timeout=self.timeout
            )
            resp.raise_for_status()
            data = resp.json()
            
            if data.get("status") != "ok":
                raise RuntimeError(f"Controller init failed: {data.get('error', 'unknown error')}")
            
            self.data_requests = data.get("data_requests", [])
            pulse_requests = []
            
            for req in self.data_requests:
                category = req.get("category")
                name = req.get("name")
                unit_str = req.get("unit")
                
                if category not in DATA_REQUEST_FACTORIES:
                    raise ValueError(f"Unknown data request category: '{category}'")
                
                factory = DATA_REQUEST_FACTORIES[category]
                
                if unit_str:
                    if unit_str not in UNIT_MAP:
                        raise ValueError(f"Unknown unit: '{unit_str}' for {category}:{name}")
                    unit = UNIT_MAP[unit_str]
                    pulse_requests.append(factory(name, unit=unit))
                else:
                    pulse_requests.append(factory(name))
            
            self.next_update_s = data.get("next_update_s", 1.0)
            self.initialized = True
            self.last_error = None
            
            return pulse_requests
            
        except http_requests.exceptions.RequestException as e:
            self.last_error = f"HTTP error during init: {e}"
            raise RuntimeError(self.last_error)
        except (KeyError, ValueError) as e:
            self.last_error = f"Invalid controller response: {e}"
            raise RuntimeError(self.last_error)
    
    def step(self, data_values, current_settings):
        if not self.initialized:
            return None

        sim_time = data_values.pop("sim_time_s", 0.0)

        payload = {
            "sim_time_s": sim_time,
            "data": data_values,
            # Simulation identifiers for consistency with batch mode
            "simulation_id": self.simulation_id,
            "job_id": self.job_id
        }

        try:
            resp = http_requests.post(
                f"{self.base_url}/update",
                json=payload,
                timeout=self.timeout
            )
            resp.raise_for_status()
            response = resp.json()
            
            if "next_update_s" in response:
                self.next_update_s = max(0.02, response["next_update_s"])
            
            commands = response.get("commands", {})
            result = current_settings.copy()
            result.update(commands)
            result["next_interval_s"] = self.next_update_s
            
            self.last_error = None
            return result
            
        except http_requests.exceptions.Timeout:
            self.last_error = f"Controller timeout after {self.timeout}s"
            print(f"[HTTPController] {self.last_error}")
            return None
        except http_requests.exceptions.RequestException as e:
            self.last_error = f"HTTP error: {e}"
            print(f"[HTTPController] {self.last_error}")
            return None
        except Exception as e:
            self.last_error = f"Error parsing response: {e}"
            print(f"[HTTPController] {self.last_error}")
            return None
    
    def shutdown(self):
        if not self.initialized:
            return
        try:
            payload = {
                "simulation_id": self.simulation_id,
                "job_id": self.job_id
            }
            http_requests.post(f"{self.base_url}/shutdown", json=payload, timeout=2.0)
        except:
            pass


class HTTPFluidController:
    """HTTP-based fluid controller that communicates with an external controller service."""

    def __init__(self, base_url, config=None, timeout=10.0, simulation_context=None):
        self.base_url = base_url.rstrip('/')
        self.config = config or {}
        self.timeout = timeout
        self.data_requests = []
        self.next_update_s = 10.0
        self.initialized = False
        self.last_error = None
        # Simulation context for identification
        self.simulation_context = simulation_context or {}
        self.simulation_id = self.simulation_context.get('simulation_id', '')
        self.job_id = self.simulation_context.get('job_id', '')

    def send_init(self, patient, fluid_settings):
        payload = {
            "patient": patient,
            "fluid_settings": fluid_settings,
            "config": self.config,
            "simulation_id": self.simulation_id,
            "job_id": self.job_id
        }

        try:
            resp = http_requests.post(
                f"{self.base_url}/init",
                json=payload,
                timeout=self.timeout
            )
            resp.raise_for_status()
            data = resp.json()

            if data.get("status") != "ok":
                raise RuntimeError(f"Fluid controller init failed: {data.get('error', 'unknown error')}")

            self.data_requests = data.get("data_requests", [])
            self.next_update_s = data.get("next_update_s", 10.0)
            self.initialized = True
            self.last_error = None

            return self.data_requests

        except http_requests.exceptions.RequestException as e:
            self.last_error = f"HTTP error during init: {e}"
            raise RuntimeError(self.last_error)
        except (KeyError, ValueError) as e:
            self.last_error = f"Invalid controller response: {e}"
            raise RuntimeError(self.last_error)

    def step(self, vitals, current_settings, blood_loss_ml=0, blood_infused_ml=0, crystalloid_infused_ml=0):
        if not self.initialized:
            return None

        sim_time = vitals.pop("sim_time_s", 0.0) if "sim_time_s" in vitals else 0.0

        payload = {
            "sim_time_s": sim_time,
            "data": vitals,
            "blood_loss_ml": blood_loss_ml,
            "blood_infused_ml": blood_infused_ml,
            "crystalloid_infused_ml": crystalloid_infused_ml,
            "simulation_id": self.simulation_id,
            "job_id": self.job_id
        }

        try:
            resp = http_requests.post(
                f"{self.base_url}/update",
                json=payload,
                timeout=self.timeout
            )
            resp.raise_for_status()
            response = resp.json()

            if "next_update_s" in response:
                self.next_update_s = max(1.0, response["next_update_s"])

            commands = response.get("commands", {})
            result = current_settings.copy()
            result.update(commands)
            result["next_interval_s"] = self.next_update_s

            self.last_error = None
            return result

        except http_requests.exceptions.Timeout:
            self.last_error = f"Fluid controller timeout after {self.timeout}s"
            print(f"[HTTPFluidController] {self.last_error}")
            return None
        except http_requests.exceptions.RequestException as e:
            self.last_error = f"HTTP error: {e}"
            print(f"[HTTPFluidController] {self.last_error}")
            return None
        except Exception as e:
            self.last_error = f"Error parsing response: {e}"
            print(f"[HTTPFluidController] {self.last_error}")
            return None

    def shutdown(self):
        if not self.initialized:
            return
        try:
            payload = {
                "simulation_id": self.simulation_id,
                "job_id": self.job_id
            }
            http_requests.post(f"{self.base_url}/shutdown", json=payload, timeout=2.0)
        except:
            pass


class BuiltinController:
    """Built-in controller implementations."""

    # Random walk parameter bounds (matching reference_controllers/random_controller.py)
    RANDOM_WALK_BOUNDS = {
        'fio2': {'min': 0.21, 'max': 1.0, 'step': 0.05, 'default': 0.4},
        'peep_cmh2o': {'min': 5, 'max': 20, 'step': 2, 'default': 5},
        'vt_ml': {'min': 300, 'max': 600, 'step': 25, 'default': 420},
        'rr': {'min': 10, 'max': 30, 'step': 2, 'default': 14},
        'itime_s': {'min': 0.8, 'max': 1.5, 'step': 0.1, 'default': 1.0},
        'pinsp_cmh2o': {'min': 10, 'max': 30, 'step': 2, 'default': 15},
    }

    def __init__(self, name):
        self.name = name
        self.settings = {}
        self.state = {'history': []}
        self.rng = None  # For random walk controller
    
    def send_init(self, patient, settings):
        self.settings = settings.copy()
        self.state = {'history': [], 'patient': patient}
        # Initialize RNG for random walk controller
        if self.name == 'random_walk_controller':
            import random
            self.rng = random.Random()  # Unseeded for variability each run
    
    def step(self, vitals, current_settings):
        self.settings = current_settings.copy()

        if self.name == 'default_controller':
            return self._simple_fio2(vitals)
        elif self.name == 'ardsnet_controller':
            return self._ardsnet(vitals)
        elif self.name == 'adaptive_controller':
            return self._adaptive(vitals)
        elif self.name == 'random_walk_controller':
            return self._random_walk(vitals)
        return None
    
    def _simple_fio2(self, vitals):
        new = self.settings.copy()
        spo2 = vitals['spo2_pct']
        fio2 = self.settings.get('fio2', 0.4)
        
        if spo2 < 92:
            new['fio2'] = min(1.0, fio2 + 0.05)
        elif spo2 > 98:
            new['fio2'] = max(0.21, fio2 - 0.05)
        return new
    
    def _ardsnet(self, vitals):
        new = self.settings.copy()
        spo2 = vitals['spo2_pct']
        ph = vitals['ph']
        pplat = vitals['pplat_cmh2o']
        
        if spo2 < 88:
            new['fio2'] = min(1.0, self.settings.get('fio2', 0.4) + 0.1)
            new['peep_cmh2o'] = min(20, self.settings.get('peep_cmh2o', 5) + 2)
        elif spo2 > 95:
            new['fio2'] = max(0.3, self.settings.get('fio2', 0.4) - 0.05)
        
        if ph < 7.30:
            new['rr'] = min(35, self.settings.get('rr', 14) + 2)
        elif ph > 7.45:
            new['rr'] = max(6, self.settings.get('rr', 14) - 2)
        
        if pplat > 30:
            new['vt_ml'] = max(300, self.settings.get('vt_ml', 420) - 20)
        
        return new
    
    def _adaptive(self, vitals):
        new = self._simple_fio2(vitals)
        spo2 = vitals['spo2_pct']

        if spo2 < 88:
            new['next_interval_s'] = 0.5
        elif spo2 < 92 or spo2 > 98:
            new['next_interval_s'] = 1.0
        else:
            new['next_interval_s'] = 5.0

        return new

    def _random_walk(self, vitals):
        """
        Bounded random walk controller - ignores vitals, randomly walks all parameters.
        Useful as a control arm to compare against intelligent controllers.
        """
        new = self.settings.copy()

        for param, bounds in self.RANDOM_WALK_BOUNDS.items():
            current = self.settings.get(param, bounds['default'])
            step = bounds['step']

            # Random direction: -1, 0, or +1
            direction = self.rng.choice([-1, 0, 1])
            new_value = current + (direction * step)

            # Clamp to bounds
            new_value = max(bounds['min'], min(bounds['max'], new_value))

            # Round appropriately
            if isinstance(bounds['default'], float):
                new_value = round(new_value, 2)
            else:
                new_value = int(round(new_value))

            new[param] = new_value

        # Random interval for next update (10-60s like the reference controller)
        new['next_interval_s'] = self.rng.uniform(10, 60)

        return new


class BuiltinFluidController:
    """Built-in fluid resuscitation controller implementations.

    Manages crystalloid and blood product infusions based on hemodynamic status.
    Designed to work independently of ventilator controllers.
    """

    def __init__(self, name):
        self.name = name
        self.settings = {
            'crystalloid_rate_ml_min': 0,
            'blood_rate_ml_min': 0,
            'crystalloid_compound': 'Saline',
            'blood_compound': 'Blood'
        }
        self.state = {
            'phase': 'monitoring',  # monitoring, resuscitating, maintaining
            'total_crystalloid_given': 0,
            'total_blood_given': 0,
            'last_map': None,
            'last_hr': None,
            'trend_improving': False
        }

    def send_init(self, patient, initial_settings=None):
        """Initialize controller with patient info and optional settings."""
        self.state['patient'] = patient
        if initial_settings:
            self.settings.update(initial_settings)

    def step(self, vitals, current_fluid_settings, blood_loss_ml=0, blood_infused_ml=0, crystalloid_infused_ml=0):
        """Evaluate hemodynamics and return fluid commands.

        Args:
            vitals: Dict with hr_bpm, map_mmhg, sbp_mmhg, etc.
            current_fluid_settings: Current infusion rates
            blood_loss_ml: Cumulative blood loss
            blood_infused_ml: Cumulative blood products given
            crystalloid_infused_ml: Cumulative crystalloid given

        Returns:
            Dict with fluid commands and next_interval_s
        """
        if self.name == 'default_fluid_controller':
            return self._simple_resuscitation(vitals, blood_loss_ml, blood_infused_ml, crystalloid_infused_ml)
        elif self.name == 'aggressive_fluid_controller':
            return self._aggressive_resuscitation(vitals, blood_loss_ml, blood_infused_ml, crystalloid_infused_ml)
        elif self.name == 'conservative_fluid_controller':
            return self._conservative_resuscitation(vitals, blood_loss_ml, blood_infused_ml, crystalloid_infused_ml)
        elif self.name == 'damage_control_fluid_controller':
            return self._damage_control_resuscitation(vitals, blood_loss_ml, blood_infused_ml, crystalloid_infused_ml)
        return None

    def _simple_resuscitation(self, vitals, blood_loss_ml, blood_infused_ml, crystalloid_infused_ml):
        """Simple MAP-based fluid resuscitation.

        Strategy:
        - MAP < 65: Start/increase crystalloid
        - MAP < 55: Add blood products
        - MAP > 75: Reduce infusion rates
        - MAP 65-75: Maintain current rates
        """
        new = self.settings.copy()
        map_mmhg = vitals.get('map_mmhg', 70)
        hr_bpm = vitals.get('hr_bpm', 80)

        # Track trends
        if self.state['last_map'] is not None:
            self.state['trend_improving'] = map_mmhg > self.state['last_map']
        self.state['last_map'] = map_mmhg
        self.state['last_hr'] = hr_bpm

        # Determine phase and action
        if map_mmhg < 55:
            # Severe hypotension - aggressive resuscitation
            self.state['phase'] = 'resuscitating'
            new['crystalloid_rate_ml_min'] = 250  # ~15 L/hr max
            # Add blood if significant blood loss
            if blood_loss_ml > 500:
                new['blood_rate_ml_min'] = 150
            else:
                new['blood_rate_ml_min'] = 0
            new['next_interval_s'] = 10  # Check frequently

        elif map_mmhg < 65:
            # Moderate hypotension
            self.state['phase'] = 'resuscitating'
            current_crystalloid = self.settings.get('crystalloid_rate_ml_min', 0)
            new['crystalloid_rate_ml_min'] = min(200, current_crystalloid + 50)
            # Blood if large loss and not keeping up
            if blood_loss_ml > 750 and (blood_loss_ml - blood_infused_ml - crystalloid_infused_ml/3) > 500:
                new['blood_rate_ml_min'] = 100
            else:
                new['blood_rate_ml_min'] = max(0, self.settings.get('blood_rate_ml_min', 0) - 25)
            new['next_interval_s'] = 15

        elif map_mmhg > 75:
            # Adequate perfusion - reduce rates
            self.state['phase'] = 'maintaining'
            current_crystalloid = self.settings.get('crystalloid_rate_ml_min', 0)
            current_blood = self.settings.get('blood_rate_ml_min', 0)
            new['crystalloid_rate_ml_min'] = max(0, current_crystalloid - 50)
            new['blood_rate_ml_min'] = max(0, current_blood - 50)
            new['next_interval_s'] = 30

        else:
            # MAP 65-75: Stable, gradual reduction
            self.state['phase'] = 'maintaining'
            current_crystalloid = self.settings.get('crystalloid_rate_ml_min', 0)
            new['crystalloid_rate_ml_min'] = max(0, current_crystalloid - 25)
            new['blood_rate_ml_min'] = max(0, self.settings.get('blood_rate_ml_min', 0) - 25)
            new['next_interval_s'] = 20

        # Tachycardia as secondary indicator (compensatory shock)
        if hr_bpm > 120 and map_mmhg < 70:
            new['crystalloid_rate_ml_min'] = max(new['crystalloid_rate_ml_min'], 150)
            new['next_interval_s'] = min(new['next_interval_s'], 15)

        self.settings = new.copy()
        return new

    def _aggressive_resuscitation(self, vitals, blood_loss_ml, blood_infused_ml, crystalloid_infused_ml):
        """Aggressive fluid resuscitation - higher rates, earlier blood."""
        new = self.settings.copy()
        map_mmhg = vitals.get('map_mmhg', 70)
        hr_bpm = vitals.get('hr_bpm', 80)

        if map_mmhg < 60:
            new['crystalloid_rate_ml_min'] = 300
            new['blood_rate_ml_min'] = 200 if blood_loss_ml > 300 else 100
            new['next_interval_s'] = 5
        elif map_mmhg < 70:
            new['crystalloid_rate_ml_min'] = 200
            new['blood_rate_ml_min'] = 100 if blood_loss_ml > 500 else 0
            new['next_interval_s'] = 10
        elif map_mmhg > 80:
            new['crystalloid_rate_ml_min'] = max(0, self.settings.get('crystalloid_rate_ml_min', 0) - 100)
            new['blood_rate_ml_min'] = max(0, self.settings.get('blood_rate_ml_min', 0) - 100)
            new['next_interval_s'] = 30
        else:
            new['crystalloid_rate_ml_min'] = max(0, self.settings.get('crystalloid_rate_ml_min', 0) - 50)
            new['blood_rate_ml_min'] = max(0, self.settings.get('blood_rate_ml_min', 0) - 50)
            new['next_interval_s'] = 20

        self.settings = new.copy()
        return new

    def _conservative_resuscitation(self, vitals, blood_loss_ml, blood_infused_ml, crystalloid_infused_ml):
        """Conservative/permissive hypotension approach - lower MAP targets."""
        new = self.settings.copy()
        map_mmhg = vitals.get('map_mmhg', 70)

        # Target MAP 50-60 (permissive hypotension)
        if map_mmhg < 50:
            new['crystalloid_rate_ml_min'] = 150
            new['blood_rate_ml_min'] = 100 if blood_loss_ml > 1000 else 0
            new['next_interval_s'] = 15
        elif map_mmhg < 55:
            new['crystalloid_rate_ml_min'] = 100
            new['blood_rate_ml_min'] = 50 if blood_loss_ml > 750 else 0
            new['next_interval_s'] = 20
        elif map_mmhg > 65:
            # Above target - reduce
            new['crystalloid_rate_ml_min'] = max(0, self.settings.get('crystalloid_rate_ml_min', 0) - 50)
            new['blood_rate_ml_min'] = max(0, self.settings.get('blood_rate_ml_min', 0) - 50)
            new['next_interval_s'] = 45
        else:
            # At target
            new['crystalloid_rate_ml_min'] = max(0, self.settings.get('crystalloid_rate_ml_min', 0) - 25)
            new['blood_rate_ml_min'] = 0
            new['next_interval_s'] = 30

        self.settings = new.copy()
        return new

    def _damage_control_resuscitation(self, vitals, blood_loss_ml, blood_infused_ml, crystalloid_infused_ml):
        """Damage control resuscitation - prioritize blood products, limit crystalloid.

        Modern trauma approach:
        - 1:1:1 ratio (if we had plasma/platelets)
        - Limit crystalloid to avoid dilutional coagulopathy
        - Permissive hypotension until hemorrhage controlled
        """
        new = self.settings.copy()
        map_mmhg = vitals.get('map_mmhg', 70)

        # Cap crystalloid at 2L total
        max_crystalloid = max(0, 2000 - crystalloid_infused_ml)

        if map_mmhg < 50:
            # Prioritize blood
            new['blood_rate_ml_min'] = 200
            new['crystalloid_rate_ml_min'] = min(100, max_crystalloid / 10) if max_crystalloid > 0 else 0
            new['next_interval_s'] = 10
        elif map_mmhg < 60:
            new['blood_rate_ml_min'] = 150
            new['crystalloid_rate_ml_min'] = min(50, max_crystalloid / 20) if max_crystalloid > 0 else 0
            new['next_interval_s'] = 15
        elif map_mmhg > 65:
            # At target - reduce
            new['blood_rate_ml_min'] = max(0, self.settings.get('blood_rate_ml_min', 0) - 50)
            new['crystalloid_rate_ml_min'] = 0
            new['next_interval_s'] = 30
        else:
            new['blood_rate_ml_min'] = max(0, self.settings.get('blood_rate_ml_min', 0) - 25)
            new['crystalloid_rate_ml_min'] = 0
            new['next_interval_s'] = 20

        self.settings = new.copy()
        return new

