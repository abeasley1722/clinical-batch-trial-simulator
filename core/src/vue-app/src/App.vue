<script setup>
import { ref } from 'vue'
import { RouterLink, RouterView } from 'vue-router'
import { serverUrl, connectionStatus, connectToServer } from './services/server.js'

const inputUrl = ref(serverUrl.value)

function handleConnect() {
  connectToServer(inputUrl.value)
}

const STATUS_COLOR = {
  disconnected: '#7f8c8d',
  connecting:   '#f39c12',
  connected:    '#27ae60',
  error:        '#e74c3c'
}
</script>

<template>
  <!-- Top Bar -->
  <div class="top-bar">
    <h3>Clinical Batch Trial Simulator</h3>
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

  <!-- Sidebar //Note: Create a settings page-->
  <div class="sidebar">
    <nav>
      <RouterLink to="/">⊞</RouterLink>
      <RouterLink to="/results">⚙</RouterLink> 
    </nav>
  </div>

  <!-- Main Content -->
  <div class="main-content">
    <RouterView />
  </div>
</template>


<style scoped>

/*Top Bar*/
.top-bar {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 60px;
  background-color: #2c3e50;
  color: white;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  z-index: 1000;
  box-sizing: border-box;
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
  top: 60px; /* below top bar */
  left: 0;
  width: 70px;
  height: calc(100vh - 60px);
  background-color: #34495e;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 20px;
}

/* Nav links */
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

/* Bottom buttons */
.bottom-buttons {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.bottom-buttons button {
  padding: 10px;
  border: none;
  cursor: pointer;
  background-color: #1abc9c;
  color: white;
  border-radius: 5px;
}


.main-content {
  margin-left: 70px;
  margin-top: 60px;
  height: calc(100vh - 60px);
}
</style>