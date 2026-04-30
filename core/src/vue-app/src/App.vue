<script setup>
import { ref, onMounted } from 'vue'
import { RouterLink, RouterView } from 'vue-router'
import { serverUrl, connectionStatus, connectToServer } from './services/server.js'
import logoUrl from './assets/logo.png'

const inputUrl = ref(serverUrl.value)

function handleConnect() {
  connectToServer(inputUrl.value)
}

onMounted(() => {
  connectToServer(inputUrl.value)
})

const STATUS_COLOR = {
  disconnected: '#7f8c8d',
  connecting:   '#f39c12',
  connected:    '#27ae60',
  error:        '#e74c3c'
}
</script>

<template>
 <div class="app-layout">
  <!-- Top Bar -->
  <div class="top-bar">
    <img :src="logoUrl" class="top-logo" alt="Clinical Batch Trial Simulator" />
    <div class="server-connect">
      <span class="status-dot" :style="{ background: STATUS_COLOR[connectionStatus] }"></span>
      <label>Server:</label>
      <input
        v-model="inputUrl"
        class="server-input"
        type="text"
        @keyup.enter="handleConnect"
      />
      <button class="connect-btn" @click="handleConnect">Connect</button>
    </div>
  </div>

  <!-- Sidebar -->
  <div class="sidebar">
    <nav>
      <RouterLink to="/">⊞</RouterLink>
      <button class="exit-btn" @click="exitApp">⏻</button>
    </nav>
  </div>

  <!-- Main Content -->
  <div class="main-content">
    <RouterView />
  </div>
</div>
</template>


<style scoped>

/* ROOT LAYOUT */
.app-layout {
  height: 100%;
}

/* TOP BAR */
.top-bar {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 60px;
  background: #01101f;
  color: white;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  z-index: 1000;
  box-sizing: border-box;
}

.top-logo {
  height: 44px;
  width: auto;
  object-fit: contain;
}

.server-connect {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
}

.status-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
  transition: background 0.3s;
}

.server-connect label {
  color: #bdc3c7;
  white-space: nowrap;
}

.server-input {
  width: 210px;
  padding: 4px 8px;
  font-size: 12px;
  background: #34495e;
  color: white;
  border: 1px solid #556b7e;
  border-radius: 4px;
  outline: none;
}

.server-input:focus {
  border-color: #3498db;
}

.connect-btn {
  padding: 4px 12px;
  font-size: 12px;
  background: #3498db;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  white-space: nowrap;
}

.connect-btn:hover {
  background: #2980b9;
}

/* Sidebar */
.sidebar {
  position: fixed;
  top: 60px;
  left: 0;
  width: 70px;
  height: calc(100vh - 60px);
  background-color: #01101f;
  display: flex;
  flex-direction: column;
  padding: 20px;
}
.logo {
  position: relative;
  z-index: 1;

  width: 90px;          /* big but controlled */
  max-width: 80vw;

  border-radius: 6px;   /* 🔥 rounded corners */
  overflow: hidden;      /* ensures clean edges */

  box-shadow: 0 25px 60px rgba(0, 0, 0, 0.6); /* depth */

}

/* NAV */
.sidebar nav {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: auto;

}

.sidebar a {
  color: white;
  text-decoration: none;
}

.sidebar a.router-link-exact-active {
  font-weight: bold;
}

/* MAIN CONTENT (🔥 FIXED) */
.main-content {
  position: absolute;
  top: 60px;
  left: 70px;

  width: calc(100% - 70px);
  height: calc(100vh - 60px);


  overflow-y: auto;
}
</style>