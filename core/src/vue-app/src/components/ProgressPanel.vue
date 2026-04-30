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
        {{ store.status }}
      </span>
    </div>

    <!-- PROGRESS BAR -->
    <div class="progress-wrapper">
      <div class="progress-bar">
        <div
          class="progress-fill"
          :style="{ width: (store.progress || 0) + '%' }"
        ></div>
      </div>

      <div class="progress-text">
        {{ store.progress ?? 0 }}%
      </div>
    </div>

    <!-- COUNTS -->
    <div class="counts">
      {{ store.completed ?? 0 }} / {{ store.total ?? 0 }}
    </div>

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
  background: #1a1a1a;
  color: white;
  padding: 15px;
  border-radius: 12px;
}

/* ========================
   TITLE
======================== */
.title {
  margin-bottom: 12px;
}

/* ========================
   STATUS
======================== */
.status-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 10px;
}

.label {
  color: #bbb;
}

.status {
  font-weight: 600;
  text-transform: capitalize;
}

/* 🔥 Status colors */
.status.running {
  color: #4da3ff;
}

.status.complete {
  color: #4caf50;
}

.status.failed {
  color: #ff6b6b;
}

.status.cancelled {
  color: #aaa;
}

/* ========================
   PROGRESS
======================== */
.progress-wrapper {
  margin-bottom: 10px;
}

.progress-bar {
  width: 100%;
  height: 18px;
  background: #333;
  border-radius: 10px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #4da3ff, #6dd5ed);
  transition: width 0.3s ease;
}

.progress-text {
  font-size: 13px;
  color: #bbb;
  margin-top: 4px;
}

/* ========================
   COUNTS
======================== */
.counts {
  color: #bbb;
  margin-bottom: 10px;
}

/* ========================
   BUTTONS
======================== */
.actions {
  display: flex;
  justify-content: flex-end;
}

.danger-btn {
  background: #333;
  border: none;
  border-radius: 8px;
  color: #ff6b6b;
  padding: 8px 12px;
  cursor: pointer;
  transition: 0.2s;
}

.danger-btn:hover {
  background: #444;
}

.danger-btn:active {
  background: #222;
}
</style>