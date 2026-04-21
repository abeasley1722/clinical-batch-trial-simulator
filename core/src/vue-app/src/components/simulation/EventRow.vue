<script setup>
import { EVENT_TYPES, getDefaultParams } from './eventConfig'

import PathologyForm from './eventForms/PathologyForm.vue'
import VentForm from './eventForms/VentForm.vue'
import BolusForm from './eventForms/BolusForm.vue'
import InfusionForm from './eventForms/InfusionForm.vue'
import ExerciseForm from './eventForms/ExerciseForm.vue'

import { useSimulationStore } from '@/stores/simulationStore'

const props = defineProps(['event', 'index'])
const store = useSimulationStore()

function updateType(newType) {
  props.event.type = newType
  props.event.params = getDefaultParams(newType)
}
</script>

<template>
  <div class="event-row">

    <!-- Activation -->
    <select v-model="event.activation">
      <option value="time">At Time</option>
      <option value="trigger">On Condition</option>
    </select>

    <input v-if="event.activation==='time'" type="number" v-model="event.time" />

    <!-- Event Type -->
    <select :value="event.type" @change="updateType($event.target.value)">
      <option v-for="t in EVENT_TYPES" :key="t.value" :value="t.value">
        {{ t.label }}
      </option>
    </select>

    <!-- Dynamic Forms -->
    <PathologyForm v-if="event.type==='pathology'" v-model="event.params" />
    <VentForm v-if="event.type.includes('vent')" v-model="event.params" />
    <BolusForm v-if="event.type==='bolus'" v-model="event.params" />
    <InfusionForm v-if="event.type==='infusion'" v-model="event.params" />
    <ExerciseForm v-if="event.type==='exercise'" v-model="event.params" />

    <button @click="store.removeEvent(index)">Remove</button>

  </div>
</template>