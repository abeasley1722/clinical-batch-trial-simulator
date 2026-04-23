<script setup>
const model = defineModel()
</script>

<template>
  <div>
    <input v-model="model.fio2" placeholder="FiO2" />
    <input v-model="model.peep" placeholder="PEEP" />
    <input v-model="model.rr" placeholder="RR" />
    <input v-model="model.vt" placeholder="Vt" />
  </div>
</template>