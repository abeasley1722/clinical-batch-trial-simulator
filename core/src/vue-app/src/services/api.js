async function request(url, options = {}) {
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    ...options
  })

  const data = await res.json()

  if (!res.ok) throw new Error(data?.message || 'API error')

  return data
}

export const api = {
  getExperiments() {
    return request('/api/experiments')
  },

  getExperimentData(id) {
    return request(`/api/experiments/${id}`)
  },

  runSimulation(payload) {
    return request('/api/run', {
      method: 'POST',
      body: JSON.stringify(payload)
    })
  }
}