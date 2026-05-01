<script setup>
import { computed, onMounted, ref } from 'vue'
import { storeToRefs } from 'pinia'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  GridComponent,
  DataZoomComponent,
  MarkLineComponent,
  LegendComponent,
  AxisPointerComponent
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
  MarkLineComponent,
  LegendComponent,
  AxisPointerComponent
])

const store = useExperimentDashboardStore()

onMounted(() => {
  store.initialize()
})

const {
  experiments,
  selectedExperimentId,
  selectedGraphType
} = storeToRefs(store)

// ========================
// BACKEND GROUPS (SOURCE OF TRUTH)
// ========================
const COLUMN_GROUPS = {
  vitals: ["hr_bpm","spo2_pct","rr_patient","sbp_mmhg","dbp_mmhg","map_mmhg","skin_temp_c"],
  gases: ["pao2_mmhg","paco2_mmhg","etco2_mmhg","ph","lactate_mmol_L","hematocrit_pct"],
  circulation: ["co_lpm","blood_volume_ml","blood_loss_ml","blood_infused_ml","crystalloid_infused_ml"],
  respiratory: ["vt_patient_ml","total_lung_volume_ml","total_pulm_ventilation_lpm"],
  ventilator: ["rr_vent","vt_vent_ml","pip_cmh2o","pplat_cmh2o","paw_mean_cmh2o","total_peep_cmh2o","ie_ratio"],
  airflow: ["insp_flow_lpm","exp_flow_lpm","peak_insp_flow_lpm","airway_pressure_cmh2o"],
  compliance: ["resp_compliance_ml_cmh2o","static_compliance_ml_cmh2o"],
  tidal: ["insp_vt_ml","exp_vt_ml"],
  controller: ["cmd_vt_ml","cmd_rr","cmd_fio2","cmd_peep_cmh2o","cmd_pinsp_cmh2o","cmd_itime_s","cmd_crystalloid_rate","cmd_blood_rate","controller_cmd","fluid_cmd"],
  states: ["is_intubated","vent_active","controller_active","fluid_controller_active"]
}

// ========================
// DATA
// ========================
const chartXAxisLabels = computed(() => store.chartXAxisLabels || [])
const chartSeries = computed(() => store.chartSeries || [])
const selectedExperiment = computed(() => store.selectedExperiment || {})

// ========================
// COLOR SYSTEM (GLOBAL CONSISTENCY)
// ========================
const COLOR_POOL = [
  '#5470C6','#91CC75','#FAC858','#EE6666','#73C0DE',
  '#3BA272','#FC8452','#9A60B4','#EA7CCC'
]

const colorMap = {}
let colorIndex = 0

function getColor(name) {
  if (!colorMap[name]) {
    colorMap[name] = COLOR_POOL[colorIndex % COLOR_POOL.length]
    colorIndex++
  }
  return colorMap[name]
}

// ========================
// GROUPING (REAL FIX)
// ========================

const PRIMARY_GROUPS = ['vitals', 'gases', 'circulation', 'respiratory']

const primaryCharts = computed(() =>
  groupedCharts.value.filter(g =>
    PRIMARY_GROUPS.includes(g.groupName)
  )
)

const secondaryCharts = computed(() =>
  groupedCharts.value.filter(g =>
    !PRIMARY_GROUPS.includes(g.groupName)
  )
)
const topSecondaryCharts = computed(() =>
  secondaryCharts.value.slice(0, 2)
)

const bottomSecondaryCharts = computed(() =>
  secondaryCharts.value.slice(2, 6)
)

const groupedCharts = computed(() => {
  if (!chartSeries.value.length) return []

  return Object.entries(COLUMN_GROUPS).map(([groupName, columns]) => {
    const series = chartSeries.value.filter(s =>
      columns.includes(s.name)
    )

    return {
      groupName,
      series
    }
  }).filter(g => g.series.length > 0)
})

// ========================
// LEGEND TOGGLE STATE
// ========================
const hiddenSeries = ref(new Set())

function toggleSeries(name) {
  const next = new Set(hiddenSeries.value)
  if (next.has(name)) {
    next.delete(name)
  } else {
    next.add(name)
  }
  hiddenSeries.value = next
}

const pageIndex = ref(0)
const PAGE_SIZE = 3

const pagedSecondaryCharts = computed(() => {
  const start = pageIndex.value * PAGE_SIZE
  return secondaryCharts.value.slice(start, start + PAGE_SIZE)
})

const totalPages = computed(() =>
  Math.ceil(secondaryCharts.value.length / PAGE_SIZE)
)

function nextPage() {
  if (pageIndex.value < totalPages.value - 1) {
    pageIndex.value++
  }
}

function prevPage() {
  if (pageIndex.value > 0) {
    pageIndex.value--
  }
}

// ========================
// HELPERS
// ========================
function formatNumber(val) {
  if (val === null || val === undefined) return '-'
  return typeof val === 'number' ? val.toFixed(2) : val
}

function formatLabel(name) {
  return name
    ?.replace(/_/g, ' ')
    ?.replace(/\b\w/g, l => l.toUpperCase())
}

function rangeBadgeStyle(pct) {
  const clamped = Math.min(100, Math.max(0, pct ?? 0))
  const hue = (clamped / 100) * 120
  return { background: `hsl(${hue}, 65%, 32%)` }
}

// ========================
// CHART OPTIONS
// ========================
function makeChartOptions(group, xAxisLabels, graphType) {
  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' }
    },

    axisPointer: {
      link: [{ xAxisIndex: 'all' }]
    },

    grid: { left: 10, right: 10, top: 10, bottom: 10 },

    dataZoom: [
      { type: 'inside', xAxisIndex: [0] },
      { type: 'slider', xAxisIndex: [0] }
    ],

    xAxis: {
      type: 'category',
      data: xAxisLabels,
      boundaryGap: false,
      axisLabel: {
        fontSize: 14,              // 👈 increase font size
        color: 'white' // 👈 your theme color
      },
    },

    yAxis: {
      type: 'value',
      scale: true,
      axisLabel: {
        fontSize: 14,              // 👈 increase font size
        color: 'white' // 👈 your theme color
      },
    },

    series: group.series.map(item => {
      const hidden = hiddenSeries.value.has(item.name)
      return {
        name: item.name,
        type: graphType,
        showSymbol: false,
        data: item.data,
        lineStyle: {
          width: 2,
          color: getColor(item.name),
          opacity: hidden ? 0 : 1
        },
        itemStyle: {
          color: getColor(item.name),
          opacity: hidden ? 0 : 1
        },
        markLine: item.target
          ? {
              symbol: ['none', 'none'],
              lineStyle: { type: 'dashed', color: 'red' },
              data: [{ yAxis: Number(item.target) }]
            }
          : undefined
      }
    })
  }
}
</script>

<template>
  <LoadingOverlay :visible="store.loading" />

  <div class="wrapper">

    

    <!-- MAIN -->
    <div class="content">

      <div class="charts-section">

       <div class="charts-layout">

        <!-- 🔥 MAIN 4 -->
        <div class="primary-grid">
          <div
            v-for="group in primaryCharts"
            :key="group.groupName"
            class="chart-card large"
          >
            <div class="card-header">{{ formatLabel(group.groupName) }}</div>

            <div class="custom-legend">
              <div
                v-for="s in group.series"
                :key="s.name"
                class="legend-item"
                @click="toggleSeries(s.name)"
              >
                <span class="legend-color" :style="{ background: getColor(s.name) }"></span>
                {{ formatLabel(s.name) }}
              </div>
            </div>

            <VChart
              class="chart large-chart"
              :option="makeChartOptions(group, chartXAxisLabels, selectedGraphType)"
            />
          </div>
        </div>

      <!-- 🔽 SECONDARY SECTION -->
<div class="secondary-section">

  <!-- Divider -->
  <div class="section-divider">
    <span>Additional Signals</span>
  </div>

  <!-- Carousel -->
  <div class="carousel">

    <!-- LEFT ARROW -->
    <button
      class="arrow left"
      @click="prevPage"
      :disabled="pageIndex === 0"
    >
      ←
    </button>

    <!-- CHARTS -->
    <div class="carousel-track">
      <div
        v-for="group in pagedSecondaryCharts"
        :key="group.groupName"
        class="chart-card carousel-card"
      >
        <div class="card-header">
          {{ formatLabel(group.groupName) }}
        </div>

        <VChart
          class="chart carousel-chart"
          :option="makeChartOptions(group, chartXAxisLabels, selectedGraphType)"
        />
      </div>
    </div>

    <!-- RIGHT ARROW -->
    <button
      class="arrow right"
      @click="nextPage"
      :disabled="pageIndex >= totalPages - 1"
    >
      →
    </button>

  </div>

</div>

</div>


</div>

      <!-- RIGHT PANEL -->
      <div class="right-panel">

        <!-- SAVED EXPERIMENTS -->
        <div class="panel-block saved-block">
          <div class="block-header">Saved Experiments</div>

          <div class="saved-list">
            <button
              v-for="exp in experiments"
              :key="exp.experiment_id"
              class="exp-btn"
              :class="{ active: exp.experiment_id === selectedExperimentId }"
              @click="store.selectExperiment(exp.experiment_id)"
            >
              {{ exp.name }}
            </button>
          </div>

          <button class="primary-btn full" @click="router.push('/')">
            + Create Experiment
          </button>
        </div>

        <!-- TARGETS -->
        <div class="panel-block">
          <div class="block-header">
            {{ selectedExperiment?.name || 'Experiment' }}
          </div>

          <div class="section-title">Targets</div>

          <div v-if="store.selectedExperimentMetrics?.length">
            <div
              v-for="m in store.selectedExperimentMetrics"
              :key="m.metric_id"
              class="panel-row"
            >
              <span>{{ formatLabel(m.vital_sign) }}</span>
              <span class="target">→ {{ m.target_value ?? '-' }}</span>
            </div>
          </div>

          <div v-else class="empty">No targets</div>
        </div>

        <!-- METRICS -->
        <div class="panel-block">
          <div class="section-title">Metrics</div>

          <div v-if="store.selectedExperimentMetrics?.length" class="metrics-grid">

            <div
              v-for="m in store.selectedExperimentMetrics"
              :key="m.metric_id"
              class="metric-card"
            >
              <div class="metric-header">
                {{ formatLabel(m.vital_sign) }}
              </div>

              <div class="metric-primary">
                <div class="metric-main">
                  <span class="metric-label">MAE</span>
                  <span class="metric-value">
                    {{ formatNumber(m.mae) }}
                  </span>
                </div>

                <div class="metric-main">
                  <span class="metric-label">Median</span>
                  <span class="metric-value">
                    {{ formatNumber(m.median) }}
                  </span>
                </div>
              </div>

              <div class="metric-secondary">
                <div class="metric-item"><span>Std</span><span>{{ formatNumber(m.std_dev) }}</span></div>
                <div class="metric-item"><span>Div</span><span>{{ formatNumber(m.divergence) }}</span></div>
                <div class="metric-item"><span>Wobble</span><span>{{ formatNumber(m.wobble) }}</span></div>
                <div class="metric-item">
                  <span>% in Range</span>
                  <span class="badge success" :style="rangeBadgeStyle(m.percent_time_within_target_range)">
                    {{ formatNumber(m.percent_time_within_target_range) }}%
                  </span>
                </div>
              </div>

              <div v-if="m.matching_function" class="matching-function-section">
                <div class="metric-item">
                  <span class="metric-label">Matching Fn</span>
                  <span class="matching-fn-name">{{ m.matching_function }}</span>
                </div>
                <div class="metric-item">
                  <span class="metric-label">Matching MAE</span>
                  <span class="metric-value">{{ formatNumber(m.matching_function_mae) }}</span>
                </div>
              </div>

            </div>

          </div>

          <div v-else class="empty">No metrics</div>
        </div>

      </div>

    </div>
  </div>
</template>

<style scoped>
/* ========================
   WRAPPER
======================== */
.wrapper {
  display: flex;
  gap: 16px;
  padding: 16px;
  height: 100vh;
  box-sizing: border-box;
  overflow: hidden;
  background: linear-gradient(180deg, rgb(12, 15, 20) 0%, rgb(20, 24, 33) 55%, rgb(2, 3, 6) 100%);
}

/* ========================
   LEFT PANEL
======================== */
.left-panel {
  width: 260px;
  background: #1a1a1a;
  color: white;
  padding: 12px;
  border-radius: 10px;
}

/* ========================
   MAIN CONTENT
======================== */
.content {
  display: grid;
  grid-template-columns: 1fr 300px;
  gap: 16px;
  flex: 1;
  height: 100%;
}

/* ========================
   CHARTS SECTION (scrollable column)
======================== */
.charts-section {
  overflow-y: auto;
  min-height: 0;
  height: 100%;
}

/* ========================
   DASHBOARD LAYOUT
======================== */
.charts-layout {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding-bottom: 24px;
}

/* ========================
   MAIN 4 GRID
======================== */
.primary-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  grid-template-rows: 1fr 1fr;  
  gap: 12px;
}

/* ========================
   SECONDARY SECTION (CAROUSEL)
======================== */
.carousel {
  display: flex;
  align-items: center;
  gap: 10px;

}

.carousel-track {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  flex: 1;
}
.secondary-section {
  display: flex;
  flex-direction: column;
  height: 100%;
  gap: 8px;
}

/* ========================
   CARDS (UNIFIED)
======================== */
.chart-card {
  background: #1c2431;
  border: 1px solid #334155;
  border-radius: 12px;
  padding: 12px;
  box-shadow: 0 4px 12px rgba(116, 114, 114, 0.2);
  display: flex;
  flex-direction: column;
  min-height: 0;
}

/* MAIN CHARTS */
.chart-card.large {
  display: flex;
  flex-direction: column;
}

/* SECONDARY CHARTS */
.carousel-card {
  flex: 1;
}

/* ========================
   HEADER
======================== */
.card-header {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 6px;
  color: #e5e7eb;
}

/* ========================
   LEGEND
======================== */
.custom-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 6px;
}

.legend-item {
  display: flex;
  align-items: center;
  font-size: 16px;
  padding: 3px 6px;
  border-radius: 6px;
  background: #2a3050;
  cursor: pointer;
}

.legend-item:hover {
  background: #3a4170;
}

.legend-color {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  margin-right: 4px;
}

/* ========================
   CHART (🔥 FIX)
======================== */
.chart {
  height: 400px;
}

/* ========================
   CAROUSEL ARROWS
======================== */
.arrow {
  background: #334155;
  border: none;
  color: white;
  width: 32px;
  height: 32px;
  border-radius: 6px;
  cursor: pointer;
}

.arrow:hover {
  background: #475569;
}

.arrow:disabled {
  opacity: 0.3;
}

/* ========================
   RIGHT PANEL
======================== */
.right-panel {
  display: flex;
  flex-direction: column;
  gap: 14px;
  overflow-y: auto;
  min-height: 0;
}

/* BLOCKS */
.panel-block {
  background: #1e293b;
  border-radius: 12px;
  padding: 12px;
  border: 1px solid #334155;
}

/* HEADER */
.block-header {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 8px;
  color: #cbd5f5;
}

/* SAVED EXPERIMENTS */
.saved-block {
  position: sticky;
  top: 0;
  z-index: 5;
  background: #1e293b;
}

/* BUTTONS */
.exp-btn {
  width: 100%;
  padding: 8px;
  margin-bottom: 6px;
  background: #334155;
  border: none;
  border-radius: 6px;
  color: white;
  text-align: left;
  font-size: 16px;
  cursor: pointer;
}

.exp-btn.active {
  background: #2563eb;
}

/* ========================
   TARGETS
======================== */
.panel-row {
  display: flex;
  justify-content: space-between;
  font-size: 16x;
  padding: 4px 0;
}

.section-title {
  font-size: 18px;
  color: #9ca3af;
  margin: 6px 0;
}

.target {
  color: #4fc3f7;
}

/* ========================
   METRICS
======================== */
.metrics-grid {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.metric-card {
  background: #222;
  border-radius: 8px;
  padding: 10px;
  border: 1px solid #333;
}

.metric-header {
  font-weight: 600;
  font-size: 16px;
  margin-bottom: 6px;
}

.metric-primary {
  display: flex;
  justify-content: space-between;
  margin-bottom: 6px;
}

.metric-label {
  font-size: 16px;
  color: #aaa;
}

.metric-value {
  font-size: 14px;
  font-weight: bold;
  color: #4fc3f7;
}

.metric-secondary {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 4px;
}

.metric-item {
  display: flex;
  justify-content: space-between;
  font-size: 15px;
  color: #ccc;
}

.matching-function-section {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid #333;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.matching-fn-name {
  font-size: 13px;
  color: #93add4;
  font-style: italic;
}

/* ========================
   BADGES
======================== */
.badge.success {
  background: #2e7d32;
  color: white;
  padding: 2px 5px;
  border-radius: 5px;
  font-size: 10px;
}

/* ========================
   MISC
======================== */
.empty {
  color: #aaa;
}

.primary-btn {
  padding: 10px;
  background: #333;
  border: none;
  border-radius: 6px;
  color: white;
  cursor: pointer;
}
</style>