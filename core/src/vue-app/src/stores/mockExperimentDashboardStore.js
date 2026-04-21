import { defineStore } from 'pinia'

export const useExperimentDashboardStore = defineStore('experimentDashboard', {
  state: () => ({
    // ------------------------
    // UI STATE
    // ------------------------
    selectedExperimentId: null,
    selectedExperimentIds: [],
    compareMode: false,
    selectedGraphType: 'line',
    selectedBatchId: null,
    selectedVitalKeys: ['spo2', 'etco2'],

    // ------------------------
    // MOCK DATA
    // ------------------------
    experiments: [
      { id: 'exp1', name: 'ARDS Ventilation Trial' },
      { id: 'exp2', name: 'Oxygen Optimization Study' }
    ],

    batches: {
      exp1: [
        { id: 'b1', label: 'Batch 1' },
        { id: 'b2', label: 'Batch 2' }
      ],
      exp2: [
        { id: 'b3', label: 'Batch 1' }
      ]
    },

    vitals: [
      { key: 'spo2', label: 'SpO₂', unit: '%' },
      { key: 'etco2', label: 'EtCO₂', unit: 'mmHg' },
      { key: 'rr', label: 'Respiratory Rate', unit: 'bpm' },
      { key: 'hr', label: 'Heart Rate', unit: 'bpm' }
    ],

    chartData: {
      exp1: {
        b1: {
          x: ['0s','10s','20s','30s','40s','50s'],
          spo2: [0.88,0.90,0.92,0.94,0.95,0.96],
          etco2: [50,48,46,44,42,40],
          rr: [22,21,20,19,18,18],
          hr: [110,108,105,102,100,98]
        },
        b2: {
          x: ['0s','10s','20s','30s','40s','50s'],
          spo2: [0.87,0.89,0.91,0.92,0.93,0.94],
          etco2: [52,50,48,47,45,43],
          rr: [24,23,22,21,20,19],
          hr: [115,112,110,107,105,103]
        }
      },
      exp2: {
        b3: {
          x: ['0s','10s','20s','30s','40s','50s'],
          spo2: [0.90,0.92,0.94,0.95,0.96,0.97],
          etco2: [45,44,43,42,41,40],
          rr: [20,20,19,18,18,17],
          hr: [100,98,96,94,92,90]
        }
      }
    },

    targets: {
      exp1: [
        { vital_sign: 'spo2', target_name: 'SpO₂ Target', target_value: 0.95, tolerance: 0.02 },
        { vital_sign: 'etco2', target_name: 'CO₂ Target', target_value: 40, tolerance: 3 }
      ],
      exp2: [
        { vital_sign: 'spo2', target_name: 'SpO₂ Target', target_value: 0.96, tolerance: 0.01 }
      ]
    },

    metrics: {
      exp1: [
        {
          metric_id: 'm1',
          vital_sign: 'spo2',
          mae: 0.015,
          median: 0.93,
          std_dev: 0.02,
          time_within_target_range: 40,
          percent_time_within_target_range: 80,
          wobble: 0.01,
          divergence: 0.02,
          matching_function: 0.95,
          matching_function_mae: 0.01
        },
        {
          metric_id: 'm2',
          vital_sign: 'etco2',
          mae: 3.5,
          median: 45,
          std_dev: 4.2,
          time_within_target_range: 30,
          percent_time_within_target_range: 60,
          wobble: 2.1,
          divergence: 3.2,
          matching_function: 0.88,
          matching_function_mae: 2.5
        }
      ],
      exp2: [
        {
          metric_id: 'm3',
          vital_sign: 'spo2',
          mae: 0.01,
          median: 0.95,
          std_dev: 0.01,
          time_within_target_range: 50,
          percent_time_within_target_range: 90,
          wobble: 0.005,
          divergence: 0.01,
          matching_function: 0.97,
          matching_function_mae: 0.008
        }
      ]
    }
  }),

  getters: {
    hasExperiments: (state) => state.experiments.length > 0,

    selectedExperiment(state) {
      return state.experiments.find(e => e.id === state.selectedExperimentId)
    },

    availableBatches(state) {
      return state.batches[state.selectedExperimentId] || []
    },

    availableVitals(state) {
      return state.vitals
    },

    selectedExperimentMetrics(state) {
      return state.metrics[state.selectedExperimentId] || []
    },

    selectedExperimentTargets(state) {
      return state.targets[state.selectedExperimentId] || []
    },

    chartXAxisLabels(state) {
      const exp = state.chartData[state.selectedExperimentId]
      if (!exp) return []
      const batch = state.selectedBatchId || Object.keys(exp)[0]
      return exp[batch]?.x || []
    },

    chartSeries(state) {
      const exp = state.chartData[state.selectedExperimentId]
      if (!exp) return []

      const batch = state.selectedBatchId || Object.keys(exp)[0]
      const batchData = exp[batch]

      return state.selectedVitalKeys.map(vitalKey => {
        const vital = state.vitals.find(v => v.key === vitalKey)
        const target = (state.targets[state.selectedExperimentId] || [])
          .find(t => t.vital_sign === vitalKey)

        return {
          name: vital.label,
          data: batchData[vitalKey],
          unit: vital.unit,
          target: target || null
        }
      })
    },

    graphTypeOptions: () => [
      { label: 'Line', value: 'line' },
      { label: 'Scatter', value: 'scatter' }
    ],

    comparisonCharts(state) {
      return state.selectedExperimentIds.map(expId => {
        const batches = state.batches[expId]
        const batchId = batches[0].id
        const data = state.chartData[expId][batchId]

        return {
          experimentId: expId,
          experimentName: state.experiments.find(e => e.id === expId)?.name,
          batchId,
          batchLabel: batches[0].label,
          availableBatches: batches,
          xAxisLabels: data.x,
          series: state.selectedVitalKeys.map(vitalKey => {
            const vital = state.vitals.find(v => v.key === vitalKey)
            const target = (state.targets[expId] || [])
              .find(t => t.vital_sign === vitalKey)

            return {
              name: vital.label,
              data: data[vitalKey],
              unit: vital.unit,
              target: target || null
            }
          }),
          metrics: state.metrics[expId] || [],
          targets: state.targets[expId] || []
        }
      })
    }
  },

  actions: {
    initialize() {
      if (this.experiments.length) {
        this.selectedExperimentId = this.experiments[0].id
      }
    },

    selectExperiment(id) {
      this.selectedExperimentId = id
      this.selectedBatchId = null
    },

    setBatch(batchId) {
      this.selectedBatchId = batchId
    },

    setGraphType(type) {
      this.selectedGraphType = type
    },

    setSelectedVitals(vitals) {
      this.selectedVitalKeys = vitals
    },

    toggleCompareMode(val) {
      this.compareMode = val
      this.selectedExperimentIds = val ? [] : this.selectedExperimentIds
    },

    toggleComparedExperiment(id) {
      if (this.selectedExperimentIds.includes(id)) {
        this.selectedExperimentIds = this.selectedExperimentIds.filter(e => e !== id)
      } else {
        this.selectedExperimentIds.push(id)
      }
    },

    setComparedExperimentBatch(expId, batchId) {
      // optional extension
    }
  }
})