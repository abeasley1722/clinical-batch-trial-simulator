<template>
  <div class="event">

    <!-- LEFT: EVENT INFO -->
    <div class="event-info">
      <div class="event-type">
        {{ event.type.toUpperCase() }}
      </div>

      <div class="event-meta">
        <span v-if="event.activation==='time'">
          ⏱ {{ event.time }}s
        </span>

        <span v-else>
          🎯 Trigger
        </span>
      </div>
    </div>

    <!-- RIGHT: REMOVE -->
    <button class="icon-btn" @click="$emit('remove')">
      ✖
    </button>

  </div>
</template>

<script setup>
defineProps(['event'])
</script>

<style scoped>
/* ========================
   EVENT CARD
======================== */
.event {
  display: flex;
  justify-content: space-between;
  align-items: center;

  background: #222;
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