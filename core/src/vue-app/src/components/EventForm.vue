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
    type: type.value,
    params: {}
  }

  if (activation.value === 'time') {
    event.time = time.value
  } else {
    event.trigger = { ...trigger }
  }

  switch (type.value) {
    case 'pathology':
      event.params = {
        type: params.pathology,
        severity: params.severity
      }
      break

    case 'intubate':
      event.params = { type: params.intubation }
      break

    case 'start_vent':
    case 'change_vent':
      event.params = {
        mode: params.mode,
        fio2: params.fio2,
        peep: params.peep,
        vt: params.vt,
        rr: params.rr,
        itime: params.itime
      }
      break

    case 'start_controller':
      event.params = { controller: params.controller }
      break

    case 'start_fluid_controller':
      event.params = { controller: params.fluid_controller }
      break

    case 'stop_fluid_controller':
      event.params = {}
      break

    case 'bolus':
      event.params = {
        drug: params.drug,
        dose: params.dose,
        route: params.route
      }
      break

    case 'infusion':
      event.params = {
        drug: params.drug,
        rate: params.infusion_rate,
        concentration: params.concentration
      }
      break

    case 'compound_infusion':
      event.params = {
        fluid: params.fluid,
        rate: params.compound_rate,
        bag_volume: params.bag_volume
      }
      break

    case 'exercise':
      event.params = {
        intensity: params.intensity,
        duration: params.duration,
        unit: params.duration_unit
      }
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
        <option value="start_controller">Vent Controller</option>
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

      <div v-if="type==='pathology'" class="row">
        <select v-model="params.pathology">
          <option>ARDS</option>
          <option>Hemorrhage</option>
        </select>
        <input v-model.number="params.severity" placeholder="Severity" />
      </div>

      <div v-if="type==='intubate'" class="row">
        <select v-model="params.intubation">
          <option>Tracheal</option>
          <option>Esophageal</option>
        </select>
      </div>

      <div v-if="type.includes('vent')" class="row">
        <input v-model="params.mode" placeholder="Mode" />
        <input v-model.number="params.fio2" placeholder="FiO2" />
        <input v-model.number="params.peep" placeholder="PEEP" />
        <input v-model.number="params.vt" placeholder="VT" />
        <input v-model.number="params.rr" placeholder="RR" />
        <input v-model.number="params.itime" placeholder="I-Time" />
      </div>

    </div>

    <!-- Submit -->
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