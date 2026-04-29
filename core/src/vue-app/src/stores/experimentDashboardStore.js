
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

    // 🔥 backend-driven grouping (gases, ventilator, etc.)
    selectedGroups: [],

    metrics: [],
    batches: [],
    rawData: [],

    // 🔥 loading state (for overlay)
    loading: false,

    // 🔥 cache for fetched datasets
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

    // 🔥 CLEAN SERIES (no fake group logic)
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
          name: key.toUpperCase(),
          data: state.rawData.map(r => r[key] ?? null),
          type: state.selectedGraphType,
          target: metric ? Number(metric.target_value) : null,
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

      // 🔥 reset cache when switching experiment
      this.cachedGroups = {}

      this.loading = true

      try {
        await Promise.all([
          this.loadMetrics(id),
          this.loadBatches(id),
          this.loadRawCSV(id) // default = core vitals
        ])
      } catch (err) {
        console.error('Experiment load failed:', err)
      } finally {
        this.loading = false
      }
    },

    async loadMetrics(experimentId) {
      const data = await getMetricsByExperiment(experimentId)

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

    // 🔥 Load CSV with caching
    async loadRawCSV(experimentId, groups = null) {
      const key = groups ? groups.join(',') : 'core'

      // ✅ use cache if available
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

        // ensure proper ordering
        data.sort((a, b) => a.sim_time_s - b.sim_time_s)

        // save to cache
        this.cachedGroups[key] = data

        this.rawData = data
      } catch (err) {
        console.error('Raw CSV load failed:', err)
      } finally {
        this.loading = false
      }
    },

    // 🔥 Change groups (triggers fetch)
    async setGroups(groups) {
      this.selectedGroups = groups

      if (!this.selectedExperimentId) return

      await this.loadRawCSV(this.selectedExperimentId, groups)
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

