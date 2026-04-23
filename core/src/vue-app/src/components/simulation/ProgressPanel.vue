<script setup>
import { useSimulationStore } from '@/stores/simulationStore'
const store = useSimulationStore()
</script>

<template>
  <div class="card">
    <h2>Status</h2>

    <div class="bar">
      <div class="fill" :style="{ width: store.progress + '%' }">
        {{ store.progress }}%
      </div>
    </div>

    <p>{{ store.status }}</p>
  </div>
</template>