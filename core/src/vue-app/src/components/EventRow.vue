<template>
  <div class="event">
    <div>
      <strong>{{ event.type }}</strong>
      <span v-if="event.activation==='time'"> @ {{ event.time }}</span>
      <span v-else> (trigger)</span>
    </div>

    <button @click="$emit('remove')">✖</button>
  </div>
</template>

<script setup>
defineProps(['event'])
</script>

<style scoped>
.event {
  display:flex;
  justify-content:space-between;
  background:#f8f9fa;
  padding:10px;
  margin-bottom:5px;
  border-radius:6px;
}
</style>