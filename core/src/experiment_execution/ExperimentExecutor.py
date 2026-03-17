# ============================================================
# Author:        Anointiyae Beasley
# Date Created:  2026-03-10
# Description:   
# - Build Pulse data requests from experiment metrics
# - Load/stabilize the patient
# - Initialize device/controller state
# - Step through simulation time
# - Apply experiment events when needed
# - Pull Pulse results
# - Store results in a structured format
# - Return those results
# ============================================================
# === PULSE IMPORTS ===
from pulse.engine.PulseEngine import PulseEngine, eModelType
from pulse.engine.PulseEnginePool import PulseEnginePool
from pulse.cdm.engine import SEDataRequest, SEDataRequestManager, SEAdvanceTime, IEventHandler, SEEventChange, eEvent
from multiprocessing import Pool as ProcessPool, TimeoutError as MPTimeoutError
from pulse.cdm.patient_actions import (
    SEIntubation, eIntubationType, 
    SEAcuteRespiratoryDistressSyndromeExacerbation,
    SESubstanceBolus, eSubstance_Administration,
    SESubstanceInfusion,
    SESubstanceCompoundInfusion,
    SEExercise,
    SEAcuteStress,
    SEHemorrhage, eHemorrhage_Compartment,
    SEAirwayObstruction,
    SERespiratoryMechanicsConfiguration
)
from pulse.cdm.physiology import eLungCompartment
from pulse.cdm.mechanical_ventilator_actions import (
    SEMechanicalVentilatorVolumeControl,
    SEMechanicalVentilatorPressureControl,
    eMechanicalVentilator_VolumeControlMode,
    eMechanicalVentilator_PressureControlMode
)
from pulse.cdm.mechanical_ventilator import eSwitch
from pulse.cdm.scalars import (
    FrequencyUnit, PressureUnit, TimeUnit,
    VolumeUnit, VolumePerTimeUnit, MassPerVolumeUnit,
    LengthUnit, MassUnit, PressureTimePerVolumeUnit, VolumePerPressureUnit,
    AmountPerVolumeUnit
)
from pulse.cdm.patient import eSex, SEPatient, SEPatientConfiguration
from pulse.cdm.io.patient import serialize_patient_from_file
#Recieve experiment object\
class ExperimentExecutor:
    def __init__(self, experiment: Experiment):
        #Unpack each experiment into new variables [unfinished]
        self.id = experiment.id
        
        self.pulse = None
        self.results = [] #May just be one csv file
        
    def initialize_engine(self):
        pass

    def build_data_requests(self):
        pass

    def load_patient(self):
        pass

    def apply_event(self, event):
        pass

    def step(self):
        pass

    def collect_results(self):
        pass

    def run(self):
        pass

