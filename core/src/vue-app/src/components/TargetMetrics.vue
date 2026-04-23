<script setup>
import { useSimulationStore } from '@/stores/simulationStore'

const store = useSimulationStore()

const metricLabels = {
  hr_bpm: 'Heart Rate (bpm)',
  spo2_pct: 'SpO₂ (%)',
  etco2_mmhg: 'EtCO₂ (mmHg)',
  rr_patient: 'Respiratory Rate'
}
</script>

<template>
  <div class="card">
    <h2>Target Metrics</h2>

    <div
      v-for="(metric, key) in store.targetMetrics"
      :key="key"
      class="metric-row"
    >
      <h3>{{ metricLabels[key] || key }}</h3>

      <label>Target</label>
      <input
        type="number"
        v-model.number="metric.target_value"
      />

      <label>Tolerance</label>
      <input
        type="number"
        v-model.number="metric.tolerance"
      />

      <label>Match Function</label>
      <input
        v-model="metric.matching_function"
        placeholder="optional"
      />
    </div>
  </div>
</template>

<style scoped>
.card {
  background: #222;
  padding: 20px;
  border-radius: 10px;
}

.metric-row {
  border-bottom: 1px solid #444;
  padding: 10px 0;
  display: flex;
  gap: 10px;
  align-items: center;
}
</style>