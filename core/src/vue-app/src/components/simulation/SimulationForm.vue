<script setup>
import { useSimulationStore } from '@/stores/simulationStore'
const store = useSimulationStore()
</script>

<template>
  <div class="card">
    <h2>Simulation Setup</h2>

    <input v-model="store.job_name" placeholder="Job Name" />

    <div class="row">
      <input type="number" v-model="store.duration" />

      <select v-model="store.duration_unit">
        <option value="min">min</option>
        <option value="sec">sec</option>
        <option value="hr">hr</option>
      </select>

      <input type="number" v-model="store.step_size" />
      <input type="number" v-model="store.replicates" />
    </div>

    <button @click="store.runSimulation()">Run Simulation</button>
  </div>
</template>