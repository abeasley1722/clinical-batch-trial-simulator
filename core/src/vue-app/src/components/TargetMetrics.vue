<script setup>
import { ref, computed } from 'vue'
import { useSimulationStore } from '@/stores/simulationStore'

const store = useSimulationStore()

const availableMetrics = [
  { key: "hr_bpm", label: "Heart Rate (bpm)" },
  { key: "spo2_pct", label: "SpO2 (%)" },
  { key: "etco2_mmhg", label: "EtCO2 (mmHg)" },
  { key: "rr_patient", label: "Resp Rate" },
  { key: "sbp_mmhg", label: "Systolic BP" },
  { key: "dbp_mmhg", label: "Diastolic BP" },
  { key: "map_mmhg", label: "Mean Arterial Pressure" }
]

const selectedMetric = ref(null)

const filteredMetrics = computed(() =>
  availableMetrics.filter(m => !(m.key in store.targetMetrics))
)

function getLabel(key) {
  return availableMetrics.find(m => m.key === key)?.label || key
}

function addMetric() {
  if (!selectedMetric.value) return
  store.addTargetMetric(selectedMetric.value)
  selectedMetric.value = null
}
</script>

<template>
  <div class="panel">
    <h3 class="title">Target Metrics</h3>

    <!-- ➕ Add Metric -->
    <div class="row">
      <select v-model="selectedMetric">
        <option :value="null" disabled>Select Metric</option>
        <option v-for="m in filteredMetrics" :key="m.key" :value="m.key">
          {{ m.label }}
        </option>
      </select>

      <button
        class="exp-btn"
        @click="addMetric"
        :disabled="!selectedMetric"
      >
        + Add
      </button>
    </div>

    <!-- Empty -->
    <p v-if="filteredMetrics.length === 0" class="muted">
      All metrics added
    </p>

    <!-- Selected Metrics -->
    <div
      v-for="(metric, key) in store.targetMetrics"
      :key="key"
      class="metric-row"
    >
      <div class="metric-label">
        {{ getLabel(key) }}
      </div>

      <div class="field">
        <label>Target Value</label>
        <input
          type="number"
          v-model.number="metric.target_value"
          placeholder="Target"
        />
      </div>

      <div class="field">
        <label>Tolerance</label>
        <input
          type="number"
          min="0"
          v-model.number="metric.tolerance"
          placeholder="Tolerance"
        />
      </div>

      <div class="field">
        <label>Matching Function</label>
        <input
          v-model="metric.matching_function"
          placeholder="Match Function"
        />
      </div>

      <button class="icon-btn" @click="store.removeTargetMetric(key)">
        ✖
      </button>
    </div>
  </div>
</template>

<style scoped>
/* ========================
   PANEL (MATCH DASHBOARD)
======================== */
.panel {
  background: #1a1a1a;
  color: white;
  padding: 15px;
  border-radius: 12px;
}

/* ========================
   TITLES
======================== */
.title {
  margin-bottom: 10px;
}

.muted {
  color: #bbb;
  margin-bottom: 10px;
}

/* ========================
   ROWS
======================== */
.row {
  display: flex;
  gap: 10px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.metric-row {
  display: flex;
  gap: 10px;
  align-items: center;
  margin-bottom: 10px;
  flex-wrap: wrap;
}

.metric-label {
  min-width: 150px;
  color: #bbb;
  font-weight: 500;
}

/* ========================
   FIELD (LABEL + INPUT STACK)
======================== */
.field {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.field label {
  font-size: 11px;
  color: #bbb;
}

/* ========================
   INPUTS
======================== */
input,
select {
  background: #333;
  border: none;
  border-radius: 8px;
  padding: 8px 10px;
  color: white;
  outline: none;
}

input::placeholder {
  color: #bbb;
}

/* ========================
   BUTTONS (MATCH exp-btn)
======================== */
.exp-btn {
  padding: 8px 14px;
  background: #333;
  border: none;
  border-radius: 8px;
  color: white;
  cursor: pointer;
  transition: 0.2s;
}

.exp-btn:hover {
  background: #444;
}

.exp-btn:active {
  background: #222;
}

.exp-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* ========================
   ICON BUTTON
======================== */
.icon-btn {
  background: #333;
  border: none;
  border-radius: 6px;
  color: white;
  padding: 6px 10px;
  cursor: pointer;
}

.icon-btn:hover {
  background: #555;
}
</style>