<script setup>
import { reactive, ref, watch } from 'vue'

const emit = defineEmits(['add'])

const activation = ref('time')
const time = ref(1)
const type = ref('pathology')

/* ---------------- TRIGGER ---------------- */
const trigger = reactive({
  type: 'vital',
  vital: 'map_mmhg',
  operator: '<=',
  value: 65,
  delay: 0,
  after_event: 'intubate'
})

/* ---------------- PARAMS ---------------- */
const params = reactive({
  /* pathology */
  pathology: 'ARDS',
  severity: 0.5,

  /* hemorrhage */
  compartment: 'RightLeg',
  rate: 100,
  total_volume: 500,

  /* intubation */
  intubation: 'Tracheal',

  /* ventilator */
  mode: 'VC-AC',
  fio2: 40,
  peep: 5,
  vt: 420,
  rr: 14,
  itime: 1.0,

  /* controller */
  controller: 'default_controller',

  /* fluid controller */
  fluid_controller: 'default_fluid_controller',

  /* drug bolus */
  drug: 'Epinephrine',
  dose: 1,
  route: 'IV',

  /* infusion */
  infusion_rate: 10,
  concentration: 1,

  /* compound infusion */
  fluid: 'Saline',
  bag_volume: 1000,
  compound_rate: 100,

  /* exercise */
  intensity: 0.1,
  duration: 5,
  duration_unit: 'min'
})

/* ---------------- RESET PARAMS PER TYPE ---------------- */
watch(type, () => {
  // ensures clean payload per event
})

function submit(e) {
  e.preventDefault()

  let event = {
    activation: activation.value,
    type: type.value,
    params: {}
  }

  /* ---------- ACTIVATION ---------- */
  if (activation.value === 'time') {
    event.time = time.value
  } else {
    event.trigger = { ...trigger }
  }

  /* ---------- TYPE HANDLING ---------- */

  switch (type.value) {
    case 'pathology':
      event.params = {
        type: params.pathology,
        severity: params.severity,
        compartment: params.compartment,
        rate: params.rate,
        total_volume: params.total_volume
      }
      break

    case 'intubate':
      event.params = {
        type: params.intubation
      }
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
      event.params = {
        controller: params.controller
      }
      break

    case 'start_fluid_controller':
      event.params = {
        controller: params.fluid_controller
      }
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

  console.log("FINAL EVENT:", event)
  emit('add', event)
}
</script>

<template>
  <form @submit="submit" class="event-form">
    <h3>Add Event</h3>

    <!-- Activation -->
    <select v-model="activation">
      <option value="time">⏱ Time</option>
      <option value="trigger">🎯 Trigger</option>
    </select>

    <input v-if="activation==='time'" v-model.number="time" type="number" />

    <!-- Trigger -->
    <div v-if="activation==='trigger'" class="row">
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

    <!-- TYPE -->
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

    <!-- DYNAMIC PARAMS -->

    <div v-if="type==='pathology'">
      <select v-model="params.pathology">
        <option>ARDS</option>
        <option>Hemorrhage</option>
      </select>
      <input v-model.number="params.severity" placeholder="Severity" />
    </div>

    <div v-if="type==='intubate'">
      <select v-model="params.intubation">
        <option>Tracheal</option>
        <option>Esophageal</option>
      </select>
    </div>

    <div v-if="type.includes('vent')">
      <input v-model="params.mode" placeholder="Mode" />
      <input v-model.number="params.fio2" placeholder="FiO2" />
      <input v-model.number="params.peep" placeholder="PEEP" />
      <input v-model.number="params.vt" placeholder="VT" />
      <input v-model.number="params.rr" placeholder="RR" />
      <input v-model.number="params.itime" placeholder="I-Time" />
    </div>

    <div v-if="type==='start_controller'">
      <input v-model="params.controller" />
    </div>

    <div v-if="type.includes('fluid_controller')">
      <input v-model="params.fluid_controller" />
    </div>

    <div v-if="type==='bolus'">
      <input v-model="params.drug" placeholder="Drug" />
      <input v-model.number="params.dose" placeholder="Dose" />
      <input v-model="params.route" placeholder="Route" />
    </div>

    <div v-if="type==='infusion'">
      <input v-model="params.drug" placeholder="Drug" />
      <input v-model.number="params.infusion_rate" placeholder="Rate" />
      <input v-model.number="params.concentration" placeholder="Concentration" />
    </div>

    <div v-if="type==='compound_infusion'">
      <input v-model="params.fluid" placeholder="Fluid" />
      <input v-model.number="params.compound_rate" placeholder="Rate" />
      <input v-model.number="params.bag_volume" placeholder="Bag Volume" />
    </div>

    <div v-if="type==='exercise'">
      <input v-model.number="params.intensity" placeholder="Intensity" />
      <input v-model.number="params.duration" placeholder="Duration" />
    </div>

    <button type="submit">Add Event</button>
  </form>
</template>

<style scoped>
.event-form {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.row {
  display: flex;
  gap: 10px;
}
</style>