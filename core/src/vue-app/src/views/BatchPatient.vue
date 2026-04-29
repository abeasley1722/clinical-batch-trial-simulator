<script setup>
import { ref, computed } from 'vue'
import BatchSetup from '../components/BatchSetup.vue'
import TimelineBuilder from '../components/TimelineBuilder.vue'
import ProgressPanel from '@/components/ProgressPanel.vue'
import TargetMetrics from '@/components/TargetMetrics.vue'
import Demographics from '@/components/Demographics.vue'
import { useSimulationStore } from '../stores/simulationStore'

const store = useSimulationStore()

const loading = ref(false)
const error = ref(null)

// 🔥 Basic validation (expand later)
const isValid = computed(() => {
  return (
    store.name &&
    store.duration > 0 &&
    store.patientCount > 0 &&
    Object.keys(store.targetMetrics).length > 0
  )
})

async function run() {
  if (!isValid.value) {
    error.value = 'Please fill out all required fields.'
    return
  }

  error.value = null
  loading.value = true

  try {
    await store.submitBatch()
  } catch (err) {
    console.error(err)
    error.value = 'Simulation failed. Please try again.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="page-wrapper">

    <div class="form-grid">
        <div class="form-item"><BatchSetup /></div>
        <div class="form-item"><Demographics /></div>
        <div class="form-item"></div>
        <div class="form-item full"><TimelineBuilder /></div>
    </div>
<TargetMetrics />

    <ProgressPanel />



    <!-- 🔥 ACTION BAR -->
    <div class="actions">

      <div class="error" v-if="error">
        {{ error }}
      </div>

      <button
        class="exp-btn run-btn"
        @click="run"
        :disabled="loading || !isValid"
      >
        <span v-if="!loading">▶ Run Batch Simulation</span>
        <span v-else>Running...</span>
      </button>

    </div>

  </div>
</template>

<style scoped>
/* ========================
   ACTION ROW
======================== */
.actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

/* ========================
   BUTTON (MATCH SYSTEM)
======================== */
.exp-btn {
  padding: 12px 18px;
  background: #333;
  border: none;
  border-radius: 8px;
  color: white;
  cursor: pointer;
  transition: all 0.2s ease;
  font-weight: 600;
}

.exp-btn:hover {
  background: #444;
}

.exp-btn:active {
  background: #222;
}

/* 🔥 Disabled state */
.exp-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* ========================
   ERROR MESSAGE
======================== */
.error {
  color: #ff6b6b;
  font-size: 14px;
}

/* ========================
   RESPONSIVE
======================== */
@media (max-width: 900px) {
  .actions {
    flex-direction: column;
    gap: 10px;
  }
}
.page-wrapper {
  padding: 20px;
  background-color: black;
}
/* ========================
   PAGE
======================== */
.page-wrapper {
  padding: 20px;
  background-color: black;
  display: flex;
  flex-direction: column;
  gap: 20px; /* 🔥 spacing between major sections */
}

/* ========================
   GRID LAYOUT
======================== */
.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px; /* 🔥 spacing between forms */
}

/* each form wrapper */
.form-item {
  display: flex;
  flex-direction: column;
}

/* make timeline full width */
.form-item.full {
  grid-column: span 2;
}

/* ========================
   PROGRESS PANEL WRAP
======================== */
.panel-wrapper {
  display: flex;
  width: 100%;
}

/* ========================
   ACTION ROW
======================== */
.actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

/* ========================
   BUTTON
======================== */
.exp-btn {
  padding: 12px 18px;
  background: #333;
  border: none;
  border-radius: 8px;
  color: white;
  cursor: pointer;
  transition: all 0.2s ease;
  font-weight: 600;
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
   ERROR
======================== */
.error {
  color: #ff6b6b;
  font-size: 14px;
}

/* ========================
   RESPONSIVE
======================== */
@media (max-width: 900px) {
  .form-grid {
    grid-template-columns: 1fr; /* 🔥 stack on mobile */
  }

  .form-item.full {
    grid-column: span 1;
  }

  .actions {
    flex-direction: column;
    gap: 10px;
  }
}
</style>