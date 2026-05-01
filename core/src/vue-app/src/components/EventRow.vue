<template>
  <div class="timeline-event" :class="[typeClass, { triggered: event.activation === 'trigger' }]">

    <!-- HEADER: title + time badge -->
    <div class="event-header">
      <span class="event-title">{{ eventLabel }}</span>

      <span class="event-time">
        <template v-if="event.activation === 'time'">
          ⏱ {{ event.time }}s
        </template>
        <template v-else>
          🎯 Trigger
        </template>
      </span>
    </div>

    <!-- DETAILS: key params -->
    <div class="event-details">{{ detailText }}</div>

    <!-- ACTIONS -->
    <div class="event-actions">
      <button class="icon-btn" @click="$emit('remove')">✖ Remove</button>
    </div>

  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps(['event'])

const TYPE_LABELS = {
  pathology: 'Pathology',
  intubate: 'Intubate',
  start_vent: 'Start Vent',
  change_vent: 'Change Vent',
  start_fluid_controller: 'Start Fluid Controller',
  stop_fluid_controller: 'Stop Fluid Controller',
  bolus: 'Drug Bolus',
  infusion: 'Drug Infusion',
  compound_infusion: 'Fluid/Blood Infusion',
  controller: 'Controller',
  exercise: 'Exercise',
}

// Maps event type → CSS class for color-coding
const TYPE_CLASS = {
  pathology: 'pathology',
  intubate: 'intubate',
  start_vent: 'ventilator',
  change_vent: 'ventilator',
  bolus: 'drug',
  infusion: 'drug',
  compound_infusion: 'drug',
  controller: 'controller',
  start_fluid_controller: 'controller',
  stop_fluid_controller: 'controller',
  exercise: 'exercise',
}

const eventLabel = computed(() => TYPE_LABELS[props.event.type] || props.event.type)
const typeClass = computed(() => TYPE_CLASS[props.event.type] || '')

const detailText = computed(() => {
  const p = props.event.params || {}
  switch (props.event.type) {
    case 'pathology':
      return `${p.type} — severity ${p.severity}`
    case 'intubate':
      return p.type
    case 'start_vent':
    case 'change_vent':
      return `${p.mode} | FiO2 ${p.fio2}% | PEEP ${p.peep} | VT ${p.vt} | RR ${p.rr} | IT ${p.itime}s`
    case 'bolus':
      return `${p.drug} ${p.dose}mg ${p.route}`
    case 'infusion':
      return `${p.drug} @ ${p.rate} mL/hr, ${p.concentration} mg/mL`
    case 'compound_infusion':
      return `${p.fluid} ${p.bag_volume}mL @ ${p.rate} mL/hr`
    case 'controller':
      return p.controller + (p.url ? ` → ${p.url}` : '')
    case 'start_fluid_controller':
      return p.controller
    case 'stop_fluid_controller':
      return 'Stop fluid controller'
    case 'exercise':
      return `Intensity ${p.intensity} for ${p.duration} ${p.unit}`
    default:
      return JSON.stringify(p)
  }
})
</script>

<style scoped>
/* ========================
   TIMELINE EVENT CARD
======================== */
.timeline-event {
  position: relative;
  padding: 12px 15px;
  background: #2a2a2a;
  border-radius: 6px;
  margin-bottom: 10px;
  border-left: 3px solid #3498db;
  cursor: pointer;
  transition: transform 0.1s, box-shadow 0.1s;
}

.timeline-event:hover {
  transform: translateX(3px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.4);
}

/* ========================
   TYPE COLORS
======================== */
.timeline-event.intubate       { border-left-color: #9b59b6; }
.timeline-event.ventilator     { border-left-color: #27ae60; }
.timeline-event.pathology      { border-left-color: #e74c3c; }
.timeline-event.controller     { border-left-color: #f39c12; }
.timeline-event.drug           { border-left-color: #1abc9c; }
.timeline-event.exercise       { border-left-color: #e67e22; }

/* ========================
   TRIGGERED (dashed border)
======================== */
.timeline-event.triggered {
  border-style: dashed;
  background: #252535;
}

.timeline-event.triggered .event-time {
  background: #8e44ad;
}

/* ========================
   HEADER
======================== */
.event-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.event-title {
  font-weight: 600;
  color: #fff;
}

.event-time {
  background: #3498db;
  color: white;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 12px;
  font-weight: 500;
}

/* ========================
   DETAILS
======================== */
.event-details {
  font-size: 13px;
  color: #aaa;
  margin-bottom: 8px;
}

/* ========================
   ACTIONS
======================== */
.event-actions {
  margin-top: 4px;
}

.icon-btn {
  background: #333;
  border: none;
  border-radius: 6px;
  color: white;
  padding: 5px 10px;
  font-size: 12px;
  cursor: pointer;
  transition: 0.2s;
}

.icon-btn:hover {
  background: #e74c3c;
}
</style>