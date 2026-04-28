<script setup>
import { RouterLink, RouterView } from 'vue-router'

</script>

<template>
  <!-- Top Bar -->
  <div class="top-bar">
    <h3>My App</h3>
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
  padding-left: 20px;
  z-index: 1000;
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