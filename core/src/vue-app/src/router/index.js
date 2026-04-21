import { createRouter, createWebHistory } from 'vue-router'

import SimulationSetupView from '@/views/SimulationSetupView.vue'
import VitalsDashboardView from '@/views/VitalsDashboardView.vue'

export default createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: SimulationSetupView },
    { path: '/dashboard', component: VitalsDashboardView }
  ]
})