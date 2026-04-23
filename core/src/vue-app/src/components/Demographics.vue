<script setup>
import { useSimulationStore } from '@/stores/simulationStore'

const store = useSimulationStore()
</script>

<template>
  <div class="card">
    <h2>Patient Demographics</h2>

    <div
      v-for="(demo, i) in store.demographics"
      :key="i"
      class="row"
    >
      <input
        v-model="demo.name"
        placeholder="Patient Type (e.g. soldier)"
      />

      <input
        type="number"
        v-model.number="demo.percent"
        placeholder="%"
      />

      <button @click="store.removeDemographic(i)">❌</button>
    </div>

    <button @click="store.addDemographic()">+ Add Demographic</button>
  </div>
</template>

<style scoped>
.card {
  background: #222;
  padding: 20px;
  border-radius: 10px;
}

.row {
  display: flex;
  gap: 10px;
  margin-bottom: 10px;
}
</style>