<script setup>
const model = defineModel()
</script>

<template>
  <div>
    <select v-model="model.type">
      <option>ARDS</option>
      <option>Hemorrhage</option>
    </select>

    <input type="number" v-model="model.severity" step="0.1" />
  </div>
</template>