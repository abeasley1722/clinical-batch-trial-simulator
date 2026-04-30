// src/stores/simulationStore.js
import { defineStore } from 'pinia'
import { runSimulation, getRawCSVData } from '@/services/api'
import router from '@/router'

export const useSimulationStore = defineStore('simulation', {
  state: () => ({
    name: '',
    duration: null,
    sampleRate: 50,

    workers: null,
    replicates: 1,

    patientCount: null,

    demographics: [],


    targetMetrics: {},

    startIntubated: false,
    ventSettings: {},

    events: [],
    triggeredEvents: [],

    // Progress tracking
    batchId: null,
    batchStatus: null,
    completed: 0,
    total: 0,
    progress: 0,
    status: 'idle',
    pollInterval: null
  }),

  actions: {
    // =========================
    // TARGET METRICS
    // =========================
    addTargetMetric(key) {
      if (this.targetMetrics[key]) return

      this.targetMetrics = {
        ...this.targetMetrics,
        [key]: {
          target_value: 0,
          tolerance: 0,
          matching_function: ''
        }
      }
    },

    removeTargetMetric(key) {
      const copy = { ...this.targetMetrics }
      delete copy[key]
      this.targetMetrics = copy
    },

    // =========================
    // DEMOGRAPHICS
    // =========================
    addDemographic() {
      this.demographics.push({ name: '', percent: 0 })
    },

    removeDemographic(index) {
      this.demographics.splice(index, 1)
    },

    // =========================
    // EVENTS
    // =========================
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

    // =========================
    // BUILD PAYLOAD
    // =========================
    buildPayload() {
      return {
        name: this.name,
        patient_count: Number(this.patientCount),

        demographics: this.demographics.map(d => ({
          name: d.name,
          percent: Number(d.percent)
        })),

        target_metrics: this.targetMetrics,

        duration_s: Number(this.duration),
        sample_rate_hz: Number(this.sampleRate),

        start_intubated: this.startIntubated,
        vent_settings: this.ventSettings || {},

        events: [...this.events, ...this.triggeredEvents],

        workers: Number(this.workers),
        replicates: Number(this.replicates)
      }
    },

    // =========================
    // VALIDATION
    // =========================
    validatePayload() {
      const total = this.demographics.reduce(
        (sum, d) => sum + Number(d.percent || 0),
        0
      )

      if (total !== 100) {
        throw new Error(`Demographics must sum to 100%. Current: ${total}%`)
      }

      for (const d of this.demographics) {
        if (!d.name) {
          throw new Error('All demographics must have a name')
        }
      }
    },

    // =========================
    // SUBMIT BATCH
    // =========================
    async submitBatch() {
      try {
        this.validatePayload()
        this.status = 'submitting'

        router.push('/loading')

        const payload = this.buildPayload()
        console.log('SENDING:\n', JSON.stringify(payload, null, 2))

        const res = await runSimulation(payload)

        this.batchId = res.batch_id

        if (!this.batchId) {
          throw new Error('batch_id missing from backend')
        }

        this.status = 'running'
        this.startPolling()

      } catch (err) {
        console.error(err)
        this.status = 'error'
        router.push('/')
        alert(err.message)
      }
    },

    // =========================
    // POLLING (FIXED)
    // =========================
    startPolling() {
      if (!this.batchId) return

      if (this.pollInterval) {
        clearInterval(this.pollInterval)
      }

      this.pollInterval = setInterval(async () => {
        try {
          const data = await getBatchStatus(this.batchId)

          this.batchStatus = data
          this.status = data.status

          this.completed = data.completed_jobs ?? 0
          this.total = data.total_jobs ?? 0
          this.progress = this.total > 0
            ? Math.round((this.completed / this.total) * 100)
            : 0

          if (data.status !== 'running') {
            clearInterval(this.pollInterval)
            this.pollInterval = null
          }
        } catch (err) {
          console.error(err)
          clearInterval(this.pollInterval)
          this.pollInterval = null
        }
      }, 2000)
    },

    // =========================
    // RESET
    // =========================
    reset() {
      this.batchId = null
      this.batchStatus = null
      this.progress = 0
      this.status = 'idle'

      if (this.pollInterval) {
        clearInterval(this.pollInterval)
        this.pollInterval = null
      }
    }
  }
})