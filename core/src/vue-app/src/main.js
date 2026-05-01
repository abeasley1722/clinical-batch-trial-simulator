// ============================================================
// Author:         Anointiyae Beasley
// Date Created:   2026-04-01
// Description:    Main entry file for initializing Vue app with
//                 router and Pinia store.
// ============================================================
import './assets/main.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'


const app = createApp(App)

app.use(createPinia())
app.use(router)


app.mount('#app')
