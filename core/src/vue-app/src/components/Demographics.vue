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

// 🔥 Breakdown
const patientBreakdown = computed(() =>
  store.demographics.map(d => ({
    name: d.name,
    percent: Number(d.percent || 0),
    count: Math.round((store.patientCount * (d.percent || 0)) / 100)
  }))
)
</script>

<template>
  <div class="panel">
    <h3 class="title">Patient Demographics</h3>

    <!-- Total Patients -->
    <div class="section">
      <div class="label">Total Patients</div>
      <input type="number" v-model.number="store.patientCount" min="1" />
    </div>

    <!-- Demographics -->
    <div
      v-for="(demo, i) in store.demographics"
      :key="i"
      class="row"
    >
      <select v-model="demo.name">
        <option disabled value="">Select Patient</option>
        <option v-for="p in patients" :key="p" :value="p">
          {{ p }}
        </option>
      </select>

      <input type="number" v-model.number="demo.percent" placeholder="%" />

      <button class="icon-btn" @click="store.removeDemographic(i)">
        ✖
      </button>
    </div>

    <button class="exp-btn add-btn" @click="store.addDemographic()">
      + Add Demographic
    </button>

    <!-- Validation -->
    <div class="validation">
      <span :class="{ error: !isValid }">
        Total: {{ totalPercent }}%
      </span>

      <span v-if="!isValid" class="error">
        Must equal 100%
      </span>
    </div>

    <!-- Breakdown -->
    <div class="section">
      <div class="label">Breakdown</div>

      <div v-for="p in patientBreakdown" :key="p.name" class="breakdown-row">
        <span v-if="p.name">
          {{ p.name }} → {{ p.count }} patients ({{ p.percent }}%)
        </span>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* ========================
   PANEL
======================== */
.panel {
  background: #1c2431;
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

.label {
  color: #bbb;
  margin-bottom: 5px;
}

/* ========================
   SECTIONS
======================== */
.section {
  margin-bottom: 15px;
}

/* ========================
   ROWS
======================== */
.row {
  display: flex;
  gap: 10px;
  margin-bottom: 10px;
  flex-wrap: wrap;
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
   BUTTONS
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

.add-btn {
  margin-bottom: 10px;
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

/* ========================
   VALIDATION
======================== */
.validation {
  display: flex;
  gap: 10px;
  align-items: center;
  margin-bottom: 10px;
}

.error {
  color: #ff6b6b;
  font-weight: 600;
}

/* ========================
   BREAKDOWN
======================== */
.breakdown-row {
  color: #bbb;
  margin-bottom: 5px;
}
</style>