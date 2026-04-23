<script setup>
import { useSimulationStore } from '@/stores/simulationStore'

const store = useSimulationStore()

// ================= EVENT TYPES =================
const EVENT_TYPES = [
  'pathology',
  'intubate',
  'start_vent',
  'change_vent',
  'start_controller',
  'start_fluid_controller',
  'stop_fluid_controller',
  'bolus',
  'infusion',
  'compound_infusion',
  'exercise'
]

// ================= DEFAULT PARAMS =================
function getDefaultParams(type) {
  switch (type) {

    case 'pathology':
      return {
        pathology: 'ARDS',
        severity: 0.5
      }

    case 'intubate':
      return {
        type: 'Tracheal'
      }

    case 'start_vent':
    case 'change_vent':
      return {
        mode: 'VC-AC',
        fio2: 40,
        peep: 5,
        vt: 420,
        rr: 14,
        itime: 1.0
      }

    case 'start_controller':
      return {
        controller: 'default_controller'
      }

    case 'start_fluid_controller':
      return {
        controller: 'default_fluid_controller',
        target_map: 65
      }

    case 'stop_fluid_controller':
      return {
        controller: 'default_fluid_controller'
      }

    case 'bolus':
      return {
        drug: 'Fentanyl',
        route: 'Intravenous',
        total_dose: 100,
        dose_unit: 'ug',
        concentration: 0.05,
        concentration_unit: 'mg/mL'
      }

    case 'infusion':
      return {
        drug: 'Propofol',
        rate: 100,
        concentration: 10,
        concentration_unit: 'mg/mL'
      }

    case 'compound_infusion':
      return {
        fluid: 'Saline',
        rate: 100,
        bag_volume: 1000
      }

    case 'exercise':
      return {
        intensity: 0.1,
        duration: 5,
        unit: 'min'
      }

    default:
      return {}
  }
}

// ================= ADD EVENT =================
function addEvent() {
  store.events.push({
    activation: 'time',

    // time mode
    time: 1,
    time_unit: 'min',

    // trigger mode
    triggerType: 'vital',
    triggerVital: 'map_mmhg',
    triggerOperator: '<=',
    triggerValue: 65,
    triggerDelay: 0,

    type: 'pathology',
    params: getDefaultParams('pathology')
  })
}

// ================= CHANGE TYPE =================
function changeType(event, newType) {
  event.type = newType
  event.params = getDefaultParams(newType)
}

// ================= REMOVE =================
function removeEvent(i) {
  store.events.splice(i, 1)
}
</script>

<template>
  <div class="card">
    <h2>Event Timeline</h2>

    <div v-for="(event, i) in store.events" :key="i" class="event-row">

      <!-- ACTIVATION -->
      <select v-model="event.activation">
        <option value="time">⏱️ Time</option>
        <option value="trigger">🎯 Trigger</option>
      </select>

      <!-- TIME MODE -->
      <div v-if="event.activation === 'time'" class="inline">
        <input type="number" v-model="event.time" />
        <select v-model="event.time_unit">
          <option>sec</option>
          <option>min</option>
          <option>hr</option>
        </select>
      </div>

      <!-- TRIGGER MODE -->
      <div v-if="event.activation === 'trigger'" class="grid">

        <select v-model="event.triggerType">
          <option value="vital">Vital</option>
          <option value="after_event">After Event</option>
        </select>

        <select v-model="event.triggerVital">
          <option value="map_mmhg">MAP</option>
          <option value="hr_bpm">HR</option>
          <option value="spo2_pct">SpO₂</option>
        </select>

        <select v-model="event.triggerOperator">
          <option value="<=">≤</option>
          <option value=">=">≥</option>
          <option value="<"><</option>
          <option value=">">></option>
        </select>

        <input type="number" v-model="event.triggerValue" />

        <input type="number" v-model="event.triggerDelay" placeholder="Delay (s)" />

      </div>

      <!-- TYPE -->
      <select :value="event.type" @change="changeType(event, $event.target.value)">
        <option v-for="t in EVENT_TYPES" :key="t" :value="t">
          {{ t }}
        </option>
      </select>

      <!-- ================= PARAMS ================= -->

      <!-- PATHOLOGY -->
      <div v-if="event.type === 'pathology'">
        <input v-model="event.params.pathology" />
        <input v-model="event.params.severity" type="number" step="0.1" />
      </div>

      <!-- INTUBATE -->
      <div v-if="event.type === 'intubate'">
        <select v-model="event.params.type">
          <option>Tracheal</option>
          <option>RightMainstem</option>
          <option>LeftMainstem</option>
          <option>Esophageal</option>
        </select>
      </div>

      <!-- VENT -->
      <div v-if="event.type.includes('vent')" class="grid">
        <select v-model="event.params.mode">
          <option>VC-AC</option>
          <option>VC-CMV</option>
          <option>PC-AC</option>
        </select>

        <input v-model="event.params.fio2" placeholder="FiO2" />
        <input v-model="event.params.peep" placeholder="PEEP" />
        <input v-model="event.params.vt" placeholder="Vt" />
        <input v-model="event.params.rr" placeholder="RR" />
        <input v-model="event.params.itime" placeholder="I-Time" />
      </div>

      <!-- CONTROLLER -->
      <div v-if="event.type === 'start_controller'">
        <select v-model="event.params.controller">
          <option>default_controller</option>
          <option>ardsnet_controller</option>
          <option>adaptive_controller</option>
        </select>
      </div>

      <!-- FLUID CONTROLLER -->
      <div v-if="event.type === 'start_fluid_controller'">
        <input v-model="event.params.target_map" placeholder="Target MAP" />
      </div>

      <!-- STOP FLUID -->
      <div v-if="event.type === 'stop_fluid_controller'">
        <span>No extra params needed</span>
      </div>

      <!-- BOLUS -->
      <div v-if="event.type === 'bolus'" class="grid">
        <input v-model="event.params.drug" />
        <input v-model="event.params.total_dose" />
        <input v-model="event.params.concentration" />
      </div>

      <!-- INFUSION -->
      <div v-if="event.type === 'infusion'" class="grid">
        <input v-model="event.params.drug" />
        <input v-model="event.params.rate" />
      </div>

      <!-- COMPOUND -->
      <div v-if="event.type === 'compound_infusion'" class="grid">
        <input v-model="event.params.fluid" />
        <input v-model="event.params.rate" />
        <input v-model="event.params.bag_volume" />
      </div>

      <!-- EXERCISE -->
      <div v-if="event.type === 'exercise'" class="inline">
        <input v-model="event.params.intensity" />
        <input v-model="event.params.duration" />
      </div>

      <button @click="removeEvent(i)">Remove</button>

    </div>

    <button @click="addEvent()">+ Add Event</button>
  </div>
</template>

<style scoped>
.event-row {
  border: 1px solid #ccc;
  padding: 10px;
  margin-bottom: 10px;
}

.inline {
  display: flex;
  gap: 8px;
}

.grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 6px;
}
</style>