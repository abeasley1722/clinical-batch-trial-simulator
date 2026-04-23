<template>
  <div class="card">
    <h3>Batch Setup</h3>

    <div class="row">
      <input v-model="store.batchName" placeholder="Batch Name" />

      <input v-model.number="store.duration" type="number" />
      <select v-model="store.durationUnit">
        <option value="min">min</option>
        <option value="sec">sec</option>
        <option value="hr">hr</option>
      </select>

      <input v-model.number="store.workers" type="number" />
      <input v-model.number="store.replicates" type="number" />
    </div>

    <h4>Patients</h4>
    <div class="patients">
      <label v-for="p in patients" :key="p">
        <input type="checkbox" :value="p" v-model="store.selectedPatients" />
        {{ p }}
      </label>
    </div>
  </div>
</template>

<script setup>
import { useSimulationStore } from '../stores/simulationStore'
const store = useSimulationStore()

const patients = [
  'StandardMale',
  'StandardFemale',
  'ARDS',
  'Hemorrhage'
]
</script>

<style scoped>
.card { background:white; padding:20px; border-radius:8px; margin-bottom:20px; }
.row { display:flex; gap:10px; flex-wrap:wrap; }
.patients { display:flex; gap:10px; flex-wrap:wrap; }
</style>