import { createRouter, createWebHistory } from 'vue-router'
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