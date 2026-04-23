import { createRouter, createWebHistory } from 'vue-router'

import CreateExperimentView from '@/views/CreateExperimentView.vue'
import MockCreateExperimentView from '@/views/MockCreateExperimentView.vue'
import VitalsDashboardView from '@/views/VitalsDashboardView.vue'
import MockVitalsDashboardView from '@/views/MockVitalsDashboardView.vue'
import BatchPatient from '@/views/BatchPatient.vue'
import Results from '@/views/Results.vue'

export default createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/create-mock', component: MockCreateExperimentView },
    { path: '/', component: BatchPatient },
    { path: '/results', component: Results },
    { path: '/c', component: CreateExperimentView },
    { path: '/dashboard-mock', component: MockVitalsDashboardView },
    { path: '/dashboard', component: VitalsDashboardView }
  ]
})