<!-- src/components/VitalsDashboard.vue -->
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

const hasExperiments = computed(() => store.hasExperiments)
const selectedExperiment = computed(() => store.selectedExperiment)
const selectedExperimentMetrics = computed(() => store.selectedExperimentMetrics)
const selectedExperimentTargets = computed(() => store.selectedExperimentTargets)
const graphTypeOptions = computed(() => store.graphTypeOptions)
const availableBatches = computed(() => store.availableBatches)
const availableVitals = computed(() => store.availableVitals)
const chartSeries = computed(() => store.chartSeries)
const chartXAxisLabels = computed(() => store.chartXAxisLabels)
const comparisonCharts = computed(() => store.comparisonCharts)

function formatMetricValue(value) {
  if (value === null || value === undefined || value === '') return '-'
  if (typeof value === 'number') return Number.isInteger(value) ? `${value}` : value.toFixed(2)
  return `${value}`
}


function makeChartOptions(title, xAxisLabels, series, graphType) {
  return {
    title: {
      text: title,
      textStyle: { color: '#000' }
    },
    tooltip: {
      trigger: 'axis',
      confine: true,
      formatter(params) {
        if (!Array.isArray(params) || !params.length) return ''

        const lines = [`<strong>${params[0].axisValue}</strong>`]

        for (const item of params) {
          const currentSeries = series.find((entry) => entry.name === item.seriesName)
          if (!currentSeries) continue
          const rawValue = currentSeries.data[item.dataIndex]
          const targetText = currentSeries.target
            ? ` | target: ${currentSeries.target.target_value}`
            : ''

          lines.push(
            `${item.marker}${currentSeries.name}: ${rawValue ?? '-'} ${currentSeries.unit}${targetText}`
          )
        }

        return lines.join('<br/>')
      }
    },
    legend: {
      top: 28
    },
    grid: {
      left: 56,
      right: 24,
      top: 88,
      bottom: 90
    },
    dataZoom: [
      { type: 'inside', start: 0, end: 100 },
      { type: 'slider', bottom: 24, start: 0, end: 100 }
    ],
    xAxis: {
      type: 'category',
      data: xAxisLabels,
      boundaryGap: false,
      axisLabel: { color: '#000' },
      axisLine: { lineStyle: { color: '#666' } }
    },
    yAxis: {
      type: 'value',
      scale: true,
      name: 'Value',
      nameTextStyle: { color: '#000' },
      axisLabel: { color: '#000' }
    },
    series: series.map((item) => ({
      name: item.name,
      type: graphType,
      smooth: false,
      showSymbol: graphType === 'scatter',
      symbolSize: graphType === 'scatter' ? 8 : 4,
      data: item.data,
      markLine: item.target
        ? {
            symbol: ['none', 'none'],
            silent: true,
            lineStyle: {
              type: 'dashed',
              width: 2,
              color: '#444'
            },
            label: {
              show: true,
              color: '#444',
              formatter: `${item.name} target: ${item.target.target_value}`
            },
            data: [
              {
                yAxis: Number(item.target.target_value),
                name: `${item.name} target`
              }
            ]
          }
        : undefined
    }))
  }
}

const singleChartOptions = computed(() =>
  makeChartOptions(
    selectedExperiment.value?.name ?? 'Experiment',
    chartXAxisLabels.value,
    chartSeries.value,
    selectedGraphType.value
  )
)

const compareChartOptions = computed(() =>
  comparisonCharts.value.map((chart) => ({
    experimentId: chart.experimentId,
    experimentName: chart.experimentName,
    batchId: chart.batchId,
    batchLabel: chart.batchLabel,
    availableBatches: chart.availableBatches,
    metrics: chart.metrics,
    targets: chart.targets,
    option: makeChartOptions(
      `${chart.experimentName} — ${chart.batchLabel}`,
      chart.xAxisLabels,
      chart.series,
      selectedGraphType.value
    )
  }))
)
</script>

<template>
  <div class="wrapper">
    <div class="left-panel">
      <h3>SAVED EXPERIMENTS</h3>

      <label
        v-if="hasExperiments"
        class="compare-toggle"
      >
        <input
          type="checkbox"
          :checked="compareMode"
          @change="store.toggleCompareMode($event.target.checked)"
        />
        <span>Compare mode</span>
      </label>

      <template v-if="hasExperiments">
        <div
          v-for="experiment in experiments"
          :key="experiment.id"
          class="experiment-row"
        >
          <button
            class="exp-btn"
            :class="{ active: experiment.id === selectedExperimentId }"
            @click="store.selectExperiment(experiment.id)"
          >
            {{ experiment.name }}
          </button>

          <input
            v-if="compareMode"
            type="checkbox"
            :checked="selectedExperimentIds.includes(experiment.id)"
            @change="store.toggleComparedExperiment(experiment.id)"
          />
        </div>
      </template>

      <div
        v-else
        class="left-empty"
      >
        No experiments
      </div>

      <div>
        <button class="primary-btn" @click="$router.push('/experiments/new')">
          Create Experiment
        </button>
      </div>
    </div>

    <div class="content">
      <template v-if="!hasExperiments">
        <div class="empty-state">
          <div class="empty-state-title">No existing experiments</div>
          <div class="empty-state-text">
            Create or load an experiment to view graphs and metrics.
          </div>
        </div>
      </template>

      <template v-else>
        <div class="toolbar">
          <label class="field">
            <span class="toolbar-label">Graph Type</span>
            <select
              :value="selectedGraphType"
              class="select"
              @change="store.setGraphType($event.target.value)"
            >
              <option
                v-for="option in graphTypeOptions"
                :key="option.value"
                :value="option.value"
              >
                {{ option.label }}
              </option>
            </select>
          </label>

          <label
            v-if="!compareMode"
            class="field"
          >
            <span class="toolbar-label">Batch</span>
            <select
              :value="selectedBatchId ?? ''"
              class="select"
              @change="store.setBatch($event.target.value || null)"
            >
              <option value="">Full Experiment Average</option>
              <option
                v-for="batch in availableBatches"
                :key="batch.id"
                :value="batch.id"
              >
                {{ batch.label }}
              </option>
            </select>
          </label>

          <div class="filter-group">
            <span class="toolbar-label">Vitals</span>

            <label
              v-for="vital in availableVitals"
              :key="vital.key"
              class="check-item"
            >
              <input
                type="checkbox"
                :checked="selectedVitalKeys.includes(vital.key)"
                @change="
                  $event.target.checked
                    ? store.setSelectedVitals([...selectedVitalKeys, vital.key])
                    : store.setSelectedVitals(selectedVitalKeys.filter((key) => key !== vital.key))
                "
              />
              <span>{{ vital.label }}</span>
            </label>
          </div>
        </div>

        <template v-if="!compareMode">
          <div class="single-layout">
            <div class="single-chart-card">
              <VChart class="chart" :option="singleChartOptions" autoresize />
            </div>

            <div class="metrics-panel">
              <div class="metrics-panel-title">Experiment Details</div>
              <div class="metrics-panel-subtitle">
                {{ selectedExperiment?.name ?? 'Experiment' }}
              </div>

              <div class="panel-section">
                <div class="panel-section-title">Targets</div>

                <div
                  v-if="selectedExperimentTargets.length"
                  class="target-groups"
                >
                  <div
                    v-for="target in selectedExperimentTargets"
                    :key="`${target.vital_sign}-${target.target_name}`"
                    class="target-group"
                  >
                    <div class="metric-vital-title">
                      {{ target.target_name }}
                    </div>

                    <ul class="metric-list">
                      <li><span>Vital</span><strong>{{ String(target.vital_sign).toUpperCase() }}</strong></li>
                      <li><span>Target Value</span><strong>{{ formatMetricValue(target.target_value) }}</strong></li>
                      <li><span>Tolerance</span><strong>{{ formatMetricValue(target.tolerance) }}</strong></li>
                    </ul>
                  </div>
                </div>

                <div v-else class="metrics-empty">
                  No targets available for selected datapoints.
                </div>
              </div>

              <div class="panel-section">
                <div class="panel-section-title">Metrics</div>

                <div
                  v-if="selectedExperimentMetrics.length"
                  class="metric-groups"
                >
                  <div
                    v-for="metric in selectedExperimentMetrics"
                    :key="metric.metric_id"
                    class="metric-group"
                  >
                    <div class="metric-vital-title">
                      {{ String(metric.vital_sign).toUpperCase() }}
                    </div>

                    <ul class="metric-list">
                      <li><span>MAE</span><strong>{{ formatMetricValue(metric.mae) }}</strong></li>
                      <li><span>Median</span><strong>{{ formatMetricValue(metric.median) }}</strong></li>
                      <li><span>Std Dev</span><strong>{{ formatMetricValue(metric.std_dev) }}</strong></li>
                      <li><span>Time In Range</span><strong>{{ formatMetricValue(metric.time_within_target_range) }}</strong></li>
                      <li><span>% In Range</span><strong>{{ formatMetricValue(metric.percent_time_within_target_range) }}</strong></li>
                      <li><span>Wobble</span><strong>{{ formatMetricValue(metric.wobble) }}</strong></li>
                      <li><span>Divergence</span><strong>{{ formatMetricValue(metric.divergence) }}</strong></li>
                      <li><span>Match Fn</span><strong>{{ formatMetricValue(metric.matching_function) }}</strong></li>
                      <li><span>Match Fn MAE</span><strong>{{ formatMetricValue(metric.matching_function_mae) }}</strong></li>
                    </ul>
                  </div>
                </div>

                <div v-else class="metrics-empty">
                  No metrics available for selected datapoints.
                </div>
              </div>
            </div>
          </div>
        </template>

        <template v-else>
          <div
            v-if="compareChartOptions.length"
            class="compare-grid"
          >
            <div
              v-for="chart in compareChartOptions"
              :key="chart.experimentId"
              class="compare-card"
            >
              <div class="compare-chart-panel">
                <VChart class="chart" :option="chart.option" autoresize />
              </div>

              <div class="compare-metrics-panel">
                <div class="compare-card-title">{{ chart.experimentName }}</div>
                <div class="compare-card-subtitle">
                  Batch: {{ chart.batchLabel }}
                </div>

                <label class="field compare-batch-field">
                  <span class="compare-metric-label">Batch Select</span>
                  <select
                    :value="chart.batchId ?? ''"
                    class="select"
                    @change="store.setComparedExperimentBatch(chart.experimentId, $event.target.value || null)"
                  >
                    <option value="">Full Experiment Average</option>
                    <option
                      v-for="batch in chart.availableBatches"
                      :key="batch.id"
                      :value="batch.id"
                    >
                      {{ batch.label }}
                    </option>
                  </select>
                </label>

                <div class="panel-section">
                  <div class="panel-section-title">Targets</div>

                  <div
                    v-if="chart.targets.length"
                    class="target-groups"
                  >
                    <div
                      v-for="target in chart.targets"
                      :key="`${chart.experimentId}-${target.vital_sign}-${target.target_name}`"
                      class="target-group"
                    >
                      <div class="metric-vital-title">
                        {{ target.target_name }}
                      </div>

                      <ul class="metric-list">
                        <li><span>Vital</span><strong>{{ String(target.vital_sign).toUpperCase() }}</strong></li>
                        <li><span>Target Value</span><strong>{{ formatMetricValue(target.target_value) }}</strong></li>
                        <li><span>Tolerance</span><strong>{{ formatMetricValue(target.tolerance) }}</strong></li>
                      </ul>
                    </div>
                  </div>

                  <div v-else class="metrics-empty">
                    No targets available for selected datapoints.
                  </div>
                </div>

                <div class="panel-section">
                  <div class="panel-section-title">Metrics</div>

                  <div
                    v-if="chart.metrics.length"
                    class="metric-groups"
                  >
                    <div
                      v-for="metric in chart.metrics"
                      :key="metric.metric_id"
                      class="metric-group"
                    >
                      <div class="metric-vital-title">
                        {{ String(metric.vital_sign).toUpperCase() }}
                      </div>

                      <ul class="metric-list">
                        <li><span>MAE</span><strong>{{ formatMetricValue(metric.mae) }}</strong></li>
                        <li><span>Median</span><strong>{{ formatMetricValue(metric.median) }}</strong></li>
                        <li><span>Std Dev</span><strong>{{ formatMetricValue(metric.std_dev) }}</strong></li>
                        <li><span>Time In Range</span><strong>{{ formatMetricValue(metric.time_within_target_range) }}</strong></li>
                        <li><span>% In Range</span><strong>{{ formatMetricValue(metric.percent_time_within_target_range) }}</strong></li>
                        <li><span>Wobble</span><strong>{{ formatMetricValue(metric.wobble) }}</strong></li>
                        <li><span>Divergence</span><strong>{{ formatMetricValue(metric.divergence) }}</strong></li>
                        <li><span>Match Fn</span><strong>{{ formatMetricValue(metric.matching_function) }}</strong></li>
                        <li><span>Match Fn MAE</span><strong>{{ formatMetricValue(metric.matching_function_mae) }}</strong></li>
                      </ul>
                    </div>
                  </div>

                  <div v-else class="metrics-empty">
                    No metrics available for selected datapoints.
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div
            v-else
            class="empty-state"
          >
            <div class="empty-state-title">No existing experiments</div>
            <div class="empty-state-text">
              Select experiments to compare.
            </div>
          </div>
        </template>
      </template>
    </div>
  </div>
</template>

<style scoped>
.wrapper {
  display: flex;
  gap: 20px;
  padding: 20px;
  min-height: 100vh;
  box-sizing: border-box;
}

.left-panel {
  width: 260px;
  background: #1a1a1a;
  border-radius: 12px;
  padding: 15px;
  color: white;
  flex-shrink: 0;
}

.left-panel h3 {
  font-size: 12px;
  margin-bottom: 15px;
}

.compare-toggle {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-bottom: 12px;
  font-size: 13px;
}

.experiment-row {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-bottom: 10px;
}

.exp-btn {
  flex: 1;
  padding: 10px;
  background: #333;
  border: none;
  border-radius: 8px;
  color: white;
  text-align: left;
  cursor: pointer;
}

.exp-btn.active {
  background: #777;
}

.left-empty {
  padding: 14px;
  border-radius: 10px;
  background: #252525;
  color: #bbb;
  font-size: 13px;
}

.content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-width: 0;
}

.toolbar {
  background: #1a1a1a;
  color: white;
  border-radius: 12px;
  padding: 12px;
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.toolbar-label {
  font-size: 12px;
  font-weight: 700;
  color: #ddd;
}

.select {
  min-width: 220px;
  padding: 8px 10px;
  border-radius: 8px;
  border: none;
  background: white;
  color: black;
}

.filter-group {
  display: flex;
  flex-wrap: wrap;
  gap: 10px 14px;
  align-items: center;
}

.check-item {
  display: inline-flex;
  gap: 6px;
  align-items: center;
  font-size: 13px;
}

.single-layout {
  display: grid;
  grid-template-columns: 1fr 340px;
  gap: 16px;
  min-height: 800px;
}

.single-chart-card {
  height: 800px;
  background: white;
  border-radius: 12px;
  padding: 16px;
}

.metrics-panel,
.compare-metrics-panel {
  background: #1a1a1a;
  color: white;
  border-radius: 12px;
  padding: 16px;
  overflow: auto;
}

.metrics-panel-title,
.compare-card-title {
  font-size: 16px;
  font-weight: 700;
  margin-bottom: 6px;
}

.metrics-panel-subtitle,
.compare-card-subtitle {
  font-size: 12px;
  color: #bbb;
  margin-bottom: 12px;
}

.compare-metric-label {
  font-size: 12px;
  font-weight: 700;
  color: #ddd;
}

.compare-batch-field {
  margin-bottom: 14px;
}

.panel-section {
  margin-top: 16px;
}

.panel-section:first-of-type {
  margin-top: 0;
}

.panel-section-title {
  font-size: 13px;
  font-weight: 700;
  color: #ddd;
  margin-bottom: 10px;
}

.chart {
  width: 100%;
  height: 100%;
}

.metric-groups,
.target-groups {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.metric-group,
.target-group {
  background: #252525;
  border-radius: 10px;
  padding: 12px;
}

.metric-vital-title {
  font-size: 13px;
  font-weight: 700;
  margin-bottom: 8px;
  color: #fff;
}

.metric-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.metric-list li {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 6px;
  font-size: 12px;
}

.metric-list li span {
  color: #bbb;
}

.metric-list li strong {
  color: #fff;
  font-weight: 600;
}

.metrics-empty {
  padding: 14px;
  border-radius: 10px;
  background: #252525;
  color: #bbb;
  font-size: 13px;
}

.compare-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 16px;
}

.compare-card {
  display: grid;
  grid-template-columns: 1fr 340px;
  gap: 16px;
  min-height: 460px;
}

.compare-chart-panel {
  background: white;
  border-radius: 12px;
  padding: 16px;
  min-height: 460px;
}

.empty-state {
  min-height: 600px;
  border-radius: 12px;
  background: #111;
  border: 1px dashed #444;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  gap: 8px;
}

.empty-state-title {
  font-size: 20px;
  font-weight: 700;
}

.empty-state-text {
  font-size: 14px;
  color: #bbb;
}

@media (max-width: 1200px) {
  .single-layout,
  .compare-card {
    grid-template-columns: 1fr;
  }

  .single-chart-card {
    height: 500px;
  }
}
</style>