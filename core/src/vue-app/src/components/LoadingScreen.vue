<!-- src/components/LoadingScreen.vue -->
<script setup>
import { computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useSimulationStore } from '@/stores/simulationStore'
import ProgressPanel from './ProgressPanel.vue'

const store = useSimulationStore()
const router = useRouter()

const message = computed(() => {
  if (store.status === 'submitting') return 'Submitting simulation...'
  if (store.status === 'running') return 'Running simulation...'
  return 'Loading simulation...'
})

const submessage = computed(() => {
  if (store.status === 'running') return `Processing ${store.total} batch jobs`
  return 'Preparing patient state, controllers, and events'
})

watch(() => store.status, (status) => {
  if (status === 'completed') {
    router.push('/results')
  } else if (status === 'cancelled' || status === 'failed') {
    router.push('/')
  }
}, { immediate: true })
</script>

<template>
  <div class="loading-screen" role="status" aria-live="polite" aria-busy="true">
    <div class="loading-card">
      <div class="spinner-wrap">
        <div class="spinner-ring"></div>
        <div class="spinner-core"></div>
      </div>

      <h1 class="title">{{ message }}</h1>
      <p class="subtitle">{{ submessage }}</p>

      <div class="progress">
        <div class="progress-bar"></div>
      </div>

      <div class="dots" aria-hidden="true">
        <span></span>
        <span></span>
        <span></span>
      </div>
    </div>

    <div class="progress-panel-wrap">
      <ProgressPanel />
    </div>
  </div>
</template>

<style scoped>
.loading-screen {
  min-height: 100vh;
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 24px;
  padding: 24px;
  box-sizing: border-box;
  background: linear-gradient(180deg, rgb(43, 42, 60) 0%, rgb(31, 38, 52) 55%, rgb(21, 27, 38) 100%);
  color: #f3f6fb;
}

.progress-panel-wrap {
  width: min(460px, 100%);
}

.loading-card {
  width: min(460px, 100%);
  padding: 32px 28px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(170, 190, 220, 0.16);
  box-shadow:
    0 16px 40px rgba(0, 0, 0, 0.35),
    inset 0 1px 0 rgba(255, 255, 255, 0.04);
  backdrop-filter: blur(10px);
  text-align: center;
}

.spinner-wrap {
  position: relative;
  width: 82px;
  height: 82px;
  margin: 0 auto 22px;
}

.spinner-ring {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  border: 4px solid rgba(133, 157, 191, 0.18);
  border-top-color: #9fb5d6;
  border-right-color: #7f97bd;
  animation: spin 1s linear infinite;
}

.spinner-core {
  position: absolute;
  inset: 16px;
  border-radius: 50%;
  background: radial-gradient(circle at top, rgba(170, 196, 230, 0.9), rgba(90, 108, 140, 0.25) 70%, transparent 72%);
  box-shadow: 0 0 22px rgba(137, 167, 214, 0.18);
}

.title {
  margin: 0 0 8px;
  font-size: 1.5rem;
  font-weight: 700;
  letter-spacing: 0.02em;
}

.subtitle {
  margin: 0 0 20px;
  color: #b8c2d3;
  font-size: 0.95rem;
  line-height: 1.5;
}

.progress {
  width: 100%;
  height: 10px;
  border-radius: 999px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.08);
  margin-bottom: 18px;
}

.progress-bar {
  width: 40%;
  height: 100%;
  border-radius: 999px;
  background: linear-gradient(90deg, #6e85aa 0%, #93add4 100%);
  animation: load 1.4s ease-in-out infinite;
}

.dots {
  display: inline-flex;
  gap: 8px;
  align-items: center;
  justify-content: center;
}

.dots span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #a3b5cf;
  opacity: 0.35;
  animation: pulse 1.2s infinite ease-in-out;
}

.dots span:nth-child(2) {
  animation-delay: 0.2s;
}

.dots span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@keyframes load {
  0% {
    transform: translateX(-120%);
  }
  50% {
    transform: translateX(180%);
  }
  100% {
    transform: translateX(300%);
  }
}

@keyframes pulse {
  0%,
  80%,
  100% {
    opacity: 0.3;
    transform: scale(0.85);
  }
  40% {
    opacity: 1;
    transform: scale(1);
  }
}
</style>