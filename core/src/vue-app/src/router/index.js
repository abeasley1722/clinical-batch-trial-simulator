
// ============================================================
// Author:         Anointiyae Beasley
// Date Created:   2026-04-01
// Description:    Vue router setup for navigating between main
//                 pages of the application.
// ============================================================

import { createRouter, createWebHashHistory } from 'vue-router'
import LoadingScreen from '@/components/LoadingScreen.vue'
import Home from '@/views/Home.vue'
import BatchPatient from '@/views/BatchPatient.vue'
import Results from '@/views/Results.vue'

export default createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: '/', component: Home },
    { path: '/batch', component: BatchPatient },
    {path: '/loading', component: LoadingScreen},
    { path: '/results', component: Results },
  ]
})