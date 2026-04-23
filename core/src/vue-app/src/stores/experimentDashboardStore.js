import { defineStore } from 'pinia'
import { api } from '@/services/api'

export const useExperimentDashboardStore = defineStore('expDash', {
  state: () => ({
    experiments: [],
    selectedExperimentId: null,
    vitalsData: [],
    selectedVitalKeys: []
  }),

  getters: {
    hasExperiments: s => s.experiments.length > 0,

    availableVitals(state) {
      if (!state.vitalsData.length) return []

      return Object.keys(state.vitalsData[0])
        .filter(k => k !== 'time')
        .map(k => ({ key: k, label: k.toUpperCase() }))
    },

    chartXAxisLabels: s => s.vitalsData.map(v => v.time),

    chartSeries(state) {
      return state.selectedVitalKeys.map(key => ({
        name: key,
        data: state.vitalsData.map(v => v[key])
      }))
    }
  },

  actions: {
    async initialize() {
      this.experiments = await api.getExperiments()
    },

    async selectExperiment(id) {
      this.selectedExperimentId = id
      const data = await api.getExperimentData(id)

      this.vitalsData = data.vitals || []
      this.selectedVitalKeys = this.availableVitals.map(v => v.key)
    },

    toggleVital(key) {
      if (this.selectedVitalKeys.includes(key)) {
        this.selectedVitalKeys = this.selectedVitalKeys.filter(k => k !== key)
      } else {
        this.selectedVitalKeys.push(key)
      }
    }
  }
})