<template>
  <div class="card">
    <h3>Event Timeline</h3>

    <div class="columns">
      <!-- Timed -->
      <div>
        <h4>⏱ Timed</h4>
        <EventRow
          v-for="(e,i) in store.events"
          :key="i"
          :event="e"
          @remove="store.removeEvent(i,'time')"
        />
      </div>

      <!-- Triggered -->
      <div>
        <h4>🎯 Triggered</h4>
        <EventRow
          v-for="(e,i) in store.triggeredEvents"
          :key="i"
          :event="e"
          @remove="store.removeEvent(i,'trigger')"
        />
      </div>
    </div>

    <EventForm @add="store.addEvent" />
  </div>
</template>

<script setup>
import { useSimulationStore } from '../stores/simulationStore'
import EventRow from './EventRow.vue'
import EventForm from './EventForm.vue'

const store = useSimulationStore()
</script>

<style scoped>
.columns {
  display: flex;
  gap: 40px;
}
</style>