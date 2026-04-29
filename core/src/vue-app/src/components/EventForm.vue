<script setup>
import { reactive, ref } from 'vue'

const emit = defineEmits(['add'])

const activation = ref('time')
const time = ref(1)
const type = ref('pathology')

const trigger = reactive({
  type: 'vital',
  vital: 'map_mmhg',
  operator: '<=',
  value: 65,
  delay: 0,
  after_event: 'intubate'
})

const params = reactive({
  pathology: 'ARDS',
  severity: 0.5,

  compartment: 'RightLeg',
  rate: 100,
  total_volume: 500,

  intubation: 'Tracheal',

  mode: 'VC-AC',
  fio2: 40,
  peep: 5,
  vt: 420,
  rr: 14,
  itime: 1.0,

  controller: 'default_controller',
  http_url: 'http://localhost:5001',
  timeout: 10,
  config: '',
  fluid_controller: 'default_fluid_controller',

  drug: 'Epinephrine',
  dose: 1,
  route: 'IV',

  infusion_rate: 10,
  concentration: 1,

  fluid: 'Saline',
  bag_volume: 1000,
  compound_rate: 100,

  intensity: 0.1,
  duration: 5,
  duration_unit: 'min'
})

function submit(e) {
  e.preventDefault()

  let event = {
  activation: activation.value,
  type: type.value
}

// ========================
// ACTIVATION
// ========================
if (activation.value === 'time') {
  event.time = time.value
} else {
  event.trigger = { ...trigger }
}

// ========================
// EVENT TYPES
// ========================
switch (type.value) {

  case 'pathology':
    event.pathology = params.pathology
    event.severity = params.severity
    break

  case 'intubate':
    event.intubationType = params.intubation
    break

  case 'start_vent':
  case 'change_vent':
    event.vent_settings = {
      mode: params.mode,
      fio2: params.fio2,
      peep_cmh2o: params.peep,
      vt_ml: params.vt,
      rr: params.rr,
      itime_s: params.itime
    }
    break

  // ========================
  // 🔥 CONTROLLER (MATCHES BACKEND EXACTLY)
  // ========================
  case 'start_controller':
    event.controller = params.controller

    if (params.controller === 'http_controller') {
      event.http_url = params.http_url || 'http://localhost:5001'
      event.http_timeout = params.timeout || 10

      if (params.config) {
        try {
          event.http_config =
            typeof params.config === 'string'
              ? JSON.parse(params.config)
              : params.config
        } catch (err) {
          console.warn('Invalid JSON config')
        }
      }
    }
    break

  // ========================
  // FLUID CONTROLLER
  // ========================
  case 'start_fluid_controller':
    event.controller = params.fluid_controller

    if (params.fluid_controller === 'http_fluid_controller') {
      event.http_url = params.fluid_http_url || 'http://localhost:5001/fluid'
      event.timeout = params.fluid_timeout || 5

      if (params.fluid_config) {
        try {
          event.config =
            typeof params.fluid_config === 'string'
              ? JSON.parse(params.fluid_config)
              : params.fluid_config
        } catch (err) {
          console.warn('Invalid JSON config')
        }
      }
    }
    break

  case 'stop_fluid_controller':
    break

  // ========================
  // MEDICATIONS
  // ========================
  case 'bolus':
    event.drug = params.drug
    event.dose = params.dose
    event.route = params.route
    break

  case 'infusion':
    event.drug = params.drug
    event.rate_ml_per_hr = params.infusion_rate
    event.concentration = params.concentration
    break

  case 'compound_infusion':
    event.compound = params.fluid
    event.rate_ml_per_min = params.compound_rate
    event.bag_volume_mL = params.bag_volume
    break

  // ========================
  // EXERCISE
  // ========================
  case 'exercise':
    event.intensity = params.intensity
    event.duration = params.duration
    event.unit = params.duration_unit
    break
}
  console.log("FINAL EVENT:", JSON.stringify(event, null, 2))
  emit('add', event)
}
</script>

<template>
  <form @submit="submit" class="panel">

  <h3 class="title">Add Event</h3>

  <!-- Activation -->
  <div class="section">
    <div class="label">Activation</div>

    <div class="row">
      <select v-model="activation">
        <option value="time">⏱ Time</option>
        <option value="trigger">🎯 Trigger</option>
      </select>

      <input
        v-if="activation==='time'"
        v-model.number="time"
        type="number"
        placeholder="Time (s)"
      />
    </div>
  </div>

  <!-- Trigger -->
  <div v-if="activation==='trigger'" class="section">
    <div class="label">Trigger Condition</div>

    <div class="row">
      <select v-model="trigger.vital">
        <option value="map_mmhg">MAP</option>
        <option value="hr_bpm">HR</option>
        <option value="spo2_pct">SpO2</option>
      </select>

      <select v-model="trigger.operator">
        <option value="<=">≤</option>
        <option value=">=">≥</option>
      </select>

      <input v-model.number="trigger.value" type="number" />
    </div>
  </div>

  <!-- Type -->
  <div class="section">
    <div class="label">Event Type</div>

    <select v-model="type">
      <option value="pathology">Pathology</option>
      <option value="intubate">Intubate</option>
      <option value="start_vent">Start Vent</option>
      <option value="change_vent">Change Vent</option>
      <option value="start_controller">Controller</option>
      <option value="start_fluid_controller">Start Fluid Controller</option>
      <option value="stop_fluid_controller">Stop Fluid Controller</option>
      <option value="bolus">Drug Bolus</option>
      <option value="infusion">Drug Infusion</option>
      <option value="compound_infusion">Fluid/Blood Infusion</option>
      <option value="exercise">Exercise</option>
    </select>
  </div>

  <!-- Dynamic Params -->
  <div class="section">

    <!-- Dynamic Params -->
<div class="section">

      <!-- ========================= -->
      <!-- PATHOLOGY -->
      <!-- ========================= -->
      <div v-if="type==='pathology'" class="section">
      <!-- Pathology Type -->
      <div class="row">
        <select v-model="params.pathology">
          <option value="ARDS">ARDS (Acute Respiratory Distress)</option>
          <option value="AirwayObstruction">Airway Obstruction</option>
          <option value="AcuteStress">Acute Stress Response</option>
          <option value="Hemorrhage">Hemorrhage</option>
        </select>
      </div>
       <!-- ========================= -->
      <!-- HEMORRHAGE OPTIONS -->
      <!-- ========================= -->
      <div v-if="params.pathology === 'Hemorrhage'" class="section">

        <!-- Location -->
        <div class="row">
          <select v-model="params.compartment">
            <option value="RightLeg">Right Leg (≤150 mL/min)</option>
            <option value="LeftLeg">Left Leg (≤150 mL/min)</option>
            <option value="RightArm">Right Arm (≤100 mL/min)</option>
            <option value="LeftArm">Left Arm (≤100 mL/min)</option>
            <option value="Aorta">Aorta (high volume)</option>
            <option value="VenaCava">Vena Cava (high volume)</option>
          </select>
        </div>

        <!-- Rate Mode -->
        <div class="row">
          <select v-model="params.rate_mode">
            <option value="absolute">mL/min (absolute)</option>
            <option value="percent_bv">% BV/min(Relative)</option>
          </select>
        </div>

        <!-- Core Inputs -->
        <div class="row">
          <input v-model.number="params.total_volume" placeholder="Total Volume (mL)" />
          <input v-model.number="params.flow_rate" placeholder="Flow Rate" />
          <input v-model.number="params.duration" placeholder="Duration" />
          <select v-model="params.duration_unit">
            <option value="min">min</option>
            <option value="sec">sec</option>
            <option value="hr">hr</option>
          </select>
        </div>

        <!-- Stop Mode -->
        <div class="row">
          <select v-model="params.stop_mode">
            <option value="fixed">Fixed (use seperate stop event)</option>
            <option value="conditional">Stop When Condition Met</option>
          </select>
        </div>

        <!-- Conditional Stop -->
        <div v-if="params.stop_mode==='conditional'" class="row">
          <select v-model="params.condition_vital">
            <option value="hr_bpm">Heart Rate (bpm)</option>
            <option value="map_mmhg">MAP (mmHg)</option>
            <option value="sbp_mmhg">SBP (mmHg)</option>
            <option value="spo2_percent">SpO₂ (%)</option>
            <option value="lactate_mmolL">Lactate (mmol/L)</option>
          </select>

          <select v-model="params.condition_operator">
            <option value=">=">≥</option>
            <option value="<=">≤</option>
          </select>

          <input v-model.number="params.condition_value" placeholder="Threshold" />
          <input v-model.number="params.max_duration" placeholder="Max Duration (min)" />
        </div>

      </div>
    </div>

  <!-- ========================= -->
  <!-- DEFAULT (non-hemorrhage) -->
  <!-- ========================= -->
  <div v-if="params.pathology !== 'Hemorrhage'" class="section">

    <!-- Severity -->
    <div class="row">
      <input
        v-model.number="params.severity"
        type="number"
        min="0"
        max="1"
        step="0.1"
        placeholder="Severity (0–1)"
      />
    </div>

    <!-- ========================= -->
    <!-- STOP WHEN CONDITION -->
    <!-- ========================= -->
    <div v-if="params.pathology !== 'Hemorrhage'" class="row">

      <!-- Vital -->
      <select v-model="params.condition_vital">
        <option value="hr_bpm">Heart Rate (bpm)</option>
        <option value="map_mmhg">MAP (mmHg)</option>
        <option value="sbp_mmhg">Systolic BP</option>
        <option value="dbp_mmhg">Diastolic BP</option>
        <option value="spo2_pct">SpO₂ (%)</option>
        <option value="co_lpm">Cardiac Output</option>
      </select>

      <!-- Operator -->
      <select v-model="params.condition_operator">
        <option value=">=">≥</option>
        <option value="<=">≤</option>
        <option value=">">></option>
        <option value="<"><</option>
      </select>

      <!-- Threshold -->
      <input
        v-model.number="params.condition_value"
        type="number"
        placeholder="Threshold"
      />

      <!-- Safety cap -->
      <input
        v-model.number="params.max_duration"
        type="number"
        placeholder="Max Duration (min)"
      />

    </div>

  </div>

      <!-- ========================= -->
      <!-- INTUBATE -->
      <!-- ========================= -->
      <div v-if="type==='intubate'" class="row">
      <select v-model="params.intubation">

        <!-- Endotracheal -->
        <optgroup label="Endotracheal">
          <option value="Tracheal">Tracheal (standard ETT)</option>
          <option value="RightMainstem">Right Mainstem (one-lung)</option>
          <option value="LeftMainstem">Left Mainstem (one-lung)</option>
        </optgroup>

        <!-- Airway Adjuncts -->
        <optgroup label="Airway Adjuncts">
          <option value="Oropharyngeal">Oropharyngeal (OPA)</option>
          <option value="Nasopharyngeal">Nasopharyngeal (NPA)</option>
        </optgroup>

        <!-- Misplacement -->
        <optgroup label="Misplacement">
          <option value="Esophageal">Esophageal (misplaced!)</option>
        </optgroup>

      </select>
    </div>

      <!-- ========================= -->
      <!-- VENT -->
      <!-- ========================= -->
      <div v-if="type==='start_vent' || type==='change_vent'" class="row">
        <input v-model="params.mode" placeholder="Mode (VC-AC)" />
        <input v-model.number="params.fio2" placeholder="FiO2 (%)" />
        <input v-model.number="params.peep" placeholder="PEEP (cmH2O)" />
        <input v-model.number="params.vt" placeholder="VT (mL)" />
        <input v-model.number="params.rr" placeholder="RR (breaths/min)" />
        <input v-model.number="params.itime" placeholder="I-Time (s)" />
      </div>

      <!-- ========================= -->
      <!-- VENT CONTROLLER -->
      <!-- ========================= -->
      <div v-if="type==='start_controller'" class="row">
        <select v-model="params.controller">
          <option value="default_controller">Simple FiO₂</option>
          <option value="ardsnet_controller">ARDSNet</option>
          <option value="adaptive_controller">Adaptive</option>
          <option value="random_walk_controller">Random Walk</option>
          <option value="http_controller">🌐 HTTP Controller</option>
        </select>
      </div>

      <div v-if="type==='start_controller' && params.controller==='http_controller'" class="row">
        <input v-model="params.http_url" placeholder="Controller URL" />
        <input v-model.number="params.timeout" type="number" placeholder="Timeout (s)" />
        <input v-model="params.config" placeholder='JSON config {"target_spo2":0.92}' />
      </div>

      <!-- ========================= -->
      <!-- FLUID CONTROLLER -->
      <!-- ========================= -->
      <div v-if="type==='start_fluid_controller'" class="row">
        <select v-model="params.fluid_controller">
          <option value="standard_resuscitation">Standard Resuscitation (MAP 65–75)</option>
          <option value="aggressive_resuscitation">Aggressive Resuscitation</option>
          <option value="permissive_hypotension">Permissive Hypotension</option>
          <option value="damage_control">Damage Control</option>
          <option value="http_fluid_controller">🌐 HTTP Controller</option>
        </select>
      </div>

      <div v-if="type==='start_fluid_controller' && params.fluid_controller==='http_fluid_controller'" class="row">
        <input v-model="params.fluid_http_url" placeholder="Fluid Controller URL" />
        <input v-model.number="params.fluid_timeout" type="number" placeholder="Timeout (s)" />
        <input v-model="params.fluid_config" placeholder='JSON config {}' />
      </div>

      <!-- ========================= -->
      <!-- DRUG BOLUS -->
      <!-- ========================= -->
      <div v-if="type==='bolus'" class="row">
        <input v-model="params.drug" placeholder="Drug (Epinephrine)" />
        <input v-model.number="params.dose" placeholder="Dose" />
        <select v-model="params.route">
          <option value="IV">IV</option>
          <option value="IM">IM</option>
          <option value="Subcutaneous">Subcutaneous</option>
        </select>
      </div>

      <!-- ========================= -->
      <!-- INFUSION -->
      <!-- ========================= -->
      <div v-if="type==='infusion'" class="row">
        <input v-model="params.drug" placeholder="Drug" />
        <input v-model.number="params.infusion_rate" placeholder="Rate (mL/hr)" />
        <input v-model.number="params.concentration" placeholder="Concentration" />
      </div>

      <!-- ========================= -->
      <!-- COMPOUND INFUSION -->
      <!-- ========================= -->
      <div v-if="type==='compound_infusion'" class="row">
        <select v-model="params.fluid">
          <option value="Saline">Saline</option>
          <option value="Blood">Blood</option>
          <option value="Plasma">Plasma</option>
        </select>

        <input v-model.number="params.compound_rate" placeholder="Rate (mL/min)" />
        <input v-model.number="params.bag_volume" placeholder="Bag Volume (mL)" />
      </div>

      <!-- ========================= -->
      <!-- EXERCISE -->
      <!-- ========================= -->
      <div v-if="type==='exercise'" class="row">
        <input v-model.number="params.intensity" placeholder="Intensity (0–1)" />
        <input v-model.number="params.duration" placeholder="Duration" />

        <select v-model="params.duration_unit">
          <option value="s">Seconds</option>
          <option value="min">Minutes</option>
        </select>
      </div>

    </div>

  </div>

  <button class="exp-btn submit-btn" type="submit">
    + Add Event
  </button>
  </form>
</template>

<style scoped>
.panel {
  background: #1a1a1a;
  color: white;
  padding: 15px;
  border-radius: 12px;
}

.title {
  margin-bottom: 10px;
}

.section {
  margin-bottom: 12px;
}

.label {
  color: #bbb;
  margin-bottom: 5px;
}

.row {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

input,
select {
  background: #333;
  border: none;
  border-radius: 8px;
  padding: 8px 10px;
  color: white;
}

input::placeholder {
  color: #bbb;
}

.exp-btn {
  padding: 10px 14px;
  background: #333;
  border: none;
  border-radius: 8px;
  color: white;
  cursor: pointer;
}

.exp-btn:hover {
  background: #444;
}

.submit-btn {
  margin-top: 10px;
}
</style>