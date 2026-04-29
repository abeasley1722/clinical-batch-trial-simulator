
<script setup>
import { computed, onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  GridComponent,
  DataZoomComponent,
  MarkLineComponent
} from 'echarts/components'
import VChart from 'vue-echarts'
import { useExperimentDashboardStore } from '../stores/experimentDashboardStore'
import { useRouter } from 'vue-router'
import LoadingOverlay from './LoadingOverlay.vue'

const router = useRouter()

use([
  CanvasRenderer,
  LineChart,
  TitleComponent,
  TooltipComponent,
  GridComponent,
  DataZoomComponent,
  MarkLineComponent
])

const store = useExperimentDashboardStore()

onMounted(() => {
  store.initialize()
})

const {
  experiments,
  selectedExperimentId,
  selectedGraphType,
  selectedGroups
} = storeToRefs(store)

// ========================
// GROUP OPTIONS
// ========================
const GROUP_OPTIONS = [
  { key: null, label: 'Core Vitals' },
  { key: 'gases', label: 'Gases' },
  { key: 'ventilator', label: 'Ventilator' },
  { key: 'circulation', label: 'Circulation' },
  { key: 'controller', label: 'Controller' }
]

// ========================
// GROUP TOGGLE
// ========================
async function toggleGroup(groupKey) {
  let updated = [...selectedGroups.value]

  if (groupKey === null) {
    updated = []
  } else {
    if (updated.includes(groupKey)) {
      updated = updated.filter(g => g !== groupKey)
    } else {
      updated.push(groupKey)
    }
  }

  await store.setGroups(updated)
}

// ========================
// COMPUTEDS
// ========================
const chartXAxisLabels = computed(() => store.chartXAxisLabels || [])
const chartSeries = computed(() => store.chartSeries || [])

const selectedExperiment = computed(() => store.selectedExperiment || {})
const visibleMetrics = computed(() => {
  if (!store.rawData?.length) return []

  const keys = Object.keys(store.rawData[0] || {})

  return store.selectedExperimentMetrics.filter(m =>
    keys.includes(m.vital_sign)
  )
})

// ========================
// SPLIT CHARTS
// ========================
const groupedSeries = computed(() => {
  const chunkSize = 4
  const chunks = []

  for (let i = 0; i < chartSeries.value.length; i += chunkSize) {
    chunks.push(chartSeries.value.slice(i, i + chunkSize))
  }

  return chunks
})

function extractGroupName(seriesGroup) {
  if (!seriesGroup.length) return ''
  const first = seriesGroup[0].name
  const parts = first.split(' - ')
  return parts.length > 1 ? parts[0] : 'Vitals'
}

// ========================
// HELPERS
// ========================
function formatMetricValue(value) {
  if (value === null || value === undefined || value === '') return '-'
  if (typeof value === 'number') {
    return Number.isInteger(value) ? `${value}` : value.toFixed(2)
  }
  return `${value}`
}

// ========================
// CHART OPTIONS
// ========================
function makeChartOptions(title, xAxisLabels, series, graphType) {
  return {
    title: { text: title },
    tooltip: { trigger: 'axis'},
    legend: { type: 'scroll', // important for many lines
      top: 25 },
    grid: { left: 50, right: 20, top: 100, bottom: 60 },

    dataZoom: [
      { type: 'inside' },
      { type: 'slider' }
    ],

    xAxis: {
      type: 'category',
      data: xAxisLabels,
      boundaryGap: false
    },

    yAxis: {
      type: 'value',
      scale: true
    },

    series: series.map(item => ({
      name: item.name,
      type: graphType,
      large: true,
      sampling: 'lttb',
      showSymbol: false,
      data: item.data,

      markLine: item.target
        ? {
            symbol: ['none', 'none'],
            lineStyle: { type: 'dashed', color: 'red' },
            data: [{ yAxis: Number(item.target) }]
          }
        : undefined
    }))
  }
}
</script>

<template>
  <LoadingOverlay :visible="store.loading" />

  <div class="wrapper">

    <!-- LEFT PANEL -->
    <div class="left-panel">
      <h3>SAVED EXPERIMENTS</h3>

      <button
        v-for="exp in experiments"
        :key="exp.experiment_id"
        class="exp-btn"
        :class="{ active: exp.experiment_id === selectedExperimentId }"
        @click="store.selectExperiment(exp.experiment_id)"
      >
        {{ exp.name }}
      </button>

      <button class="primary-btn" @click="router.push('/')">
        Create Experiment
      </button>
    </div>

    <!-- MAIN CONTENT -->
    <div class="content">

      <!-- LEFT SIDE (charts + toggle) -->
      <div class="charts-section">

        <!-- GROUP TOGGLER -->
        <div class="group-toggle">
          <button
            v-for="g in GROUP_OPTIONS"
            :key="g.label"
            :class="{
              active:
                g.key === null
                  ? selectedGroups.length === 0
                  : selectedGroups.includes(g.key)
            }"
            @click="toggleGroup(g.key)"
          >
            ✔ {{ g.label }}
          </button>
        </div>

        <!-- CHARTS -->
        <div class="charts-container">
          <div
            v-for="(seriesGroup, index) in groupedSeries"
            :key="index"
            class="chart-card"
          >
            <VChart
              class="chart"
              :option="makeChartOptions(
                extractGroupName(seriesGroup) + ' Data',
                chartXAxisLabels,
                seriesGroup,
                selectedGraphType
              )"
              autoresize
            />
          </div>
        </div>

      </div>

      <!-- RIGHT PANEL -->
      <div class="right-panel">

        <div class="panel-title">
          {{ selectedExperiment?.name || 'Experiment' }}
        </div>

        <!-- TARGETS -->
        <div class="panel-section">
          <div class="section-title">Targets</div>

          <div v-if="visibleMetrics.length">
            <div
              v-for="m in visibleMetrics"
              :key="m.metric_id"
              class="panel-row"
            >
              <span>{{ m.vital_sign }}</span>
              <span class="target">→ {{ m.target_value ?? '-' }}</span>
            </div>
          </div>

          <div v-else class="empty">
            No targets available
          </div>
        </div>

        <!-- METRICS -->
        <div class="panel-section">
          <div class="section-title">Metrics</div>

          <div v-if="visibleMetrics.length">
            <div
              v-for="m in visibleMetrics"
              :key="m.metric_id"
              class="panel-row"
            >
              <span>{{ m.vital_sign }}</span>
              <span class="metric">
                {{ formatMetricValue(m.mae) }}
              </span>
            </div>
          </div>

          <div v-else class="empty">
            No metrics available
          </div>
        </div>

      </div>

    </div>
  </div>
</template>

<style scoped>
.wrapper {
  display: flex;
  gap: 20px;
  padding: 20px;
}

.left-panel {
  width: 260px;
  background: #1a1a1a;
  color: white;
  padding: 15px;
  border-radius: 12px;
}

.exp-btn {
  width: 100%;
  padding: 10px;
  background: #333;
  border: none;
  border-radius: 8px;
  color: white;
  margin-bottom: 8px;
}

.exp-btn.active {
  background: #777;
}

.content {
  display: grid;
  grid-template-columns: 1fr 300px;
  gap: 20px;
  flex: 1;
}

.chart {
  height: 400px;
}

/* CHART AREA */
.charts-section {
  display: flex;
  flex-direction: column;
}

.charts-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* TOGGLE */
.group-toggle {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.group-toggle button {
  padding: 8px 14px;
  border-radius: 8px;
  border: none;
  background: #ddd;
  cursor: pointer;
}

.group-toggle button.active {
  background: #42b883;
  color: white;
  font-weight: bold;
}

/* RIGHT PANEL */
.right-panel {
  background: #1a1a1a;
  color: white;
  padding: 15px;
  border-radius: 12px;
}

.panel-title {
  font-size: 18px;
  margin-bottom: 12px;
}

.panel-section {
  margin-bottom: 20px;
}

.section-title {
  font-weight: bold;
  margin-bottom: 8px;
}

.panel-row {
  display: flex;
  justify-content: space-between;
  padding: 4px 0;
}

.target {
  color: #4fc3f7;
}

.metric {
  color: #81c784;
}

.empty {
  color: #aaa;
}

.primary-btn {
  padding: 12px 18px;
  background: #333;
  border: none;
  border-radius: 8px;
  color: white;
  cursor: pointer;
  margin-bottom: 40px;
}

.primary-btn:hover {
  background: #444;
}
</style>

