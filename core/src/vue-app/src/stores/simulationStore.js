import { defineStore } from 'pinia'

export const useSimulationStore = defineStore('simulation', {
  state: () => ({
    name: 'Test Batch',

    duration: 300, // seconds
    sampleRate: 50,

    workers: 4,
    replicates: 1,

    patientCount: 8,

    demographics: [
      { name: 'soldier', percent: 50 },
      { name: 'adult', percent: 50 }
    ],

    targetMetrics: {
      hr_bpm: { target_value: 75, tolerance: 5, matching_function: '' },
      spo2_pct: { target_value: 98, tolerance: 2, matching_function: '' },
      etco2_mmhg: { target_value: 40, tolerance: 5, matching_function: '' },
      rr_patient: { target_value: 16, tolerance: 3, matching_function: '' }
    },

    startIntubated: false,
    ventSettings: {},

    events: [],
    triggeredEvents: []
  }),

  actions: {
    addEvent(event) {
      const newEvent = JSON.parse(JSON.stringify(event))

      if (event.activation === 'trigger') {
        this.triggeredEvents.push(newEvent)
      } else {
        this.events.push(newEvent)
      }
    },

    removeEvent(index, type) {
      if (type === 'trigger') this.triggeredEvents.splice(index, 1)
      else this.events.splice(index, 1)
    },

    addDemographic() {
      this.demographics.push({ name: '', percent: 0 })
    },

    removeDemographic(index) {
      this.demographics.splice(index, 1)
    },

    updateMetric(key, field, value) {
      this.targetMetrics[key][field] = value
    },

    buildPayload() {
      return {
        name: this.name,
        patient_count: this.patientCount,

        demographics: this.demographics,

        target_metrics: this.targetMetrics,

        duration_s: this.duration,
        sample_rate_hz: this.sampleRate,

        start_intubated: this.startIntubated,
        vent_settings: this.ventSettings,

        events: [...this.events, ...this.triggeredEvents],

        workers: this.workers,
        replicates: this.replicates
      }
    }

  }
})



// import { defineStore } from 'pinia'
// import { api } from '@/services/api'

// export const useSimulationStore = defineStore('simulation', {
//   state: () => ({
//     job_name: '',
//     duration: 5,
//     duration_unit: 'min',
//     step_size: 0.02,
//     replicates: 1,

//     events: [],
//     progress: 0,
//     status: 'Ready'
//   }),

//   actions: {
//     addEvent() {
//       this.events.push({
//         activation: 'time',
//         time: 1,
//         unit: 'min',
//         type: 'pathology',
//         params: getDefaultParams('pathology')
//       })
//     },

//     removeEvent(i) {
//       this.events.splice(i, 1)
//     },

//     async runSimulation() {
//       this.status = 'Submitting...'
//       this.progress = 10

//       await api.runSimulation({
//         job_name: this.job_name,
//         duration: this.duration,
//         duration_unit: this.duration_unit,
//         step_size: this.step_size,
//         replicates: this.replicates,
//         events: this.events
//       })

//       this.progress = 100
//       this.status = 'Complete'
//     }
//   }
// })