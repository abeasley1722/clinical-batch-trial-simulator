<!-- src/views/Home.vue -->
<script setup>
import { useRouter } from 'vue-router'
import logo from '@/assets/large-logo.png'

const router = useRouter()

function goToBatch() {
  router.push('/batch')
}

function goToResults() {
  router.push('/results')
}
</script>

<template>
  <div class="home">
    <div class="overlay"></div>

    <div class="content">
      <!-- 🔥 HERO LOGO -->
      <div class="logo-wrapper">
        <div class="logo-glow"></div>
        <img :src="logo" alt="App Logo" class="logo" />
      </div>

      <p class="tagline">
        Design, run, and analyze complex patient scenarios with full control over
        physiology, interventions, and outcomes.
      </p>

      <div class="actions">
        <button class="primary" @click="goToBatch">
          Start New Simulation
        </button>

        <button class="secondary" @click="goToResults">
          View Results
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.home {
  position: relative;
  height: 100%;
  display: grid;
  place-items: center;
  overflow: hidden;

  background: linear-gradient(
    180deg,
    rgb(5, 2, 52) 0%,
    rgb(31, 38, 52) 55%,
    rgb(2, 14, 37) 100%
  );

  color: white;
}

/* ambient background glow */
.overlay {
  position: absolute;
  width: 900px;
  height: 900px;
  background: radial-gradient(
    circle,
    rgba(120, 150, 200, 0.18),
    transparent 70%
  );
  filter: blur(80px);
  z-index: 0;
}

/* ===================== */
/* 🔥 LOGO HERO */
/* ===================== */
/* wrapper spacing */
/* center wrapper */
.logo-wrapper {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-bottom: 40px;
  position: relative;
}

/* glow stays centered */
.logo-glow {
  position: absolute;
  width: 420px;
  height: 420px;
  background: radial-gradient(
    circle,
    rgba(140, 170, 220, 0.35),
    transparent 70%
  );
  filter: blur(60px);
  z-index: 0;
}

/* 🔥 FINAL LOGO */
.logo {
  position: relative;
  z-index: 1;

  width: 720px;          /* big but controlled */
  max-width: 80vw;

  border-radius: 24px;   /* 🔥 rounded corners */
  overflow: hidden;      /* ensures clean edges */

  box-shadow: 0 25px 60px rgba(0, 0, 0, 0.6); /* depth */

  animation: float 4s ease-in-out infinite;
}
/* ===================== */
/* TEXT */
/* ===================== */
.content {
  position: relative;
  z-index: 1;

  max-width: 700px;
  text-align: center;
  padding: 40px;
}

.headline {
  font-size: 2.6rem;
  font-weight: 700;
  margin-bottom: 16px;
}

.tagline {
  font-size: 1.1rem;
  color: #b8c2d3;
  line-height: 1.6;
  margin-bottom: 30px;
}

/* ===================== */
/* BUTTONS */
/* ===================== */
.actions {
  display: flex;
  gap: 16px;
  justify-content: center;
}

.primary {
  padding: 14px 24px;
  border-radius: 12px;
  border: none;

  background: linear-gradient(90deg, #6e85aa, #93add4);
  color: white;
  font-weight: 600;
  cursor: pointer;

  transition: 0.2s ease;
}

.primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 25px rgba(0,0,0,0.35);
}

.secondary {
  padding: 14px 24px;
  border-radius: 12px;
  border: 1px solid rgba(170, 190, 220, 0.25);

  background: rgba(255, 255, 255, 0.04);
  color: #c9d3e3;
  cursor: pointer;
}

.secondary:hover {
  background: rgba(255,255,255,0.08);
}

/* ===================== */
/* ANIMATIONS */
/* ===================== */
@keyframes float {
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-8px); }
}

@keyframes pulseGlow {
  0%, 100% { opacity: 0.6; transform: scale(1); }
  50% { opacity: 1; transform: scale(1.1); }
}
</style>