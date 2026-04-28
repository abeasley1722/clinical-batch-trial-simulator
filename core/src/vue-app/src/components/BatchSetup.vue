<template>
  <div class="card">
    <h3>Batch Setup</h3>

    <div class="row">
      <input v-model="store.name" placeholder="Batch Name" />

      <input v-model.number="store.duration" type="number" placeholder="Duration (s)" />
      <input v-model.number="store.workers" type="number" placeholder="Workers" />
      <input v-model.number="store.replicates" type="number" placeholder="Replicates" />
    </div>

    <h4>Patient Count</h4>
    <input v-model.number="store.patientCount" type="number" />

    <h4>Demographics</h4>

    <div v-for="(demo, i) in store.demographics" :key="i" class="row">
      <select v-model="demo.name">
        <option disabled value="">Select Patient</option>
        <option v-for="p in patients" :key="p" :value="p">
          {{ p }}
        </option>
      </select>

      <input type="number" v-model.number="demo.percent" placeholder="%" />

      <button @click="store.removeDemographic(i)">❌</button>
    </div>

    <button @click="store.demographics.push({ name: '', percent: 0 })">
      + Add Demographic
    </button>
  </div>
</template>

<script setup>
import { useSimulationStore } from '@/stores/simulationStore'
const store = useSimulationStore()

const patients = ['soldier', 'adult', 'StandardMale', 'StandardFemale']
</script>

<style scoped>
.card { background: white; padding: 20px; border-radius: 8px; }
.row { display: flex; gap: 10px; flex-wrap: wrap; }
</style>