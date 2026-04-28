<script setup>
import { computed, onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, ScatterChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  GridComponent,
  LegendComponent,
  DataZoomComponent,
  MarkLineComponent
} from 'echarts/components'
import VChart from 'vue-echarts'
import { useExperimentDashboardStore } from '../stores/experimentDashboardStore'
import { useRouter } from 'vue-router'

const router = useRouter()

use([
  CanvasRenderer,
  LineChart,
  ScatterChart,
  TitleComponent,
  TooltipComponent,
  GridComponent,
  LegendComponent,
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
  selectedExperimentIds,
  compareMode,
  selectedGraphType,
  selectedBatchId,
  selectedVitalKeys
} = storeToRefs(store)

// ✅ SAFE COMPUTEDS
const hasExperiments = computed(() => (store.experiments || []).length > 0)
const selectedExperiment = computed(() => store.selectedExperiment || {})
const selectedExperimentMetrics = computed(() => store.selectedExperimentMetrics || [])
const selectedExperimentTargets = computed(() => store.selectedExperimentTargets || [])
const graphTypeOptions = computed(() => store.graphTypeOptions || [])
const availableBatches = computed(() => store.availableBatches || [])
const availableVitals = computed(() => store.availableVitals || [])
const chartSeries = computed(() => store.chartSeries || [])
const chartXAxisLabels = computed(() => store.chartXAxisLabels || [])
const comparisonCharts = computed(() => store.comparisonCharts || [])

// ========================
// HELPERS
// ========================
function formatMetricValue(value) {
  if (value === null || value === undefined || value === '') return '-'
  if (typeof value === 'number') return Number.isInteger(value) ? `${value}` : value.toFixed(2)
  return `${value}`
}

// ========================
// CHART BUILDER
// ========================
function makeChartOptions(title, xAxisLabels = [], series = [], graphType) {
  return {
    title: { text: title },
    tooltip: { trigger: 'axis' },
    legend: { top: 28 },
    grid: { left: 56, right: 24, top: 88, bottom: 90 },
    dataZoom: [
      { type: 'inside', start: 0, end: 100 },
      { type: 'slider', bottom: 24, start: 0, end: 100 }
    ],
    xAxis: {
      type: 'category',
      data: xAxisLabels || [],
      boundaryGap: false
    },
    yAxis: {
      type: 'value',
      scale: true
    },
    series: (series || []).map((item) => ({
      name: item.name,
      type: graphType,
      data: item.data || [],
      markLine: item.target
        ? {
            symbol: ['none', 'none'],
            silent: true,
            lineStyle: { type: 'dashed' },
            data: [{ yAxis: Number(item.target.target_value) }]
          }
        : undefined
    }))
  }
}

const singleChartOptions = computed(() =>
  makeChartOptions(
    selectedExperiment.value?.name || 'Experiment',
    chartXAxisLabels.value,
    chartSeries.value,
    selectedGraphType.value
  )
)

const compareChartOptions = computed(() =>
  (comparisonCharts.value || []).map((chart) => ({
    ...chart,
    option: makeChartOptions(
      `${chart.experimentName} — ${chart.batchLabel}`,
      chart.xAxisLabels || [],
      chart.series || [],
      selectedGraphType.value
    )
  }))
)
</script>

<template>
  <div class="wrapper">
    <!-- LEFT PANEL -->
    <div class="left-panel">
      <h3>SAVED EXPERIMENTS</h3>

      <template v-if="hasExperiments">
        <div
          v-for="experiment in experiments"
          :key="experiment.experiment_id"
          class="experiment-row"
        >
          <button
            class="exp-btn"
            :class="{ active: experiment.experiment_id === selectedExperimentId }"
            @click="store.selectExperiment(experiment.experiment_id)"
          >
            {{ experiment.name }}
          </button>
        </div>
      </template>

      <div v-else class="left-empty">
        No experiments
      </div>

      <button class="primary-btn" @click="router.push('/')">
        Create Experiment
      </button>
    </div>

    <!-- MAIN CONTENT -->
    <div class="content">
      <template v-if="!hasExperiments">
        <div class="empty-state">
          <div class="empty-state-title">No existing experiments</div>
        </div>
      </template>

      <template v-else>
        <!-- CHART -->
        <div class="single-layout">
          <div class="single-chart-card">
            <VChart class="chart" :option="singleChartOptions" autoresize />
          </div>

          <!-- METRICS PANEL -->
          <div class="metrics-panel">
            <div class="metrics-panel-title">
              {{ selectedExperiment?.name || 'Experiment' }}
            </div>

            <!-- TARGETS -->
            <div class="panel-section">
              <div class="panel-section-title">Targets</div>

              <div v-if="selectedExperimentTargets?.length">
                <div
                  v-for="target in selectedExperimentTargets"
                  :key="target.target_name"
                >
                  {{ target.target_name }}: {{ target.target_value }}
                </div>
              </div>

              <div v-else class="metrics-empty">
                No targets available
              </div>
            </div>

            <!-- METRICS -->
            <div class="panel-section">
              <div class="panel-section-title">Metrics</div>

              <div v-if="selectedExperimentMetrics?.length">
                <div
                  v-for="metric in selectedExperimentMetrics"
                  :key="metric.metric_id"
                >
                  {{ metric.vital_sign }}: {{ formatMetricValue(metric.mae) }}
                </div>
              </div>

              <div v-else class="metrics-empty">
                No metrics available
              </div>
            </div>
          </div>
        </div>
      </template>
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
  flex: 1;
}

.single-layout {
  display: grid;
  grid-template-columns: 1fr 300px;
  gap: 16px;
}

.chart {
  height: 500px;
}

.metrics-panel {
  background: #1a1a1a;
  color: white;
  padding: 15px;
  border-radius: 12px;
}

.metrics-empty {
  color: #bbb;
}
</style>