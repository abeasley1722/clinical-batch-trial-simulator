<script setup>
import { computed, onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import VChart from 'vue-echarts'
import { useExperimentDashboardStore } from '@/stores/experimentDashboardStore'

const store = useExperimentDashboardStore()

onMounted(async () => {
  await store.initialize()
})

const {
  experiments,
  selectedExperimentId,
  selectedVitalKeys
} = storeToRefs(store)

const hasExperiments = computed(() => store.hasExperiments)
const availableVitals = computed(() => store.availableVitals)

const chartOptions = computed(() => ({
  xAxis: { type: 'category', data: store.chartXAxisLabels },
  yAxis: { type: 'value' },
  series: store.chartSeries.map(s => ({
    name: s.name,
    type: 'line',
    data: s.data
  }))
}))
</script>

<template>
  <div class="wrapper">

    <div class="left-panel">
      <div v-for="exp in experiments" :key="exp.id">
        <button @click="store.selectExperiment(exp.id)">
          {{ exp.name }}
        </button>
      </div>
    </div>

    <div class="content">

      <div v-if="!hasExperiments">
        No experiments
      </div>

      <div v-else>

        <div>
          <label v-for="v in availableVitals" :key="v.key">
            <input
              type="checkbox"
              :checked="selectedVitalKeys.includes(v.key)"
              @change="store.toggleVital(v.key)"
            />
            {{ v.label }}
          </label>
        </div>

        <VChart :option="chartOptions" autoresize />

      </div>
    </div>

  </div>
</template>