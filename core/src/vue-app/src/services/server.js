import { ref } from 'vue'

export const serverUrl = ref(`http://${window.location.hostname}:8080`)
export const connectionStatus = ref('disconnected') // 'disconnected' | 'connecting' | 'connected' | 'error'

export async function connectToServer(url) {
  let target = (url ?? serverUrl.value).trim().replace(/\/+$/, '')
  if (!/^https?:\/\//i.test(target)) target = 'http://' + target
  serverUrl.value = target
  connectionStatus.value = 'connecting'
  try {
    const res = await fetch(`${target}/api/available_variables`)
    if (!res.ok) throw new Error('Server returned non-OK status')
    connectionStatus.value = 'connected'
  } catch {
    connectionStatus.value = 'error'
  }
}
