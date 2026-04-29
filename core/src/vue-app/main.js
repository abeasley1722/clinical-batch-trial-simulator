import { app, BrowserWindow } from 'electron'
import path from 'path'
import { fileURLToPath } from 'url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

let win

function createWindow() {
  win = new BrowserWindow({
    width: 1200,
    height: 800,
    title: 'Clinical Batch Trial Simulator',
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false
    }
  })

  if (!app.isPackaged) {
    win.loadURL('http://localhost:5173/')
    win.webContents.openDevTools()
  } else {
    const indexPath = path.join(app.getAppPath(), 'dist/index.html')
    win.loadFile(indexPath)
  }

  win.on('closed', () => {
    win = null
  })
}

app.whenReady().then(() => {
  createWindow()

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow()
    }
  })
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})