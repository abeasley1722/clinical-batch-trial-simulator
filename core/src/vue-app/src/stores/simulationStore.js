import { defineStore } from 'pinia'
import { api } from '@/services/api'

export const useSimulationStore = defineStore('simulation', {
  state: () => ({
    job_name: '',
    duration: 5,
    duration_unit: 'min',
    step_size: 0.02,
    replicates: 1,

    events: [],
    progress: 0,
    status: 'Ready'
  }),

  actions: {
    addEvent() {
      this.events.push({
        activation: 'time',
        time: 1,
        unit: 'min',
        type: 'pathology',
        params: getDefaultParams('pathology')
      })
    },

    removeEvent(i) {
      this.events.splice(i, 1)
    },

    async runSimulation() {
      this.status = 'Submitting...'
      this.progress = 10

      await api.runSimulation({
        job_name: this.job_name,
        duration: this.duration,
        duration_unit: this.duration_unit,
        step_size: this.step_size,
        replicates: this.replicates,
        events: this.events
      })

      this.progress = 100
      this.status = 'Complete'
    }
  }
})