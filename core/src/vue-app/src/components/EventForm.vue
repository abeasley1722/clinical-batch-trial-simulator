<!-- src/components/AddEventForm.vue -->
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
  rate_mode: 'absolute',
  flow_rate: 100,
  total_volume: 500,
  stop_mode: 'fixed',
  condition_vital: 'hr_bpm',
  condition_operator: '>=',
  condition_value: 120,
  max_duration: 10,

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

  fluid_controller: 'standard_resuscitation',
  fluid_http_url: 'http://localhost:5001/fluid',
  fluid_timeout: 5,
  fluid_config: '',

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

  const event = {
    activation: activation.value,
    type: type.value
  }

  if (activation.value === 'time') {
    event.time = time.value
  } else {
    event.trigger = { ...trigger }
  }

  switch (type.value) {
    case 'pathology':
      event.pathology = params.pathology
      event.severity = params.severity

      if (params.pathology === 'Hemorrhage') {
        event.compartment = params.compartment
        event.rate_mode = params.rate_mode
        event.total_volume = params.total_volume
        event.flow_rate = params.flow_rate
        event.duration = params.duration
        event.duration_unit = params.duration_unit
        event.stop_mode = params.stop_mode

        if (params.stop_mode === 'conditional') {
          event.condition_vital = params.condition_vital
          event.condition_operator = params.condition_operator
          event.condition_value = params.condition_value
          event.max_duration = params.max_duration
        }
      } else {
        event.condition_vital = params.condition_vital
        event.condition_operator = params.condition_operator
        event.condition_value = params.condition_value
        event.max_duration = params.max_duration
      }
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
          } catch {
            console.warn('Invalid JSON config')
          }
        }
      }
      break

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
          } catch {
            console.warn('Invalid JSON config')
          }
        }
      }
      break

    case 'stop_fluid_controller':
      break

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

    case 'exercise':
      event.intensity = params.intensity
      event.duration = params.duration
      event.unit = params.duration_unit
      break
  }

  console.log('FINAL EVENT:', JSON.stringify(event, null, 2))
  emit('add', event)
}
</script>

<template>
  <form @submit="submit" class="panel">
    <h3 class="title">Add Event</h3>

    <div class="section">
      <div class="label">Activation</div>

      <div class="field-group">
        <label class="field">
          <span class="field-label">Activation Mode</span>
          <select v-model="activation">
            <option value="time">⏱ Time</option>
            <option value="trigger">🎯 Trigger</option>
          </select>
        </label>

        <label v-if="activation === 'time'" class="field">
          <span class="field-label">Time (seconds)</span>
          <input v-model.number="time" type="number" min="0" />
        </label>
      </div>
    </div>

    <div v-if="activation === 'trigger'" class="section">
      <div class="label">Trigger Condition</div>

      <div class="field-group">
        <label class="field">
          <span class="field-label">Vital</span>
          <select v-model="trigger.vital">
            <option value="map_mmhg">MAP</option>
            <option value="hr_bpm">HR</option>
            <option value="spo2_pct">SpO2</option>
          </select>
        </label>

        <label class="field">
          <span class="field-label">Operator</span>
          <select v-model="trigger.operator">
            <option value="<=">≤</option>
            <option value=">=">≥</option>
          </select>
        </label>

        <label class="field">
          <span class="field-label">Threshold</span>
          <input v-model.number="trigger.value" type="number" />
        </label>
      </div>
    </div>

    <div class="section">
      <div class="label">Event Type</div>

      <label class="field">
        <span class="field-label">Type</span>
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
      </label>
    </div>

    <div class="section">
      <div class="label">Parameters</div>

      <template v-if="type === 'pathology'">
        <div class="field-group">
          <label class="field">
            <span class="field-label">Pathology</span>
            <select v-model="params.pathology">
              <option value="ARDS">ARDS (Acute Respiratory Distress)</option>
              <option value="AirwayObstruction">Airway Obstruction</option>
              <option value="AcuteStress">Acute Stress Response</option>
              <option value="Hemorrhage">Hemorrhage</option>
            </select>
          </label>
        </div>

        <div v-if="params.pathology === 'Hemorrhage'" class="subsection">
          <div class="field-group">
            <label class="field">
              <span class="field-label">Bleed Location</span>
              <select v-model="params.compartment">
                <option value="RightLeg">Right Leg (≤150 mL/min)</option>
                <option value="LeftLeg">Left Leg (≤150 mL/min)</option>
                <option value="RightArm">Right Arm (≤100 mL/min)</option>
                <option value="LeftArm">Left Arm (≤100 mL/min)</option>
                <option value="Aorta">Aorta (high volume)</option>
                <option value="VenaCava">Vena Cava (high volume)</option>
              </select>
            </label>

            <label class="field">
              <span class="field-label">Rate Mode</span>
              <select v-model="params.rate_mode">
                <option value="absolute">mL/min (absolute)</option>
                <option value="percent_bv">% BV/min (relative)</option>
              </select>
            </label>
          </div>

          <div class="field-group">
            <label class="field">
              <span class="field-label">Total Volume (mL)</span>
              <input v-model.number="params.total_volume" type="number" min="0" />
            </label>

            <label class="field">
              <span class="field-label">Flow Rate</span>
              <input v-model.number="params.flow_rate" type="number" min="0" />
            </label>

            <label class="field">
              <span class="field-label">Duration</span>
              <input v-model.number="params.duration" type="number" min="0" />
            </label>

            <label class="field">
              <span class="field-label">Duration Unit</span>
              <select v-model="params.duration_unit">
                <option value="min">min</option>
                <option value="sec">sec</option>
                <option value="hr">hr</option>
              </select>
            </label>
          </div>

          <div class="field-group">
            <label class="field">
              <span class="field-label">Stop Mode</span>
              <select v-model="params.stop_mode">
                <option value="fixed">Fixed (use separate stop event)</option>
                <option value="conditional">Stop When Condition Met</option>
              </select>
            </label>
          </div>

          <div v-if="params.stop_mode === 'conditional'" class="field-group">
            <label class="field">
              <span class="field-label">Condition Vital</span>
              <select v-model="params.condition_vital">
                <option value="hr_bpm">Heart Rate (bpm)</option>
                <option value="map_mmhg">MAP (mmHg)</option>
                <option value="sbp_mmhg">SBP (mmHg)</option>
                <option value="spo2_percent">SpO₂ (%)</option>
                <option value="lactate_mmolL">Lactate (mmol/L)</option>
              </select>
            </label>

            <label class="field">
              <span class="field-label">Condition Operator</span>
              <select v-model="params.condition_operator">
                <option value=">=">≥</option>
                <option value="<=">≤</option>
              </select>
            </label>

            <label class="field">
              <span class="field-label">Condition Threshold</span>
              <input v-model.number="params.condition_value" type="number" />
            </label>

            <label class="field">
              <span class="field-label">Max Duration (min)</span>
              <input v-model.number="params.max_duration" type="number" min="0" />
            </label>
          </div>
        </div>

        <div v-else class="subsection">
          <div class="field-group">
            <label class="field">
              <span class="field-label">Severity (0–1)</span>
              <input
                v-model.number="params.severity"
                type="number"
                min="0"
                max="1"
                step="0.1"
              />
            </label>
          </div>

          <div class="field-group">
            <label class="field">
              <span class="field-label">Stop Condition Vital</span>
              <select v-model="params.condition_vital">
                <option value="hr_bpm">Heart Rate (bpm)</option>
                <option value="map_mmhg">MAP (mmHg)</option>
                <option value="sbp_mmhg">Systolic BP</option>
                <option value="dbp_mmhg">Diastolic BP</option>
                <option value="spo2_pct">SpO₂ (%)</option>
                <option value="co_lpm">Cardiac Output</option>
              </select>
            </label>

            <label class="field">
              <span class="field-label">Stop Condition Operator</span>
              <select v-model="params.condition_operator">
                <option value=">=">≥</option>
                <option value="<=">≤</option>
                <option value=">">&gt;</option>
                <option value="<">&lt;</option>
              </select>
            </label>

            <label class="field">
              <span class="field-label">Threshold</span>
              <input v-model.number="params.condition_value" type="number" />
            </label>

            <label class="field">
              <span class="field-label">Max Duration (min)</span>
              <input v-model.number="params.max_duration" type="number" min="0" />
            </label>
          </div>
        </div>
      </template>

      <template v-if="type === 'intubate'">
        <div class="field-group">
          <label class="field">
            <span class="field-label">Intubation Type</span>
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
          </label>
        </div>
      </template>

      <template v-if="type === 'start_vent' || type === 'change_vent'">
        <div class="field-group">
          <label class="field">
            <span class="field-label">Mode</span>
            <input v-model="params.mode" />
          </label>

          <label class="field">
            <span class="field-label">FiO2 (%)</span>
            <input v-model.number="params.fio2" type="number" min="0" />
          </label>

          <label class="field">
            <span class="field-label">PEEP (cmH2O)</span>
            <input v-model.number="params.peep" type="number" min="0" />
          </label>

          <label class="field">
            <span class="field-label">VT (mL)</span>
            <input v-model.number="params.vt" type="number" min="0" />
          </label>

          <label class="field">
            <span class="field-label">RR (breaths/min)</span>
            <input v-model.number="params.rr" type="number" min="0" />
          </label>

          <label class="field">
            <span class="field-label">I-Time (s)</span>
            <input v-model.number="params.itime" type="number" min="0" step="0.1" />
          </label>
        </div>
      </template>

      <template v-if="type === 'start_controller'">
        <div class="field-group">
          <label class="field">
            <span class="field-label">Vent Controller</span>
            <select v-model="params.controller">
              <option value="default_controller">Simple FiO₂</option>
              <option value="ardsnet_controller">ARDSNet</option>
              <option value="adaptive_controller">Adaptive</option>
              <option value="random_walk_controller">Random Walk</option>
              <option value="http_controller">🌐 HTTP Controller</option>
            </select>
          </label>
        </div>

        <div
          v-if="params.controller === 'http_controller'"
          class="field-group"
        >
          <label class="field">
            <span class="field-label">Controller URL</span>
            <input v-model="params.http_url" type="url" />
          </label>

          <label class="field">
            <span class="field-label">Timeout (s)</span>
            <input v-model.number="params.timeout" type="number" min="0" />
          </label>

          <label class="field">
            <span class="field-label">JSON Config</span>
            <input v-model="params.config" />
          </label>
        </div>
      </template>

      <template v-if="type === 'start_fluid_controller'">
        <div class="field-group">
          <label class="field">
            <span class="field-label">Fluid Controller</span>
            <select v-model="params.fluid_controller">
              <option value="standard_resuscitation">Standard Resuscitation (MAP 65–75)</option>
              <option value="aggressive_resuscitation">Aggressive Resuscitation</option>
              <option value="permissive_hypotension">Permissive Hypotension</option>
              <option value="damage_control">Damage Control</option>
              <option value="http_fluid_controller">🌐 HTTP Controller</option>
            </select>
          </label>
        </div>

        <div
          v-if="params.fluid_controller === 'http_fluid_controller'"
          class="field-group"
        >
          <label class="field">
            <span class="field-label">Fluid Controller URL</span>
            <input v-model="params.fluid_http_url" type="url" />
          </label>

          <label class="field">
            <span class="field-label">Timeout (s)</span>
            <input v-model.number="params.fluid_timeout" type="number" min="0" />
          </label>

          <label class="field">
            <span class="field-label">JSON Config</span>
            <input v-model="params.fluid_config" />
          </label>
        </div>
      </template>

      <template v-if="type === 'bolus'">
        <div class="field-group">
          <label class="field">
            <span class="field-label">Drug</span>
            <input v-model="params.drug" />
          </label>

          <label class="field">
            <span class="field-label">Dose</span>
            <input v-model.number="params.dose" type="number" min="0" step="any" />
          </label>

          <label class="field">
            <span class="field-label">Route</span>
            <select v-model="params.route">
              <option value="IV">IV</option>
              <option value="IM">IM</option>
              <option value="Subcutaneous">Subcutaneous</option>
            </select>
          </label>
        </div>
      </template>

      <template v-if="type === 'infusion'">
        <div class="field-group">
          <label class="field">
            <span class="field-label">Drug</span>
            <input v-model="params.drug" />
          </label>

          <label class="field">
            <span class="field-label">Rate (mL/hr)</span>
            <input v-model.number="params.infusion_rate" type="number" min="0" />
          </label>

          <label class="field">
            <span class="field-label">Concentration</span>
            <input v-model.number="params.concentration" type="number" min="0" step="any" />
          </label>
        </div>
      </template>

      <template v-if="type === 'compound_infusion'">
        <div class="field-group">
          <label class="field">
            <span class="field-label">Fluid / Compound</span>
            <select v-model="params.fluid">
              <option value="Saline">Saline</option>
              <option value="Blood">Blood</option>
              <option value="Plasma">Plasma</option>
            </select>
          </label>

          <label class="field">
            <span class="field-label">Rate (mL/min)</span>
            <input v-model.number="params.compound_rate" type="number" min="0" />
          </label>

          <label class="field">
            <span class="field-label">Bag Volume (mL)</span>
            <input v-model.number="params.bag_volume" type="number" min="0" />
          </label>
        </div>
      </template>

      <template v-if="type === 'exercise'">
        <div class="field-group">
          <label class="field">
            <span class="field-label">Intensity (0–1)</span>
            <input v-model.number="params.intensity" type="number" min="0" max="1" step="0.1" />
          </label>

          <label class="field">
            <span class="field-label">Duration</span>
            <input v-model.number="params.duration" type="number" min="0" />
          </label>

          <label class="field">
            <span class="field-label">Duration Unit</span>
            <select v-model="params.duration_unit">
              <option value="s">Seconds</option>
              <option value="min">Minutes</option>
            </select>
          </label>
        </div>
      </template>
    </div>

    <button class="exp-btn submit-btn" type="submit" aria-label="Add event">
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

.section,
.subsection {
  padding: 10px;
  border-radius: 10px;
  background: rgba(209, 202, 202, 0.041);
}

.subsection {
  margin-top: 10px;
}

.label {
  color: #bbb;
  margin-bottom: 8px;
  font-weight: 600;
}

.field-group {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  align-items: flex-start;
  margin-bottom: 10px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex: 1;
  min-width: 180px;
}

.field-label {
  font-size: 12px;
  color: #cfcfcf;
}

input,
select {
  background: #333;
  border: none;
  border-radius: 8px;
  padding: 10px 12px;
  color: white;
  font-size: 13px;
  min-width: 120px;
  width: 100%;
  box-sizing: border-box;
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