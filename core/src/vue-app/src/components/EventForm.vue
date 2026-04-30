<!-- src/components/AddEventForm.vue -->
<script setup>
import { reactive, ref, watch } from 'vue'

const emit = defineEmits(['add'])

const activation = ref('time')
const time = ref(1)
const timeUnit = ref('min')
const type = ref('pathology')

const trigger = reactive({
  triggerType: 'vital',
  vital: 'map_mmhg',
  operator: '<=',
  value: 65,
  after_event: 'intubate',
  delay: 0,
})

// Drug defaults keyed by drug name
const BOLUS_DEFAULTS = {
  Rocuronium:     { dose: 50, doseUnit: 'mg', conc: 10,    concUnit: 'mg/mL', weightDose: 0.6,  weightUnit: 'mg/kg' },
  Succinylcholine:{ dose: 100,doseUnit: 'mg', conc: 20,    concUnit: 'mg/mL', weightDose: 1.0,  weightUnit: 'mg/kg' },
  Epinephrine:    { dose: 100,doseUnit: 'ug', conc: 0.1,   concUnit: 'mg/mL', weightDose: 1.0,  weightUnit: 'ug/kg' },
  Fentanyl:       { dose: 100,doseUnit: 'ug', conc: 0.05,  concUnit: 'mg/mL', weightDose: 1.0,  weightUnit: 'ug/kg' },
  Morphine:       { dose: 8,  doseUnit: 'mg', conc: 2,     concUnit: 'mg/mL', weightDose: 0.1,  weightUnit: 'mg/kg' },
  Midazolam:      { dose: 2,  doseUnit: 'mg', conc: 1,     concUnit: 'mg/mL', weightDose: 0.02, weightUnit: 'mg/kg' },
}

const INFUSION_DEFAULTS = {
  Propofol:       { rate: 100, conc: 10,    unit: 'mg/mL' },
  Norepinephrine: { rate: 10,  conc: 0.004, unit: 'mg/mL' },
  Epinephrine:    { rate: 10,  conc: 0.004, unit: 'mg/mL' },
  Fentanyl:       { rate: 10,  conc: 0.01,  unit: 'mg/mL' },
  Morphine:       { rate: 10,  conc: 1,     unit: 'mg/mL' },
  Midazolam:      { rate: 10,  conc: 1,     unit: 'mg/mL' },
}

const params = reactive({
  // pathology
  pathology: 'ARDS',
  severity: 0.5,

  // hemorrhage
  compartment: 'RightLeg',
  rate_mode: 'absolute',
  flow_rate: 100,
  rate_mode: 'absolute',
  flow_rate: 100,
  total_volume: 500,
  hemorrhage_duration: 5,
  hemorrhage_duration_unit: 'min',
  stop_mode: 'fixed',
  stop_vital: 'map_mmhg',
  stop_operator: '<=',
  stop_value: 65,
  stop_max_duration: 10,

  // intubate
  intubation: 'Tracheal',

  // vent
  vent_mode: 'VC-AC',
  fio2: 40,
  peep: 5,
  vt: 420,
  rr: 14,
  itime: 1.0,

  // vent controller
  controller: 'default_controller',
  http_url: 'http://localhost:5001',
  http_timeout: 10,
  http_config: '',

  // fluid controller
  fluid_controller: 'default_fluid_controller',
  fluid_http_url: 'http://localhost:5001/fluid',

  // bolus
  bolus_drug: 'Rocuronium',
  bolus_route: 'Intravenous',
  bolus_dose_mode: 'fixed',
  bolus_total_dose: 50,
  bolus_total_dose_unit: 'mg',
  bolus_weight_dose: 0.6,
  bolus_weight_dose_unit: 'mg/kg',
  bolus_concentration: 10,
  bolus_concentration_unit: 'mg/mL',
  bolus_volume_mL: 5,

  // infusion
  infusion_drug: 'Propofol',
  infusion_rate: 100,
  infusion_concentration: 10,
  infusion_concentration_unit: 'mg/mL',

  // compound infusion
  compound_fluid: 'Saline',
  compound_rate: 100,
  compound_bag_volume: 1000,

  // exercise
  intensity: 0.1,
  exercise_duration: 5,
  exercise_duration_unit: 'min',
})

// ── Bolus 3-field auto-calculation ──────────────────────────────────────────
// Tracks which 2 fields were edited most recently; the third is calculated.
// Default: volume is calculated from total dose + concentration.
const bolusEditOrder = ref(['total', 'conc'])

function toConcMgMl(conc, unit) {
  if (unit === 'ug/mL') return conc / 1000
  if (unit === 'g/L')   return conc          // g/L == mg/mL
  return conc
}

function toTotalMg(dose, unit) {
  if (unit === 'ug') return dose / 1000
  if (unit === 'g')  return dose * 1000
  return dose
}

function fromTotalMg(mg, unit) {
  if (unit === 'ug') return mg * 1000
  if (unit === 'g')  return mg / 1000
  return mg
}

function fromConcMgMl(mgml, unit) {
  if (unit === 'ug/mL') return mgml * 1000
  if (unit === 'g/L')   return mgml
  return mgml
}

function bolusFieldEdited(field) {
  bolusEditOrder.value = [...bolusEditOrder.value.filter(f => f !== field), field].slice(-2)
  bolusRecalculate()
}

function bolusRecalculate() {
  const volume    = params.bolus_volume_mL
  const conc      = params.bolus_concentration
  const concUnit  = params.bolus_concentration_unit
  const totalDose = params.bolus_total_dose
  const totalUnit = params.bolus_total_dose_unit

  const concMgMl = toConcMgMl(conc, concUnit)
  const totalMg  = toTotalMg(totalDose, totalUnit)

  const allFields = ['volume', 'conc', 'total']
  const calcField = allFields.find(f => !bolusEditOrder.value.includes(f)) || 'volume'

  if (calcField === 'total' && volume > 0 && concMgMl > 0) {
    params.bolus_total_dose = parseFloat(fromTotalMg(volume * concMgMl, totalUnit).toFixed(4).replace(/\.?0+$/, ''))
  } else if (calcField === 'volume' && concMgMl > 0 && totalMg > 0) {
    params.bolus_volume_mL = parseFloat((totalMg / concMgMl).toFixed(4).replace(/\.?0+$/, ''))
  } else if (calcField === 'conc' && volume > 0 && totalMg > 0) {
    params.bolus_concentration = parseFloat(fromConcMgMl(totalMg / volume, concUnit).toFixed(4).replace(/\.?0+$/, ''))
  }
}

// Which field is currently being auto-calculated
const bolusCalcField = ref('volume')
watch(bolusEditOrder, (order) => {
  const all = ['volume', 'conc', 'total']
  bolusCalcField.value = all.find(f => !order.includes(f)) || 'volume'
}, { deep: true })

// When drug changes, load defaults and reset edit order
watch(() => params.bolus_drug, (drug) => {
  const d = BOLUS_DEFAULTS[drug]
  if (!d) return
  params.bolus_total_dose      = d.dose
  params.bolus_total_dose_unit = d.doseUnit
  params.bolus_concentration   = d.conc
  params.bolus_concentration_unit = d.concUnit
  params.bolus_weight_dose     = d.weightDose
  params.bolus_weight_dose_unit= d.weightUnit
  bolusEditOrder.value = ['total', 'conc']
  bolusRecalculate()
})

// When infusion drug changes, load defaults
watch(() => params.infusion_drug, (drug) => {
  const d = INFUSION_DEFAULTS[drug]
  if (!d) return
  params.infusion_rate = d.rate
  params.infusion_concentration = d.conc
  params.infusion_concentration_unit = d.unit
})

// ── Submit ───────────────────────────────────────────────────────────────────
function submit(e) {
  e.preventDefault()

  const event = {
    activation: activation.value,
    type: type.value
  }

  if (activation.value === 'time') {
    event.time = time.value
    event.timeUnit = timeUnit.value
  } else {
    if (trigger.triggerType === 'after_event') {
      event.trigger = { after_event: trigger.after_event }
    } else {
      event.trigger = {
        vital: trigger.vital,
        operator: trigger.operator,
        value: trigger.value,
      }
    }
    if (trigger.delay > 0) event.trigger.delay_s = trigger.delay
  }

  switch (type.value) {
    case 'pathology':
      event.params = { type: params.pathology }
      if (params.pathology === 'Hemorrhage') {
        event.params.compartment  = params.compartment
        event.params.flowRate     = params.flow_rate
        event.params.flowRateMode = params.rate_mode
        event.params.stopMode     = params.stop_mode
        if (params.stop_mode === 'fixed') {
          event.params.totalVolume  = params.total_volume
          event.params.duration     = params.hemorrhage_duration
          event.params.durationUnit = params.hemorrhage_duration_unit
        } else {
          event.params.stopCondition = {
            vital: params.stop_vital,
            operator: params.stop_operator,
            value: params.stop_value,
          }
          event.params.maxDurationSec = params.stop_max_duration * 60
        }
      } else {
        event.params.severity = params.severity
      }
      break

    case 'intubate':
      event.intubationType = params.intubation
      break

    case 'start_vent':
    case 'change_vent':
      event.params = {
        mode:      params.vent_mode,
        fio2:      params.fio2 / 100,
        peep_cmh2o:params.peep,
        vt_ml:     params.vt,
        rr:        params.rr,
        itime_s:   params.itime,
        flow_lpm:  50,
      }
      break

    case 'start_controller':
      event.params = { controller: params.controller }
      if (params.controller === 'http_controller') {
        event.params.url     = params.http_url
        event.params.timeout = params.http_timeout
        try {
          event.params.config = params.http_config ? JSON.parse(params.http_config) : {}
        } catch {
          console.warn('Invalid controller config JSON')
          event.params.config = {}
        }
      }
      break

    case 'start_fluid_controller':
      event.params = { controller: params.fluid_controller }
      if (params.fluid_controller === 'http_fluid_controller') {
        event.params.url = params.fluid_http_url
      }
      break

    case 'stop_fluid_controller':
      break

    case 'bolus':
      event.params = {
        drug:                params.bolus_drug,
        route:               params.bolus_route,
        concentration:       params.bolus_concentration,
        concentration_unit:  params.bolus_concentration_unit,
        dose_mode:           params.bolus_dose_mode,
      }
      if (params.bolus_dose_mode === 'weight') {
        event.params.dose_per_kg      = params.bolus_weight_dose
        event.params.dose_per_kg_unit = params.bolus_weight_dose_unit
      } else {
        event.params.dose_mL          = params.bolus_volume_mL
        event.params.total_dose       = params.bolus_total_dose
        event.params.total_dose_unit  = params.bolus_total_dose_unit
      }
      break

    case 'infusion':
      event.params = {
        drug:               params.infusion_drug,
        rate_mL_per_min:    params.infusion_rate,
        concentration:      params.infusion_concentration,
        concentration_unit: params.infusion_concentration_unit,
      }
      break

    case 'compound_infusion':
      event.params = {
        compound:       params.compound_fluid,
        rate_mL_per_min:params.compound_rate,
        bag_volume_mL:  params.compound_bag_volume,
      }
      break

    case 'exercise':
      event.params = {
        intensity: params.intensity,
        duration:  params.exercise_duration,
        unit:      params.exercise_duration_unit,
      }
      break
  }

  console.log('FINAL EVENT:', JSON.stringify(event, null, 2))
  emit('add', event)
}
</script>

<template>
  <form @submit="submit" class="panel">
    <h3 class="title">Add Event</h3>

    <!-- ── ACTIVATION ── -->
    <div class="section">
      <div class="label">Activation</div>
      <div class="row">
        <div class="field">
          <label>Mode</label>
          <select v-model="activation">
            <option value="time">⏱️ At Time</option>
            <option value="trigger">🎯 On Condition</option>
          </select>
        </div>
        <template v-if="activation === 'time'">
          <div class="field">
            <label>Time</label>
            <input v-model.number="time" type="number" min="0" />
          </div>
          <div class="field">
            <label>Unit</label>
            <select v-model="timeUnit">
              <option value="min">min</option>
              <option value="sec">sec</option>
              <option value="hr">hr</option>
            </select>
          </div>
        </template>
      </div>
    </div>

    <!-- ── TRIGGER CONDITION ── -->
    <div v-if="activation === 'trigger'" class="section">
      <div class="label">Trigger Condition</div>
      <div class="row">
        <div class="field">
          <label>Trigger Type</label>
          <select v-model="trigger.triggerType">
            <option value="vital">📊 Vital Sign</option>
            <option value="after_event">🔗 After Event</option>
          </select>
        </div>

        <template v-if="trigger.triggerType === 'vital'">
          <div class="field">
            <label>When</label>
            <select v-model="trigger.vital">
              <option value="map_mmhg">MAP (mmHg)</option>
              <option value="hr_bpm">Heart Rate (bpm)</option>
              <option value="lactate_mmol_L">Lactate (mmol/L)</option>
              <option value="spo2_pct">SpO₂ (%)</option>
              <option value="sbp_mmhg">Systolic BP (mmHg)</option>
              <option value="dbp_mmhg">Diastolic BP (mmHg)</option>
              <option value="ph">Blood pH</option>
              <option value="pao2_mmhg">PaO₂ (mmHg)</option>
              <option value="paco2_mmhg">PaCO₂ (mmHg)</option>
              <option value="etco2_mmhg">EtCO₂ (mmHg)</option>
              <option value="co_lpm">Cardiac Output (L/min)</option>
              <option value="rr_patient">Resp Rate (patient)</option>
            </select>
          </div>
          <div class="field">
            <label>Is</label>
            <select v-model="trigger.operator">
              <option value="<=">≤</option>
              <option value=">=">≥</option>
              <option value="<">&lt;</option>
              <option value=">">&gt;</option>
              <option value="==">=</option>
            </select>
          </div>
          <div class="field">
            <label>Value</label>
            <input v-model.number="trigger.value" type="number" step="0.1" />
          </div>
        </template>

        <template v-if="trigger.triggerType === 'after_event'">
          <div class="field">
            <label>After Event</label>
            <select v-model="trigger.after_event">
              <option value="intubate">💉 Intubate</option>
              <option value="start_vent">🌬️ Start Ventilator</option>
              <option value="change_vent">🔧 Change Ventilator</option>
              <option value="pathology">🦠 Pathology</option>
              <option value="start_controller">🎮 Start Controller</option>
              <option value="start_fluid_controller">💉 Start Fluid Controller</option>
              <option value="stop_fluid_controller">🛑 Stop Fluid Controller</option>
              <option value="bolus">💊 Drug Bolus</option>
              <option value="infusion">💧 Drug Infusion</option>
              <option value="compound_infusion">🩸 Compound Infusion</option>
              <option value="exercise">🏃 Exercise</option>
            </select>
          </div>
        </template>

        <div class="field">
          <label>Delay (s)</label>
          <input v-model.number="trigger.delay" type="number" min="0" step="1" />
        </div>
      </div>
    </div>

    <!-- ── EVENT TYPE ── -->
    <div class="section">
      <div class="label">Event Type</div>
      <select v-model="type">
        <option value="pathology">🦠 Apply Pathology</option>
        <option value="intubate">💉 Intubate Patient</option>
        <option value="start_vent">🌬️ Start Ventilator</option>
        <option value="change_vent">🔧 Change Ventilator Settings</option>
        <option value="start_controller">🎮 Start Vent Controller</option>
        <option value="start_fluid_controller">💉 Start Fluid Controller</option>
        <option value="stop_fluid_controller">🛑 Stop Fluid Controller</option>
        <option value="bolus">💊 Drug Bolus (push)</option>
        <option value="infusion">💧 Drug Infusion (drip)</option>
        <option value="compound_infusion">🩸 Fluid/Blood Infusion</option>
        <option value="exercise">🏃 Exercise (↑ Metabolic Rate)</option>
      </select>
    </div>

    <!-- ── PATHOLOGY ── -->
    <div v-if="type === 'pathology'" class="section">
      <div class="row">
        <div class="field">
          <label>Pathology Type</label>
          <select v-model="params.pathology">
            <option value="ARDS">ARDS (Acute Respiratory Distress)</option>
            <option value="AirwayObstruction">Airway Obstruction</option>
            <option value="AcuteStress">Acute Stress Response</option>
            <option value="Hemorrhage">Hemorrhage</option>
          </select>
        </div>
        <div v-if="params.pathology !== 'Hemorrhage'" class="field">
          <label>Severity (0–1)</label>
          <input v-model.number="params.severity" type="number" min="0" max="1" step="0.1" />
        </div>
      </div>

      <template v-if="params.pathology === 'Hemorrhage'">
        <div class="row" style="margin-top: 8px;">
          <div class="field">
            <label>Hemorrhage Location</label>
            <select v-model="params.compartment">
              <option value="RightLeg">Right Leg (≤150 mL/min)</option>
              <option value="LeftLeg">Left Leg (≤150 mL/min)</option>
              <option value="RightArm">Right Arm (≤100 mL/min)</option>
              <option value="LeftArm">Left Arm (≤100 mL/min)</option>
              <option value="Aorta">Aorta — high volume OK</option>
              <option value="VenaCava">Vena Cava — high volume OK</option>
            </select>
          </div>
          <div class="field">
            <label>Rate Mode</label>
            <select v-model="params.rate_mode">
              <option value="absolute">mL/min (absolute)</option>
              <option value="percent_bv">% BV/min (relative)</option>
            </select>
          </div>
          <div class="field">
            <label>Flow Rate</label>
            <input v-model.number="params.flow_rate" type="number" min="1" max="1000" step="10" />
          </div>
          <div class="field">
            <label>Total Volume (mL)</label>
            <input v-model.number="params.total_volume" type="number" min="1" max="3000" step="10" />
          </div>
          <div class="field">
            <label>Duration</label>
            <input v-model.number="params.hemorrhage_duration" type="number" min="0.1" step="0.5" />
          </div>
          <div class="field">
            <label>Unit</label>
            <select v-model="params.hemorrhage_duration_unit">
              <option value="min">min</option>
              <option value="sec">sec</option>
              <option value="hr">hr</option>
            </select>
          </div>
        </div>
        <div class="row" style="margin-top: 8px;">
          <div class="field">
            <label>Stop Mode</label>
            <select v-model="params.stop_mode">
              <option value="fixed">Fixed Duration/Volume</option>
              <option value="conditional">Stop When Condition Met</option>
            </select>
          </div>
        </div>
        <div v-if="params.stop_mode === 'conditional'" class="row" style="margin-top: 8px;">
          <div class="field">
            <label>Stop When</label>
            <select v-model="params.stop_vital">
              <option value="hr_bpm">Heart Rate (bpm)</option>
              <option value="map_mmhg">MAP (mmHg)</option>
              <option value="sbp_mmhg">Systolic BP (mmHg)</option>
              <option value="dbp_mmhg">Diastolic BP (mmHg)</option>
              <option value="spo2_pct">SpO₂ (%)</option>
              <option value="co_lpm">Cardiac Output (L/min)</option>
            </select>
          </div>
          <div class="field">
            <label>Operator</label>
            <select v-model="params.stop_operator">
              <option value=">=">≥ (at or above)</option>
              <option value="<=">≤ (at or below)</option>
              <option value=">">﹥ (above)</option>
              <option value="<">﹤ (below)</option>
            </select>
          </div>
          <div class="field">
            <label>Threshold</label>
            <input v-model.number="params.stop_value" type="number" min="0" step="1" />
          </div>
          <div class="field">
            <label>Max Duration (min)</label>
            <input v-model.number="params.stop_max_duration" type="number" min="1" max="60" step="1" />
          </div>
        </div>
      </template>
    </div>

    <!-- ── INTUBATE ── -->
    <div v-if="type === 'intubate'" class="section">
      <div class="row">
        <div class="field">
          <label>Intubation Type</label>
          <select v-model="params.intubation">
            <optgroup label="Endotracheal">
              <option value="Tracheal">Tracheal (standard ETT)</option>
              <option value="RightMainstem">Right Mainstem (one-lung)</option>
              <option value="LeftMainstem">Left Mainstem (one-lung)</option>
            </optgroup>
            <optgroup label="Airway Adjuncts">
              <option value="Oropharyngeal">Oropharyngeal (OPA)</option>
              <option value="Nasopharyngeal">Nasopharyngeal (NPA)</option>
            </optgroup>
            <optgroup label="Misplacement">
              <option value="Esophageal">Esophageal (misplaced!)</option>
            </optgroup>
          </select>
        </div>
      </div>
    </div>

    <!-- ── VENTILATOR ── -->
    <div v-if="type === 'start_vent' || type === 'change_vent'" class="section">
      <div class="row">
        <div class="field">
          <label>Mode</label>
          <select v-model="params.vent_mode">
            <optgroup label="Volume Control">
              <option value="VC-AC">VC-AC (Assist Control)</option>
              <option value="VC-CMV">VC-CMV (Continuous Mandatory)</option>
              <option value="VC-IMV">VC-IMV (Intermittent Mandatory)</option>
            </optgroup>
            <optgroup label="Pressure Control">
              <option value="PC-AC">PC-AC (Assist Control)</option>
              <option value="PC-CMV">PC-CMV (Continuous Mandatory)</option>
              <option value="PC-IMV">PC-IMV (Intermittent Mandatory)</option>
            </optgroup>
          </select>
        </div>
        <div class="field">
          <label>FiO₂ (%)</label>
          <input v-model.number="params.fio2" type="number" min="21" max="100" step="1" />
        </div>
        <div class="field">
          <label>PEEP</label>
          <input v-model.number="params.peep" type="number" min="0" max="24" step="1" />
        </div>
        <div class="field">
          <label>Vt (mL)</label>
          <input v-model.number="params.vt" type="number" min="200" max="800" step="1" />
        </div>
        <div class="field">
          <label>RR (/min)</label>
          <input v-model.number="params.rr" type="number" min="6" max="35" step="1" />
        </div>
        <div class="field">
          <label>I-Time (s)</label>
          <input v-model.number="params.itime" type="number" min="0.5" max="2.0" step="0.1" />
        </div>
      </div>
    </div>

    <!-- ── VENT CONTROLLER ── -->
    <div v-if="type === 'start_controller'" class="section">
      <div class="row">
        <div class="field">
          <label>Controller</label>
          <select v-model="params.controller">
            <option value="default_controller">Simple FiO₂ Controller</option>
            <option value="ardsnet_controller">ARDSNet Protocol</option>
            <option value="adaptive_controller">Adaptive (Variable Rate)</option>
            <option value="random_walk_controller">🎲 Random Walk (Control Arm)</option>
            <option value="http_controller">🌐 HTTP Controller (External)</option>
          </select>
        </div>
      </div>
      <template v-if="params.controller === 'http_controller'">
        <div class="row" style="margin-top: 8px;">
          <div class="field" style="flex: 2;">
            <label>Controller URL</label>
            <input v-model="params.http_url" placeholder="http://localhost:5001" />
            <span class="help-text">Base URL of your controller's HTTP server</span>
          </div>
          <div class="field">
            <label>Timeout (s)</label>
            <input v-model.number="params.http_timeout" type="number" min="1" max="60" />
          </div>
        </div>
        <div class="row" style="margin-top: 8px;">
          <div class="field" style="flex: 1;">
            <label>Config JSON (optional)</label>
            <textarea v-model="params.http_config" rows="3" placeholder='{"param1": "value1", "param2": 123}'></textarea>
            <span class="help-text">Arbitrary JSON passed to your controller's /init endpoint</span>
          </div>
        </div>
      </template>
    </div>

    <!-- ── FLUID CONTROLLER ── -->
    <div v-if="type === 'start_fluid_controller'" class="section">
      <div class="row">
        <div class="field">
          <label>Fluid Controller</label>
          <select v-model="params.fluid_controller">
            <option value="default_fluid_controller">Standard Resuscitation (MAP 65–75)</option>
            <option value="aggressive_fluid_controller">Aggressive Resuscitation</option>
            <option value="conservative_fluid_controller">Conservative/Permissive Hypotension</option>
            <option value="damage_control_fluid_controller">Damage Control (Blood Priority)</option>
            <option value="http_fluid_controller">🌐 HTTP Controller (External)</option>
          </select>
        </div>
        <div v-if="params.fluid_controller === 'http_fluid_controller'" class="field" style="flex: 2;">
          <label>HTTP URL</label>
          <input v-model="params.fluid_http_url" placeholder="http://localhost:5001/fluid" />
        </div>
      </div>
    </div>

    <!-- ── DRUG BOLUS ── -->
    <div v-if="type === 'bolus'" class="section">
      <div class="row">
        <div class="field">
          <label>Drug</label>
          <select v-model="params.bolus_drug">
            <option value="Rocuronium">Rocuronium (paralytic)</option>
            <option value="Succinylcholine">Succinylcholine (paralytic)</option>
            <option value="Epinephrine">Epinephrine (vasopressor)</option>
            <option value="Fentanyl">Fentanyl (analgesic)</option>
            <option value="Morphine">Morphine (analgesic)</option>
            <option value="Midazolam">Midazolam (sedative)</option>
          </select>
        </div>
        <div class="field">
          <label>Route</label>
          <select v-model="params.bolus_route">
            <option value="Intravenous">IV</option>
            <option value="Intramuscular">IM</option>
          </select>
        </div>
        <div class="field">
          <label>Dosing Mode</label>
          <select v-model="params.bolus_dose_mode">
            <option value="fixed">Fixed Dose</option>
            <option value="weight">Weight-Based (mg/kg)</option>
          </select>
        </div>
      </div>

      <!-- Fixed dose: 3-field auto-calc -->
      <template v-if="params.bolus_dose_mode === 'fixed'">
        <div class="row" style="margin-top: 8px;">
          <div class="field">
            <label>Total Dose {{ bolusCalcField === 'total' ? '(calculated)' : '' }}</label>
            <input
              v-model.number="params.bolus_total_dose"
              type="number" min="0.001" step="0.1"
              :class="{ calculated: bolusCalcField === 'total' }"
              @input="bolusFieldEdited('total')"
            />
          </div>
          <div class="field">
            <label>Unit</label>
            <select v-model="params.bolus_total_dose_unit" @change="bolusRecalculate()">
              <option value="mg">mg</option>
              <option value="ug">μg</option>
              <option value="g">g</option>
            </select>
          </div>
          <div class="field">
            <label>Concentration {{ bolusCalcField === 'conc' ? '(calculated)' : '' }}</label>
            <input
              v-model.number="params.bolus_concentration"
              type="number" min="0.001" step="0.1"
              :class="{ calculated: bolusCalcField === 'conc' }"
              @input="bolusFieldEdited('conc')"
            />
          </div>
          <div class="field">
            <label>Unit</label>
            <select v-model="params.bolus_concentration_unit" @change="bolusRecalculate()">
              <option value="mg/mL">mg/mL</option>
              <option value="ug/mL">μg/mL</option>
              <option value="g/L">g/L</option>
            </select>
          </div>
          <div class="field">
            <label>Volume (mL) {{ bolusCalcField === 'volume' ? '(calculated)' : '' }}</label>
            <input
              v-model.number="params.bolus_volume_mL"
              type="number" min="0.1" step="0.1"
              :class="{ calculated: bolusCalcField === 'volume' }"
              @input="bolusFieldEdited('volume')"
            />
          </div>
        </div>
      </template>

      <!-- Weight-based dose -->
      <template v-if="params.bolus_dose_mode === 'weight'">
        <div class="row" style="margin-top: 8px;">
          <div class="field">
            <label>Dose per kg</label>
            <input v-model.number="params.bolus_weight_dose" type="number" min="0.001" step="0.01" />
          </div>
          <div class="field">
            <label>Unit</label>
            <select v-model="params.bolus_weight_dose_unit">
              <option value="mg/kg">mg/kg</option>
              <option value="ug/kg">μg/kg</option>
              <option value="mcg/kg">mcg/kg</option>
            </select>
          </div>
          <div class="field">
            <label>Concentration</label>
            <input v-model.number="params.bolus_concentration" type="number" min="0.001" step="0.1" />
          </div>
          <div class="field">
            <label>Unit</label>
            <select v-model="params.bolus_concentration_unit">
              <option value="mg/mL">mg/mL</option>
              <option value="ug/mL">μg/mL</option>
              <option value="g/L">g/L</option>
            </select>
          </div>
        </div>
        <span class="help-text">Volume calculated at runtime based on patient weight</span>
      </template>
    </div>

    <!-- ── DRUG INFUSION ── -->
    <div v-if="type === 'infusion'" class="section">
      <div class="row">
        <div class="field">
          <label>Drug</label>
          <select v-model="params.infusion_drug">
            <option value="Propofol">Propofol (sedative)</option>
            <option value="Norepinephrine">Norepinephrine (vasopressor)</option>
            <option value="Epinephrine">Epinephrine (vasopressor)</option>
            <option value="Fentanyl">Fentanyl (analgesic)</option>
            <option value="Morphine">Morphine (analgesic)</option>
            <option value="Midazolam">Midazolam (sedative)</option>
          </select>
        </div>
      </div>
      <div class="row" style="margin-top: 8px;">
        <div class="field">
          <label>Rate (mL/min)</label>
          <input v-model.number="params.infusion_rate" type="number" min="0.1" step="1" />
        </div>
        <div class="field">
          <label>Concentration</label>
          <input v-model.number="params.infusion_concentration" type="number" min="0.001" step="0.1" />
        </div>
        <div class="field">
          <label>Unit</label>
          <select v-model="params.infusion_concentration_unit">
            <option value="mg/mL">mg/mL</option>
            <option value="ug/mL">μg/mL</option>
            <option value="g/L">g/L</option>
          </select>
        </div>
      </div>
      <span class="help-text">Infusion continues until stopped or simulation ends</span>
    </div>

    <!-- ── FLUID / BLOOD INFUSION ── -->
    <div v-if="type === 'compound_infusion'" class="section">
      <div class="row">
        <div class="field">
          <label>Fluid Type</label>
          <select v-model="params.compound_fluid">
            <option value="Saline">Normal Saline</option>
            <option value="Blood">Whole Blood</option>
            <option value="RingersLactate">Ringer's Lactate</option>
          </select>
        </div>
        <div class="field">
          <label>Rate (mL/min)</label>
          <input v-model.number="params.compound_rate" type="number" min="1" step="10" />
        </div>
        <div class="field">
          <label>Bag Volume (mL)</label>
          <input v-model.number="params.compound_bag_volume" type="number" min="100" step="100" />
        </div>
      </div>
      <span class="help-text">Infusion stops when bag is empty</span>
    </div>

    <!-- ── EXERCISE ── -->
    <div v-if="type === 'exercise'" class="section">
      <div class="row">
        <div class="field">
          <label>Intensity (0–1)</label>
          <input v-model.number="params.intensity" type="number" min="0" max="1" step="0.05" />
        </div>
        <div class="field">
          <label>Duration</label>
          <input v-model.number="params.exercise_duration" type="number" min="0" step="1" />
        </div>
        <div class="field">
          <label>Unit</label>
          <select v-model="params.exercise_duration_unit">
            <option value="min">min</option>
            <option value="sec">sec</option>
            <option value="hr">hr</option>
          </select>
        </div>
      </div>
      <span class="help-text">
        0.05 = light activity, 0.1 = moderate, 0.3 = vigorous, 0.5+ = extreme<br />
        Exercise automatically stops after the specified duration
      </span>
    </div>

    <button class="exp-btn submit-btn" type="submit">+ Add Event</button>

  </form>
</template>

<style scoped>
.panel {
  background: #1a1a1a;
  color: white;
  padding: 15px;
  border-radius: 12px;
}
.title { margin-bottom: 10px; }
.section { margin-bottom: 12px; }
.label { color: #bbb; margin-bottom: 5px; }
.row { display: flex; gap: 10px; flex-wrap: wrap; }
.field { display: flex; flex-direction: column; gap: 4px; }
.field label { font-size: 11px; color: #bbb; }

input, select, textarea {
  background: #333;
  border: none;
  border-radius: 8px;
  padding: 10px 12px;
  color: white;
  font-family: inherit;
  font-size: 14px;
}
textarea { resize: vertical; font-family: monospace; font-size: 12px; }
input::placeholder, textarea::placeholder { color: #bbb; }

/* Calculated field indicator */
input.calculated {
  background: #2a3a2a;
  color: #8fc;
}

.help-text { font-size: 11px; color: #888; margin-top: 2px; }

.exp-btn {
  padding: 10px 14px;
  background: #333;
  border: none;
  border-radius: 8px;
  color: white;
  cursor: pointer;
  transition: 0.2s;
}
.exp-btn:hover { background: #444; }
.submit-btn { margin-top: 10px; }
</style>