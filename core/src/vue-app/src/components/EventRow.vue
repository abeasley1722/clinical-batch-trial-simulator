<template>
  <div class="event">

    <!-- LEFT -->
    <div class="event-info">

      <!-- Type -->
      <div class="event-type">
        {{ formatType(event.type) }}
      </div>

      <!-- Time / Trigger -->
      <div class="event-meta">
        <span v-if="event.activation==='time'">
          ⏱ {{ event.time }}s
        </span>

        <span v-else>
          🎯 Trigger
        </span>
      </div>

      <!-- ========================= -->
      <!-- 🔥 DETAILS -->
      <!-- ========================= -->
      <div class="event-details">

        <!-- PATHOLOGY -->
        <div v-if="event.type==='pathology'">
          <span>🧬 {{ event.pathology }}</span>
          <span v-if="event.severity !== undefined">
            | Severity: {{ event.severity }}
          </span>

          <span v-if="event.stop_mode==='conditional'">
            | Stop: {{ event.condition_vital }} {{ event.condition_operator }} {{ event.condition_value }}
          </span>
        </div>

        <!-- INTUBATE -->
        <div v-if="event.type==='intubate'">
          🫁 {{ event.intubationType }}
        </div>

        <!-- VENT -->
        <div v-if="event.type==='start_vent' || event.type==='change_vent'">
          ⚙️ {{ event.vent_settings?.mode }}
          | FiO₂: {{ event.vent_settings?.fio2 }}
          | PEEP: {{ event.vent_settings?.peep_cmh2o }}
        </div>

        <!-- CONTROLLER -->
        <div v-if="event.type==='start_controller'">
          🧠 {{ event.controller }}

          <span v-if="event.controller==='http_controller'">
            | 🌐 {{ event.http_url }}
          </span>
        </div>

        <!-- FLUID CONTROLLER -->
        <div v-if="event.type==='start_fluid_controller'">
          💧 {{ event.controller }}

          <span v-if="event.controller==='http_fluid_controller'">
            | 🌐 {{ event.http_url }}
          </span>
        </div>

        <!-- BOLUS -->
        <div v-if="event.type==='bolus'">
          💉 {{ event.drug }} | {{ event.dose }} {{ event.route }}
        </div>

        <!-- INFUSION -->
        <div v-if="event.type==='infusion'">
          💧 {{ event.drug }} | {{ event.rate_ml_per_hr }} mL/hr
        </div>

        <!-- COMPOUND -->
        <div v-if="event.type==='compound_infusion'">
          🧪 {{ event.compound }} | {{ event.rate_ml_per_min }} mL/min
        </div>

        <!-- EXERCISE -->
        <div v-if="event.type==='exercise'">
          🏃 Intensity: {{ event.intensity }}
          | Duration: {{ event.duration }} {{ event.unit }}
        </div>

      </div>
    </div>

    <!-- REMOVE -->
    <button class="icon-btn" @click="$emit('remove')">
      ✖
    </button>

  </div>
</template>

<script setup>
defineProps(['event'])

function formatType(type) {
  return type.replace(/_/g, ' ').toUpperCase()
}
</script>

<style scoped>
/* ========================
   EVENT CARD
======================== */
.event {
  display: flex;
  justify-content: space-between;
  align-items: center;

  background: #2b3545;
  padding: 10px 12px;
  margin-bottom: 8px;
  border-radius: 8px;
}

/* ========================
   LEFT SIDE
======================== */
.event-info {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

/* event name */
.event-type {
  font-weight: 600;
  color: white;
}

/* metadata (time / trigger) */
.event-meta {
  font-size: 13px;
  color: #bbb;
}
.event-details {
  font-size: 12px;
  color: #aaa;
  margin-top: 4px;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

/* ========================
   BUTTON (MATCH SYSTEM)
======================== */
.icon-btn {
  background: #333;
  border: none;
  border-radius: 6px;
  color: white;
  padding: 5px 9px;
  cursor: pointer;
  transition: 0.2s;
}

.icon-btn:hover {
  background: #555;
}

.icon-btn:active {
  background: #111;
}
</style>