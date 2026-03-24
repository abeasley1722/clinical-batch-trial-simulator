# === AVAILABLE CSV OUTPUT VARIABLES ===
# Each entry defines a Pulse data request that can be selected for CSV output.
# "key" = CSV column name, "pulse_name" = Pulse engine variable name
# "request_type": "physiology", "mechanical_ventilator", or "compartment_substance"
# "transform": post-processing applied to raw Pulse value before CSV output
# Variables with "default": True match the original hardcoded set.


AVAILABLE_VARIABLES = [
    # --- Vital Signs ---
    {"key": "hr_bpm", "label": "Heart Rate", "unit": "bpm", "category": "Vital Signs",
     "default": True, "request_type": "physiology", "pulse_name": "HeartRate",
     "pulse_unit": "FrequencyUnit.Per_min", "transform": None},
    {"key": "spo2_pct", "label": "SpO2", "unit": "%", "category": "Vital Signs",
     "default": True, "request_type": "physiology", "pulse_name": "OxygenSaturation",
     "pulse_unit": None, "transform": "multiply_100"},
    {"key": "etco2_mmhg", "label": "EtCO2", "unit": "mmHg", "category": "Vital Signs",
     "default": True, "request_type": "physiology", "pulse_name": "EndTidalCarbonDioxidePressure",
     "pulse_unit": "PressureUnit.mmHg", "transform": None},
    {"key": "rr_patient", "label": "Resp Rate (patient)", "unit": "bpm", "category": "Vital Signs",
     "default": True, "request_type": "physiology", "pulse_name": "RespirationRate",
     "pulse_unit": "FrequencyUnit.Per_min", "transform": None},
    {"key": "sbp_mmhg", "label": "Systolic BP", "unit": "mmHg", "category": "Vital Signs",
     "default": True, "request_type": "physiology", "pulse_name": "SystolicArterialPressure",
     "pulse_unit": "PressureUnit.mmHg", "transform": None},
    {"key": "dbp_mmhg", "label": "Diastolic BP", "unit": "mmHg", "category": "Vital Signs",
     "default": True, "request_type": "physiology", "pulse_name": "DiastolicArterialPressure",
     "pulse_unit": "PressureUnit.mmHg", "transform": None},
    {"key": "map_mmhg", "label": "Mean Arterial Pressure", "unit": "mmHg", "category": "Vital Signs",
     "default": True, "request_type": "physiology", "pulse_name": "MeanArterialPressure",
     "pulse_unit": "PressureUnit.mmHg", "transform": None},

    # --- Blood Gas ---
    {"key": "pao2_mmhg", "label": "PaO2", "unit": "mmHg", "category": "Blood Gas",
     "default": True, "request_type": "physiology", "pulse_name": "ArterialOxygenPressure",
     "pulse_unit": "PressureUnit.mmHg", "transform": None},
    {"key": "paco2_mmhg", "label": "PaCO2", "unit": "mmHg", "category": "Blood Gas",
     "default": True, "request_type": "physiology", "pulse_name": "ArterialCarbonDioxidePressure",
     "pulse_unit": "PressureUnit.mmHg", "transform": None},
    {"key": "ph", "label": "Blood pH", "unit": "", "category": "Blood Gas",
     "default": True, "request_type": "physiology", "pulse_name": "BloodPH",
     "pulse_unit": None, "transform": None},

    # --- Cardiac ---
    {"key": "vt_patient_ml", "label": "Tidal Volume (patient)", "unit": "mL", "category": "Cardiac",
     "default": True, "request_type": "physiology", "pulse_name": "TidalVolume",
     "pulse_unit": "VolumeUnit.mL", "transform": None},
    {"key": "co_lpm", "label": "Cardiac Output", "unit": "L/min", "category": "Cardiac",
     "default": True, "request_type": "physiology", "pulse_name": "CardiacOutput",
     "pulse_unit": "VolumePerTimeUnit.L_Per_min", "transform": None},

    # --- Hematology (DEFAULT in PSB for shock/resuscitation monitoring) ---
    {"key": "lactate_mmol_L", "label": "Lactate", "unit": "mmol/L", "category": "Hematology",
     "default": True, "request_type": "compartment_substance",
     "pulse_name": "Lactate", "pulse_unit": "MassPerVolumeUnit.g_Per_L",
     "compartment": "Aorta", "property": "Concentration",
     "transform": "lactate_g_to_mmol"},
    {"key": "blood_volume_ml", "label": "Blood Volume", "unit": "mL", "category": "Hematology",
     "default": True, "request_type": "physiology", "pulse_name": "BloodVolume",
     "pulse_unit": "VolumeUnit.mL", "transform": None},
    {"key": "hematocrit_pct", "label": "Hematocrit", "unit": "%", "category": "Hematology",
     "default": False, "request_type": "physiology", "pulse_name": "Hematocrit",
     "pulse_unit": None, "transform": None},

    # --- Ventilator (measured) ---
    {"key": "rr_vent", "label": "Resp Rate (vent)", "unit": "bpm", "category": "Ventilator",
     "default": True, "request_type": "mechanical_ventilator", "pulse_name": "RespirationRate",
     "pulse_unit": "FrequencyUnit.Per_min", "transform": None},
    {"key": "vt_vent_ml", "label": "Tidal Volume (vent)", "unit": "mL", "category": "Ventilator",
     "default": True, "request_type": "mechanical_ventilator", "pulse_name": "TidalVolume",
     "pulse_unit": "VolumeUnit.mL", "transform": None},
    {"key": "pip_cmh2o", "label": "Peak Insp Pressure", "unit": "cmH2O", "category": "Ventilator",
     "default": True, "request_type": "mechanical_ventilator", "pulse_name": "PeakInspiratoryPressure",
     "pulse_unit": "PressureUnit.cmH2O", "transform": None},
    {"key": "pplat_cmh2o", "label": "Plateau Pressure", "unit": "cmH2O", "category": "Ventilator",
     "default": True, "request_type": "mechanical_ventilator", "pulse_name": "PlateauPressure",
     "pulse_unit": "PressureUnit.cmH2O", "transform": None},
    {"key": "paw_mean_cmh2o", "label": "Mean Airway Pressure", "unit": "cmH2O", "category": "Ventilator",
     "default": True, "request_type": "mechanical_ventilator", "pulse_name": "MeanAirwayPressure",
     "pulse_unit": "PressureUnit.cmH2O", "transform": None},
    {"key": "insp_flow_lpm", "label": "Inspiratory Flow", "unit": "L/min", "category": "Ventilator",
     "default": True, "request_type": "mechanical_ventilator", "pulse_name": "InspiratoryFlow",
     "pulse_unit": "VolumePerTimeUnit.L_Per_min", "transform": None},
    {"key": "exp_flow_lpm", "label": "Expiratory Flow", "unit": "L/min", "category": "Ventilator",
     "default": True, "request_type": "mechanical_ventilator", "pulse_name": "ExpiratoryFlow",
     "pulse_unit": "VolumePerTimeUnit.L_Per_min", "transform": None},

    # --- Respiratory Mechanics (non-default) ---
    {"key": "resp_compliance_ml_cmh2o", "label": "Respiratory Compliance", "unit": "mL/cmH2O",
     "category": "Respiratory Mechanics", "default": False, "request_type": "mechanical_ventilator",
     "pulse_name": "DynamicRespiratoryCompliance",
     "pulse_unit": "VolumePerPressureUnit.mL_Per_cmH2O", "transform": None},
    {"key": "static_compliance_ml_cmh2o", "label": "Static Compliance", "unit": "mL/cmH2O",
     "category": "Respiratory Mechanics", "default": False, "request_type": "mechanical_ventilator",
     "pulse_name": "StaticRespiratoryCompliance",
     "pulse_unit": "VolumePerPressureUnit.mL_Per_cmH2O", "transform": None},

    # --- Additional Ventilator (non-default) ---
    {"key": "airway_pressure_cmh2o", "label": "Airway Pressure", "unit": "cmH2O",
     "category": "Additional Ventilator", "default": False, "request_type": "mechanical_ventilator",
     "pulse_name": "AirwayPressure", "pulse_unit": "PressureUnit.cmH2O", "transform": None},
    {"key": "total_peep_cmh2o", "label": "Total PEEP", "unit": "cmH2O",
     "category": "Additional Ventilator", "default": False, "request_type": "mechanical_ventilator",
     "pulse_name": "TotalPositiveEndExpiratoryPressure",
     "pulse_unit": "PressureUnit.cmH2O", "transform": None},
    {"key": "ie_ratio", "label": "I:E Ratio", "unit": "",
     "category": "Additional Ventilator", "default": False, "request_type": "mechanical_ventilator",
     "pulse_name": "InspiratoryExpiratoryRatio", "pulse_unit": None, "transform": None},
    {"key": "insp_vt_ml", "label": "Inspiratory Vt", "unit": "mL",
     "category": "Additional Ventilator", "default": False, "request_type": "mechanical_ventilator",
     "pulse_name": "InspiratoryTidalVolume", "pulse_unit": "VolumeUnit.mL", "transform": None},
    {"key": "exp_vt_ml", "label": "Expiratory Vt", "unit": "mL",
     "category": "Additional Ventilator", "default": False, "request_type": "mechanical_ventilator",
     "pulse_name": "ExpiratoryTidalVolume", "pulse_unit": "VolumeUnit.mL", "transform": None},
    {"key": "peak_insp_flow_lpm", "label": "Peak Insp Flow", "unit": "L/min",
     "category": "Additional Ventilator", "default": False, "request_type": "mechanical_ventilator",
     "pulse_name": "PeakInspiratoryFlow", "pulse_unit": "VolumePerTimeUnit.L_Per_min", "transform": None},

    # --- Temperature (non-default) ---
    {"key": "skin_temp_c", "label": "Skin Temperature", "unit": "C",
     "category": "Temperature", "default": False, "request_type": "physiology",
     "pulse_name": "SkinTemperature", "pulse_unit": None, "transform": None},

    # --- Advanced Respiratory (non-default) ---
    {"key": "total_lung_volume_ml", "label": "Total Lung Volume", "unit": "mL",
     "category": "Advanced Respiratory", "default": False, "request_type": "physiology",
     "pulse_name": "TotalLungVolume", "pulse_unit": "VolumeUnit.mL", "transform": None},
    {"key": "total_pulm_ventilation_lpm", "label": "Total Pulmonary Ventilation", "unit": "L/min",
     "category": "Advanced Respiratory", "default": False, "request_type": "physiology",
     "pulse_name": "TotalPulmonaryVentilation", "pulse_unit": "VolumePerTimeUnit.L_Per_min", "transform": None},
]

# Columns always included in CSV (not Pulse data requests - internally tracked state)
# PSB includes fluid controller columns
ALWAYS_INCLUDED_COLUMNS = [
    "cmd_mode", "cmd_vt_ml", "cmd_rr", "cmd_fio2",
    "cmd_peep_cmh2o", "cmd_pinsp_cmh2o", "cmd_itime_s",
    "is_intubated", "vent_active", "controller_active", "fluid_controller_active",
    "blood_loss_ml", "blood_infused_ml", "crystalloid_infused_ml",
    "cmd_crystalloid_rate", "cmd_blood_rate",
    "event", "controller_cmd", "fluid_cmd"
]

# Default variable keys (for backward compatibility when no output_columns specified)
DEFAULT_OUTPUT_KEYS = [v["key"] for v in AVAILABLE_VARIABLES if v["default"]]