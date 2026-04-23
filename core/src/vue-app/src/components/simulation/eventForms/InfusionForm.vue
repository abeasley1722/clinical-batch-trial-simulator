<script setup>
const model = defineModel()
</script>

<template>
  <div>
    <input v-model="model.drug" />
    <input v-model="model.rate" type="number" />
  </div>
</template>