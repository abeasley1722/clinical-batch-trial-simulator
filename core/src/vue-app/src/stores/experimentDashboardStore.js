import { defineStore } from 'pinia'
import {
  getExperiments,
  getMetricsByExperiment,
  getBatchesByExperiment,
  getRawCSVData
} from '@/services/api'

export const useExperimentDashboardStore = defineStore('experimentDashboard', {
  state: () => ({
    experiments: [],
    selectedExperimentId: null,
    selectedBatchId: null,

    selectedVitalKeys: [],
    selectedGraphType: 'line',

    metrics: [],
    batches: [],
    rawData: []
  }),

  getters: {
    hasExperiments: (state) => state.experiments.length > 0,

    selectedExperiment(state) {
      return state.experiments.find(
        e => e.experiment_id === state.selectedExperimentId
      )
    },

    selectedExperimentMetrics: (state) => state.metrics,

    availableBatches(state) {
      return state.batches.map(b => ({
        id: b.batch_id,
        label: b.batch_id
      }))
    },

    // ✅ only numeric vitals
    availableVitals(state) {
      if (!state.rawData?.length) return []

      return Object.keys(state.rawData[0])
        .filter(k => k !== 'sim_time_s')
        .filter(k => typeof state.rawData[0][k] === 'number')
        .map(k => ({
          key: k,
          label: k.toUpperCase()
        }))
    },

    chartXAxisLabels(state) {
      if (!state.rawData?.length) return []
      return state.rawData.map(row => row.sim_time_s)
    },

    // 🔥 FIXED: now includes target_value
    chartSeries(state) {
      if (!state.rawData?.length) return []

      const keys = state.selectedVitalKeys.length
        ? state.selectedVitalKeys
        : Object.keys(state.rawData[0])
            .filter(k => k !== 'sim_time_s')
            .filter(k => typeof state.rawData[0][k] === 'number')

      return keys.map(key => {
        // 🔥 MATCH METRIC TO VITAL
        const metric = state.metrics.find(
          m => m.vital_sign === key
        )

        return {
          name: key.toUpperCase(),
          data: state.rawData.map(row => row[key] ?? null),
          unit: '',

          // 🔥 THIS IS THE FIX
          target: metric ? Number(metric.target_value) : null,

          // optional (if you later store tolerance in metrics)
          tolerance: metric?.tolerance ?? null
        }
      })
    }
  },

  actions: {
    async initialize() {
      await this.loadExperiments()

      if (this.experiments.length) {
        await this.selectExperiment(this.experiments[0].experiment_id)
      }
    },

    async loadExperiments() {
      this.experiments = await getExperiments()
    },

    async selectExperiment(id) {
      this.selectedExperimentId = id

      try {
        await Promise.all([
          this.loadMetrics(id),
          this.loadBatches(id),
          this.loadRawCSV(id)
        ])
      } catch (err) {
        console.error('Experiment load failed:', err)
      }
    },

    async loadMetrics(experimentId) {
      const data = await getMetricsByExperiment(experimentId)

      // 🔥 SAFETY: ensure numbers (prevents bytes/strings issues)
      this.metrics = (data || []).map(m => ({
        ...m,
        target_value:
          m.target_value !== null && m.target_value !== undefined
            ? Number(m.target_value)
            : null
      }))
    },

    async loadBatches(experimentId) {
      this.batches = await getBatchesByExperiment(experimentId)
    },

    async loadRawCSV(experimentId) {
      const data = await getRawCSVData(experimentId)

      if (!data?.length) {
        this.rawData = []
        return
      }

      // ensure proper ordering
      data.sort((a, b) => a.sim_time_s - b.sim_time_s)

      this.rawData = data
    },

    setGraphType(type) {
      this.selectedGraphType = type
    },

    setBatch(batchId) {
      this.selectedBatchId = batchId
    },

    setSelectedVitals(vitals) {
      this.selectedVitalKeys = vitals
    }
  }
})