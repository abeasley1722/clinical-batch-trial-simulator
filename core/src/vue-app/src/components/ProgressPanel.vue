<script setup>
import { useSimulationStore } from '@/stores/simulationStore'
import { cancelBatch } from '@/services/api'

const store = useSimulationStore()

async function cancel() {
  if (!store.batchId) return

  try {
    await cancelBatch(store.batchId)
    store.status = 'cancelled'
  } catch (err) {
    console.error(err)
  }
}
</script>

<template>
  <div class="panel">
    <h3 class="title">Batch Progress</h3>

    <!-- STATUS -->
    <div class="status-row">
      <span class="label">Status</span>
      <span :class="['status', store.status]">
        {{ store.phase === 'generating_patients' ? 'Generating Patients' : store.status }}
      </span>
    </div>

    <!-- PATIENT GENERATION BAR (only when generating) -->
    <template v-if="store.phase === 'generating_patients' && store.patientGenTotal > 0">
      <div class="phase-label">Patient Generation</div>
      <div class="progress-wrapper">
        <div class="progress-bar">
          <div
            class="progress-fill"
            :style="{ width: store.patientGenProgress + '%' }"
          ></div>
        </div>
        <div class="progress-text">
          {{ store.patientGenCompleted }} / {{ store.patientGenTotal }} &mdash; {{ store.patientGenProgress }}%
        </div>
      </div>
    </template>

    <!-- SIMULATION PROGRESS BAR -->
    <template v-if="store.phase !== 'generating_patients' || store.total > 0">
      <div v-if="store.phase === 'generating_patients'" class="phase-label">Simulation</div>
      <div class="progress-wrapper">
        <div class="progress-bar">
          <div
            class="progress-fill"
            :style="{ width: (store.progress || 0) + '%' }"
          ></div>
        </div>
        <div class="progress-text">
          {{ store.completed ?? 0 }} / {{ store.total ?? 0 }} &mdash; {{ store.progress ?? 0 }}%
        </div>
      </div>
    </template>

    <!-- ACTION -->
    <div class="actions">
      <button
        v-if="store.status === 'running'"
        class="danger-btn"
        @click="cancel"
      >
        ✖ Cancel
      </button>
    </div>
  </div>
</template>

<style scoped>
/* ========================
   PANEL
======================== */
.panel {
  color: #f3f6fb;
  padding: 24px 22px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(170, 190, 220, 0.16);
  box-shadow:
    0 16px 40px rgba(0, 0, 0, 0.35),
    inset 0 1px 0 rgba(255, 255, 255, 0.04);
  backdrop-filter: blur(10px);
}

/* ========================
   TITLE
======================== */
.title {
  margin-bottom: 14px;
  font-size: 1.1rem;
  font-weight: 700;
  letter-spacing: 0.02em;
}

/* ========================
   STATUS
======================== */
.status-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 12px;
}

.label {
  color: #b8c2d3;
}

.status {
  font-weight: 600;
  text-transform: capitalize;
}

.status.running  { color: #9fb5d6; }
.status.complete,
.status.completed { color: #6fcf97; }
.status.failed   { color: #eb5757; }
.status.cancelled { color: #b8c2d3; }

/* ========================
   PROGRESS
======================== */
.phase-label {
  font-size: 12px;
  color: #b8c2d3;
  margin-bottom: 6px;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.progress-wrapper {
  margin-bottom: 10px;
}

.progress-bar {
  width: 100%;
  height: 10px;
  border-radius: 999px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.08);
}

.progress-fill {
  height: 100%;
  border-radius: 999px;
  background: linear-gradient(90deg, #6e85aa 0%, #93add4 100%);
  transition: width 0.3s ease;
}

.progress-text {
  font-size: 13px;
  color: #b8c2d3;
  margin-top: 6px;
}

/* ========================
   COUNTS
======================== */
.counts {
  color: #b8c2d3;
  margin-bottom: 12px;
}

/* ========================
   BUTTONS
======================== */
.actions {
  display: flex;
  justify-content: flex-end;
}

.danger-btn {
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(170, 190, 220, 0.2);
  border-radius: 8px;
  color: #eb5757;
  padding: 6px 14px;
  font-size: 13px;
  cursor: pointer;
  transition: background 0.2s;
}

.danger-btn:hover  { background: rgba(255, 255, 255, 0.1); }
.danger-btn:active { background: rgba(255, 255, 255, 0.03); }
</style>