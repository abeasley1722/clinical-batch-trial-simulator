<script setup>
import { computed } from 'vue'
import { useSimulationStore } from '@/stores/simulationStore'

const store = useSimulationStore()

const patients = [
  'soldier',
  'adult',
  'StandardMale',
  'StandardFemale',
  'ARDS',
  'Hemorrhage'
]

const totalPercent = computed(() =>
  store.demographics.reduce((sum, d) => sum + Number(d.percent || 0), 0)
)

const isValid = computed(() => totalPercent.value === 100)

// 🔥 NEW: breakdown
const patientBreakdown = computed(() =>
  store.demographics.map(d => ({
    name: d.name,
    percent: Number(d.percent || 0),
    count: Math.round((store.patientCount * (d.percent || 0)) / 100)
  }))
)
</script>

<template>
  <div class="card">
    <h2>Patient Demographics</h2>

    <!-- 🔥 Total Patients -->
    <h3>Total Patients</h3>
    <input type="number" v-model.number="store.patientCount" min="1" />

    <!-- 🔥 Demographics -->
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

    <button @click="store.addDemographic()">+ Add Demographic</button>

    <!-- 🔥 Validation -->
    <p :class="{ error: !isValid }">
      Total: {{ totalPercent }}%
    </p>

    <p v-if="!isValid" class="error">
      Percent must equal 100%
    </p>

    <!-- 🔥 Breakdown -->
    <h4>Breakdown</h4>

    <div v-for="p in patientBreakdown" :key="p.name">
      <span v-if="p.name">
        {{ p.name }}: {{ p.count }} patients ({{ p.percent }}%)
      </span>
    </div>
  </div>
</template>

<style scoped>
.card {
  background: #222;
  padding: 20px;
  border-radius: 10px;
  color: white;
}

.row {
  display: flex;
  gap: 10px;
  margin-bottom: 10px;
}

.error {
  color: red;
  font-weight: bold;
}
</style>