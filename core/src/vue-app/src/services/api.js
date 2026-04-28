const BASE_URL = 'http://localhost:8080'

// ========================
// REQUEST HELPER (FIXES YOUR ERROR)
// ========================
async function request(url, options = {}) {
  const res = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {})
    },
    ...options
  })

  const contentType = res.headers.get('content-type') || ''

  let data
  if (contentType.includes('application/json')) {
    data = await res.json()
  } else {
    data = await res.text()
  }

  if (!res.ok) {
    throw new Error(
      typeof data === 'object'
        ? JSON.stringify(data)
        : data || 'API request failed'
    )
  }

  return data
}

// ========================
// BATCH EXECUTION
// ========================
export async function runSimulation(payload) {
  const res = await fetch(`${BASE_URL}/api/submit_batch`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })

  const data = await res.json()

  if (!res.ok) {
    throw new Error(`Simulation failed: ${JSON.stringify(data)}`)
  }

  console.log('Simulation submitted:', data)

  return data // { batch_id }
}

// ========================
// BATCHES
// ========================
export async function getBatchStatus(batchId) {
  const res = await fetch(`${BASE_URL}/api/batch_status/${batchId}`)

  if (!res.ok) {
    throw new Error('Failed to fetch batch status')
  }

  return res.json()
}

export function getBatch(batchId) {
  return request(`${BASE_URL}/api/batches/${batchId}`)
}

export function getBatchesByExperiment(experimentId) {
  return request(`${BASE_URL}/api/batches/by_experiment/${experimentId}`)
}

export function getBatchesByPatient(patientId) {
  return request(`${BASE_URL}/api/batches/by_patient/${patientId}`)
}

export async function cancelBatch(batchId) {
  const res = await fetch(`${BASE_URL}/api/cancel_batch/${batchId}`, {
    method: 'POST'
  })

  if (!res.ok) {
    throw new Error('Failed to cancel batch')
  }

  return res.json()
}

// ========================
// EXPERIMENTS
// ========================
export function getExperiments() {
  return request(`${BASE_URL}/api/experiments`)
}

export function getExperiment(experimentId) {
  return request(`${BASE_URL}/api/experiments/${experimentId}`)
}

// ========================
// METRICS (FOR SIDE PANEL)
// ========================
export function getMetricsByExperiment(experimentId) {
  return request(`${BASE_URL}/api/metrics/by_experiment/${experimentId}`)
}

// ========================
// PATIENTS
// ========================
export function getPatients() {
  return request(`${BASE_URL}/api/patients`)
}

export function getPatient(patientId) {
  return request(`${BASE_URL}/api/patients/${patientId}`)
}

export function getPatientsByCohort(cohortId) {
  return request(`${BASE_URL}/api/patients/by_cohort/${cohortId}`)
}

// ========================
// 🔥 RETRIEVAL (FOR CHARTS — MOST IMPORTANT)
// ========================
export function getMetricsDataframe(experimentId) {
  return request(`${BASE_URL}/api/retrieval/metrics/${experimentId}`)
}

export function getRawCSVPaths(experimentId) {
  return request(`${BASE_URL}/api/retrieval/raw_csv_paths/${experimentId}`)
}

export function getRawCSVData(experimentId) {
  return request(`${BASE_URL}/api/retrieval/raw_csv/${experimentId}`)
}

// ========================
// MISC
// ========================
export function getAvailableVariables() {
  return request(`${BASE_URL}/api/available_variables`)
}

export function testHttpController(payload) {
  return request(`${BASE_URL}/api/test_http_controller`, {
    method: 'POST',
    body: JSON.stringify(payload)
  })
}