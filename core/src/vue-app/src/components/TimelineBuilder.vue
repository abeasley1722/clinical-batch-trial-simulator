<template>
  <div class="panel">
    <h3 class="title">Event Timeline</h3>

    <div class="columns">

      <!-- Timed Events -->
      <div class="column">
        <div class="column-title">⏱ Timed</div>

        <div v-if="store.events.length">
          <EventRow
            v-for="(e,i) in store.events"
            :key="i"
            :event="e"
            @remove="store.removeEvent(i,'time')"
          />
        </div>

        <div v-else class="empty">
          No timed events
        </div>
      </div>

      <!-- Triggered Events -->
      <div class="column">
        <div class="column-title">🎯 Triggered</div>

        <div v-if="store.triggeredEvents.length">
          <EventRow
            v-for="(e,i) in store.triggeredEvents"
            :key="i"
            :event="e"
            @remove="store.removeEvent(i,'trigger')"
          />
        </div>

        <div v-else class="empty">
          No triggered events
        </div>
      </div>

    </div>

    <!-- Add Event -->
    <div class="form-section">
      <EventForm @add="store.addEvent" />
    </div>
  </div>
</template>

<script setup>
import { useSimulationStore } from '../stores/simulationStore'
import EventRow from './EventRow.vue'
import EventForm from './EventForm.vue'

const store = useSimulationStore()
</script>

<style scoped>
/* ========================
   PANEL (MATCH DASHBOARD)
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
  margin-bottom: 12px;
}

.column-title {
  color: #bbb;
  margin-bottom: 8px;
  font-weight: 600;
}

/* ========================
   COLUMNS
======================== */
.columns {
  display: flex;
  gap: 20px;
}

.column {
  flex: 1;
  background: #222;
  padding: 10px;
  border-radius: 10px;
  min-height: 120px;
}

/* ========================
   EMPTY STATE
======================== */
.empty {
  color: #888;
  font-size: 14px;
}

/* ========================
   FORM SECTION
======================== */
.form-section {
  margin-top: 15px;
}

/* ========================
   RESPONSIVE
======================== */
@media (max-width: 900px) {
  .columns {
    flex-direction: column;
  }
}
</style>