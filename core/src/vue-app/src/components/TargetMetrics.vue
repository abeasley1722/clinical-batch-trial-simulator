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

// ✅ safer filtering
const filteredMetrics = computed(() =>
  availableMetrics.filter(m => !(m.key in store.targetMetrics))
)

// 🔥 helper to get label
function getLabel(key) {
  return availableMetrics.find(m => m.key === key)?.label || key
}

function addMetric() {
  if (!selectedMetric.value) return

  store.addTargetMetric(selectedMetric.value)

  selectedMetric.value = null // ✅ proper reset
}
</script>

<template>
  <div class="card">
    <h2>Target Metrics</h2>

    <!-- ➕ Add Metric -->
    <div class="add-row">
      <select v-model="selectedMetric">
        <option :value="null" disabled>Select Metric</option>

        <option
          v-for="m in filteredMetrics"
          :key="m.key"
          :value="m.key"
        >
          {{ m.label }}
        </option>
      </select>

      <button
        @click="addMetric"
        :disabled="!selectedMetric"
      >
        + Add
      </button>
    </div>

    <!-- 🔥 Empty state -->
    <p v-if="filteredMetrics.length === 0" class="info">
      All metrics added
    </p>

    <!-- 🔥 Selected Metrics -->
    <div
      v-for="(metric, key) in store.targetMetrics"
      :key="key"
      class="metric-row"
    >
      <!-- ✅ label instead of raw key -->
      <h3>{{ getLabel(key) }}</h3>

      <input
        type="number"
        v-model.number="metric.target_value"
        placeholder="Target"
      />

      <input
        type="number"
        min="0"
        v-model.number="metric.tolerance"
        placeholder="Tolerance"
      />

      <input
        v-model="metric.matching_function"
        placeholder="Match Function"
      />

      <button @click="store.removeTargetMetric(key)">❌</button>
    </div>
  </div>
</template>

<style scoped>
.card {
  background: #222;
  color: white;
  padding: 20px;
  border-radius: 10px;
}

.add-row {
  display: flex;
  gap: 10px;
  margin-bottom: 15px;
}

.metric-row {
  display: flex;
  gap: 10px;
  align-items: center;
  margin-bottom: 10px;
}

.info {
  color: #aaa;
  margin-bottom: 10px;
}
</style>