<template>
  <div class="card">
    <h2>Batch Progress</h2>

    <p>Status: {{ store.status }}</p>

    <!-- ✅ Progress Bar -->
    <div class="progress-bar">
      <div
        class="progress-fill"
        :style="{ width: (store.progress || 0) + '%' }"
      ></div>
    </div>


    <p>
      {{ store.completed ?? 0 }} / {{ store.total ?? 0 }}
    </p>


    <p v-if="store.progress !== null">
      {{ store.progress }}%
    </p>

    <!-- ✅ Cancel -->
    <button
      v-if="store.status === 'running'"
      @click="cancel"
    >
      Cancel
    </button>
  </div>
</template>

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

<style scoped>
.card {
  background: #222;
  color: white;
  padding: 20px;
  border-radius: 10px;
}

.progress-bar {
  width: 100%;
  height: 20px;
  background: #444;
  border-radius: 10px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: limegreen;
  transition: width 0.3s ease;
}
</style>