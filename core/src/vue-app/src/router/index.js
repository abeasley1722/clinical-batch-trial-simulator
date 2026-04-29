import { createRouter, createWebHashHistory } from 'vue-router'
import BatchPatient from '@/views/BatchPatient.vue'
import Results from '@/views/Results.vue'

export default createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: '/', component: BatchPatient },
    { path: '/results', component: Results },
  ]
})