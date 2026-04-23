const BASE_URL = 'http://localhost:8080'

export async function runSimulation(payload) {
  const res = await fetch(`${BASE_URL}/api/submit_batch`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })

  if (!res.ok) throw new Error('Simulation failed')

  return res.json()
}