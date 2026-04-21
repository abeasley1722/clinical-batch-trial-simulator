import { ref, computed } from 'vue'
import { defineStore } from 'pinia'

export const useCounterStore = defineStore('counter', () => {
  const count = ref(0)
  const doubleCount = computed(() => count.value * 2)
  function increment() {
    count.value++
  }

  return { count, doubleCount, increment }
})

// export const useExperimentStore = defineStore('experiments', {
//   state: () => ({
//     experiments: [],
//     loaded: false
//   }),

//   actions: {
//     async fetchExperiments() {
//       const res = await api.get('/experiments') // Fetch the endpoint for experiments
//       this.experiments = res.data
//       this.loaded = true
//     },

//     addExperiment(exp) {
//       this.experiments.push(exp)
//     }
//   }
// })
