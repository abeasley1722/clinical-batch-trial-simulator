<script setup>
import BatchSetup from '../components/BatchSetup.vue'
import TimelineBuilder from '../components/TimelineBuilder.vue'
import ProgressPanel from '@/components/ProgressPanel.vue'
import TargetMetrics from '@/components/TargetMetrics.vue'
import Demographics from '@/components/Demographics.vue'
import { useSimulationStore } from '../stores/simulationStore'

const store = useSimulationStore()

async function run() {
  await store.submitBatch()
}
</script>

<template>
  <BatchSetup />
  <TimelineBuilder />
  <TargetMetrics />
  <Demographics />
  <ProgressPanel />

  <button class="run-btn" @click="run">
    ▶ Run Batch Simulation
  </button>
</template>

<style scoped>
.run-btn {
  margin-top: 20px;
  padding: 12px 20px;
  background: #3498db;
  color: white;
  border: none;
  border-radius: 6px;
}
</style>