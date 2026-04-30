<script setup>
import { RouterLink, RouterView } from 'vue-router'
import logo from '@/assets/large-logo.png'
function exitApp() {
  window.close()
}


</script>

<template>
 <div class="app-layout">
  <!-- Top Bar -->
  <div class="top-bar">
    <img :src="logo" alt="App Logo" class="logo" />
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
  padding-left: 20px;
  z-index: 1000;
}

/* SIDEBAR */
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