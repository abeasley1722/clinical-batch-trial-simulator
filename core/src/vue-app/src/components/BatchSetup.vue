<template>
  <div class="panel">
    <h3 class="title">Batch Setup</h3>

    <div class="row">
      <input v-model="store.name" placeholder="Batch Name" />

      <input v-model.number="store.duration" type="number" placeholder="Duration (s)" />
      <input v-model.number="store.workers" type="number" placeholder="Workers" />
      <input v-model.number="store.replicates" type="number" placeholder="Replicates" />
    </div>

    <h4 class="section-title">Patient Count</h4>
    <input v-model.number="store.patientCount" type="number" />

    <h4 class="section-title">Demographics</h4>

    <div v-for="(demo, i) in store.demographics" :key="i" class="row">
      <select v-model="demo.name">
        <option disabled value="">Select Patient</option>
        <option v-for="p in patients" :key="p" :value="p">
          {{ p }}
        </option>
      </select>

      <input type="number" v-model.number="demo.percent" placeholder="%" />

      <button class="icon-btn" @click="store.removeDemographic(i)">✖</button>
    </div>

    <button class="exp-btn add-btn" @click="store.demographics.push({ name: '', percent: 0 })">
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
   HEADINGS
======================== */
.title {
  margin-bottom: 10px;
}

.section-title {
  margin-top: 15px;
  margin-bottom: 5px;
  color: #bbb;
}

/* ========================
   ROW LAYOUT
======================== */
.row {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 10px;
}

/* ========================
   INPUTS (MATCH DARK THEME)
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

/* placeholder styling */
input::placeholder {
  color: #bbb;
}

/* ========================
   BUTTONS (REUSE exp-btn)
======================== */
.exp-btn {
  padding: 10px 14px;
  background: #333;
  border: none;
  border-radius: 8px;
  color: white;
  cursor: pointer;
  transition: all 0.2s ease;
}

.exp-btn:hover {
  background: #444;
}

.exp-btn:active {
  background: #222;
}

/* ========================
   SMALL ICON BUTTON
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
   ADD BUTTON
======================== */
.add-btn {
  margin-top: 10px;
}
</style>