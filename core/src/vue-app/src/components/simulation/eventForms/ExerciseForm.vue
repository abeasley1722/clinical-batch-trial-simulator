<script setup>
const model = defineModel()
</script>

<template>
  <div>
    <input v-model="model.intensity" type="number" step="0.05" />
    <input v-model="model.duration" type="number" />
  </div>
</template>