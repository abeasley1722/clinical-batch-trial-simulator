<script setup>
const model = defineModel()
</script>

<template>
  <div>
    <input v-model="model.drug" placeholder="Drug" />
    <input v-model="model.dose" type="number" />
    <select v-model="model.unit">
      <option>mg</option>
      <option>ug</option>
    </select>
  </div>
</template>