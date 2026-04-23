// src/views/CreateExperimentView.vue
<script setup>
import { computed, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const API_ENDPOINT = '/api/experiments'

function createDemographic() {
  return {
    demographic: '',
    percentage: ''
  }
}

function createEvent() {
  return {
    name: '',
    source: 'html'
  }
}

function createTarget() {
  return {
    vital_sign: '',
    target_name: '',
    target_value: '',
    tolerance: ''
  }
}

const form = reactive({
  experimentName: '',
  simulationDuration: '',
  totalPatients: '',
  demographics: [createDemographic(), createDemographic()],
  events: [createEvent()],
  targets: [createTarget()]
})

const availableDemographics = [
  'Age 18-40',
  'Age 41-65',
  'Age 65+',
  'Male',
  'Female',
  'Diabetic',
  'Hypertensive'
]

const availableVitals = [
  { value: 'hr', label: 'HR' },
  { value: 'spo2', label: 'SpO2' },
  { value: 'fio2', label: 'FiO2' },
  { value: 'rr', label: 'RR' },
  { value: 'temperature', label: 'Temperature' },
  { value: 'sbp', label: 'SBP' },
  { value: 'dbp', label: 'DBP' },
  { value: 'map', label: 'MAP' },
  { value: 'etco2', label: 'EtCO2' }
]

const loading = ref(false)
const errorMessage = ref('')
const successMessage = ref('')

const demographicTotal = computed(() =>
  form.demographics.reduce((sum, item) => sum + Number(item.percentage || 0), 0)
)

function addDemographic() {
  form.demographics.push(createDemographic())
}

function removeDemographic(index) {
  if (form.demographics.length <= 1) return
  form.demographics.splice(index, 1)
}

function addEvent() {
  form.events.push(createEvent())
}

function removeEvent(index) {
  if (form.events.length <= 1) return
  form.events.splice(index, 1)
}

function addTarget() {
  form.targets.push(createTarget())
}

function removeTarget(index) {
  if (form.targets.length <= 1) return
  form.targets.splice(index, 1)
}

function validateForm() {
  if (!form.experimentName.trim()) {
    return 'Experiment name is required.'
  }

  if (!form.simulationDuration || Number(form.simulationDuration) <= 0) {
    return 'Simulation duration must be greater than 0.'
  }

  if (!form.totalPatients || Number(form.totalPatients) <= 0) {
    return 'Total number of patients must be greater than 0.'
  }

  for (const demographic of form.demographics) {
    if (!demographic.demographic.trim()) {
      return 'Each demographic row needs a demographic.'
    }
    if (demographic.percentage === '' || Number(demographic.percentage) < 0) {
      return 'Each demographic row needs a valid percentage.'
    }
  }

  if (demographicTotal.value !== 100) {
    return 'Demographic percentages must add up to 100.'
  }

  for (const event of form.events) {
    if (!event.name.trim()) {
      return 'Each event row needs an event name.'
    }
  }

  for (const target of form.targets) {
    if (!target.vital_sign) {
      return 'Each target row needs a vital sign.'
    }
    if (!target.target_name.trim()) {
      return 'Each target row needs a target name.'
    }
    if (target.target_value === '' || Number.isNaN(Number(target.target_value))) {
      return 'Each target row needs a numeric target value.'
    }
    if (target.tolerance === '' || Number.isNaN(Number(target.tolerance))) {
      return 'Each target row needs a numeric tolerance.'
    }
  }

  return ''
}

function buildPayload() {
  return {
    experiment_name: form.experimentName.trim(),
    simulation_duration: Number(form.simulationDuration),
    total_patients: Number(form.totalPatients),
    demographics: form.demographics.map((item) => ({
      demographic: item.demographic.trim(),
      percentage: Number(item.percentage)
    })),
    events: form.events.map((item) => ({
      name: item.name.trim(),
      source: item.source
    })),
    targets: form.targets.map((item) => ({
      vital_sign: item.vital_sign,
      target_name: item.target_name.trim(),
      target_value: Number(item.target_value),
      tolerance: Number(item.tolerance)
    }))
  }
}

async function submitExperiment() {
  errorMessage.value = ''
  successMessage.value = ''

  const validationError = validateForm()
  if (validationError) {
    errorMessage.value = validationError
    return
  }

  loading.value = true

  try {
    const payload = buildPayload()
    //Sends the experiment configuration to the backend API to create a new experiment
    const response = await fetch(API_ENDPOINT, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    })

    if (!response.ok) {
      const text = await response.text()
      throw new Error(text || 'Failed to create experiment.')
    }

    successMessage.value = 'Experiment created successfully.'
    router.push('/')
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : 'Unknown error.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="page">
    <main class="content">

      <div class="layout">
        <section class="left-column">
          <div class="panel">
            <div class="field">
              <label>Experiment Name</label>
              <input v-model="form.experimentName" type="text" placeholder="Experiment Name" />
            </div>

            <div class="field">
              <label>Simulation Duration</label>
              <input
                v-model="form.simulationDuration"
                type="number"
                min="1"
                placeholder="Simulation duration"
              />
            </div>
          </div>

          <div class="panel tall">
            <h2>Event Configuration</h2>

            <div
              v-for="(event, index) in form.events"
              :key="`event-${index}`"
              class="row-block"
            >
              <input
                v-model="event.name"
                type="text"
                placeholder="Event name"
              />

              <select v-model="event.source">
                <option value="html">Use the html's version</option>
                <option value="api">Use API version</option>
              </select>

              <button class="remove-btn" @click="removeEvent(index)">Remove</button>
            </div>

            <button class="add-btn" @click="addEvent">+ Add new event</button>
          </div>
        </section>

        <section class="right-column">
          <div class="panel">
            <div class="section-header split">
              <h2>Patient Configuration</h2>

              <div class="field small">
                <label>Total number of patients</label>
                <input
                  v-model="form.totalPatients"
                  type="number"
                  min="1"
                  placeholder="Total number of patients"
                />
              </div>
            </div>

            <div
              v-for="(item, index) in form.demographics"
              :key="`demo-${index}`"
              class="grid-two demographic-row"
            >
              <select v-model="item.demographic">
                <option disabled value="">Select demographic</option>
                <option
                  v-for="option in availableDemographics"
                  :key="option"
                  :value="option"
                >
                  {{ option }}
                </option>
              </select>

              <div class="percentage-wrap">
                <input
                  v-model="item.percentage"
                  type="number"
                  min="0"
                  max="100"
                  placeholder="Percentage"
                />
                <button class="remove-btn small-btn" @click="removeDemographic(index)">
                  Remove
                </button>
              </div>
            </div>

            <div class="helper-text">
              Total percentage: {{ demographicTotal }}%
            </div>

            <button class="add-btn" @click="addDemographic">+ Select new demographic</button>
          </div>

          <div class="panel">
            <h2>Target Configuration</h2>

            <div
              v-for="(target, index) in form.targets"
              :key="`target-${index}`"
              class="target-grid"
            >
              <select v-model="target.vital_sign">
                <option disabled value="">Vital</option>
                <option
                  v-for="vital in availableVitals"
                  :key="vital.value"
                  :value="vital.value"
                >
                  {{ vital.label }}
                </option>
              </select>

              <input
                v-model="target.target_name"
                type="text"
                placeholder="Target Name"
              />

              <input
                v-model="target.target_value"
                type="number"
                step="any"
                placeholder="Target Value"
              />

              <div class="tolerance-wrap">
                <input
                  v-model="target.tolerance"
                  type="number"
                  step="any"
                  placeholder="Tolerance"
                />
                <button class="remove-btn small-btn" @click="removeTarget(index)">
                  Remove
                </button>
              </div>
            </div>

            <button class="add-btn" @click="addTarget">+ Select new target</button>
          </div>
        </section>
      </div>

      <div v-if="errorMessage" class="message error">
        {{ errorMessage }}
      </div>

      <div v-if="successMessage" class="message success">
        {{ successMessage }}
      </div>

      <footer class="bottom-actions">


      </footer>
    </main>
  </div>
</template>

<style scoped>
.page {
  min-height: 100vh;
  background: #060606;
  color: white;
}

.content {
  padding: 18px 20px 20px;
}

.topbar {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 14px;
}

.topbar h1 {
  font-size: 18px;
  margin: 0;
}

.layout {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 18px;
}

.left-column,
.right-column {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.panel {
  background: linear-gradient(180deg, #1a1a1d 0%, #17171a 100%);
  border: 1px solid #2d2d33;
  border-radius: 14px;
  padding: 16px;
}

.tall {
  min-height: 310px;
}

.section-header.split {
  display: flex;
  gap: 16px;
  align-items: flex-start;
  justify-content: space-between;
}

h2 {
  margin: 0 0 14px;
  font-size: 18px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 12px;
}

.field.small {
  min-width: 260px;
  margin-bottom: 0;
}

label {
  font-size: 12px;
  color: #cfcfcf;
  font-weight: 700;
}

input,
select {
  width: 100%;
  box-sizing: border-box;
  background: #3a3a3d;
  border: 1px solid #444;
  color: white;
  border-radius: 12px;
  padding: 12px 14px;
  font-size: 14px;
  outline: none;
}

input::placeholder {
  color: #c4c4c4;
}

.row-block {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 12px;
}

.grid-two {
  display: grid;
  grid-template-columns: 1fr 180px;
  gap: 16px;
}

.demographic-row {
  margin-bottom: 12px;
}

.percentage-wrap,
.tolerance-wrap {
  display: flex;
  gap: 8px;
  align-items: center;
}

.target-grid {
  display: grid;
  grid-template-columns: 180px 1fr 160px 220px;
  gap: 12px;
  margin-bottom: 12px;
}

.add-btn,
.remove-btn,
.primary-btn,
.secondary-btn {
  border: none;
  border-radius: 14px;
  cursor: pointer;
  font-weight: 700;
}

.add-btn {
  background: #404046;
  color: white;
  padding: 10px 14px;
  align-self: flex-start;
}

.remove-btn {
  background: #5a2a2a;
  color: #ffd2d2;
  padding: 10px 12px;
}

.small-btn {
  white-space: nowrap;
}

.helper-text {
  font-size: 12px;
  color: #bdbdbd;
  margin-bottom: 12px;
}

.message {
  margin-top: 16px;
  padding: 12px 14px;
  border-radius: 12px;
  font-size: 14px;
}

.message.error {
  background: #4a1f1f;
  color: #ffd6d6;
}

.message.success {
  background: #1f4a31;
  color: #d6ffe7;
}

.bottom-actions {
  display: flex;
  gap: 12px;
  margin-top: 20px;
}

.primary-btn {
  background: #4a4a50;
  color: white;
  padding: 12px 18px;
}

.secondary-btn {
  background: #4a4a50;
  color: white;
  padding: 12px 18px;
}

.primary-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

@media (max-width: 1200px) {
  .layout {
    grid-template-columns: 1fr;
  }

  .target-grid {
    grid-template-columns: 1fr;
  }

  .grid-two {
    grid-template-columns: 1fr;
  }

  .section-header.split {
    flex-direction: column;
  }

  .field.small {
    min-width: 0;
    width: 100%;
  }
}
</style>