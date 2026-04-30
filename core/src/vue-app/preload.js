import { contextBridge, ipcRenderer } from 'electron'

contextBridge.exposeInMainWorld('electronAPI', {
  exitApp: () => ipcRenderer.send('exit-app')
})
