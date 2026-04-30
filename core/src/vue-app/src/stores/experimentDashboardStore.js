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
    rawData: [],

    loading: false,

    // 🔥 cache per selection set
    cachedGroups: {}
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

    // ✅ Available numeric vitals
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

    // 🔥 CLEAN SERIES (matches backend columns EXACTLY)
    chartSeries(state) {
      if (!state.rawData?.length) return []

      const keys = state.selectedVitalKeys.length
        ? state.selectedVitalKeys
        : Object.keys(state.rawData[0])
            .filter(k => k !== 'sim_time_s')
            .filter(k => typeof state.rawData[0][k] === 'number')

      return keys.map(key => {
        const metric = state.metrics.find(
          m => m.vital_sign === key
        )

        return {
          name: key, // 🔥 DO NOT uppercase (must match backend columns)
          data: state.rawData.map(r => r[key] ?? null),
          type: state.selectedGraphType,
          target: metric ? Number(metric.target_value) : null,
          tolerance: metric?.tolerance ?? null
        }
      })
    }
  },

  actions: {
    // ========================
    // INIT
    // ========================
    async initialize() {
      await this.loadExperiments()

      if (this.experiments.length) {
        await this.selectExperiment(this.experiments[0].experiment_id)
      }
    },

    async loadExperiments() {
      this.experiments = await getExperiments()
    },

    // ========================
    // SELECT EXPERIMENT
    // ========================
    async selectExperiment(id) {
      this.selectedExperimentId = id

      // reset cache
      this.cachedGroups = {}

      this.loading = true

      try {
        await Promise.all([
          this.loadMetrics(id),
          this.loadBatches(id),
          this.loadRawCSV(id, ['all']) // 🔥 FIXED (load ALL groups)
        ])
      } catch (err) {
        console.error('Experiment load failed:', err)
      } finally {
        this.loading = false
      }
    },

    // ========================
    // METRICS
    // ========================
    async loadMetrics(experimentId) {
    const data = await getMetricsByExperiment(experimentId)

    function toNumberOrNull(value) {
      return value != null ? Number(value) : null
    }

    this.metrics = (data || []).map(m => ({
      ...m,

      // 🔥 normalize ALL numeric fields
      target_value: toNumberOrNull(m.target_value),
      mae: toNumberOrNull(m.mae),
      median: toNumberOrNull(m.median),
      std_dev: toNumberOrNull(m.std_dev),
      wobble: toNumberOrNull(m.wobble),
      divergence: toNumberOrNull(m.divergence),
      percent_time_within_target_range: toNumberOrNull(m.percent_time_within_target_range),
      time_within_target_range: toNumberOrNull(m.time_within_target_range)
    }))
  },

    // ========================
    // BATCHES
    // ========================
    async loadBatches(experimentId) {
      this.batches = await getBatchesByExperiment(experimentId)
    },

    // ========================
    // LOAD CSV (FIXED)
    // ========================
    async loadRawCSV(experimentId, groups = null) {
      const key = groups?.length ? groups.join(',') : 'core'

      // ✅ use cache
      if (this.cachedGroups[key]) {
        this.rawData = this.cachedGroups[key]
        return
      }

      this.loading = true

      try {
        const data = await getRawCSVData(experimentId, groups)

        if (!data?.length) {
          this.rawData = []
          return
        }

        // ensure sorted
        data.sort((a, b) => a.sim_time_s - b.sim_time_s)

        // cache it
        this.cachedGroups[key] = data

        this.rawData = data
      } catch (err) {
        console.error('Raw CSV load failed:', err)
      } finally {
        this.loading = false
      }
    },

    // ========================
    // UI CONTROLS
    // ========================
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