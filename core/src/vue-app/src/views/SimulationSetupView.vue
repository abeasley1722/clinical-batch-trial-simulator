<script setup>
import SimulationForm from '@/components/simulation/SimulationForm.vue'
import TimelineBuilder from '@/components/simulation/TimelineBuilder.vue'
import ProgressPanel from '@/components/simulation/ProgressPanel.vue'
</script>

<template>
  <div class="page">
    <SimulationForm />
    <TimelineBuilder />
    <ProgressPanel />
  </div>
</template>